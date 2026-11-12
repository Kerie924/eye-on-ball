#!/usr/bin/env python3
"""Lance On Control — Windows app to start/stop capture and edit cameras / watermark."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import traceback
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

# Allow running from C:\LanceOn\capture or repo checkout
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

IS_WINDOWS = sys.platform.startswith("win")
MAX_CAMERAS = 6
BG = "#0f1117"
FG = "#f5f5f5"
MUTED = "#9ca3af"
GREEN = "#22c55e"
CARD = "#1a1f2e"
TASK_NAME = "LanceOnCapture"
DEFAULT_API_URL = "https://api.lanceonpara.com.br"
# Hide console windows for helper processes (status poll used to flash CMD/PowerShell).
_CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000) if IS_WINDOWS else 0
_DETACHED = getattr(subprocess, "DETACHED_PROCESS", 0x00000008) if IS_WINDOWS else 0
_CREATE_NEW_CONSOLE = getattr(subprocess, "CREATE_NEW_CONSOLE", 0x00000010) if IS_WINDOWS else 0
_STATUS_WINDOW_TITLE = "LanceOn Status"


def _run_hidden(command: list[str], **kwargs) -> subprocess.CompletedProcess:
    """subprocess.run without flashing a console window on Windows."""
    if IS_WINDOWS:
        kwargs.setdefault("creationflags", kwargs.get("creationflags", 0) | _CREATE_NO_WINDOW)
    kwargs.setdefault("capture_output", True)
    kwargs.setdefault("text", True)
    kwargs.setdefault("check", False)
    return subprocess.run(command, **kwargs)


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if IS_WINDOWS:
        # Avoid PowerShell/tasklist — OpenProcess is silent.
        try:
            import ctypes

            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            handle = ctypes.windll.kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION, False, pid
            )
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


def _pid_image_name(pid: int) -> str | None:
    """Return lowercase full image path for PID, or None if gone / inaccessible."""
    if pid <= 0 or not IS_WINDOWS:
        return None
    try:
        import ctypes
        from ctypes import wintypes

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid)
        )
        if not handle:
            return None
        try:
            buf = ctypes.create_unicode_buffer(1024)
            size = wintypes.DWORD(1024)
            ok = ctypes.windll.kernel32.QueryFullProcessImageNameW(
                handle, 0, buf, ctypes.byref(size)
            )
            if not ok:
                return None
            return buf.value.lower()
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
    except Exception:
        return None


def _error_log_path() -> Path:
    try:
        from agent.paths import program_data_root

        return program_data_root() / "logs" / "control-app-error.log"
    except Exception:
        return ROOT.parent / "logs" / "control-app-error.log"


def _fatal(message: str, exc: BaseException | None = None) -> None:
    """Show a visible error when the GUI cannot start (avoids silent bat flash-close)."""
    detail = message
    if exc is not None:
        detail = f"{message}\n\n{exc}\n\n{traceback.format_exc()}"
    log_path = _error_log_path()
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(detail, encoding="utf-8")
    except OSError:
        pass
    if IS_WINDOWS:
        try:
            import ctypes

            ctypes.windll.user32.MessageBoxW(0, detail[:1000], "Lance On — erro", 0x10)
            return
        except Exception:
            pass
    print(detail, file=sys.stderr)
    try:
        input("Press Enter to close...")
    except EOFError:
        pass


try:
    from tkinter import filedialog, messagebox
    import tkinter as tk
except Exception as _tk_exc:  # pragma: no cover - Windows install without tcl/tk
    _fatal(
        "Tkinter nao esta disponivel neste Python.\n"
        "Reinstale Python de https://www.python.org/downloads/\n"
        "e marque a opcao tcl/tk.",
        _tk_exc,
    )
    raise SystemExit(1) from _tk_exc

try:
    from agent.paths import (  # noqa: E402
        default_config_path,
        default_install_dir,
        default_log_dir,
        program_data_root,
    )
    from agent.yaml_util import safe_load  # noqa: E402
except Exception as _imp_exc:  # pragma: no cover
    _fatal("Falha ao importar o agente Lance On.", _imp_exc)
    raise SystemExit(1) from _imp_exc


def _rtsp_url(user: str, password: str, ip: str) -> str:
    return (
        f"rtsp://{quote(user, safe='')}:{quote(password, safe='')}@{ip.strip()}"
        ":554/cam/realmonitor?channel=1&subtype=0"
    )


def _parse_rtsp(url: str) -> tuple[str, str, str]:
    """Return (user, password, host) from an RTSP URL."""
    try:
        parsed = urlparse(url)
        user = unquote(parsed.username or "admin")
        password = unquote(parsed.password or "")
        host = parsed.hostname or ""
        return user, password, host
    except Exception:
        return "admin", "", ""


def _yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


class ControlApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Lance On — Controle da quadra")
        self.configure(bg=BG)
        self.minsize(720, 820)

        self.install_root = program_data_root()
        self.config_path = default_config_path()
        self.capture_dir = default_install_dir()
        self.log_dir = default_log_dir()
        self.watermark_dest = self.capture_dir / "assets" / "video-watermark.jpeg"

        self.api_url = tk.StringVar(value=DEFAULT_API_URL)
        self.device_key = tk.StringVar()
        self.camera_user = tk.StringVar(value="admin")
        self.camera_password = tk.StringVar()
        self.camera_count = tk.IntVar(value=2)
        self.watermark_path = tk.StringVar(value="")
        self.watermark_height_percent = tk.DoubleVar(value=16.0)
        self.status_text = tk.StringVar(value="Verificando...")
        self.health_text = tk.StringVar(value="Clique em “Testar conexoes” apos preencher os IPs.")
        self.camera_ips = [tk.StringVar() for _ in range(MAX_CAMERAS)]
        self._testing = False
        self._busy = False
        self._log_pos: int | None = None
        self._btn_iniciar: tk.Button | None = None
        self._btn_parar: tk.Button | None = None

        self._build()
        self._load_config()
        self._refresh_status()
        self.after(1500, self._poll_log_tail)
        self.after(4000, self._poll_status)

    def _build(self) -> None:
        outer = tk.Frame(self, bg=BG, padx=24, pady=20)
        outer.pack(fill=tk.BOTH, expand=True)

        tk.Label(outer, text="Lance On", fg=GREEN, bg=BG, font=("Segoe UI", 22, "bold")).pack(
            anchor="w"
        )
        tk.Label(
            outer,
            text="Controle do gravador — altere IPs e logo, depois salve e reinicie.",
            fg=MUTED,
            bg=BG,
            font=("Segoe UI", 11),
        ).pack(anchor="w", pady=(0, 4))
        tk.Label(
            outer,
            text="Botoes fixos Arduino: CAM1=D2/D3 … CAM6=D12/D13 (USB serial auto).",
            fg=MUTED,
            bg=BG,
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(0, 12))

        status = tk.Frame(outer, bg=CARD, padx=16, pady=12)
        status.pack(fill=tk.X, pady=(0, 12))
        tk.Label(status, text="Status do gravador", fg=MUTED, bg=CARD).pack(anchor="w")
        tk.Label(
            status, textvariable=self.status_text, fg=FG, bg=CARD, font=("Segoe UI", 12, "bold")
        ).pack(anchor="w")
        tk.Label(status, text="Cameras e botoes", fg=MUTED, bg=CARD).pack(anchor="w", pady=(8, 0))
        tk.Label(
            status,
            textvariable=self.health_text,
            fg=FG,
            bg=CARD,
            font=("Segoe UI", 10),
            justify="left",
            wraplength=600,
        ).pack(anchor="w")

        btn_row = tk.Frame(outer, bg=BG)
        btn_row.pack(fill=tk.X, pady=(0, 12))
        self._btn_iniciar = tk.Button(
            btn_row, text="Iniciar", bg=GREEN, fg="#052e16", command=self._start_capture, padx=12
        )
        self._btn_iniciar.pack(side=tk.LEFT, padx=(0, 8))
        self._btn_parar = tk.Button(
            btn_row, text="Parar", bg="#374151", fg=FG, command=self._stop_capture, padx=12
        )
        self._btn_parar.pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(
            btn_row,
            text="Testar conexoes",
            bg="#2563eb",
            fg="#eff6ff",
            command=self._test_connections,
            padx=12,
        ).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(
            btn_row,
            text="Ver status",
            bg="#0ea5e9",
            fg="#082f49",
            command=self._open_status_console,
            padx=12,
        ).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(
            btn_row, text="Abrir logs", bg="#374151", fg=FG, command=self._open_logs, padx=12
        ).pack(side=tk.LEFT)

        form = tk.Frame(outer, bg=CARD, padx=18, pady=16)
        form.pack(fill=tk.BOTH, expand=True)

        self._field(form, "URL da API", self.api_url)
        self._field(form, "Chave do dispositivo", self.device_key)
        self._field(form, "Usuario da camera", self.camera_user)
        self._field(form, "Senha da camera", self.camera_password, show="*")

        count_row = tk.Frame(form, bg=CARD)
        count_row.pack(fill=tk.X, pady=8)
        tk.Label(count_row, text="Quantidade de cameras", fg=FG, bg=CARD).pack(anchor="w")
        spin = tk.Spinbox(
            count_row,
            from_=1,
            to=MAX_CAMERAS,
            textvariable=self.camera_count,
            width=6,
            command=self._refresh_cameras,
        )
        spin.pack(anchor="w", pady=(4, 0))
        spin.bind("<KeyRelease>", lambda _e: self._refresh_cameras())
        spin.bind("<ButtonRelease-1>", lambda _e: self.after(50, self._refresh_cameras))

        self.camera_frame = tk.Frame(form, bg=CARD)
        self.camera_frame.pack(fill=tk.X, pady=8)
        self.ip_rows: list[tk.Frame] = []
        for index in range(MAX_CAMERAS):
            row = tk.Frame(self.camera_frame, bg=CARD)
            tk.Label(row, text=f"IP da camera {index + 1}", fg=FG, bg=CARD).pack(anchor="w")
            tk.Entry(row, textvariable=self.camera_ips[index], width=40).pack(
                anchor="w", pady=(2, 8)
            )
            self.ip_rows.append(row)

        mark = tk.Frame(form, bg=CARD)
        mark.pack(fill=tk.X, pady=8)
        tk.Label(mark, text="Logo / marca d'agua (imagem)", fg=FG, bg=CARD).pack(anchor="w")
        pick = tk.Frame(mark, bg=CARD)
        pick.pack(fill=tk.X)
        tk.Entry(pick, textvariable=self.watermark_path).pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Button(pick, text="Escolher...", command=self._pick_watermark).pack(
            side=tk.LEFT, padx=(8, 0)
        )

        size_row = tk.Frame(form, bg=CARD)
        size_row.pack(fill=tk.X, pady=8)
        tk.Label(
            size_row,
            text="Tamanho da logo no video (% da altura do quadro, 5–40)",
            fg=FG,
            bg=CARD,
        ).pack(anchor="w")
        size_controls = tk.Frame(size_row, bg=CARD)
        size_controls.pack(anchor="w", pady=(4, 0))
        tk.Spinbox(
            size_controls,
            from_=5,
            to=40,
            increment=1,
            textvariable=self.watermark_height_percent,
            width=8,
        ).pack(side=tk.LEFT)
        tk.Label(
            size_controls,
            text="  (padrao 16; 18–22 = grande e legivel)",
            fg=MUTED,
            bg=CARD,
        ).pack(side=tk.LEFT)

        tk.Button(
            outer,
            text="Salvar e reiniciar gravador",
            bg=GREEN,
            fg="#052e16",
            font=("Segoe UI", 13, "bold"),
            command=self._save_and_restart,
            pady=10,
        ).pack(fill=tk.X, pady=(16, 8))

        tk.Label(
            outer,
            text="Log ao vivo (capture.log). Iniciar abre a janela LanceOnCapture; Ver status e opcional.",
            fg=MUTED,
            bg=BG,
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(4, 2))
        self.log = tk.Text(
            outer,
            height=14,
            bg="#111827",
            fg=FG,
            relief=tk.FLAT,
            font=("Consolas", 9),
            wrap=tk.WORD,
        )
        self.log.pack(fill=tk.BOTH, expand=True)
        self._refresh_cameras()

    def _field(self, parent: tk.Frame, label: str, var: tk.StringVar, show: str = "") -> None:
        tk.Label(parent, text=label, fg=FG, bg=CARD).pack(anchor="w", pady=(8, 0))
        tk.Entry(parent, textvariable=var, show=show, width=48).pack(anchor="w", pady=(2, 0))

    def _refresh_cameras(self) -> None:
        try:
            count = int(self.camera_count.get())
        except (tk.TclError, ValueError):
            count = 1
        count = max(1, min(MAX_CAMERAS, count))
        for index, row in enumerate(self.ip_rows):
            if index < count:
                row.pack(fill=tk.X)
            else:
                row.pack_forget()

    def _pick_watermark(self) -> None:
        path = filedialog.askopenfilename(
            title="Logo / marca d'agua",
            filetypes=[("Imagens", "*.jpg *.jpeg *.png *.webp"), ("Todos", "*.*")],
        )
        if path:
            self.watermark_path.set(path)

    def _append(self, message: str) -> None:
        self.log.insert(tk.END, f"[painel] {message}\n")
        self.log.see(tk.END)

    def _capture_log_path(self) -> Path:
        return self.log_dir / "capture.log"

    def _focus_status_console(self) -> bool:
        """Bring an existing LanceOn Status window to the front. True if found."""
        if not IS_WINDOWS:
            return False
        try:
            import ctypes

            hwnd = ctypes.windll.user32.FindWindowW(None, _STATUS_WINDOW_TITLE)
            if not hwnd:
                return False
            ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            ctypes.windll.user32.SetForegroundWindow(hwnd)
            return True
        except Exception:
            return False

    def _open_status_console(self) -> None:
        """Open (or focus) a live CMD tail of capture.log — does not stop/start capture."""
        self.log_dir.mkdir(parents=True, exist_ok=True)
        log_path = self._capture_log_path()
        if not log_path.is_file():
            try:
                log_path.write_text("", encoding="utf-8")
            except OSError:
                pass
        if self._focus_status_console():
            self._append("Janela de status ja aberta — trazida para frente.")
            return
        if not IS_WINDOWS:
            self._append(f"Veja o log em: {log_path}")
            return
        # Escaped path for PowerShell single-quoted literal
        ps_path = str(log_path).replace("'", "''")
        ps_script = (
            f"$Host.UI.RawUI.WindowTitle = '{_STATUS_WINDOW_TITLE}'; "
            "Write-Host 'Lance On — status ao vivo (fechar esta janela NAO para o gravador)' "
            "-ForegroundColor Green; "
            f"Get-Content -LiteralPath '{ps_path}' -Tail 80 -Wait"
        )
        try:
            # Optional log tail only — does not start/stop capture.
            subprocess.Popen(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    ps_script,
                ],
                cwd=str(self.install_root),
                creationflags=_CREATE_NEW_CONSOLE,
            )
            self._append("Janela de status aberta (log ao vivo).")
        except Exception as exc:
            self._append(f"Nao foi possivel abrir a janela de status: {exc}")

    def _poll_log_tail(self) -> None:
        """Mirror capture.log into the panel without spawning CMD/PowerShell."""
        path = self._capture_log_path()
        try:
            if path.is_file():
                size = path.stat().st_size
                if self._log_pos is None:
                    self._log_pos = max(0, size - 12_000)
                if size < self._log_pos:
                    self._log_pos = 0
                if size > self._log_pos:
                    with path.open("r", encoding="utf-8", errors="ignore") as handle:
                        handle.seek(self._log_pos)
                        chunk = handle.read()
                        self._log_pos = handle.tell()
                    if chunk:
                        self.log.insert(tk.END, chunk)
                        if not chunk.endswith("\n"):
                            self.log.insert(tk.END, "\n")
                        # Cap widget size so the UI stays responsive
                        try:
                            line_count = int(self.log.index("end-1c").split(".")[0])
                            if line_count > 800:
                                self.log.delete("1.0", f"{line_count - 600}.0")
                        except (tk.TclError, ValueError):
                            pass
                        self.log.see(tk.END)
        except OSError:
            pass
        self.after(1500, self._poll_log_tail)

    def _load_config(self) -> None:
        if not self.config_path.is_file():
            self._append(f"Config nao encontrada: {self.config_path}")
            self._append("Rode o instalador (LanceOn-Setup.bat) primeiro.")
            return
        try:
            with self.config_path.open(encoding="utf-8") as handle:
                raw = safe_load(handle) or {}
        except Exception as exc:
            self._append(f"Erro ao ler config: {exc}")
            return

        self.api_url.set(str(raw.get("api_url") or DEFAULT_API_URL))
        self.device_key.set(str(raw.get("device_key") or ""))
        cameras = raw.get("cameras") or []
        self.camera_count.set(max(1, min(MAX_CAMERAS, len(cameras) or 2)))
        user = "admin"
        password = ""
        for index, cam in enumerate(cameras[:MAX_CAMERAS]):
            u, p, host = _parse_rtsp(str(cam.get("rtsp_url") or ""))
            if index == 0:
                user, password = u, p
            self.camera_ips[index].set(host)
        self.camera_user.set(user)
        self.camera_password.set(password)
        wm = raw.get("watermark_path")
        if wm:
            self.watermark_path.set(str(wm))
        try:
            pct = float(raw.get("watermark_height_percent", 16))
        except (TypeError, ValueError):
            pct = 16.0
        # Legacy configs used broken scale (main_h); values like 80 looked tiny.
        if pct > 40.0:
            self._append(
                f"Tamanho da logo {pct:.0f}% era da escala antiga (pequena). "
                "Ajustado para 16% da altura do video — use 18–22 se quiser maior."
            )
            pct = 16.0
        self.watermark_height_percent.set(max(5.0, min(40.0, pct)))
        self._refresh_cameras()
        self._append(f"Config carregada: {self.config_path}")

    def _pid_file(self) -> Path:
        return self.install_root / "logs" / "capture.pid"

    def _is_running(self) -> bool:
        """True if capture agent process is alive (PID file — no PowerShell/CMD flash)."""
        pid_path = self._pid_file()
        if not pid_path.is_file():
            return False
        try:
            pid = int(pid_path.read_text(encoding="utf-8").strip().split()[0])
        except (OSError, ValueError, IndexError):
            return False
        # Live PID required. If we can read the image name, it must be python/pythonw
        # (PID reuse by unrelated apps must not block Iniciar / fake "em execucao").
        if not _pid_alive(pid):
            try:
                pid_path.unlink(missing_ok=True)
            except OSError:
                pass
            return False
        if IS_WINDOWS:
            image = _pid_image_name(pid)
            if image is not None and Path(image).name not in ("python.exe", "pythonw.exe"):
                try:
                    pid_path.unlink(missing_ok=True)
                except OSError:
                    pass
                return False
        return True

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        state = tk.DISABLED if busy else tk.NORMAL
        for btn in (self._btn_iniciar, self._btn_parar):
            if btn is not None:
                try:
                    btn.configure(state=state)
                except tk.TclError:
                    pass

    def _read_log_health_hints(self) -> str:
        log_path = self.log_dir / "capture.log"
        if not log_path.is_file():
            return ""
        try:
            lines = log_path.read_text(encoding="utf-8", errors="ignore").splitlines()[-80:]
        except OSError:
            return ""
        hints: list[str] = []
        for line in lines:
            if "DIAGNOSTICO LANCE ON" in line or "[FALHOU]" in line or "[OK]" in line:
                # keep the message after the logger prefix when possible
                if "[FALHOU]" in line or "[OK]" in line:
                    part = line.split("] ", 2)[-1] if "] " in line else line
                    if part not in hints:
                        hints.append(part)
            elif "Serial button hub READY" in line:
                hints.append("Botoes: placa USB pronta")
            elif "No serial button board" in line or "Nenhuma placa Arduino" in line:
                hints.append("Botoes: placa USB nao encontrada")
            elif "Camera" in line and "buffer stopped" in line:
                hints.append(line.split("] ", 2)[-1])
            elif "Camera" in line and "buffer healthy" in line:
                hints.append(line.split("] ", 2)[-1])
        return "\n".join(hints[-8:])

    def _refresh_status(self) -> None:
        try:
            running = self._is_running()
        except Exception:
            running = False
        if running:
            self.status_text.set("Gravador em execucao")
        else:
            self.status_text.set("Gravador parado")
        if not self._testing:
            hints = self._read_log_health_hints()
            if hints:
                self.health_text.set(hints)

    def _poll_status(self) -> None:
        self._refresh_status()
        self.after(5000, self._poll_status)

    def _venv_python(self, *, console: bool = False) -> Path | None:
        """Return venv interpreter. console=True prefers python.exe (visible logs)."""
        names = ("python.exe", "pythonw.exe") if console else ("pythonw.exe", "python.exe")
        for name in names:
            path = self.capture_dir / ".venv" / "Scripts" / name
            if path.is_file():
                return path
        return None

    def _start_capture_process(self) -> None:
        """Start capture and wait until capture.pid is owned by a live python process.

        On Windows, opens one titled LanceOnCapture console with live agent logs.
        ffmpeg stays hidden (CREATE_NO_WINDOW in buffer.py). Closing that console
        stops capture — use Parar for a clean stop.
        """
        # Never leave a stale lock that blocks a new instance.
        if not self._is_running():
            try:
                self._pid_file().unlink(missing_ok=True)
            except OSError:
                pass

        python = self._venv_python(console=True)
        run_py = self.capture_dir / "run.py"
        if python and run_py.is_file() and self.config_path.is_file():
            kwargs: dict = {
                "cwd": str(self.capture_dir),
                "stdin": subprocess.DEVNULL,
            }
            if IS_WINDOWS:
                # Own visible console = live capture.log stream (title set in service.py).
                # Do NOT redirect stdout/stderr or the window stays blank.
                # Do NOT use DETACHED_PROCESS / pythonw here — operators need this window.
                kwargs["creationflags"] = _CREATE_NEW_CONSOLE
            subprocess.Popen(
                [str(python), str(run_py), "--config", str(self.config_path)],
                **kwargs,
            )
            for _ in range(40):  # up to ~10s
                time.sleep(0.25)
                if self._is_running():
                    return
            raise RuntimeError(
                "Capture nao permaneceu ativo. Veja logs\\capture.log e logs\\capture-crash.log"
            )

        _run_hidden(["schtasks", "/Run", "/TN", TASK_NAME], timeout=30)
        for _ in range(40):
            time.sleep(0.25)
            if self._is_running():
                return
        raise RuntimeError(
            "Capture nao iniciou via Agendador de Tarefas. "
            "Veja logs\\capture.log e logs\\capture-crash.log"
        )

    def _stop_capture_process(self) -> None:
        """Stop every Lance On capture instance (PID, window title, schtasks, sweep)."""
        pid_path = self._pid_file()
        pids: set[int] = set()
        if pid_path.is_file():
            try:
                pids.add(int(pid_path.read_text(encoding="utf-8").strip().split()[0]))
            except (OSError, ValueError, IndexError):
                pass
        for pid in list(pids):
            if pid > 0 and _pid_alive(pid):
                _run_hidden(["taskkill", "/PID", str(pid), "/T", "/F"], timeout=30)

        # Visible console started with title LanceOnCapture
        _run_hidden(
            ["taskkill", "/F", "/FI", "WINDOWTITLE eq LanceOnCapture*", "/T"],
            timeout=30,
        )
        # End scheduled task if it launched capture
        _run_hidden(["schtasks", "/End", "/TN", TASK_NAME], timeout=30)
        # Sweep leftovers: any python running our run.py --config (hidden PowerShell)
        _run_hidden(
            [
                "powershell",
                "-NoProfile",
                "-WindowStyle",
                "Hidden",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | "
                "Where-Object { "
                "$_.CommandLine -and ("
                "($_.CommandLine -like '*run.py*--config*') -or "
                "($_.CommandLine -like '*run.py* --config*')"
                ") -and ("
                "$_.CommandLine -like '*LanceOn*' -or "
                "$_.CommandLine -like '*capture\\\\run.py*' -or "
                "$_.CommandLine -like '*capture/run.py*'"
                ") } | "
                "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }",
            ],
            timeout=30,
        )
        try:
            pid_path.unlink(missing_ok=True)
        except OSError:
            pass
        # Confirm death so a following Iniciar does not hit the single-instance lock.
        for _ in range(20):
            still_alive = False
            for pid in list(pids):
                if _pid_alive(pid):
                    still_alive = True
                    _run_hidden(["taskkill", "/PID", str(pid), "/T", "/F"], timeout=15)
            if not still_alive and not self._is_running():
                break
            time.sleep(0.25)
        try:
            pid_path.unlink(missing_ok=True)
        except OSError:
            pass

    def _test_connections(self) -> None:
        if self._testing:
            return
        settings = self._collect_settings()
        if not settings:
            return
        running = False
        try:
            running = self._is_running()
        except Exception:
            running = False
        if running:
            if not messagebox.askyesno(
                "Lance On — teste",
                "O gravador esta em execucao e pode ocupar a porta USB dos botoes.\n\n"
                "Continuar mesmo assim?\n"
                "(Cameras serao testadas; botoes podem falhar com 'em uso'.)",
            ):
                return
        self._testing = True
        self.health_text.set("Testando cameras e botoes USB... aguarde.")
        self._append("Iniciando teste de conexoes...")

        def work() -> None:
            try:
                from agent.diagnostics import format_report, run_setup_diagnostics

                cameras = []
                user = settings["camera_user"]
                password = settings["camera_password"]
                for item in settings["cameras"]:
                    url = _rtsp_url(user, password, item["ip"])
                    cameras.append((int(item["index"]), f"Camera {item['index']}", url))
                results = run_setup_diagnostics(
                    cameras,
                    button_port="auto",
                    check_buttons=True,
                )
                report = format_report(results)
                failed = [item for item in results if not item.ok]

                def done() -> None:
                    self._testing = False
                    self.health_text.set("\n".join(item.line() for item in results))
                    for line in report.splitlines():
                        self._append(line)
                    if failed:
                        messagebox.showerror(
                            "Lance On — teste",
                            "Algumas conexoes falharam.\n\n"
                            + "\n".join(item.line() for item in failed)
                            + "\n\nCorrija IP/senha/Arduino e teste de novo.",
                        )
                    else:
                        messagebox.showinfo(
                            "Lance On — teste",
                            "Cameras e botoes OK.\n"
                            "Pode salvar/reiniciar e usar a quadra.",
                        )

                self.after(0, done)
            except Exception as exc:
                self.after(
                    0,
                    lambda: (
                        setattr(self, "_testing", False),
                        self.health_text.set(f"Erro no teste: {exc}"),
                        self._append(f"Erro no teste: {exc}"),
                        messagebox.showerror("Lance On — teste", str(exc)),
                    ),
                )

        threading.Thread(target=work, daemon=True).start()

    def _start_capture(self) -> None:
        if self._busy:
            return
        self._set_busy(True)
        self._append("Iniciando gravador...")

        def work() -> None:
            error: str | None = None
            already = False
            try:
                if self._is_running():
                    already = True
                else:
                    self._start_capture_process()
                    if not self._is_running():
                        error = (
                            "Gravador nao ficou ativo apos iniciar. "
                            "Veja logs\\capture.log e a janela LanceOnCapture."
                        )
            except Exception as exc:
                error = str(exc)

            def done() -> None:
                self._set_busy(False)
                self._refresh_status()
                if already:
                    self._append("Gravador ja esta em execucao.")
                    self.status_text.set("Gravador em execucao")
                elif error:
                    self._append(f"Falha ao iniciar: {error}")
                    self.status_text.set("Gravador parado")
                    messagebox.showerror("Lance On — Iniciar", error)
                else:
                    self._append("Gravador iniciado. Janela LanceOnCapture = log ao vivo.")
                    self.status_text.set("Gravador em execucao")

            self.after(0, done)

        threading.Thread(target=work, daemon=True).start()

    def _stop_capture(self) -> None:
        if self._busy:
            return
        self._set_busy(True)
        self._append("Parando gravador...")

        def work() -> None:
            error: str | None = None
            try:
                self._stop_capture_process()
                if self._is_running():
                    error = (
                        "Ainda ha processo do gravador ativo apos Parar. "
                        "Tente de novo ou feche a janela LanceOnCapture."
                    )
            except Exception as exc:
                error = str(exc)

            def done() -> None:
                self._set_busy(False)
                self._refresh_status()
                if error:
                    self._append(f"Falha ao parar: {error}")
                    messagebox.showerror("Lance On — Parar", error)
                else:
                    self._append("Gravador parado.")
                    self.status_text.set("Gravador parado")

            self.after(0, done)

        threading.Thread(target=work, daemon=True).start()

    def _open_logs(self) -> None:
        self.log_dir.mkdir(parents=True, exist_ok=True)
        if IS_WINDOWS:
            os.startfile(str(self.log_dir))  # type: ignore[attr-defined]
        else:
            subprocess.run(["xdg-open", str(self.log_dir)], check=False)

    def _collect_settings(self) -> dict | None:
        if not self.device_key.get().strip():
            messagebox.showerror("Lance On", "Informe a chave do dispositivo.")
            return None
        if not self.camera_password.get():
            messagebox.showerror("Lance On", "Informe a senha das cameras.")
            return None
        try:
            count = int(self.camera_count.get())
        except (tk.TclError, ValueError):
            messagebox.showerror("Lance On", "Quantidade de cameras invalida.")
            return None
        cameras = []
        for index in range(count):
            ip = self.camera_ips[index].get().strip()
            if not ip:
                messagebox.showerror("Lance On", f"Informe o IP da camera {index + 1}.")
                return None
            cameras.append({"index": index + 1, "ip": ip})
        return {
            "api_url": self.api_url.get().strip() or DEFAULT_API_URL,
            "device_key": self.device_key.get().strip(),
            "camera_user": self.camera_user.get().strip() or "admin",
            "camera_password": self.camera_password.get(),
            "cameras": cameras,
            "watermark_path": self.watermark_path.get().strip() or None,
            "watermark_height_percent": float(self.watermark_height_percent.get()),
            "use_gpio": True,
        }

    def _write_config(self, settings: dict) -> None:
        self.install_root.mkdir(parents=True, exist_ok=True)
        (self.install_root / "data").mkdir(parents=True, exist_ok=True)
        (self.install_root / "logs").mkdir(parents=True, exist_ok=True)
        self.watermark_dest.parent.mkdir(parents=True, exist_ok=True)

        selected = settings.get("watermark_path")
        if selected:
            src = Path(str(selected)).expanduser()
            if src.is_file() and src.resolve() != self.watermark_dest.resolve():
                shutil.copy2(src, self.watermark_dest)
                self._append(f"Logo atualizada: {self.watermark_dest}")
        elif not self.watermark_dest.is_file():
            bundled = self.capture_dir / "assets" / "video-watermark.jpeg"
            if bundled.is_file():
                shutil.copy2(bundled, self.watermark_dest)

        user = settings["camera_user"]
        password = settings["camera_password"]
        use_buttons = bool(settings.get("use_gpio", True))
        try:
            from windows_pins import button_hub_yaml, camera_button_yaml
        except ImportError:
            import sys as _sys

            _sys.path.insert(0, str(self.capture_dir))
            from windows_pins import button_hub_yaml, camera_button_yaml

        camera_lines = []
        for item in settings["cameras"]:
            index = int(item["index"])
            camera_lines.append(
                "\n".join(
                    [
                        f"  - index: {index}",
                        f"    name: Camera {index}",
                        f"    rtsp_url: {_yaml_quote(_rtsp_url(user, password, item['ip']))}",
                        camera_button_yaml(index, enabled=use_buttons),
                    ]
                )
            )

        content = f"""# Updated by Lance On Control
