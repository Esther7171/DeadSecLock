#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DLP Marker GUI
Mark or unmark files as sensitive on Windows using NTFS ADS + SQLite DB
"""

import os
import sqlite3
import hashlib
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

PROGRAMDATA = os.environ.get("PROGRAMDATA", r"C:\ProgramData")
DB_DIR = os.path.join(PROGRAMDATA, "DLP")
DB_PATH = os.path.join(DB_DIR, "dlp.db")
ADS_NAME = "dlp"

# --- DLP Logic ---------------------------------------------------------

def ensure_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS files (
        sha256 TEXT UNIQUE,
        label TEXT,
        example_path TEXT
    )
    """)
    conn.commit()
    return conn

def sha256_file(path, block_size=4*1024*1024):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            data = f.read(block_size)
            if not data:
                break
            h.update(data)
    return h.hexdigest()

def write_ads(path, label):
    with open(f"{path}:{ADS_NAME}", "w", encoding="utf-8") as ads:
        ads.write(label)

def read_ads(path):
    try:
        with open(f"{path}:{ADS_NAME}", "r", encoding="utf-8") as ads:
            return ads.read().strip()
    except FileNotFoundError:
        return None
    except PermissionError:
        return None

def remove_ads(path):
    try:
        os.remove(f"{path}:{ADS_NAME}")
        return True
    except Exception:
        return False

def register_in_db(path, label):
    sha = sha256_file(path)
    conn = ensure_db()
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO files (sha256, label, example_path) VALUES (?, ?, ?)",
                (sha, label, path))
    conn.commit()
    conn.close()

def remove_from_db(path):
    sha = sha256_file(path)
    conn = ensure_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM files WHERE sha256 = ?", (sha,))
    conn.commit()
    conn.close()

def check_marker(path):
    ads = read_ads(path)
    conn = ensure_db()
    sha = sha256_file(path)
    cur = conn.cursor()
    cur.execute("SELECT label FROM files WHERE sha256 = ?", (sha,))
    row = cur.fetchone()
    conn.close()
    return ads, row[0] if row else None

# --- GUI ---------------------------------------------------------------

class DLPApp:
    def __init__(self, root):
        self.root = root
        root.title("🛡️ Windows DLP Marker Tool")
        root.geometry("520x300")
        root.resizable(False, False)

        self.file_path = tk.StringVar()
        self.label_choice = tk.StringVar(value="confidential")

        tk.Label(root, text="Select File:", font=("Segoe UI", 10, "bold")).pack(pady=10)
        frm = tk.Frame(root)
        frm.pack()
        tk.Entry(frm, textvariable=self.file_path, width=55).pack(side="left", padx=5)
        tk.Button(frm, text="Browse", command=self.browse_file).pack(side="left")

        tk.Label(root, text="Select Sensitivity Label:", font=("Segoe UI", 10, "bold")).pack(pady=10)
        ttk.Combobox(root, textvariable=self.label_choice, values=[
            "confidential", "secret", "internal", "restricted"
        ], width=30, state="readonly").pack()

        tk.Button(root, text="Mark File", command=self.mark_file, bg="#4CAF50", fg="white", width=20).pack(pady=10)
        tk.Button(root, text="Check Marker", command=self.check_file, bg="#2196F3", fg="white", width=20).pack(pady=5)
        tk.Button(root, text="Remove Marker", command=self.remove_marker, bg="#F44336", fg="white", width=20).pack(pady=5)

        self.status = tk.Label(root, text="", fg="gray", wraplength=480, justify="center")
        self.status.pack(pady=10)

    def browse_file(self):
        file = filedialog.askopenfilename(title="Select File to Mark")
        if file:
            self.file_path.set(file)

    def mark_file(self):
        path = self.file_path.get().strip()
        label = self.label_choice.get().strip()
        if not path:
            messagebox.showerror("Error", "Please select a file first.")
            return
        if not os.path.exists(path):
            messagebox.showerror("Error", "File not found.")
            return
        try:
            write_ads(path, label)
            register_in_db(path, label)
            self.status.config(text=f"✅ File marked as '{label}' successfully.", fg="green")
        except Exception as e:
            self.status.config(text=f"❌ Error marking file: {e}", fg="red")

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
            self.status.config(text=f"ℹ️ File status checked.\n{msg}", fg="blue")
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
        try:
            remove_ads(path)
            remove_from_db(path)
            self.status.config(text="🧹 Marker removed successfully.", fg="green")
        except Exception as e:
            self.status.config(text=f"❌ Error removing marker: {e}", fg="red")

# --- Run GUI -----------------------------------------------------------

if __name__ == "__main__":
    root = tk.Tk()
    app = DLPApp(root)
    root.mainloop()
