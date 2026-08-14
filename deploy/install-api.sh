#!/usr/bin/env bash
# Install Lance On API on Ubuntu EC2 so it starts on boot and stays running.
set -euo pipefail

INSTALL_ROOT="/opt/lance-on"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SERVICE_USER="${SUDO_USER:-ubuntu}"
SERVICE_HOME="$(getent passwd "${SERVICE_USER}" | cut -d: -f6)"

echo "Installing Lance On API to ${INSTALL_ROOT}..."

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required. Install with:"
  echo "  sudo apt update && sudo apt install -y docker.io docker-compose-v2"
  echo "  sudo usermod -aG docker ${SERVICE_USER}"
  exit 1
fi

python_version() {
  "$1" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || true
}

is_supported_python() {
  local ver major minor
  ver="$(python_version "$1")"
  [ -n "$ver" ] || return 1
  major="${ver%%.*}"
  minor="${ver#*.}"
  [ "$major" -eq 3 ] && [ "$minor" -ge 11 ] && [ "$minor" -le 13 ]
}

resolve_system_python() {
  local candidate
  for candidate in python3.13 python3.12 python3.11 python3; do
    if command -v "$candidate" >/dev/null 2>&1 && is_supported_python "$candidate"; then
      echo "$candidate"
      return 0
    fi
  done
  return 1
}

install_uv() {
  if command -v uv >/dev/null 2>&1; then
    return 0
  fi
  if [ -x "${SERVICE_HOME}/.local/bin/uv" ]; then
    export PATH="${SERVICE_HOME}/.local/bin:${PATH}"
    return 0
  fi
  echo "Installing uv (to fetch Python 3.12)..."
  curl -LsSf https://astral.sh/uv/install.sh | sudo -u "${SERVICE_USER}" sh
  export PATH="${SERVICE_HOME}/.local/bin:${PATH}"
  command -v uv >/dev/null 2>&1
}

ensure_python() {
  local bin

  if bin="$(resolve_system_python)"; then
    echo "$bin"
    return 0
  fi

  echo "System Python is too new or missing (need 3.11–3.13)."
  echo "Current default: $(python3 --version 2>/dev/null || echo unknown)"

  sudo apt-get update -y
  sudo apt-get install -y curl ca-certificates build-essential libpq-dev rsync

  # Try deadsnakes on Ubuntu (may not exist for every release)
  if [ -f /etc/os-release ]; then
    # shellcheck source=/dev/null
    . /etc/os-release
    if [ "${ID:-}" = "ubuntu" ]; then
      echo "Trying deadsnakes PPA for Python 3.12..."
      if sudo apt-get install -y software-properties-common \
        && sudo add-apt-repository -y ppa:deadsnakes/ppa \
        && sudo apt-get update -y \
        && sudo apt-get install -y python3.12 python3.12-venv python3.12-dev; then
        if bin="$(resolve_system_python)"; then
          echo "$bin"
          return 0
        fi
      else
        echo "deadsnakes not available on this release; falling back to uv."
      fi
    fi
  fi

  # Reliable fallback: uv installs a standalone CPython 3.12
  if ! install_uv; then
    echo "Failed to install uv."
    exit 1
  fi
  echo "Installing CPython 3.12 via uv..."
  sudo -u "${SERVICE_USER}" "${SERVICE_HOME}/.local/bin/uv" python install 3.12
  bin="$(sudo -u "${SERVICE_USER}" "${SERVICE_HOME}/.local/bin/uv" python find 3.12)"
  if [ -z "$bin" ] || [ ! -x "$bin" ]; then
    echo "uv could not provide Python 3.12"
    exit 1
  fi
  echo "$bin"
}

PYTHON_BIN="$(ensure_python)"
echo "Using $($PYTHON_BIN --version) ($PYTHON_BIN)"

sudo apt-get update -y
sudo apt-get install -y build-essential libpq-dev rsync curl ca-certificates

sudo mkdir -p "${INSTALL_ROOT}"
sudo rsync -a --delete \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude '.git' \
  --exclude 'mobile/node_modules' \
  --exclude 'admin/node_modules' \
  "${REPO_ROOT}/" "${INSTALL_ROOT}/"

sudo chown -R "${SERVICE_USER}:${SERVICE_USER}" "${INSTALL_ROOT}"

if [ ! -f "${INSTALL_ROOT}/deploy/postgres.env" ]; then
  sudo cp "${INSTALL_ROOT}/deploy/postgres.env.example" "${INSTALL_ROOT}/deploy/postgres.env"
  echo "Created ${INSTALL_ROOT}/deploy/postgres.env — set POSTGRES_PASSWORD"
fi

cd "${INSTALL_ROOT}/deploy"
sudo docker compose -f docker-compose.prod.yml --env-file postgres.env up -d

cd "${INSTALL_ROOT}/backend"
if [ -d .venv ]; then
  echo "Removing existing .venv so it is recreated with $($PYTHON_BIN --version)..."
  sudo rm -rf .venv
fi

# Prefer uv venv when available (works with uv-managed Python 3.12)
if command -v uv >/dev/null 2>&1 || [ -x "${SERVICE_HOME}/.local/bin/uv" ]; then
  UV_BIN="$(command -v uv || echo "${SERVICE_HOME}/.local/bin/uv")"
  sudo -u "${SERVICE_USER}" "$UV_BIN" venv --python "$PYTHON_BIN" .venv
  sudo -u "${SERVICE_USER}" "$UV_BIN" pip install --python .venv/bin/python --upgrade pip
  sudo -u "${SERVICE_USER}" "$UV_BIN" pip install --python .venv/bin/python -r requirements.txt
else
  sudo -u "${SERVICE_USER}" "$PYTHON_BIN" -m venv .venv
  sudo -u "${SERVICE_USER}" .venv/bin/pip install --upgrade pip
  sudo -u "${SERVICE_USER}" .venv/bin/pip install -r requirements.txt
fi

if [ ! -f "${INSTALL_ROOT}/backend/.env" ]; then
  sudo -u "${SERVICE_USER}" cp "${INSTALL_ROOT}/deploy/.env.aws.example" "${INSTALL_ROOT}/backend/.env"
  echo "Created ${INSTALL_ROOT}/backend/.env — edit S3 keys, SECRET_KEY, DB password"
fi

TMP_UNIT="$(mktemp)"
sed "s/User=ubuntu/User=${SERVICE_USER}/; s/Group=ubuntu/Group=${SERVICE_USER}/" \
  "${INSTALL_ROOT}/deploy/lanceon-api.service" > "${TMP_UNIT}"
sudo cp "${TMP_UNIT}" /etc/systemd/system/lanceon-api.service
rm -f "${TMP_UNIT}"

sudo systemctl daemon-reload
sudo systemctl enable lanceon-api.service

echo ""
echo "Installation staged with $($PYTHON_BIN --version)."
echo "1. Edit DB password:  sudo nano ${INSTALL_ROOT}/deploy/postgres.env"
echo "   Then: cd ${INSTALL_ROOT}/deploy && sudo docker compose -f docker-compose.prod.yml --env-file postgres.env up -d"
echo "2. Edit API env:      sudo nano ${INSTALL_ROOT}/backend/.env"
echo "   Match DATABASE_URL password to postgres.env; set S3_* and SECRET_KEY"
echo "3. Start API:         sudo systemctl start lanceon-api"
echo "4. Status:            sudo systemctl status lanceon-api"
echo "5. Logs:              sudo journalctl -u lanceon-api -f"
echo "6. Health:            curl http://127.0.0.1:8000/health"
