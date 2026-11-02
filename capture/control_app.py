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
        self.minsize(680, 760)

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
        self.watermark_height_percent = tk.DoubleVar(value=28.0)
        self.status_text = tk.StringVar(value="Verificando...")
        self.health_text = tk.StringVar(value="Clique em “Testar conexoes” apos preencher os IPs.")
        self.camera_ips = [tk.StringVar() for _ in range(MAX_CAMERAS)]
        self._testing = False

        self._build()
        self._load_config()
        self._refresh_status()
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
        tk.Button(
            btn_row, text="Iniciar", bg=GREEN, fg="#052e16", command=self._start_capture, padx=12
        ).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(
            btn_row, text="Parar", bg="#374151", fg=FG, command=self._stop_capture, padx=12
        ).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(
            btn_row,
            text="Testar conexoes",
            bg="#2563eb",
            fg="#eff6ff",
            command=self._test_connections,
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
            text="Tamanho da logo no video (% da altura do quadro, 5–80)",
            fg=FG,
            bg=CARD,
        ).pack(anchor="w")
        size_controls = tk.Frame(size_row, bg=CARD)
        size_controls.pack(anchor="w", pady=(4, 0))
        tk.Spinbox(
            size_controls,
            from_=5,
            to=80,
            increment=1,
            textvariable=self.watermark_height_percent,
            width=8,
        ).pack(side=tk.LEFT)
        tk.Label(
            size_controls,
            text="  (padrao 28 — maior = logo maior)",
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

        self.log = tk.Text(outer, height=6, bg="#111827", fg=FG, relief=tk.FLAT)
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
        self.log.insert(tk.END, message + "\n")
        self.log.see(tk.END)

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
            pct = float(raw.get("watermark_height_percent", 28))
        except (TypeError, ValueError):
            pct = 28.0
        self.watermark_height_percent.set(max(5.0, min(80.0, pct)))
        self._refresh_cameras()
        self._append(f"Config carregada: {self.config_path}")

    def _capture_pids(self) -> list[str]:
        """PIDs of capture run.py. Avoids wmic (removed on many Windows 11 PCs)."""
        ps = (
            "Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | "
            "Where-Object { $_.CommandLine -and "
            "($_.CommandLine -like '*LanceOn*run.py*' -or "
            "$_.CommandLine -like '*lance-on*run.py*') } | "
            "Select-Object -ExpandProperty ProcessId"
        )
        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    ps,
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=20,
            )
            return re.findall(r"\d+", result.stdout or "")
        except (OSError, subprocess.TimeoutExpired):
            return []

    def _is_running(self) -> bool:
        if not IS_WINDOWS:
            return False
        try:
            result = subprocess.run(
                ["schtasks", "/Query", "/TN", TASK_NAME],
                capture_output=True,
                text=True,
                check=False,
                timeout=15,
            )
            text = (result.stdout or "") + (result.stderr or "")
            task_running = result.returncode == 0 and "Running" in text
        except (OSError, subprocess.TimeoutExpired):
            task_running = False
        return task_running or bool(self._capture_pids())

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
        self.after(4000, self._poll_status)

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
        def work() -> None:
            start_bat = self.install_root / "start-capture.bat"
            if start_bat.is_file():
                subprocess.run(["cmd", "/c", str(start_bat)], check=False)
            else:
                subprocess.run(["schtasks", "/Run", "/TN", TASK_NAME], check=False)
            self.after(0, lambda: (self._append("Comando iniciar enviado."), self._refresh_status()))

        threading.Thread(target=work, daemon=True).start()

    def _stop_capture(self) -> None:
        def work() -> None:
            stop_bat = self.install_root / "stop-capture.bat"
            if stop_bat.is_file():
                subprocess.run(["cmd", "/c", str(stop_bat)], check=False)
            else:
                subprocess.run(["schtasks", "/End", "/TN", TASK_NAME], check=False)
            self.after(0, lambda: (self._append("Comando parar enviado."), self._refresh_status()))

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
watermark_height_percent: {max(5.0, min(80.0, float(settings.get('watermark_height_percent', 28))))}
"""
        self.config_path.write_text(content, encoding="utf-8")
        self._append(f"Config salva: {self.config_path}")
        self._append(
            f"Tamanho da logo: {max(5.0, min(80.0, float(settings.get('watermark_height_percent', 28))))}%"
        )
        if use_buttons:
            self._append(
                "Botoes fixos: CAM1=D2/D3 CAM2=D4/D5 CAM3=D6/D7 "
                "CAM4=D8/D9 CAM5=D10/D11 CAM6=D12/D13"
            )

    def _save_and_restart(self) -> None:
        settings = self._collect_settings()
        if not settings:
            return

        def work() -> None:
            try:
                self.after(0, lambda: self._append("Parando gravador..."))
                stop_bat = self.install_root / "stop-capture.bat"
                if stop_bat.is_file():
                    subprocess.run(["cmd", "/c", str(stop_bat)], check=False)
                else:
                    subprocess.run(["schtasks", "/End", "/TN", TASK_NAME], check=False)
                self._write_config(settings)
                self.after(0, lambda: self._append("Iniciando gravador..."))
                start_bat = self.install_root / "start-capture.bat"
                if start_bat.is_file():
                    subprocess.run(["cmd", "/c", str(start_bat)], check=False)
                else:
                    subprocess.run(["schtasks", "/Run", "/TN", TASK_NAME], check=False)
                self.after(
                    0,
                    lambda: (
                        self._append("Pronto. IPs/logo aplicados."),
                        self._refresh_status(),
                        messagebox.showinfo(
                            "Lance On",
                            "Configuracao salva e gravador reiniciado.",
                        ),
                    ),
                )
            except Exception as exc:
                self.after(
                    0,
                    lambda: messagebox.showerror("Lance On", f"Falha ao salvar: {exc}"),
                )

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
