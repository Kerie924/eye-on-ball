#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="/opt/olho-no-lance/capture"
CONFIG_DIR="/etc/olho-no-lance"
DATA_DIR="/var/lib/olho-no-lance"

echo "Installing Olho no Lance capture agent..."

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "FFmpeg is required. Install it first:"
  echo "  sudo apt update && sudo apt install -y ffmpeg"
  exit 1
fi

sudo mkdir -p "$INSTALL_DIR" "$CONFIG_DIR" "$DATA_DIR"
sudo rsync -a --delete ./ "$INSTALL_DIR"/
cd "$INSTALL_DIR"
sudo python3 -m venv .venv
sudo .venv/bin/pip install -r requirements.txt

if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
  sudo cp config.example.yaml "$CONFIG_DIR/config.yaml"
  echo "Created $CONFIG_DIR/config.yaml — edit API URL, device key, and camera RTSP URLs."
fi

sudo cp olho-capture.service /etc/systemd/system/olho-capture.service
sudo systemctl daemon-reload
sudo systemctl enable olho-capture.service

echo ""
echo "Installation complete."
echo "1. Edit $CONFIG_DIR/config.yaml"
echo "2. Start service: sudo systemctl start olho-capture"
echo "3. View logs:    sudo journalctl -u olho-capture -f"
echo "4. Mock test:    python3 scripts/simulate_button.py 1"
