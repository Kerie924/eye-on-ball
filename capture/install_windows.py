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

# Camera index -> keyboard key for USB/HID arcade buttons
DEFAULT_KEYS = {1: "f1", 2: "f2", 3: "f3", 4: "f4", 5: "f5", 6: "f6"}
DEFAULT_API_URL = "https://api.lanceonpara.com.br"
INSTALL_ROOT = Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData")) / "LanceOn"
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


def find_python() -> str:
    return sys.executable


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
    venv = INSTALL_DIR / ".venv"
    python = venv / "Scripts" / "python.exe"
    pip = venv / "Scripts" / "pip.exe"
    if not python.exists():
        run([find_python(), "-m", "venv", str(venv)])
    run([str(pip), "install", "--upgrade", "pip"])
    req = INSTALL_DIR / "requirements-windows.txt"
    if not req.exists():
        req = INSTALL_DIR / "requirements.txt"
    run([str(pip), "install", "-r", str(req)])
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
    if not enabled:
        return "    button:\n      type: none"
    key = DEFAULT_KEYS.get(index, f"f{index}")
    return (
        f"    button:\n"
        f"      type: keyboard\n"
        f"      key: {key}  # USB/HID button or press {key.upper()} on the keyboard"
    )


def write_config(settings: dict, watermark: Path) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    api_url = str(settings.get("api_url") or DEFAULT_API_URL).rstrip("/")
    device_key = str(settings["device_key"]).strip()
    user = str(settings.get("camera_user") or "admin").strip()
    password = str(settings["camera_password"])
    use_buttons = bool(settings.get("use_gpio", True))  # reuse UI flag name

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

    content = f"""# Generated by Lance On Setup (Windows)
api_url: {yaml_quote(api_url)}
device_key: {yaml_quote(device_key)}

buffer_seconds: 300
clip_seconds: 30
segment_seconds: 10
heartbeat_seconds: 60
button_cooldown_seconds: 3
queue_max_hours: 48
queue_max_mb: 4096
upload_retry_seconds: 20

# Keyboard / USB-HID buttons: F1 = camera 1, F2 = camera 2, ...
cameras:
{chr(10).join(camera_lines)}

data_dir: {yaml_quote(str(DATA_DIR).replace(chr(92), "/"))}
watermark_path: {yaml_quote(str(watermark).replace(chr(92), "/"))}
"""
    CONFIG_PATH.write_text(content, encoding="utf-8")
    log(f"Wrote {CONFIG_PATH}")


def write_helper_scripts(python: Path) -> None:
    start = INSTALL_ROOT / "start-capture.bat"
    stop = INSTALL_ROOT / "stop-capture.bat"
    status = INSTALL_ROOT / "status-capture.bat"
    start.write_text(
        "\n".join(
            [
                "@echo off",
                f'"{python}" "{INSTALL_DIR / "run.py"}" --config "{CONFIG_PATH}"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    stop.write_text(
        "\n".join(
            [
                "@echo off",
                "echo Stopping Lance On capture...",
                'taskkill /F /FI "WINDOWTITLE eq LanceOnCapture*" 2>nul',
                'wmic process where "CommandLine like \'%LanceOn%run.py%\'" call terminate 2>nul',
                "schtasks /End /TN LanceOnCapture 2>nul",
                "echo Done.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    status.write_text(
        "\n".join(
            [
                "@echo off",
                f'type "{LOG_DIR / "capture.log"}"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    log(f"Helper scripts in {INSTALL_ROOT}")


def install_startup_task(python: Path) -> None:
    """Run at user logon so keyboard/USB buttons work in an interactive session."""
    tr = f'"{python}" "{INSTALL_DIR / "run.py"}" --config "{CONFIG_PATH}"'
    # Remove old task if present
    subprocess.run(["schtasks", "/Delete", "/TN", TASK_NAME, "/F"], check=False)
    run(
        [
            "schtasks",
            "/Create",
            "/TN",
            TASK_NAME,
            "/TR",
            tr,
            "/SC",
            "ONLOGON",
            "/RL",
            "HIGHEST",
            "/F",
        ]
    )
    # Start now
    subprocess.run(["schtasks", "/Run", "/TN", TASK_NAME], check=False)
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

    log("Checking FFmpeg...")
    ensure_ffmpeg()
    copy_agent(source)
    log("Installing Python packages...")
    python = install_python_deps()
    watermark = install_watermark(settings.get("watermark_path"))
    write_config(settings, watermark)
    write_helper_scripts(python)
    install_startup_task(python)
    log("INSTALL_OK")
    log(f"Config: {CONFIG_PATH}")
    log(f"Logs:   {LOG_DIR / 'capture.log'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
