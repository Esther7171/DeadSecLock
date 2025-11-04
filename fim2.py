#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DLP File Monitor Service
Monitors tagged files using Windows minifilter driver approach
Runs as a Windows service with real-time monitoring
"""

import os
import sys
import sqlite3
import hashlib
import json
import time
import threading
from datetime import datetime
from pathlib import Path
import win32file
import win32con
import pywintypes
import win32api
import win32security
import ntsecuritycon as con

# Flask for web dashboard
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit

PROGRAMDATA = os.environ.get("PROGRAMDATA", r"C:\ProgramData")
DB_DIR = os.path.join(PROGRAMDATA, "DLP")
DB_PATH = os.path.join(DB_DIR, "dlp.db")
EVENTS_DB = os.path.join(DB_DIR, "events.db")
ADS_NAME = "dlp"

# Flask app for web dashboard
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dlp-secret-key-change-in-production'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global monitoring state
monitoring_active = False
monitor_thread = None
file_handles = {}

# ============================================================================
# Database Functions
# ============================================================================

def ensure_db():
    """Ensure DLP database exists"""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS files (
        sha256 TEXT UNIQUE,
        label TEXT,
        example_path TEXT,
        monitored INTEGER DEFAULT 1
    )
    """)
    conn.commit()
    return conn

