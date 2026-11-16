import os
import sys
import time
import socket
import ctypes
import subprocess
import urllib.request
from pathlib import Path

# 准确获取程序真实安装/运行所在的根目录（避免 PyInstaller 临时目录 _MEI 导致的路径错误）
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent

BACKEND_DIR = BASE_DIR / "backend"

def show_error(title: str, msg: str):
    if sys.platform == "win32":
        ctypes.windll.user32.MessageBoxW(0, msg, title, 0x10)
    else:
        print(f"[{title}] {msg}")

def find_free_port(start_port: int = 8000) -> int:
    """查找空闲端口，避免8000被占用时报错"""
    for port in range(start_port, start_port + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return start_port

def wait_for_server(url: str, timeout: int = 35):
    """等待后台服务完全就绪"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status in (200, 404):
                    return True
        except Exception:
            time.sleep(0.5)
    return False

def find_browser_app_cmd(url: str, profile_dir: Path):
    """查找系统中可用于以原生独立 App 窗口打开的浏览器"""
    candidates = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    ]
    for exe in candidates:
        if os.path.isfile(exe):
            # 传入独立的 user-data-dir 确保弹出独立进程窗口，关闭窗口时才退出
            return [
                exe,
                f"--app={url}",
                f"--user-data-dir={profile_dir}",
                "--window-size=1366,850",
                "--no-first-run",
                "--no-default-browser-check",
            ]
    return None

def main():
    if not BACKEND_DIR.exists():
        show_error("启动失败", f"找不到后端目录：\n{BACKEND_DIR}\n请确保不要将本程序单独移动到文件夹外部运行。")
        return

    # 优先使用绿色便携版自带的 runtime/python.exe
    runtime_py = BASE_DIR / "runtime" / "python.exe"
    venv_py = BACKEND_DIR / ".venv" / "Scripts" / "python.exe"

    if runtime_py.exists():
        py_exec = str(runtime_py)
    elif venv_py.exists():
        py_exec = str(venv_py)
    else:
        show_error("启动失败", "找不到 Python 运行时环境 (runtime 或 .venv)。")
        return

    port = find_free_port(8000)
    target_url = f"http://127.0.0.1:{port}/"

    os.chdir(str(BACKEND_DIR))
    server_cmd = [
        py_exec,
        "-m", "uvicorn",
        "app.main:app",
        "--host", "127.0.0.1",
        "--port", str(port)
    ]

    creation_flags = 0
    if sys.platform == "win32":
        creation_flags = subprocess.CREATE_NO_WINDOW

    log_dir = BASE_DIR / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = open(log_dir / "app_runtime.log", "w", encoding="utf-8")

    server_process = subprocess.Popen(
        server_cmd,
        cwd=str(BACKEND_DIR),
        stdout=log_file,
        stderr=subprocess.STDOUT,
        creationflags=creation_flags,
    )

    try:
        if not wait_for_server(target_url, timeout=40):
            show_error("服务启动超时", f"后台服务未能成功启动，请查看日志：\n{log_dir / 'app_runtime.log'}")
            return

        profile_dir = BASE_DIR / "logs" / "app_window_profile"
        profile_dir.mkdir(parents=True, exist_ok=True)
        browser_cmd = find_browser_app_cmd(target_url, profile_dir)

        if browser_cmd:
            browser_process = subprocess.Popen(browser_cmd)
            browser_process.wait()
        else:
            import webbrowser
            webbrowser.open(target_url)
            server_process.wait()
    except KeyboardInterrupt:
        pass
    finally:
        server_process.terminate()
        try:
            server_process.wait(timeout=3)
        except Exception:
            server_process.kill()
        log_file.close()

if __name__ == "__main__":
    main()
