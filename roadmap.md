## ✅ PHASE 1: SYSTEM DESIGN & GOAL MAPPING

### 🎯 Core Goals Recap

| Feature                          | Goal                           |
| -------------------------------- | ------------------------------ |
| File Monitoring (all ops)        | ✅ Real-time                    |
| Agent Info (group, dept, mail)   | ✅ Optional metadata            |
| Event Filtering & De-duplication | ✅ Avoid flood logs             |
| Alert Engine (Slack, Telegram)   | ✅ Prioritized alerts           |
| Upload Blocking & Enforcement    | ✅ Revoker system               |
| Template & Fingerprint Control   | ✅ Hash, SimHash, Pattern match |
| Clipboard & Screenshot Monitor   | ✅ Sensitive monitoring         |
| Daily PDF Reports                | ✅ Summary reports              |
| USB/Port Controller              | ✅ Access enforcement           |
| Future Dashboard Integration     | ✅ Postpone UI dev              |
| Production-level Engineering     | ✅ Scalable, secure, modular    |

---

## 🏗️ PHASE 2: UPDATED ARCHITECTURE

### 📁 Suggested Directory Structure

```
DeadSecLock/
├── dlp_core/
│   ├── monitor/                    # Real-time file + clipboard + screen
│   │   ├── file_monitor.py
│   │   ├── clipboard_monitor.py
│   │   ├── screen_capture.py
│   │   └── usb_control.py
│   ├── analysis/                  # Intelligence layer
│   │   ├── event_filter.py        # Deduplication, file-time span
│   │   ├── fingerprint_engine.py  # Hash + similarity detection
│   │   ├── pattern_detector.py    # Regex-based DLP
│   ├── enforcement/
│   │   ├── revoker.py             # Remove perms to block upload
│   │   ├── upload_blocker.py      # Web/email/ftp detection
│   ├── reporting/
│   │   ├── pdf_reporter.py
│   │   ├── logger.py              # Slack, Telegram, local logs
│   │   └── reporter_engine.py     # Message formatter
│   ├── config/
│   │   ├── agent_info.json        # Company, dept, email etc.
│   │   └── rules.yaml             # Whitelist/blacklist templates
│   └── utils/
│       ├── hash_utils.py
│       ├── id_gen.py
│       ├── time_utils.py
│       └── path_utils.py
│
├── gui/
│   ├── app.py
│   └── dashboard.py (later)
│
├── installer/
│   └── pyinstaller.spec
├── logs/
│   ├── dlp.log
│   └── events.db (sqlite/localstore)
├── tests/
├── requirements.txt
└── README.md
```

---

## 🧠 PHASE 3: EVENT LOGIC & BACKEND ENGINE

### 🔍 Real-time File Monitor Logic (`file_monitor.py`)

```python
# pseudo code logic for file tracking
EVENT_LOG = {}

def on_file_event(event):
    fpath = event.path
    current_hash = hash_file(fpath)
    timestamp = get_now()

    if fpath not in EVENT_LOG:
        EVENT_LOG[fpath] = {"hash": current_hash, "open": timestamp}
        log_event("open", fpath)
    else:
        old_hash = EVENT_LOG[fpath]["hash"]
        if current_hash != old_hash:
            log_event("modify", fpath)
            EVENT_LOG[fpath]["hash"] = current_hash

    # handle rename, move by path difference
    # handle file close using a timeout or OS hook
```

### 🧹 Flood Control + Analysis Engine (`event_filter.py`)

```python
# pseudo: suppress duplicate alerts unless file has major change
def should_alert(event_type, fpath):
    if recent_similar_event(fpath, within_minutes=5):
        return False
    return True
```

---

## 🔐 PHASE 4: ENFORCEMENT MECHANISMS

### 🛑 Upload Blocking (`revoker.py` + `upload_blocker.py`)

* Use `os.chmod()` or Windows ACL to restrict write/upload.
* Monitor common upload vectors:

  * Web Browsers (Inject Proxy or WinAPI hook)
  * Email Clients (file open from outlook/thunderbird)
  * FTP/Cloud (detect open or send attempt)

> Use `netstat` + `proc monitor` or Proxy level sniffing for blocking logic.

---

## 🧠 PHASE 5: SMART FINGERPRINTING & MATCHING

### 🧬 `fingerprint_engine.py`

```python
def is_file_modified(original_hash, new_hash, sim_threshold=90):
    return sha256 != new_sha256 or simhash_diff(sha256, new_sha256) > threshold
```

* Integrate `SimHash` for approximate content changes
* Match `.lnk` files to avoid false triggers
* Store entries in SQLite or flat JSON for lookup

---

## 🔔 PHASE 6: SLACK / TELEGRAM ALERT FORMATTING

### Example Format

```json
{
  "title": "DeadSecLock Alert 🚨",
  "agent_name": "Cybrotech-PC1",
  "company": "Cybrotech Ltd.",
  "email": "test@cybro.com",
  "event": [
    {"type": "create", "file": "confidential.docx", "path": "C:/Users/Reports"},
    {"type": "rename", "old": "oldname.docx", "new": "secret.docx"},
    {"type": "open_time", "opened": "11:30", "closed": "11:45"}
  ]
}
```

---

## 📋 PHASE 7: PDF DAILY REPORT

* Use `reportlab` or `fpdf`
* Summarize by:

  * Most modified files
  * Attempted uploads
  * Policy Violations
  * Screen captures index

---

## 💻 PHASE 8: CLIPBOARD & SCREENSHOT INTEGRATION

* Clipboard: Use `pyperclip` or `keyboard` to monitor `Ctrl+C`, etc.
* Screenshot every 3s: Use `mss` or `Pillow` with timestamp-based saving

---

## 🧰 PHASE 9: USB & ETHERNET BLOCKER

### USB Control (Windows)

* Use `reg add` or `devcon` to disable devices

```powershell
reg add "HKLM\SYSTEM\CurrentControlSet\Services\USBSTOR" /v Start /t REG_DWORD /d 4 /f
```

### Ethernet

* Disable with:

```cmd
netsh interface set interface name="Ethernet" admin=disabled
```

> Wrap in Python via `subprocess.run()` for control panel GUI.

---

## 🔚 FINAL PHASE: DEPLOYMENT & HARDENING

* Build with PyInstaller
* Pack configs + hashes + log engine into a **SQLite database**
* Create centralized API endpoint (later) to sync dashboards

---

## ✅ Summary: Module Status Plan

| Module                   | Status                    | Plan |
| ------------------------ | ------------------------- | ---- |
| Real-time File Monitor   | ✅ Existing, enhance logic |      |
| Clipboard Monitor        | ✅ Exists                  |      |
| Screenshot Engine        | 🔄 Add via `mss`          |      |
| Upload Blocker           | 🔄 Hook/proxy/web monitor |      |
| File Fingerprint Engine  | 🔄 Implement SimHash + DB |      |
| Alert Engine             | 🔄 Format & filter alerts |      |
| PDF Reporter             | ✅ Exists, needs detail    |      |
| USB & Network Controller | 🔄 Shell command wrapper  |      |
| Config/Policy Templates  | 🔄 JSON/YAML + GUI config |      |
| Daily Logs & SQLite      | 🔄 Replace loose files    |      |
