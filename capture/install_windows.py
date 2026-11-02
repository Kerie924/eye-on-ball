#!/usr/bin/env python3
"""Privileged installer for Lance On capture on Windows."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

# Prefer package import; fall back if run as a loose script before copy.
try:
    from agent.paths import DEFAULT_WINDOWS_HOME, program_data_root
except ImportError:  # pragma: no cover
    DEFAULT_WINDOWS_HOME = Path(r"C:\LanceOn")

    def program_data_root() -> Path:  # type: ignore[misc]
        override = (os.environ.get("LANCEON_HOME") or "").strip()
        return Path(override) if override else DEFAULT_WINDOWS_HOME

DEFAULT_API_URL = "https://api.lanceonpara.com.br"

try:
    from windows_pins import button_hub_yaml, camera_button_yaml as win_camera_button_yaml
except ImportError:  # staged copy may already be on sys.path via INSTALL_DIR later
    button_hub_yaml = None  # type: ignore[assignment]
    win_camera_button_yaml = None  # type: ignore[assignment]
# Visible folder on every Windows language (not ProgramData).
INSTALL_ROOT = program_data_root()
INSTALL_DIR = INSTALL_ROOT / "capture"
CONFIG_PATH = INSTALL_ROOT / "config.yaml"
DATA_DIR = INSTALL_ROOT / "data"
LOG_DIR = INSTALL_ROOT / "logs"
TASK_NAME = "LanceOnCapture"


def log(message: str) -> None:
    print(message, flush=True)


def run(command: list[str], **kwargs) -> subprocess.CompletedProcess:
    log("+ " + " ".join(command))
    return subprocess.run(command, check=True, **kwargs)


def yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def rtsp_url(user: str, password: str, ip: str) -> str:
    return (
        f"rtsp://{quote(user, safe='')}:{quote(password, safe='')}@{ip.strip()}"
        ":554/cam/realmonitor?channel=1&subtype=0"
    )


def require_admin() -> None:
    try:
        import ctypes

        if ctypes.windll.shell32.IsUserAnAdmin():
            return
    except Exception:
        pass
    raise SystemExit("Run this installer as Administrator (right-click → Run as administrator).")


def _python_version(executable: str) -> tuple[int, int] | None:
    try:
        result = subprocess.run(
            [executable, "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
            capture_output=True,
            text=True,
            check=False,
        )
        text = (result.stdout or "").strip()
        if result.returncode != 0 or "." not in text:
            return None
        major_s, minor_s = text.split(".", 1)
        return int(major_s), int(minor_s)
    except (OSError, ValueError):
        return None


def find_python() -> str:
    """Use the best available Python 3.11+ (including 3.15). Skip Microsoft Store stub."""
    candidates: list[str] = []

    # Prefer current process, then py launcher versions, then PATH
    if sys.executable:
        candidates.append(sys.executable)
    for minor in (15, 14, 13, 12, 11):
        for args in (
            ["py", f"-3.{minor}", "-c", "import sys; print(sys.executable)"],
            [f"python3.{minor}", "-c", "import sys; print(sys.executable)"],
        ):
            try:
                result = subprocess.run(args, capture_output=True, text=True, check=False)
                path = (result.stdout or "").strip()
                if result.returncode == 0 and path and Path(path).is_file():
                    candidates.append(path)
            except OSError:
                continue
    which = shutil.which("python") or shutil.which("python3")
    if which:
        candidates.append(which)

    seen: set[str] = set()
    for path in candidates:
        key = str(Path(path).resolve()).lower() if Path(path).exists() else path.lower()
        if key in seen or "\\windowsapps\\" in key.replace("/", "\\"):
            continue
        seen.add(key)
        ver = _python_version(path)
        if ver is None or ver[0] != 3 or ver[1] < 11:
            continue
        log(f"Using Python {ver[0]}.{ver[1]}: {path}")
        return path

    raise SystemExit(
        "Python 3.11+ not found. Install from https://www.python.org/downloads/\n"
        "Check 'Add python.exe to PATH'."
    )


def ensure_ffmpeg() -> None:
    if shutil.which("ffmpeg"):
        log("FFmpeg found on PATH.")
        return
    log("FFmpeg not found. Trying winget install...")
    try:
        run(
            [
                "winget",
                "install",
                "-e",
                "--id",
                "Gyan.FFmpeg",
                "--accept-package-agreements",
                "--accept-source-agreements",
            ]
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        log(
            "WARNING: Install FFmpeg manually and add it to PATH, then restart the PC.\n"
            "  https://www.gyan.dev/ffmpeg/builds/  or  winget install Gyan.FFmpeg"
        )


def copy_agent(source: Path) -> None:
    INSTALL_ROOT.mkdir(parents=True, exist_ok=True)
    if source.resolve() == INSTALL_DIR.resolve():
        log(f"Source is already {INSTALL_DIR}; skipping copy.")
        return

    log(f"Copying capture agent to {INSTALL_DIR}")
    if INSTALL_DIR.exists():
        shutil.rmtree(INSTALL_DIR)
    shutil.copytree(
        source,
        INSTALL_DIR,
        ignore=shutil.ignore_patterns(
            ".venv",
            "__pycache__",
            "*.pyc",
            ".git",
            ".gitignore",
        ),
    )


def install_python_deps() -> Path:
    host_python = find_python()
    venv = INSTALL_DIR / ".venv"
    python = venv / "Scripts" / "python.exe"
    pip = venv / "Scripts" / "pip.exe"
    # Recreate venv if missing or built with a different host interpreter
    recreate = not python.exists()
    if python.exists():
        ver = _python_version(str(python))
        host_ver = _python_version(host_python)
        if ver is None or (host_ver and ver != host_ver):
            log(f"Recreating venv (was {ver}, host {host_ver})...")
            shutil.rmtree(venv)
            recreate = True
    if recreate:
        run([host_python, "-m", "venv", str(venv)])
    run([str(pip), "install", "--upgrade", "pip", "wheel"])
    req = INSTALL_DIR / "requirements-windows.txt"
    if not req.exists():
        req = INSTALL_DIR / "requirements.txt"
    # Prefer binary wheels; Windows deps use ruamel.yaml (no MSVC needed on 3.15)
    try:
        run([str(pip), "install", "--prefer-binary", "-r", str(req)])
    except subprocess.CalledProcessError as exc:
        raise SystemExit(
            "Failed to install Python packages.\n"
            "Delete C:\\LanceOn\\capture\\.venv and run Setup again.\n"
            f"Details: {exc}"
        ) from exc
    return python


def install_watermark(selected: str | None) -> Path:
    dest = INSTALL_DIR / "assets" / "video-watermark.jpeg"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if selected:
        src = Path(selected).expanduser()
        if not src.is_file():
            raise FileNotFoundError(f"Watermark not found: {src}")
        shutil.copy2(src, dest)
        log(f"Watermark copied from {src}")
    return dest


def camera_button_yaml(index: int, *, enabled: bool) -> str:
    """Fixed Arduino pairs: CAM1=D2/D3 … CAM6=D12/D13 via shared serial hub."""
    if win_camera_button_yaml is not None:
        return win_camera_button_yaml(index, enabled=enabled)
    # Fallback if windows_pins is unavailable during early import
    if not enabled:
        return "    button:\n      type: none"
    return (
        "    button:\n"
        "      type: serial_hub\n"
        f'      trigger_on: "{index}"'
    )


def write_config(settings: dict, watermark: Path) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    api_url = str(settings.get("api_url") or DEFAULT_API_URL).rstrip("/")
    device_key = str(settings["device_key"]).strip()
    user = str(settings.get("camera_user") or "admin").strip()
    password = str(settings["camera_password"])
    use_buttons = bool(settings.get("use_gpio", True))  # reuse UI flag name
    hub_port = str(settings.get("button_hub_port") or "auto").strip() or "auto"

    cameras = settings.get("cameras") or []
    camera_lines = []
    for item in cameras:
        index = int(item["index"])
        ip = str(item["ip"]).strip()
        url = rtsp_url(user, password, ip)
        camera_lines.append(
            "\n".join(
                [
                    f"  - index: {index}",
                    f"    name: Camera {index}",
                    f"    rtsp_url: {yaml_quote(url)}",
                    camera_button_yaml(index, enabled=use_buttons),
                ]
            )
        )

    if button_hub_yaml is not None:
        hub_block = button_hub_yaml(port=hub_port)
    else:
        hub_block = (
            "button_hub:\n"
            "  type: serial\n"
            f"  port: {hub_port}\n"
            "  baudrate: 115200"
        )

    content = f"""# Generated by Lance On Setup (Windows)
