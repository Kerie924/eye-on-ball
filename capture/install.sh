#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="/opt/lance-on/capture"
CONFIG_DIR="/etc/lance-on"
DATA_DIR="/var/lib/lance-on"

echo "Installing Lance On capture agent..."

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

sudo cp lanceon-capture.service /etc/systemd/system/lanceon-capture.service
sudo systemctl daemon-reload
sudo systemctl enable lanceon-capture.service

echo ""
echo "Installation complete."
echo "1. Edit $CONFIG_DIR/config.yaml"
echo "2. Start service: sudo systemctl start lanceon-capture"
echo "3. View logs:    sudo journalctl -u lanceon-capture -f"
echo "4. Mock test:    python3 scripts/simulate_button.py 1"
