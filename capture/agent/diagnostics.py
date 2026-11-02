"""Startup / setup diagnostics for cameras (RTSP) and Windows button hub."""

from __future__ import annotations

import logging
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

READY_TOKEN = "LANCEON_BUTTONS_READY"


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str

    def line(self) -> str:
        mark = "OK" if self.ok else "FALHOU"
        return f"[{mark}] {self.name}: {self.detail}"


def _host_from_rtsp(url: str) -> str:
    try:
        host = urlparse(url).hostname or ""
        return host or url
    except Exception:
        return url


def probe_rtsp(url: str, *, timeout_seconds: float = 10.0) -> CheckResult:
    """Verify an RTSP URL is reachable (ffprobe preferred, ffmpeg fallback)."""
    host = _host_from_rtsp(url)
    name = f"Camera RTSP ({host})"
    if not url or not url.strip():
        return CheckResult(name, False, "URL RTSP vazia")
    if url.startswith("test://"):
        return CheckResult(name, True, "fonte de teste local")

    ffprobe = shutil.which("ffprobe")
    ffmpeg = shutil.which("ffmpeg")
    if not ffprobe and not ffmpeg:
        return CheckResult(name, False, "ffmpeg/ffprobe nao encontrado no PATH")

    if ffprobe:
        command = [
            ffprobe,
            "-v",
            "error",
            "-rtsp_transport",
            "tcp",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            url,
        ]
    else:
        command = [
            ffmpeg,  # type: ignore[list-item]
            "-hide_banner",
            "-loglevel",
            "error",
            "-rtsp_transport",
            "tcp",
            "-i",
            url,
            "-t",
            "1",
            "-f",
            "null",
            "-",
        ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds + 5,
        )
    except subprocess.TimeoutExpired:
        return CheckResult(
            name,
            False,
            f"tempo esgotado ({timeout_seconds:.0f}s) — confira IP, cabo e se a camera esta ligada",
        )
    except OSError as exc:
        return CheckResult(name, False, f"nao foi possivel executar o teste: {exc}")

    err = (result.stderr or result.stdout or "").strip()
    if result.returncode == 0:
        return CheckResult(name, True, "sinal OK")
    short = err.splitlines()[-1] if err else f"codigo {result.returncode}"
    hint = ""
    low = short.lower()
    if "401" in low or "unauthorized" in low:
        hint = " (usuario/senha da camera incorretos?)"
    elif "timed out" in low or "timeout" in low or "10060" in low:
        hint = " (IP errado ou camera fora da rede?)"
    elif "connection refused" in low or "10061" in low:
        hint = " (porta 554 bloqueada ou camera offline?)"
    return CheckResult(name, False, f"{short}{hint}")


def list_serial_ports() -> list[tuple[str, str, bool]]:
    """Return (device, description, is_usb_candidate) for each COM/TTY port."""
    try:
        from serial.tools import list_ports
    except ImportError:
        return []

    from agent.buttons import is_usb_serial_candidate

    rows: list[tuple[str, str, bool]] = []
    for port in list_ports.comports():
        desc = port.description or port.device
        rows.append((port.device, desc, is_usb_serial_candidate(port)))
    return rows


