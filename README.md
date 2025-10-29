

<!-- DeadSecLock Banner -->
<p align="center">
  <img src="https://github.com/user-attachments/assets/a90dec8c-cab6-492d-aff5-d6943124fbab" alt="DeadSecLock Banner" width="400"/>
</p>

# 🛡️ DeadSecLock – Advanced Offline-Capable Data Loss Prevention (DLP) Suite

**DeadSecLock** is a powerful, self-contained, agent-based DLP framework built for internal organizational use. It monitors file operations, blocks unauthorized data movements, captures insider threats, and generates evidence-based incident reports — all while respecting offline and air-gapped environments.

> 🧪 This repository is currently in **private development**. Keep logs and reports reviewed daily for debugging & enhancement.

---

## 🚀 Core Capabilities

### 🔐 File & Clipboard Monitoring
- Track file events: **Create, Modify, Delete, Rename, Move, Copy, Save As, File Open/Close durations**
- **Clipboard watcher**: Captures copy-paste data
- SHA256-based file diffing for integrity tracking

### 📸 Insider Threat Detection
- Capture **screenshots every 3 seconds**
- Detect external device insertion (USB, mouse, HDD)
- Monitor upload attempts to the web
- Block uploads of restricted files/templates

### ⚙️ System Control
- Enable/disable USB, Ethernet, Wi-Fi, Bluetooth
- Restrict edit/copy of blacklisted templates and critical formats (e.g., Aadhaar, PAN)

### 📑 Template Enforcement
- Match files against known templates
- Restrict editing or uploading if template similarity is high (fuzzy hashing or visual match)

### 🧪 Malware Detection
- Scan every file via **VirusTotal** using SHA256 lookup
- Flag and alert if detection > 0
- Upload unknown files to VT for future analysis

### 🧰 Agent Identity & Isolation
- Unique ID for every agent with department & company tagging
- Per-agent logs and report segmentation

### 📊 Reporting & Dashboards
- Daily incident PDF report generation
- Slack + Telegram + File Logging
- Company-specific dashboards

---

## 📁 Project Structure

```

DeadSecLock/
├── dlp\_core/
│   ├── watcher.py             # File event detection
│   ├── logger.py              # Slack + file logging
│   ├── hash\_utils.py          # File hashing
│   ├── clipboard-monitor.py   # Clipboard activity
│   ├── HIDS.py                # Device detection
│   ├── screencap.py           # Auto screenshot
│   ├── id.py                  # Agent ID assignment
│   ├── file-lister.py         # Whitelist/Blacklist control
│   ├── web-watcher.py         # Detect web uploads (future: proxy/plugin)
│   ├── revoker.py             # Restrict file movement/upload
│   ├── template-revoker.py    # Template similarity + restriction
│   ├── template crator.py     # Template creation & fingerprinting
│   ├── usb-controler.py       # GUI control over ports
│   ├── pdf\_reporter.py        # Daily incident reporting
│   ├── vt\_scanner.py          # VirusTotal integration
│   └── config.py              # Centralized config (tokens, paths, ignore patterns)
│
├── gui/
│   ├── app.py                 # GUI entrypoint
│   ├── assets/                # Icons, logos
│   └── seprate.dashboard.py   # Per-company dashboard
│
├── installer/
│   └── build\_config.spec      # PyInstaller EXE spec
│
├── tests/
│   └── test\_watcher.py        # Unit tests
│
├── DeadSecLock.exe            # Optional compiled agent
├── dlp.log                    # Live logging
├── dlp\_report.pdf             # Daily summary
├── README.md                  # Documentation
└── requirements.txt           # Python dependencies

````

---

## 🛠️ Setup Instructions

### 1. 🐍 Python Environment

```bash
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
````

### 2. 🔐 API Keys Setup

Edit `dlp_core/config.py`:

```python
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/..."
TELEGRAM_BOT_TOKEN = "your_bot_token"
TELEGRAM_CHAT_ID = "your_group_id"
VT_API_KEY = "your_virustotal_api_key"

AGENT_ID = "user01-dev"
COMPANY_NAME = "AcmeCorp"
DEPARTMENT = "Research"
WATCH_PATHS = ["/home/user/docs", "C:\\Users\\Admin\\Documents"]
BLACKLIST = ["*.docx", "aadhaar_template.pdf"]
```

---

## 🖥️ Running the Agent

```bash
python dlp_core/watcher.py
```

Or run the compiled agent:

```bash
./DeadSecLock.exe
```

The agent auto-loads:

* `logger.py`, `clipboard-monitor.py`, `screencap.py`, `vt_scanner.py`, etc.
* Real-time event watcher and file hash comparisons
* Background screenshot capture & HIDS logic

---

## 📤 Logging & Alerts

* All events stored in `dlp.log`
* Alerts sent to **Slack** and **Telegram** if enabled
* PDF summary generated nightly via `pdf_reporter.py`

---

## 🛡️ Security Goals

* **No external dependencies** (works offline except VirusTotal)
* Works on **Windows/Linux/Mac**
* Designed for **air-gapped**, **regulated**, and **sensitive** environments
* Custom **blacklist and revocation** rules per company

---

## 📦 Build EXE

```bash
pyinstaller --onefile installer/build_config.spec
```

---

## ✅ Next Steps & Roadmap

* [ ] Add MITM-based `web-watcher` to monitor browser file uploads
* [ ] Enhance template matching using OCR + fuzzy hashing
* [ ] Build central log collector for multi-agent deployments
* [ ] Add USB activity logging to report
* [ ] Web dashboard (Flask + SQLite) for all agents

---

## 🧠 Tips for You (as Dev)

* Check logs in `dlp.log` for false positives
* Ensure `config.py` paths match your actual monitored folders
* Use `tests/` to validate watcher logic before deployment
* If files aren’t detected, check `WATCH_PATHS` and file permissions

---

## 👨‍💻 Author

**DeadSecLock** is developed and maintained privately by Yash (Cybersecurity Analyst / Red + Blue Team)

---

## ⚠️ Disclaimer

This tool is for **internal cybersecurity defense** and awareness only. Do not use it on systems you do not own or without proper consent.
