#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced DLP Marker GUI with Integrated Monitoring
Mark files/folders and start real-time monitoring
"""

import os
import sys
import sqlite3
import hashlib
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import subprocess
import webbrowser
from datetime import datetime

PROGRAMDATA = os.environ.get("PROGRAMDATA", r"C:\ProgramData")
DB_DIR = os.path.join(PROGRAMDATA, "DLP")
DB_PATH = os.path.join(DB_DIR, "dlp.db")
EVENTS_DB = os.path.join(DB_DIR, "events.db")
ADS_NAME = "dlp"

# ============================================================================
# DLP Core Functions
# ============================================================================

def ensure_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS files (
        sha256 TEXT UNIQUE,
        label TEXT,
        example_path TEXT,
        monitored INTEGER DEFAULT 1,
        tagged_date TEXT
    )
    """)
    conn.commit()
    return conn

def ensure_events_db():
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

def sha256_file(path, block_size=4*1024*1024):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while True:
                data = f.read(block_size)
                if not data:
                    break
                h.update(data)
        return h.hexdigest()
    except Exception as e:
        print(f"Error hashing {path}: {e}")
        return None

def write_ads(path, label):
    try:
        with open(f"{path}:{ADS_NAME}", "w", encoding="utf-8") as ads:
            ads.write(label)
        return True
    except Exception as e:
        print(f"Error writing ADS to {path}: {e}")
        return False

def read_ads(path):
    try:
        with open(f"{path}:{ADS_NAME}", "r", encoding="utf-8") as ads:
            return ads.read().strip()
    except:
        return None

def remove_ads(path):
    try:
        os.remove(f"{path}:{ADS_NAME}")
        return True
    except Exception:
        return False