# Fixed button pairs: CAM1=D2+D3 … CAM6=D12+D13 (Arduino USB)
api_url: {_yaml_quote(settings['api_url'])}
device_key: {_yaml_quote(settings['device_key'])}

buffer_seconds: 300
clip_seconds: 30
segment_seconds: 2
heartbeat_seconds: 60
button_cooldown_seconds: 3
queue_max_hours: 48
queue_max_mb: 4096
upload_retry_seconds: 20

{button_hub_yaml(port="auto")}

cameras:
{chr(10).join(camera_lines)}

data_dir: {_yaml_quote(str((self.install_root / 'data')).replace(chr(92), '/'))}
watermark_path: {_yaml_quote(str(self.watermark_dest).replace(chr(92), '/'))}
watermark_height_percent: {max(5.0, min(40.0, float(settings.get('watermark_height_percent', 16))))}
"""
        self.config_path.write_text(content, encoding="utf-8")
        self._append(f"Config salva: {self.config_path}")
        self._append(
            f"Tamanho da logo: {max(5.0, min(40.0, float(settings.get('watermark_height_percent', 16))))}% da altura do video"
        )
        if use_buttons:
            self._append(
                "Botoes fixos: CAM1=D2/D3 CAM2=D4/D5 CAM3=D6/D7 "
                "CAM4=D8/D9 CAM5=D10/D11 CAM6=D12/D13"
            )

    def _save_and_restart(self) -> None:
        if self._busy:
            return
        settings = self._collect_settings()
        if not settings:
            return
        self._set_busy(True)
        self._append("Parando gravador...")

        def work() -> None:
            error: str | None = None
            running = False
            try:
                self._stop_capture_process()
                time.sleep(1.0)
                self._write_config(settings)
                self.after(0, lambda: self._append("Iniciando gravador..."))
                self._start_capture_process()
                running = self._is_running()
                if not running:
                    error = (
                        "Config salva, mas o gravador nao iniciou. "
                        "Veja logs\\capture.log e tente Iniciar."
                    )
            except Exception as exc:
                error = f"Falha ao salvar: {exc}"

            def done() -> None:
                self._set_busy(False)
                self._refresh_status()
                if error:
                    self._append(error)
                    messagebox.showerror("Lance On", error)
                else:
                    self._append("Pronto. IPs/logo aplicados. Gravador em execucao.")
                    messagebox.showinfo(
                        "Lance On",
                        "Configuracao salva e gravador reiniciado.\n"
                        "A janela LanceOnCapture mostra o log ao vivo.",
                    )

            self.after(0, done)

        threading.Thread(target=work, daemon=True).start()


def main() -> int:
    if not IS_WINDOWS:
        print("This control app is intended for Windows court PCs.", file=sys.stderr)
    try:
        app = ControlApp()
        app.mainloop()
        return 0
    except Exception as exc:
        _fatal("O painel Lance On nao conseguiu abrir.", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
