import os
import sys
import time
import socket
import subprocess
import webbrowser
import atexit
from pathlib import Path
import webview

ROOT_DIR = Path(__file__).resolve().parent
CRM_DIR = ROOT_DIR / "credit-crm"
SHELL_HTML = ROOT_DIR / "desktop_shell.html"

# Track child processes spawned by desktop app
spawned_processes = []

def cleanup_children():
    """Ensure all background processes spawned by this desktop app are terminated."""
    for proc in spawned_processes:
        try:
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=2)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

atexit.register(cleanup_children)

def is_port_open(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a specific TCP port is listening."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0

def ensure_services():
    """Ensure TrueBuild Engine and Credit CRM are running, launching them if needed."""
    python_exe = sys.executable

    # 1. TrueBuild FastAPI (Port 8000)
    if not is_port_open(8000):
        print("[Desktop App] Starting TrueBuild Engine on http://127.0.0.1:8000...")
        tb_proc = subprocess.Popen(
            [python_exe, "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", "8000"],
            cwd=str(ROOT_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        )
        spawned_processes.append(tb_proc)
    else:
        print("[Desktop App] TrueBuild Engine is already running on port 8000.")

    # 2. Credit Acceleration CRM (Port 3002)
    if not is_port_open(3002):
        print("[Desktop App] Starting Credit Acceleration CRM on http://127.0.0.1:3002...")
        npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
        crm_proc = subprocess.Popen(
            [npm_cmd, "run", "server"],
            cwd=str(CRM_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        )
        spawned_processes.append(crm_proc)
    else:
        print("[Desktop App] Credit CRM is already running on port 3002.")

    # Give services a brief moment to initialize
    time.sleep(1.5)

class DesktopApi:
    """JavaScript bridge exposed to the webview."""
    def open_external(self, url: str):
        webbrowser.open(url)

    def restart_services(self):
        cleanup_children()
        ensure_services()
        return True

def main():
    print("==================================================")
    print("   TrueBuild Dual-Engine Desktop Application      ")
    print("   Sumthin3lse Global Solutions LLC               ")
    print("==================================================")

    # 1. Start backend engines
    ensure_services()

    # 2. Create Desktop Window
    api = DesktopApi()
    window = webview.create_window(
        title="TrueBuild Suite — Desktop Edition (Sumthin3lse Global)",
        url=str(SHELL_HTML.as_uri()),
        width=1440,
        height=900,
        min_size=(1080, 720),
        background_color="#090d16",
        js_api=api
    )

    # 3. Start Native Window GUI
    try:
        webview.start(debug=False)
    finally:
        cleanup_children()

if __name__ == "__main__":
    main()