def register_in_db(path, label):
    sha = sha256_file(path)
    if not sha:
        return False
    
    conn = ensure_db()
    cur = conn.cursor()
    cur.execute("""
    INSERT OR REPLACE INTO files (sha256, label, example_path, monitored, tagged_date)
    VALUES (?, ?, ?, 1, ?)
    """, (sha, label, path, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return True

def remove_from_db(path):
    sha = sha256_file(path)
    if not sha:
        return False
    
    conn = ensure_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM files WHERE sha256 = ?", (sha,))
    conn.commit()
    conn.close()
    return True

def check_marker(path):
    ads = read_ads(path)
    sha = sha256_file(path)
    if not sha:
        return None, None
    
    conn = ensure_db()
    cur = conn.cursor()
    cur.execute("SELECT label FROM files WHERE sha256 = ?", (sha,))
    row = cur.fetchone()
    conn.close()
    return ads, row[0] if row else None

def mark_folder_recursive(folder_path, label, progress_callback=None):
    """Recursively mark all files in a folder"""
    marked_count = 0
    failed_count = 0
    
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                if write_ads(file_path, label):
                    if register_in_db(file_path, label):
                        marked_count += 1
                        if progress_callback:
                            progress_callback(file_path, marked_count, failed_count)
                    else:
                        failed_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                failed_count += 1
                print(f"Error marking {file_path}: {e}")
    
    return marked_count, failed_count

def get_monitored_files_count():
    """Get count of monitored files"""
    conn = ensure_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM files WHERE monitored = 1")
    count = cur.fetchone()[0]
    conn.close()
    return count

def get_recent_events(limit=10):
    """Get recent events"""
    try:
        conn = ensure_events_db()
        cur = conn.cursor()
        cur.execute("""
        SELECT timestamp, event_type, file_path, label
        FROM events ORDER BY id DESC LIMIT ?
        """, (limit,))
        events = cur.fetchall()
        conn.close()
        return events
    except:
        return []

# ============================================================================
# Enhanced GUI Application
# ============================================================================

class EnhancedDLPApp:
    def __init__(self, root):
        self.root = root
        root.title("🛡️ Enhanced DLP Marker & Monitor")
        root.geometry("800x700")
        root.resizable(False, False)
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        self.file_path = tk.StringVar()
        self.label_choice = tk.StringVar(value="confidential")
        self.monitoring_active = tk.BooleanVar(value=False)
        
        self.create_widgets()
        self.update_stats()
        
    def create_widgets(self):
        # Header
        header = tk.Frame(self.root, bg="#667eea", height=80)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(header, text="🛡️ DLP Marker & Monitor",
                font=("Segoe UI", 20, "bold"), bg="#667eea", fg="white").pack(pady=20)
        
        # Main container
        main_frame = tk.Frame(self.root, bg="white")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # File Selection Section
        file_section = tk.LabelFrame(main_frame, text="  📁 File/Folder Selection  ",
                                     font=("Segoe UI", 11, "bold"), bg="white",
                                     relief="solid", borderwidth=1)
        file_section.pack(fill="x", pady=(0, 15))
        
        file_frame = tk.Frame(file_section, bg="white")
        file_frame.pack(padx=10, pady=10, fill="x")
        
        tk.Entry(file_frame, textvariable=self.file_path, width=60,
                font=("Segoe UI", 10)).pack(side="left", padx=(0, 10))
        tk.Button(file_frame, text="Browse File", command=self.browse_file,
                 bg="#4CAF50", fg="white", font=("Segoe UI", 9, "bold"),
                 relief="flat", padx=15, pady=5).pack(side="left", padx=2)
        tk.Button(file_frame, text="Browse Folder", command=self.browse_folder,
                 bg="#2196F3", fg="white", font=("Segoe UI", 9, "bold"),
                 relief="flat", padx=15, pady=5).pack(side="left")
        
        # Label Selection Section
        label_section = tk.LabelFrame(main_frame, text="  🏷️ Sensitivity Label  ",
                                      font=("Segoe UI", 11, "bold"), bg="white",
                                      relief="solid", borderwidth=1)
        label_section.pack(fill="x", pady=(0, 15))
        
        label_frame = tk.Frame(label_section, bg="white")
        label_frame.pack(padx=10, pady=10)
        
        labels = [
            ("confidential", "#e74c3c"),
            ("secret", "#c0392b"),
            ("internal", "#f39c12"),
            ("restricted", "#e67e22")
        ]
        
        for label, color in labels:
            rb = tk.Radiobutton(label_frame, text=label.upper(), variable=self.label_choice,
                               value=label, bg="white", font=("Segoe UI", 10, "bold"),
                               fg=color, selectcolor="white", activebackground="white")
            rb.pack(side="left", padx=15)
        
        # Action Buttons Section
        action_section = tk.LabelFrame(main_frame, text="  ⚡ Actions  ",
                                       font=("Segoe UI", 11, "bold"), bg="white",
                                       relief="solid", borderwidth=1)
        action_section.pack(fill="x", pady=(0, 15))
        
        btn_frame = tk.Frame(action_section, bg="white")
        btn_frame.pack(padx=10, pady=10)
        
        tk.Button(btn_frame, text="🏷️ Mark File/Folder", command=self.mark_file,
                 bg="#4CAF50", fg="white", font=("Segoe UI", 10, "bold"),
                 relief="flat", padx=25, pady=10, width=20).pack(pady=5)
        tk.Button(btn_frame, text="🔍 Check Marker", command=self.check_file,
                 bg="#2196F3", fg="white", font=("Segoe UI", 10, "bold"),
                 relief="flat", padx=25, pady=10, width=20).pack(pady=5)
        tk.Button(btn_frame, text="🗑️ Remove Marker", command=self.remove_marker,
                 bg="#F44336", fg="white", font=("Segoe UI", 10, "bold"),
                 relief="flat", padx=25, pady=10, width=20).pack(pady=5)
        
        # Monitoring Section
        monitor_section = tk.LabelFrame(main_frame, text="  📡 Real-Time Monitoring  ",
                                        font=("Segoe UI", 11, "bold"), bg="white",
                                        relief="solid", borderwidth=1)
        monitor_section.pack(fill="x", pady=(0, 15))
        
        monitor_frame = tk.Frame(monitor_section, bg="white")
        monitor_frame.pack(padx=10, pady=10)
        
        self.monitor_status_label = tk.Label(monitor_frame, text="⚫ Monitoring Inactive",
                                             font=("Segoe UI", 10), bg="white", fg="#e74c3c")
        self.monitor_status_label.pack(pady=5)
        
        tk.Button(monitor_frame, text="▶️ Start Monitor Service",
                 command=self.start_monitoring,
                 bg="#2ecc71", fg="white", font=("Segoe UI", 10, "bold"),
                 relief="flat", padx=20, pady=8).pack(pady=5)
        
        tk.Button(monitor_frame, text="🌐 Open Web Dashboard",
                 command=self.open_dashboard,
                 bg="#667eea", fg="white", font=("Segoe UI", 10, "bold"),
                 relief="flat", padx=20, pady=8).pack(pady=5)
        
        # Statistics Section
        stats_section = tk.LabelFrame(main_frame, text="  📊 Statistics  ",
                                      font=("Segoe UI", 11, "bold"), bg="white",
                                      relief="solid", borderwidth=1)
        stats_section.pack(fill="both", expand=True)
        
        stats_frame = tk.Frame(stats_section, bg="white")
        stats_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        self.stats_text = tk.Text(stats_frame, height=6, width=70,
                                  font=("Segoe UI", 9), bg="#f8f9fa",
                                  relief="flat", padx=10, pady=10)
        self.stats_text.pack(fill="both", expand=True)
        
        # Status bar
        self.status = tk.Label(self.root, text="Ready", bg="#f0f0f0",
                              font=("Segoe UI", 9), anchor="w", padx=10, pady=5)
        self.status.pack(side="bottom", fill="x")
    
    def browse_file(self):
        file = filedialog.askopenfilename(title="Select File to Mark")
        if file:
            self.file_path.set(file)
    
    def browse_folder(self):
        folder = filedialog.askdirectory(title="Select Folder to Mark")
        if folder:
            self.file_path.set(folder)
    
    def mark_file(self):
        path = self.file_path.get().strip()
        label = self.label_choice.get().strip()
        
        if not path:
            messagebox.showerror("Error", "Please select a file or folder first.")
            return
        if not os.path.exists(path):
            messagebox.showerror("Error", "Path not found.")
            return
        
        self.status.config(text="Marking files...", fg="blue")
        self.root.update()
        
        try:
            if os.path.isfile(path):
                # Mark single file
                write_ads(path, label)
                register_in_db(path, label)
                self.status.config(text=f"✅ File marked as '{label}' successfully.", fg="green")
                messagebox.showinfo("Success", f"File marked as '{label}'")
            else:
                # Mark folder recursively
                result = messagebox.askyesno("Mark Folder",
                    f"This will mark ALL files in the folder recursively with label '{label}'.\n\nContinue?")
                if result:
                    progress_window = tk.Toplevel(self.root)
                    progress_window.title("Marking Files...")
                    progress_window.geometry("400x150")
                    progress_window.resizable(False, False)
                    
                    tk.Label(progress_window, text="Marking files, please wait...",
                            font=("Segoe UI", 11)).pack(pady=20)
                    
                    progress_label = tk.Label(progress_window, text="Files marked: 0",
                                            font=("Segoe UI", 10))
                    progress_label.pack(pady=10)
                    
                    def update_progress(file_path, marked, failed):
                        progress_label.config(text=f"Files marked: {marked} | Failed: {failed}")
                        progress_window.update()
                    
                    def mark_thread():
                        marked, failed = mark_folder_recursive(path, label, update_progress)
                        progress_window.destroy()
                        messagebox.showinfo("Complete",
                            f"Folder marking complete!\n\nMarked: {marked}\nFailed: {failed}")
                        self.status.config(text=f"✅ Folder marked: {marked} files", fg="green")
                        self.update_stats()
                    
                    threading.Thread(target=mark_thread, daemon=True).start()
            
            self.update_stats()
            
        except Exception as e:
            self.status.config(text=f"❌ Error: {e}", fg="red")
            messagebox.showerror("Error", str(e))
    
    def check_file(self):
        path = self.file_path.get().strip()
        if not path:
            messagebox.showerror("Error", "Select a file first.")
            return
        if not os.path.exists(path):
            messagebox.showerror("Error", "File not found.")
            return
        
        ads, db = check_marker(path)
        if ads or db:
            msg = f"ADS Tag: {ads or 'None'}\nDB Label: {db or 'None'}"
            messagebox.showinfo("Marker Info", msg)
            self.status.config(text=f"ℹ️ File has marker: {ads or db}", fg="blue")
        else:
            messagebox.showinfo("Marker Info", "No DLP marker found.")
            self.status.config(text="ℹ️ No marker found.", fg="gray")
    
    def remove_marker(self):
        path = self.file_path.get().strip()
        if not path:
            messagebox.showerror("Error", "Select a file first.")
            return
        if not os.path.exists(path):
            messagebox.showerror("Error", "File not found.")
            return
        
        result = messagebox.askyesno("Confirm", "Remove DLP marker from this file?")
        if not result:
            return
        
        try:
            remove_ads(path)
            remove_from_db(path)
            self.status.config(text="🧹 Marker removed successfully.", fg="green")
            self.update_stats()
        except Exception as e:
            self.status.config(text=f"❌ Error: {e}", fg="red")
    
    def start_monitoring(self):
        """Start the monitoring service"""
        try:
            # Check if monitor script exists
            monitor_script = os.path.join(os.path.dirname(__file__), "dlp_monitor_service.py")
            
            if not os.path.exists(monitor_script):
                messagebox.showerror("Error",
                    "Monitor service script not found!\n\n"
                    "Please ensure 'dlp_monitor_service.py' is in the same directory.")
                return
            
            # Start monitor as subprocess
            subprocess.Popen([sys.executable, monitor_script],
                           creationflags=subprocess.CREATE_NO_WINDOW)
            
            self.monitor_status_label.config(text="🟢 Monitoring Active", fg="#2ecc71")
            self.status.config(text="✅ Monitoring service started", fg="green")
            
            messagebox.showinfo("Monitoring Started",
                "DLP monitoring service is now running!\n\n"
                "Open the web dashboard to view real-time events.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start monitoring:\n{e}")
            self.status.config(text=f"❌ Failed to start monitoring", fg="red")
    
    def open_dashboard(self):
        """Open web dashboard in browser"""
        webbrowser.open("http://localhost:5000")
        self.status.config(text="🌐 Opening web dashboard...", fg="blue")
    
    def update_stats(self):
        """Update statistics display"""
        count = get_monitored_files_count()
        events = get_recent_events(5)
        
        stats_text = f"📊 Monitored Files: {count}\n\n"
        stats_text += "📜 Recent Events:\n"
        
        if events:
            for timestamp, event_type, file_path, label in events:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                file_name = os.path.basename(file_path)
                stats_text += f"  • [{time_str}] {event_type}: {file_name}\n"
        else:
            stats_text += "  No events yet\n"
        
        self.stats_text.delete("1.0", tk.END)
        self.stats_text.insert("1.0", stats_text)

# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    # Ensure databases exist
    ensure_db()
    ensure_events_db()
    
    root = tk.Tk()
    app = EnhancedDLPApp(root)
    root.mainloop()
