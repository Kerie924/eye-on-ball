#!/usr/bin/env python3
"""Lance On Setup App — Ubuntu wizard for court capture."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

SOURCE_DIR = Path(__file__).resolve().parent
INSTALLER = SOURCE_DIR / "install_capture.py"
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
        tk.Label(
            outer,
            text="Instale o gravador da quadra. O painel admin fica na nuvem.",
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
            text="Botao fisico no GPIO17 (Mini PC / Raspberry Pi)",
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
            os.chmod(handle.name, 0o600)
            self.install_btn.configure(state=tk.DISABLED, text="Instalando...")
            self._log("Solicitando senha de administrador e instalando pacotes...")
            self._log("Isso instala FFmpeg, Python e o servico de gravacao.")
            python = sys_executable()
            installer_args = [
                python,
                str(INSTALLER),
                "--source",
                str(SOURCE_DIR),
                "--settings",
                handle.name,
            ]
            if shutil.which("pkexec"):
                command = ["pkexec", *installer_args]
            else:
                command = ["sudo", *installer_args]
            result = subprocess.run(command, capture_output=True, text=True)
            output = (result.stdout or "") + (result.stderr or "")
            self._log(output.strip() or "(sem saida)")
            if result.returncode == 0 and "INSTALL_OK" in output:
                messagebox.showinfo(
                    "Lance On",
                    "Instalacao concluida.\nO gravador inicia sozinho quando o Mini PC ligar.",
                )
            else:
                messagebox.showerror(
                    "Lance On",
                    "A instalacao falhou. Veja o log na parte de baixo da janela.",
                )
        finally:
            Path(handle.name).unlink(missing_ok=True)
            self.install_btn.configure(state=tk.NORMAL, text="Instalar e iniciar")


def sys_executable() -> str:
    return "/usr/bin/python3"


def main() -> None:
    app = SetupApp()
    app.mainloop()


if __name__ == "__main__":
    main()
