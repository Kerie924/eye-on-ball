"""Platform-specific paths for the Lance On capture agent."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def is_windows() -> bool:
    return sys.platform.startswith("win")


def program_data_root() -> Path:
    if is_windows():
        base = Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData"))
        return base / "LanceOn"
    return Path("/opt/lance-on")


def default_install_dir() -> Path:
    if is_windows():
        return program_data_root() / "capture"
    return Path("/opt/lance-on/capture")


def default_config_dir() -> Path:
    if is_windows():
        return program_data_root()
    return Path("/etc/lance-on")


def default_config_path() -> Path:
    return default_config_dir() / "config.yaml"


def default_data_dir() -> Path:
    if is_windows():
        return program_data_root() / "data"
    return Path("/var/lib/lance-on")


def default_log_dir() -> Path:
    if is_windows():
        return program_data_root() / "logs"
    return Path("/var/log/lance-on")


def mock_trigger_path(camera_index: int) -> Path:
    if is_windows():
        return Path(os.environ.get("TEMP", r"C:\Temp")) / f"lanceon-button-{camera_index}.trigger"
    return Path(f"/tmp/lanceon-button-{camera_index}.trigger")
