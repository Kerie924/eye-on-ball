#!/usr/bin/env bash
# Double-click this file on Ubuntu to install Lance On capture.
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Instalando Python..."
  pkexec apt-get update -y
  pkexec apt-get install -y python3 python3-tk python3-venv
fi

if ! python3 -c "import tkinter" 2>/dev/null; then
  echo "Instalando a interface grafica (python3-tk)..."
  pkexec apt-get install -y python3-tk
fi

exec python3 "$DIR/setup_app.py"
