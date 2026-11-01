#!/usr/bin/env python3
"""Lance On Setup App — court capture installer (Ubuntu + Windows)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

SOURCE_DIR = Path(__file__).resolve().parent
IS_WINDOWS = sys.platform.startswith("win")
INSTALLER = SOURCE_DIR / ("install_windows.py" if IS_WINDOWS else "install_capture.py")
DEFAULT_API_URL = "https://api.lanceonpara.com.br"
MAX_CAMERAS = 6
BG = "#0f1117"
FG = "#f5f5f5"
MUTED = "#9ca3af"
GREEN = "#22c55e"
CARD = "#1a1f2e"


class SetupApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Lance On — Instalacao da quadra")
        self.configure(bg=BG)
        self.minsize(640, 720)
        self.watermark_path = tk.StringVar(value="")
        self.api_url = tk.StringVar(value=DEFAULT_API_URL)
        self.device_key = tk.StringVar()
        self.camera_count = tk.IntVar(value=2)
        self.camera_user = tk.StringVar(value="admin")
        self.camera_password = tk.StringVar()
        self.use_gpio = tk.BooleanVar(value=True)
        self.camera_ips = [tk.StringVar() for _ in range(MAX_CAMERAS)]
        self._build()
        self._refresh_cameras()

    def _button_label(self) -> str:
        if IS_WINDOWS:
            return "Botoes fisicos USB/teclado (F1=cam1, F2=cam2, ...)"
        return "Um botao fisico por camera (GPIO17, GPIO22, ... no Mini PC)"

    def _build(self) -> None:
        outer = tk.Frame(self, bg=BG, padx=24, pady=20)
        outer.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            outer,
            text="Lance On",
            fg=GREEN,
            bg=BG,
            font=("Sans", 22, "bold"),
        ).pack(anchor="w")
        platform = "Windows" if IS_WINDOWS else "Ubuntu"
        tk.Label(
            outer,
            text=f"Instale o gravador da quadra ({platform}). O painel admin fica na nuvem.",
            fg=MUTED,
            bg=BG,
            font=("Sans", 11),
        ).pack(anchor="w", pady=(0, 16))

        form = tk.Frame(outer, bg=CARD, padx=18, pady=16)
        form.pack(fill=tk.BOTH, expand=True)

        self._field(form, "URL da API", self.api_url)
        self._field(form, "Chave do dispositivo (painel admin)", self.device_key)
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

        mark_row = tk.Frame(form, bg=CARD)
        mark_row.pack(fill=tk.X, pady=8)
        tk.Label(mark_row, text="Imagem da marca d'agua (opcional)", fg=FG, bg=CARD).pack(
            anchor="w"
        )
        pick = tk.Frame(mark_row, bg=CARD)
        pick.pack(fill=tk.X)
        tk.Entry(pick, textvariable=self.watermark_path).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )
        tk.Button(pick, text="Escolher...", command=self._pick_watermark).pack(
            side=tk.LEFT, padx=(8, 0)
        )

        tk.Checkbutton(
            form,
            text=self._button_label(),
            variable=self.use_gpio,
            fg=FG,
            bg=CARD,
            selectcolor=BG,
            activebackground=CARD,
            activeforeground=FG,
        ).pack(anchor="w", pady=8)

        self.install_btn = tk.Button(
            outer,
            text="Instalar e iniciar",
            bg=GREEN,
            fg="#052e16",
            font=("Sans", 13, "bold"),
            command=self._install,
            pady=10,
        )
        self.install_btn.pack(fill=tk.X, pady=(16, 8))

        self.status = tk.Text(outer, height=8, bg="#111827", fg=FG, relief=tk.FLAT)
        self.status.pack(fill=tk.BOTH, expand=True)

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
            title="Marca d'agua",
            filetypes=[
                ("Imagens", "*.jpg *.jpeg *.png *.webp"),
                ("Todos", "*.*"),
            ],
        )
        if path:
            self.watermark_path.set(path)

    def _log(self, message: str) -> None:
        self.status.insert(tk.END, message + "\n")
        self.status.see(tk.END)
        self.update_idletasks()

    def _run_installer(self, settings_path: str) -> subprocess.CompletedProcess:
        python = resolve_windows_python() if IS_WINDOWS else sys_executable()
        if IS_WINDOWS:
            # Stage under C:\LanceOn (visible on PT-BR PCs; no ProgramData required).
            # Avoids accented paths like "Área de Trabalho" that break UAC .bat elevation.
            if str(SOURCE_DIR) not in sys.path:
                sys.path.insert(0, str(SOURCE_DIR))
            from agent.paths import program_data_root

            install_home = program_data_root()
            try:
                install_home.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                return subprocess.CompletedProcess(
                    ["install_windows.py"],
                    1,
                    f"Nao foi possivel criar {install_home}: {exc}\n"
                    "Rode o Setup como Administrador ou defina LANCEON_HOME.",
                    "",
                )

            stage_root = install_home / "setup-staging"
            stage_root.mkdir(parents=True, exist_ok=True)
            staged_source = stage_root / "capture"
            if staged_source.exists():
                shutil.rmtree(staged_source)
            shutil.copytree(
                SOURCE_DIR,
                staged_source,
                ignore=shutil.ignore_patterns(
                    ".venv", "__pycache__", "*.pyc", ".git", "setup-staging"
                ),
            )
            staged_settings = stage_root / "settings.json"
            shutil.copy2(settings_path, staged_settings)
            staged_installer = staged_source / "install_windows.py"
            log_path = stage_root / "lanceon-install.log"
            wrapper = stage_root / "lanceon-install-run.bat"
            if log_path.exists():
                log_path.unlink(missing_ok=True)

            installer_args = [
                str(staged_installer),
                "--source",
                str(staged_source),
                "--settings",
                str(staged_settings),
            ]
            quoted = " ".join(f'"{a}"' for a in [python, *installer_args])
            lines = [
                "@echo off",
                "setlocal",
                "chcp 65001 >nul",
                f'cd /d "{staged_source}"',
                f"{quoted} > \"{log_path}\" 2>&1",
                "exit /b %ERRORLEVEL%",
            ]
            wrapper.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")

            wrapper_ps = str(wrapper).replace("'", "''")
            python_ps = python.replace("'", "''")
            home_ps = str(install_home).replace("'", "''")
            ps = (
                f"if (-not (Test-Path -LiteralPath '{python_ps}')) {{ "
                f"Write-Error ('Python not found: ' + '{python_ps}'); exit 1 }}; "
                f"if (-not (Test-Path -LiteralPath '{wrapper_ps}')) {{ "
                f"Write-Error ('Wrapper not found: ' + '{wrapper_ps}'); exit 1 }}; "
                f"$p = Start-Process -FilePath 'cmd.exe' "
                f"-ArgumentList '/c','\"\"{wrapper_ps}\"\"' "
                f"-Verb RunAs -Wait -PassThru; "
                f"if ($null -eq $p) {{ Write-Error 'UAC cancelado ou falhou.'; exit 1 }}; "
                f"exit $p.ExitCode"
            )
            result = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
                capture_output=True,
                text=True,
            )
            out = (
                f"Python: {python}\n"
                f"Install home: {home_ps}\n"
                f"Staging: {stage_root}\n"
                f"Installer log: {log_path}\n"
            )
            if log_path.exists():
                out += log_path.read_text(encoding="utf-8", errors="ignore")
            else:
                out += (
                    "(log de instalacao nao foi criado — a elevacao UAC pode ter falhado)\n"
                )
            out += (result.stdout or "") + (result.stderr or "")
            path_err = (
                "cannot find the specified path" in out.lower()
                or "nao pode encontrar o caminho" in out.lower()
                or "não pode encontrar o caminho" in out.lower()
            )
            if path_err and "WindowsApps" in python:
                out += (
                    "\nDICA: Python da Microsoft Store detectado. Instale Python 3.12+ de "
                    "https://www.python.org/downloads/ com 'Add python.exe to PATH'.\n"
                )
            elif path_err:
                out += (
                    "\nDICA: Copie a pasta capture para C:\\LanceOn\\setup-src (sem acentos) "
                    "e rode LanceOn-Setup.bat de la.\n"
                )
            code = 0 if "INSTALL_OK" in out else (result.returncode or 1)
            return subprocess.CompletedProcess(["install_windows.py"], code, out, "")

        installer_args = [
            str(INSTALLER),
            "--source",
            str(SOURCE_DIR),
            "--settings",
            settings_path,
        ]
        if shutil.which("pkexec"):
            command = ["pkexec", python, *installer_args]
        else:
            command = ["sudo", python, *installer_args]
        return subprocess.run(command, capture_output=True, text=True)

    def _install(self) -> None:
        try:
            count = int(self.camera_count.get())
        except (tk.TclError, ValueError):
            messagebox.showerror("Lance On", "Informe a quantidade de cameras (1 a 6).")
            return
        if not self.device_key.get().strip():
            messagebox.showerror("Lance On", "Cole a chave do dispositivo do painel admin.")
            return
        if not self.camera_password.get():
            messagebox.showerror("Lance On", "Informe a senha das cameras.")
            return

        cameras = []
        for index in range(count):
            ip = self.camera_ips[index].get().strip()
            if not ip:
                messagebox.showerror("Lance On", f"Informe o IP da camera {index + 1}.")
                return
            cameras.append({"index": index + 1, "ip": ip})

        settings = {
            "api_url": self.api_url.get().strip() or DEFAULT_API_URL,
            "device_key": self.device_key.get().strip(),
            "camera_user": self.camera_user.get().strip() or "admin",
            "camera_password": self.camera_password.get(),
            "cameras": cameras,
            "watermark_path": self.watermark_path.get().strip() or None,
            "use_gpio": bool(self.use_gpio.get()),
        }

        handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        try:
            json.dump(settings, handle)
            handle.close()
            try:
                os.chmod(handle.name, 0o600)
            except OSError:
                pass
            self.install_btn.configure(state=tk.DISABLED, text="Instalando...")
            self._log("Solicitando permissao de administrador e instalando...")
            if IS_WINDOWS:
                self._log("Windows: FFmpeg, Python venv e tarefa de inicializacao.")
            else:
                self._log("Ubuntu: FFmpeg, Python, GPIO e servico systemd.")
            result = self._run_installer(handle.name)
            output = (result.stdout or "") + (result.stderr or "")
            self._log(output.strip() or "(sem saida)")
            if result.returncode == 0 and "INSTALL_OK" in output:
                if IS_WINDOWS:
                    msg = (
                        "Instalacao concluida.\n\n"
                        "Pasta: C:\\LanceOn\\\n"
                        "Config: C:\\LanceOn\\config.yaml\n"
                        "O gravador inicia sozinho no login do usuario."
                    )
                else:
                    msg = (
                        "Instalacao concluida.\n"
                        "O gravador inicia sozinho quando o Mini PC ligar."
                    )
                messagebox.showinfo("Lance On", msg)
            else:
                messagebox.showerror(
                    "Lance On",
                    "A instalacao falhou. Veja o log na parte de baixo da janela.",
                )
        finally:
            Path(handle.name).unlink(missing_ok=True)
            self.install_btn.configure(state=tk.NORMAL, text="Instalar e iniciar")


def sys_executable() -> str:
    if IS_WINDOWS:
        return sys.executable
    return "/usr/bin/python3"


def resolve_windows_python() -> str:
    """Prefer a real python.exe (3.11+), including 3.15. Skip Microsoft Store stub."""
    candidates: list[str] = []
    current = sys.executable or ""
    if current:
        candidates.append(current)

    for minor in (15, 14, 13, 12, 11):
        try:
            result = subprocess.run(
                ["py", f"-3.{minor}", "-c", "import sys; print(sys.executable)"],
                capture_output=True,
                text=True,
                check=False,
            )
            path = (result.stdout or "").strip()
            if result.returncode == 0 and path and Path(path).is_file():
                candidates.append(path)
        except OSError:
            pass

    which = shutil.which("python") or shutil.which("python3")
    if which:
        candidates.append(which)

    def is_store_stub(path: str) -> bool:
        return "\\windowsapps\\" in path.replace("/", "\\").lower()

    for path in candidates:
        if path and Path(path).is_file() and not is_store_stub(path):
            return str(Path(path).resolve())

    if current:
        return current
    raise SystemExit(
        "Python not found. Install Python 3.11+ from https://www.python.org/downloads/ "
        "and check 'Add python.exe to PATH'."
    )


def main() -> None:
    app = SetupApp()
    app.mainloop()


if __name__ == "__main__":
    main()
