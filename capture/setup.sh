#!/usr/bin/env bash
# Lance On — simple court setup (Mini PC / Raspberry Pi, Ubuntu).
# Run once:  chmod +x setup.sh && ./setup.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_PATH="/etc/lance-on/config.yaml"

echo ""
echo "=========================================="
echo "  Lance On — Instalacao da quadra"
echo "=========================================="
echo ""
echo "Este assistente configura a gravacao no Mini PC."
echo "O painel admin fica na nuvem (navegador) — nao instala aqui."
echo ""

read -r -p "URL da API [http://13.210.97.155:8000]: " API_URL
API_URL="${API_URL:-http://13.210.97.155:8000}"
API_URL="${API_URL%/}"

read -r -p "Chave do dispositivo (copie do painel admin): " DEVICE_KEY
if [ -z "$DEVICE_KEY" ]; then
  echo "Erro: a chave do dispositivo e obrigatoria."
  exit 1
fi

read -r -p "Quantas cameras nesta quadra? (1-6) [1]: " CAMERA_COUNT
CAMERA_COUNT="${CAMERA_COUNT:-1}"
if ! [[ "$CAMERA_COUNT" =~ ^[1-6]$ ]]; then
  echo "Erro: use um numero de 1 a 6."
  exit 1
fi

read -r -p "Usuario da camera [admin]: " CAM_USER
CAM_USER="${CAM_USER:-admin}"

read -r -s -p "Senha da camera: " CAM_PASS
echo ""
if [ -z "$CAM_PASS" ]; then
  echo "Erro: senha da camera e obrigatoria."
  exit 1
fi

read -r -p "Um botao fisico por camera? (s/n) [s]: " USE_GPIO
USE_GPIO="${USE_GPIO:-s}"

CAMERAS_YAML=""
GPIO_PINS=(17 27 22 23 24 25)
PHYS_PINS=(11 13 15 16 18 22)
for i in $(seq 1 "$CAMERA_COUNT"); do
  default_ip="192.168.15.1$((i + 9))"
  read -r -p "  IP da camera $i [$default_ip]: " CAM_IP
  CAM_IP="${CAM_IP:-$default_ip}"
  RTSP="rtsp://${CAM_USER}:${CAM_PASS}@${CAM_IP}:554/cam/realmonitor?channel=1&subtype=0"
  gpio="${GPIO_PINS[$((i - 1))]}"
  phys="${PHYS_PINS[$((i - 1))]}"
  if [[ "$USE_GPIO" =~ ^[sS] ]]; then
    BUTTON_LINES="    button:
      type: gpio
      pin: ${gpio}  # camera ${i} — physical pin ${phys} + GND"
  else
    BUTTON_LINES="    button:
      type: none"
  fi
  CAMERAS_YAML="${CAMERAS_YAML}
  - index: ${i}
    name: Camera ${i}
    rtsp_url: \"${RTSP}\"
${BUTTON_LINES}
"
done

echo ""
echo "Instalando pacotes e servico..."
cd "$SCRIPT_DIR"
chmod +x install.sh
./install.sh

echo ""
echo "Gravando configuracao em ${CONFIG_PATH} ..."
sudo tee "$CONFIG_PATH" > /dev/null <<EOF
# Gerado por setup.sh — Lance On
api_url: ${API_URL}
device_key: ${DEVICE_KEY}

buffer_seconds: 300
clip_seconds: 30
segment_seconds: 10
heartbeat_seconds: 60
button_cooldown_seconds: 3

# One physical button per camera (see button.pin under each camera).
cameras:${CAMERAS_YAML}
data_dir: /var/lib/lance-on

# Bottom watermark on every clip (copied with the capture install)
watermark_path: /opt/lance-on/capture/assets/video-watermark.jpeg
EOF

sudo systemctl restart lanceon-capture

echo ""
echo "=========================================="
echo "  Instalacao concluida"
echo "=========================================="
echo ""
echo "  O software inicia sozinho quando o Mini PC liga."
echo ""
echo "  Ver status:  sudo systemctl status lanceon-capture"
echo "  Ver logs:    sudo journalctl -u lanceon-capture -f"
echo "  Painel web:  abra o admin no navegador (na nuvem)"
echo ""
echo "  Teste: pressione o botao ou use Gravar no admin."
echo ""

if curl -sf "${API_URL}/health" > /dev/null; then
  echo "  API online: OK"
else
  echo "  Aviso: API nao respondeu agora. Clips serao enviados quando a internet voltar"
  echo "  (fila offline completa — proxima versao)."
fi
echo ""
