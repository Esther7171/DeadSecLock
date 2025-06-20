<!-- DeadSecLock Banner -->
<p align="center">
  <img src="https://github.com/user-attachments/assets/a90dec8c-cab6-492d-aff5-d6943124fbab" alt="DeadSecLock Banner" width="400"/>
</p>

<h1 align="center">🛡️ DeadSecLock</h1>
<p align="center"><strong>Next-Gen Lightweight DLP (Data Loss Prevention)</strong></p>

---

**DeadSecLock** is a real-time, open-source Data Loss Prevention (DLP) solution built entirely in Python.  
Designed for transparency, speed, and flexibility, it detects sensitive file activity like copying, renaming, deletion, or exfiltration, and instantly alerts via Slack while storing encrypted logs and PDF reports.

---

### 🔧 Features

- ✅ Real-time file monitoring (Create, Copy, Modify, Move, Delete)
- 📄 PDF-based incident report generation
- 📩 Slack alert integration
- 🚫 Junk file filtering and noise suppression
- 🧠 Smart hash-diff logic to detect true content modifications
- 🔐 Local-only mode (No cloud dependencies)

---

### 📂 Architecture Overview

- `dlp_core/` – All backend monitoring logic (watcher, logger, hashing, PDF report)
- `gui/` – Lightweight Python GUI wrapper
- `installer/` – PyInstaller scripts to generate `.exe`
- `tests/` – Test scripts to ensure detection accuracy

```plaintext
DeadSecLock/
├── dlp_core/
│   ├── watcher.py             # File event detection (create, modify, move, delete)
│   ├── logger.py              # Slack + file logging
│   ├── hash_utils.py          # SHA256 hashing for file diff
│   ├── pdf_reporter.py        # Daily PDF incident report
│   └── config.py              # Configuration (tokens, paths, ignore patterns)
│
├── gui/
│   ├── app.py                 # GUI entrypoint
│   └── assets/                # Images and icons
│
├── installer/
│   └── build_config.spec      # PyInstaller EXE build spec
│
├── tests/
│   └── test_watcher.py        # Unit tests
│
├── DeadSecLock.exe            # Optional compiled EXE
├── dlp.log                    # Activity log
├── dlp_report.pdf             # Daily incident PDF
├── README.md                  # Project documentation
└── requirements.txt           # Python dependencies
````

---

### 🚀 Getting Started

```bash
git clone https://github.com/yourname/DeadSecLock.git
cd DeadSecLock
pip install -r requirements.txt
python gui/app.py
```

---

### 🖼️ GUI Preview

![GUI Preview](./gui/assets/deadseclock-banner.png)

---

### 🤝 Contribute

We’re building the world’s **most open and transparent DLP tool**.
Pull Requests, Issues, and Ideas are welcome. Join us in securing endpoints the right way—**from scratch**.

---

### 📜 License

Licensed under the **MIT License** © 2025 [DeadSecLock Authors](https://github.com/Esther7171/DeadSecLock).
