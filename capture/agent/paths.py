"""Platform-specific paths for the Lance On capture agent."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Visible, ASCII-safe root on Windows (works on PT-BR without ProgramData).
# Override with env LANCEON_HOME if needed, e.g. D:\LanceOn
DEFAULT_WINDOWS_HOME = Path(r"C:\LanceOn")


def is_windows() -> bool:
    return sys.platform.startswith("win")


def windows_install_home() -> Path:
    """Where Lance On lives on Windows: C:\\LanceOn (or %LANCEON_HOME%).

    Does not use ProgramData — that folder is hidden / hard to find on many
    Portuguese Windows PCs. C:\\LanceOn is always visible and accent-free.
    """
    if not is_windows():
        raise RuntimeError("windows_install_home() is Windows-only")

    override = (os.environ.get("LANCEON_HOME") or "").strip()
    if override:
        return Path(override)

    # Prefer existing install if already present under legacy ProgramData path
    legacy = _legacy_programdata_lanceon()
    if legacy is not None and (legacy / "config.yaml").is_file():
        return legacy

    return DEFAULT_WINDOWS_HOME


def _legacy_programdata_lanceon() -> Path | None:
    """Optional migration: keep using an old ProgramData install if it exists."""
    env = os.environ.get("PROGRAMDATA") or os.environ.get("ALLUSERSPROFILE")
    candidates = []
    if env:
        candidates.append(Path(env) / "LanceOn")
    candidates.append(Path(r"C:\ProgramData") / "LanceOn")
    for path in candidates:
        try:
            if path.is_dir():
                return path
        except OSError:
            continue
    return None


def windows_temp_dir() -> Path:
    """TEMP via env; fall back under the Lance On home."""
    for key in ("TEMP", "TMP"):
        value = os.environ.get(key)
        if value:
            path = Path(value)
            try:
                path.mkdir(parents=True, exist_ok=True)
                return path
            except OSError:
                pass
    fallback = windows_install_home() / "temp"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def program_data_root() -> Path:
    """Install root (name kept for callers). Windows → C:\\LanceOn."""
    if is_windows():
        return windows_install_home()
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
        return windows_temp_dir() / f"lanceon-button-{camera_index}.trigger"
    return Path(f"/tmp/lanceon-button-{camera_index}.trigger")