def ensure_events_db():
    """Create events database for logging all file operations"""
    conn = sqlite3.connect(EVENTS_DB)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        event_type TEXT,
        file_path TEXT,
        new_path TEXT,
        label TEXT,
        sha256 TEXT,
        user TEXT,
        details TEXT
    )
    """)
    conn.commit()
    return conn

def log_event(event_type, file_path, label, sha256, new_path=None, details=None):
    """Log file event to database and send to web dashboard"""
    try:
        import getpass
        user = getpass.getuser()
    except:
        user = "SYSTEM"
    
    timestamp = datetime.now().isoformat()
    
    conn = ensure_events_db()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO events (timestamp, event_type, file_path, new_path, label, sha256, user, details)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, event_type, file_path, new_path, label, sha256, user, details))
    conn.commit()
    conn.close()
    
    # Send to web dashboard
    event_data = {
        'timestamp': timestamp,
        'event_type': event_type,
        'file_path': file_path,
        'new_path': new_path,
        'label': label,
        'user': user,
        'details': details
    }
    socketio.emit('file_event', event_data)
    
    print(f"[{timestamp}] {event_type}: {file_path} ({label})")

def sha256_file(path, block_size=4*1024*1024):
    """Calculate SHA256 hash of file"""
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while True:
                data = f.read(block_size)
                if not data:
                    break
                h.update(data)
        return h.hexdigest()
    except Exception as e:
        return None

def read_ads(path):
    """Read ADS tag from file"""
    try:
        with open(f"{path}:{ADS_NAME}", "r", encoding="utf-8") as ads:
            return ads.read().strip()
    except:
        return None

def write_ads(path, label):
    """Write ADS tag to file"""
    try:
        with open(f"{path}:{ADS_NAME}", "w", encoding="utf-8") as ads:
            ads.write(label)
        return True
    except:
        return False

def is_monitored_file(path):
    """Check if file is monitored based on ADS or DB"""
    ads_label = read_ads(path)
    if ads_label:
        return True, ads_label
    
    sha = sha256_file(path)
    if sha:
        conn = ensure_db()
        cur = conn.cursor()
        cur.execute("SELECT label FROM files WHERE sha256 = ? AND monitored = 1", (sha,))
        row = cur.fetchone()
        conn.close()
        if row:
            return True, row[0]
    
    return False, None

# ============================================================================
# File System Monitoring
# ============================================================================

class FileSystemMonitor:
    def __init__(self):
        self.watched_paths = set()
        self.stop_flag = threading.Event()
        
    def add_monitored_file(self, path):
        """Add file to monitoring list"""
        self.watched_paths.add(os.path.abspath(path))
        
    def scan_all_monitored_files(self):
        """Scan database for all monitored files"""
        conn = ensure_db()
        cur = conn.cursor()
        cur.execute("SELECT example_path FROM files WHERE monitored = 1")
        for row in cur.fetchall():
            if row[0] and os.path.exists(row[0]):
                self.add_monitored_file(row[0])
        conn.close()
        
    def monitor_directory(self, path):
        """Monitor a directory for changes using ReadDirectoryChangesW"""
        try:
            hDir = win32file.CreateFile(
                path,
                win32con.GENERIC_READ,
                win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
                None,
                win32con.OPEN_EXISTING,
                win32con.FILE_FLAG_BACKUP_SEMANTICS,
                None
            )
            
            while not self.stop_flag.is_set():
                try:
                    results = win32file.ReadDirectoryChangesW(
                        hDir,
                        1024,
                        True,  # Watch subtree
                        win32con.FILE_NOTIFY_CHANGE_FILE_NAME |
                        win32con.FILE_NOTIFY_CHANGE_DIR_NAME |
                        win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES |
                        win32con.FILE_NOTIFY_CHANGE_SIZE |
                        win32con.FILE_NOTIFY_CHANGE_LAST_WRITE,
                        None,
                        None
                    )
                    
                    for action, file_name in results:
                        full_path = os.path.join(path, file_name)
                        self.handle_file_change(action, full_path)
                        
                except pywintypes.error as e:
                    if e.winerror == 995:  # Operation aborted
                        break
                    time.sleep(1)
                    
        except Exception as e:
            print(f"Error monitoring {path}: {e}")
        finally:
            try:
                win32file.CloseHandle(hDir)
            except:
                pass
    
    def handle_file_change(self, action, file_path):
        """Handle file system change event"""
        # Check if file is monitored
        if os.path.isfile(file_path):
            is_monitored, label = is_monitored_file(file_path)
            if not is_monitored:
                return
            
            sha = sha256_file(file_path)
            
            # Map action to event type
            action_map = {
                1: "CREATED",
                2: "DELETED",
                3: "MODIFIED",
                4: "RENAMED_OLD",
                5: "RENAMED_NEW"
            }
            
            event_type = action_map.get(action, "UNKNOWN")
            
            # Log the event
            if event_type == "MODIFIED":
                log_event("FILE_MODIFIED", file_path, label, sha, details="File content changed")
            elif event_type == "CREATED":
                log_event("FILE_CREATED", file_path, label, sha, details="File created/copied")
                # Copy ADS tag if it's a monitored file
                write_ads(file_path, label)
            elif event_type == "DELETED":
                log_event("FILE_DELETED", file_path, label, sha, details="File deleted")
            elif event_type in ["RENAMED_OLD", "RENAMED_NEW"]:
                log_event("FILE_RENAMED", file_path, label, sha, details="File renamed/moved")
    
    def start_monitoring(self):
        """Start monitoring all drives"""
        self.scan_all_monitored_files()
        
        # Monitor all drives
        drives = [f"{d}:\\" for d in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" 
                  if os.path.exists(f"{d}:\\")]
        
        threads = []
        for drive in drives:
            t = threading.Thread(target=self.monitor_directory, args=(drive,))
            t.daemon = True
            t.start()
            threads.append(t)
        
        return threads
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.stop_flag.set()

# Global monitor instance
monitor = FileSystemMonitor()

# ============================================================================
# Web Dashboard Routes
# ============================================================================

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/events')
def get_events():
    """Get recent events"""
    limit = request.args.get('limit', 100, type=int)
    conn = ensure_events_db()
    cur = conn.cursor()
    cur.execute("""
    SELECT timestamp, event_type, file_path, new_path, label, user, details
    FROM events ORDER BY id DESC LIMIT ?
    """, (limit,))
    events = []
    for row in cur.fetchall():
        events.append({
            'timestamp': row[0],
            'event_type': row[1],
            'file_path': row[2],
            'new_path': row[3],
            'label': row[4],
            'user': row[5],
            'details': row[6]
        })
    conn.close()
    return jsonify(events)

@app.route('/api/monitored_files')
def get_monitored_files():
    """Get list of monitored files"""
    conn = ensure_db()
    cur = conn.cursor()
    cur.execute("SELECT sha256, label, example_path FROM files WHERE monitored = 1")
    files = []
    for row in cur.fetchall():
        files.append({
            'sha256': row[0],
            'label': row[1],
            'path': row[2]
        })
    conn.close()
    return jsonify(files)

@app.route('/api/monitoring/status')
def monitoring_status():
    """Get monitoring status"""
    return jsonify({
        'active': monitoring_active,
        'watched_files': len(monitor.watched_paths)
    })

@app.route('/api/monitoring/start', methods=['POST'])
def start_monitoring():
    """Start monitoring service"""
    global monitoring_active, monitor_thread
    if not monitoring_active:
        monitoring_active = True
        monitor_thread = threading.Thread(target=monitor.start_monitoring)
        monitor_thread.daemon = True
        monitor_thread.start()
        return jsonify({'success': True, 'message': 'Monitoring started'})
    return jsonify({'success': False, 'message': 'Already monitoring'})

@app.route('/api/monitoring/stop', methods=['POST'])
def stop_monitoring():
    """Stop monitoring service"""
    global monitoring_active
    if monitoring_active:
        monitoring_active = False
        monitor.stop_monitoring()
        return jsonify({'success': True, 'message': 'Monitoring stopped'})
    return jsonify({'success': False, 'message': 'Not monitoring'})

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('connected', {'data': 'Connected to DLP Monitor'})

# ============================================================================
# Main Entry Point
# ============================================================================

def run_web_server():
    """Run the web dashboard server"""
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)

if __name__ == "__main__":
    print("=" * 60)
    print("DLP File Monitor Service")
    print("=" * 60)
    
    # Ensure databases exist
    ensure_db()
    ensure_events_db()
    
    # Start monitoring automatically
    print("Starting file system monitoring...")
    monitoring_active = True
    monitor_threads = monitor.start_monitoring()
    
    print(f"Monitoring {len(monitor.watched_paths)} files")
    print("Web dashboard starting on http://localhost:5000")
    print("=" * 60)
    
    # Run web server
    run_web_server()