# Fixed button pairs (Arduino): CAM1=D2+D3 … CAM6=D12+D13 — no per-site remap.
api_url: {yaml_quote(api_url)}
device_key: {yaml_quote(device_key)}

buffer_seconds: 300
clip_seconds: 30
# Short segments reduce max lag if a flush ever fails (was 10s → early cutoff reports)
segment_seconds: 2
heartbeat_seconds: 60
button_cooldown_seconds: 3
queue_max_hours: 48
queue_max_mb: 4096
upload_retry_seconds: 20

{hub_block}

cameras:
{chr(10).join(camera_lines)}

data_dir: {yaml_quote(str(DATA_DIR).replace(chr(92), "/"))}
watermark_path: {yaml_quote(str(watermark).replace(chr(92), "/"))}
# Logo size on video: percent of frame height (5–80). Change in Lance On Control app anytime.
watermark_height_percent: {float(settings.get("watermark_height_percent", 28))}
"""
    CONFIG_PATH.write_text(content, encoding="utf-8")
    log(f"Wrote {CONFIG_PATH}")
    if use_buttons:
        log("Button wiring: CAM1=D2/D3 CAM2=D4/D5 CAM3=D6/D7 CAM4=D8/D9 CAM5=D10/D11 CAM6=D12/D13")


def _write_bat(path: Path, lines: list[str]) -> None:
    """Write a Windows .bat with CRLF endings (LF-only files often exit instantly)."""
    text = "\r\n".join(lines) + "\r\n"
    path.write_text(text, encoding="utf-8")


def write_helper_scripts(python: Path) -> Path:
    start = INSTALL_ROOT / "start-capture.bat"
    stop = INSTALL_ROOT / "stop-capture.bat"
    status = INSTALL_ROOT / "status-capture.bat"
    control = INSTALL_ROOT / "LanceOn.bat"
    python_exe = Path(python)
    # Prefer GUI binary so closing the black console does not kill the app.
    pythonw_exe = python_exe.with_name("pythonw.exe")
    if not pythonw_exe.is_file():
        pythonw_exe = python_exe

    _write_bat(
        start,
        [
            "@echo off",
            "setlocal EnableExtensions",
            f'cd /d "{INSTALL_DIR}"',
            f'if not exist "{python_exe}" (',
            f'  echo [Lance On] Python missing: {python_exe}',
            f'  echo Re-run LanceOn-Setup.bat',
            "  exit /b 1",
            ")",
            f'"{python_exe}" "{INSTALL_DIR / "run.py"}" --config "{CONFIG_PATH}"',
            "exit /b %ERRORLEVEL%",
        ],
    )
    _write_bat(
        stop,
        [
            "@echo off",
            "setlocal EnableExtensions",
            "echo Stopping Lance On capture...",
            'taskkill /F /FI "WINDOWTITLE eq LanceOnCapture*" 2>nul',
            # wmic is removed on many Windows 11 installs — use PowerShell instead
            "powershell -NoProfile -ExecutionPolicy Bypass -Command "
            "\"Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | "
            "Where-Object { $_.CommandLine -and $_.CommandLine -like '*LanceOn*run.py*' } | "
            "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }\" "
            "2>nul",
            f"schtasks /End /TN {TASK_NAME} 2>nul",
            "echo Done.",
        ],
    )
    _write_bat(
        status,
        [
            "@echo off",
            "setlocal EnableExtensions",
            f'if exist "{LOG_DIR / "capture.log"}" (',
            f'  type "{LOG_DIR / "capture.log"}"',
            ") else (",
            "  echo Log not found yet.",
            ")",
            "echo.",
            "pause",
        ],
    )
    # Prefer the portable template (CRLF, preflight, detached pythonw).
    template = Path(__file__).resolve().parent / "LanceOn.bat"
    if template.is_file():
        body = template.read_text(encoding="utf-8", errors="replace")
        lines = body.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        while lines and lines[-1] == "":
            lines.pop()
        _write_bat(control, lines)
    else:
        _write_bat(
            control,
            [
                "@echo off",
                "setlocal EnableExtensions",
                "title Lance On",
                'cd /d "%~dp0"',
                'set "ROOT=%~dp0"',
                'if "%ROOT:~-1%"=="\\" set "ROOT=%ROOT:~0,-1%"',
                'set "CAPTURE=%ROOT%\\capture"',
                'set "PY=%CAPTURE%\\.venv\\Scripts\\python.exe"',
                'set "PYW=%CAPTURE%\\.venv\\Scripts\\pythonw.exe"',
                'set "APP=%CAPTURE%\\control_app.py"',
                'set "ERRLOG=%ROOT%\\logs\\control-app-error.log"',
                'if not exist "%ROOT%\\logs" mkdir "%ROOT%\\logs"',
                f'if not exist "%PY%" (echo Missing {python_exe}& pause& exit /b 1)',
                'if exist "%PYW%" (set "LAUNCHER=%PYW%") else (set "LAUNCHER=%PY%")',
                'cd /d "%CAPTURE%"',
                '"%PY%" -c "import tkinter; import control_app" 1>"%ERRLOG%" 2>&1',
                "if errorlevel 1 (type \"%ERRLOG%\"& pause& exit /b 1)",
                'start "Lance On" "%LAUNCHER%" "%APP%"',
                "exit /b 0",
            ],
        )
    _create_desktop_shortcut(control)
    log(f"Helper scripts in {INSTALL_ROOT}")
    log(f"Open anytime: {control}")
    return start


def _create_desktop_shortcut(target_bat: Path) -> None:
    """Create Desktop\\Lance On.lnk → LanceOn.bat (best-effort)."""
    try:
        desktop = Path(os.environ.get("PUBLIC", r"C:\Users\Public")) / "Desktop"
        if not desktop.is_dir():
            user_profile = os.environ.get("USERPROFILE")
            if user_profile:
                desktop = Path(user_profile) / "Desktop"
        if not desktop.is_dir():
            return
        shortcut = desktop / "Lance On.lnk"
        ps = (
            f"$ws = New-Object -ComObject WScript.Shell; "
            f"$s = $ws.CreateShortcut('{str(shortcut).replace(chr(39), chr(39)+chr(39))}'); "
            f"$s.TargetPath = '{str(target_bat).replace(chr(39), chr(39)+chr(39))}'; "
            f"$s.WorkingDirectory = '{str(INSTALL_ROOT).replace(chr(39), chr(39)+chr(39))}'; "
            f"$s.Description = 'Lance On Controle da Quadra'; "
            f"$s.Save()"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
            check=False,
            capture_output=True,
            text=True,
        )
        log(f"Desktop shortcut: {shortcut}")
    except Exception as exc:
        log(f"WARNING: could not create desktop shortcut ({exc})")


def install_startup_task(start_bat: Path) -> None:
    """Run at user logon so keyboard/USB buttons work in an interactive session.

    Point the task at start-capture.bat (not a nested quoted python command).
    Nested quotes in schtasks /TR often fail with "cannot find the specified path".
    """
    # Remove old task if present
    subprocess.run(["schtasks", "/Delete", "/TN", TASK_NAME, "/F"], check=False)
    # /TR with a single .bat path is reliable on Windows 10/11
    run(
        [
            "schtasks",
            "/Create",
            "/TN",
            TASK_NAME,
            "/TR",
            str(start_bat),
            "/SC",
            "ONLOGON",
            "/RL",
            "HIGHEST",
            "/F",
        ]
    )
    # Start now
    run_now = subprocess.run(["schtasks", "/Run", "/TN", TASK_NAME], check=False)
    if run_now.returncode != 0:
        log(
            "WARNING: Scheduled task created but could not start immediately. "
            f"Try: schtasks /Run /TN {TASK_NAME}"
        )
    log(f"Scheduled task {TASK_NAME} created (starts at logon).")


def main() -> int:
    if not sys.platform.startswith("win"):
        print("This installer is for Windows only.", file=sys.stderr)
        return 1
    require_admin()

    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, help="Path to the capture folder")
    parser.add_argument("--settings", required=True, help="JSON settings from the Setup App")
    args = parser.parse_args()

    source = Path(args.source).resolve()
    settings = json.loads(Path(args.settings).read_text(encoding="utf-8"))

    if not str(settings.get("device_key", "")).strip():
        raise SystemExit("Device key is required.")
    cameras = settings.get("cameras") or []
    if not cameras:
        raise SystemExit("At least one camera IP is required.")

    log(f"Source: {source}")
    log(f"Install root: {INSTALL_ROOT}")
    log(f"Python: {find_python()}")
    if not source.is_dir() or not (source / "run.py").is_file():
        raise SystemExit(f"Invalid capture source folder: {source}")

    INSTALL_ROOT.mkdir(parents=True, exist_ok=True)
    log("Checking FFmpeg...")
    ensure_ffmpeg()
    copy_agent(source)
    log("Installing Python packages...")
    python = install_python_deps()
    watermark = install_watermark(settings.get("watermark_path"))
    write_config(settings, watermark)
    start_bat = write_helper_scripts(python)
    install_startup_task(start_bat)
    log("INSTALL_OK")
    log(f"Config: {CONFIG_PATH}")
    log(f"Logs:   {LOG_DIR / 'capture.log'}")
    log(f"Start:  {start_bat}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
