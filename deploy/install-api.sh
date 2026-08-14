#!/usr/bin/env bash
# Install Lance On API on Ubuntu EC2 so it starts on boot and stays running.
set -euo pipefail

INSTALL_ROOT="/opt/lance-on"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SERVICE_USER="${SUDO_USER:-ubuntu}"

echo "Installing Lance On API to ${INSTALL_ROOT}..."

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required. Install with:"
  echo "  sudo apt update && sudo apt install -y docker.io docker-compose-v2"
  echo "  sudo usermod -aG docker ${SERVICE_USER}"
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required."
  exit 1
fi

sudo mkdir -p "${INSTALL_ROOT}"
sudo rsync -a --delete \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude '.git' \
  --exclude 'mobile/node_modules' \
  --exclude 'admin/node_modules' \
  "${REPO_ROOT}/" "${INSTALL_ROOT}/"

sudo chown -R "${SERVICE_USER}:${SERVICE_USER}" "${INSTALL_ROOT}"

# Postgres (production compose — no MinIO)
if [ ! -f "${INSTALL_ROOT}/deploy/postgres.env" ]; then
  sudo cp "${INSTALL_ROOT}/deploy/postgres.env.example" "${INSTALL_ROOT}/deploy/postgres.env"
  echo "Created ${INSTALL_ROOT}/deploy/postgres.env — set POSTGRES_PASSWORD"
fi

cd "${INSTALL_ROOT}/deploy"
sudo docker compose -f docker-compose.prod.yml --env-file postgres.env up -d

# Python venv + deps
cd "${INSTALL_ROOT}/backend"
if [ ! -d .venv ]; then
  sudo -u "${SERVICE_USER}" python3 -m venv .venv
fi
sudo -u "${SERVICE_USER}" .venv/bin/pip install --upgrade pip
sudo -u "${SERVICE_USER}" .venv/bin/pip install -r requirements.txt

if [ ! -f "${INSTALL_ROOT}/backend/.env" ]; then
  sudo -u "${SERVICE_USER}" cp "${INSTALL_ROOT}/deploy/.env.aws.example" "${INSTALL_ROOT}/backend/.env"
  echo "Created ${INSTALL_ROOT}/backend/.env — edit S3 keys, SECRET_KEY, DB password"
fi

# systemd unit (adjust User if not ubuntu)
TMP_UNIT="$(mktemp)"
sed "s/User=ubuntu/User=${SERVICE_USER}/; s/Group=ubuntu/Group=${SERVICE_USER}/" \
  "${INSTALL_ROOT}/deploy/lanceon-api.service" > "${TMP_UNIT}"
sudo cp "${TMP_UNIT}" /etc/systemd/system/lanceon-api.service
rm -f "${TMP_UNIT}"

sudo systemctl daemon-reload
sudo systemctl enable lanceon-api.service

echo ""
echo "Installation staged."
echo "1. Edit DB password:  sudo nano ${INSTALL_ROOT}/deploy/postgres.env"
echo "   Then: cd ${INSTALL_ROOT}/deploy && sudo docker compose -f docker-compose.prod.yml --env-file postgres.env up -d"
echo "2. Edit API env:      sudo nano ${INSTALL_ROOT}/backend/.env"
echo "   Match DATABASE_URL password to postgres.env; set S3_* and SECRET_KEY"
echo "3. Start API:         sudo systemctl start lanceon-api"
echo "4. Status:            sudo systemctl status lanceon-api"
echo "5. Logs:              sudo journalctl -u lanceon-api -f"
echo "6. Health:            curl http://127.0.0.1:8000/health"
echo ""
echo "Open security group port 8000 (or 443 via Nginx later)."
echo "On reboot, Docker Postgres + lanceon-api will start automatically."
