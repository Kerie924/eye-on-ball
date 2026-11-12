"""Single-instance lock for the Windows capture agent (PID file)."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if sys.platform.startswith("win"):
        try:
            import ctypes

            handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, int(pid))
            if handle:
                ctypes.windll.kernel32.CloseHandle(handle)
                return True
            return False
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def read_pid(pid_path: Path) -> int | None:
    if not pid_path.is_file():
        return None
    try:
        return int(pid_path.read_text(encoding="utf-8").strip().split()[0])
    except (OSError, ValueError, IndexError):
        return None


def acquire_pid_lock(pid_path: Path) -> bool:
    """Return True if this process owns the lock. False if another live instance exists."""
    pid_path.parent.mkdir(parents=True, exist_ok=True)
    existing = read_pid(pid_path)
    if existing is not None and existing != os.getpid() and pid_alive(existing):
        logger.error(
            "Capture ja esta em execucao (PID %s). "
            "Nao inicie uma segunda copia — ela nao consegue abrir o Arduino (COM Access denied). "
            "Use Parar no painel, ou: taskkill /PID %s /T /F",
            existing,
            existing,
        )
        return False
    try:
        pid_path.write_text(str(os.getpid()), encoding="utf-8")
    except OSError as exc:
        logger.warning("Could not write PID file %s: %s", pid_path, exc)
        return True
    return True


def release_pid_lock(pid_path: Path | None) -> None:
    if pid_path is None:
        return
    try:
        current = read_pid(pid_path)
        if current is None or current == os.getpid():
            pid_path.unlink(missing_ok=True)
    except OSError:
        pass