def probe_button_hub(
    preferred_port: str = "auto",
    *,
    baudrate: int = 115200,
    timeout_seconds: float = 8.0,
) -> CheckResult:
    """Open the Arduino hub and wait for LANCEON_BUTTONS_READY (board resets on open)."""
    name = "Botoes USB (Arduino)"
    try:
        import serial
        from serial.tools import list_ports
    except ImportError:
        return CheckResult(name, False, "pyserial nao instalado no ambiente")

    from agent.buttons import is_usb_serial_candidate, resolve_serial_port, serial_port_candidates

    preferred = (preferred_port or "auto").strip()
    ports = serial_port_candidates(preferred)
    if not ports:
        all_ports = list(list_ports.comports())
        if not all_ports:
            return CheckResult(
                name,
                False,
                "nenhuma porta COM encontrada — conecte o Arduino via USB",
            )
        skipped = ", ".join(
            f"{p.device} ({p.description})"
            for p in all_ports
            if not is_usb_serial_candidate(p)
        )
        return CheckResult(
            name,
            False,
            "Arduino/CH340/CP210x nao encontrado. "
            + (f"Portas nativas ignoradas: {skipped}" if skipped else "Conecte a placa USB."),
        )

    errors: list[str] = []
    for port in ports:
        try:
            with serial.Serial(port, baudrate, timeout=1) as device:
                # Arduino resets when the port opens; READY is printed in setup().
                deadline = time.time() + timeout_seconds
                got_ready = False
                while time.time() < deadline:
                    raw = device.readline()
                    if not raw:
                        continue
                    message = raw.decode("utf-8", errors="ignore").strip()
                    if not message:
                        continue
                    if message.upper() == READY_TOKEN or READY_TOKEN in message.upper():
                        got_ready = True
                        break
                if got_ready:
                    return CheckResult(
                        name,
                        True,
                        f"placa OK em {port} (recebeu {READY_TOKEN})",
                    )
                errors.append(f"{port}: abriu mas nao enviou {READY_TOKEN}")
        except Exception as exc:
            low = str(exc).lower()
            if "access is denied" in low or "permission" in low or "busy" in low:
                errors.append(
                    f"{port}: em uso — pare o gravador no painel e teste de novo "
                    "(ou a placa ja esta OK com o agente)"
                )
            else:
                errors.append(f"{port}: {exc}")

    # Still report the preferred resolution for the message
    resolved = resolve_serial_port(preferred)
    detail = "; ".join(errors) if errors else "falha desconhecida"
    if resolved:
        detail = f"{detail}. Dica: grave o firmware lanceon_buttons.ino na placa."
    return CheckResult(name, False, detail)


def probe_ffmpeg_buffer(buffer_dir: Path, *, wait_seconds: float = 4.0) -> CheckResult:
    """After recorder start, check that at least one segment file appears."""
    name = f"Buffer ({buffer_dir.name})"
    deadline = time.time() + wait_seconds
    while time.time() < deadline:
        segments = list(buffer_dir.glob("segment_*.mp4"))
        live = [p for p in segments if p.stat().st_size > 0]
        if live:
            return CheckResult(name, True, f"{len(live)} segmento(s) gravando")
        time.sleep(0.4)
    stderr_path = buffer_dir / "ffmpeg.stderr.log"
    extra = ""
    if stderr_path.is_file():
        try:
            text = stderr_path.read_text(encoding="utf-8", errors="ignore").strip()
            if text:
                extra = " | " + text.splitlines()[-1]
        except OSError:
            pass
    return CheckResult(
        name,
        False,
        f"nenhum segmento em {wait_seconds:.0f}s — camera sem sinal?{extra}",
    )


def run_setup_diagnostics(
    cameras: list[tuple[int, str, str]],
    *,
    button_port: str = "auto",
    button_baudrate: int = 115200,
    check_buttons: bool = True,
) -> list[CheckResult]:
    """cameras: list of (index, name, rtsp_url)."""
    results: list[CheckResult] = []
    for index, cam_name, rtsp_url in cameras:
        result = probe_rtsp(rtsp_url)
        result.name = f"Camera {index} ({cam_name})"
        results.append(result)
    if check_buttons:
        results.append(probe_button_hub(button_port, baudrate=button_baudrate))
    return results


def format_report(results: list[CheckResult]) -> str:
    lines = ["======== DIAGNOSTICO LANCE ON ========", *[r.line() for r in results]]
    failed = [r for r in results if not r.ok]
    if failed:
        lines.append("--------------------------------------")
        lines.append(f"{len(failed)} item(ns) com problema — corrija antes de usar na quadra.")
    else:
        lines.append("--------------------------------------")
        lines.append("Tudo OK — aguardando botoes / app PRONTO.")
    lines.append("======================================")
    return "\n".join(lines)
