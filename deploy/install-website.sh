#!/usr/bin/env bash
# Build the public Lance On website and publish it for Nginx (site root).
# Usage:
#   sudo ./install-website.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WEB_SRC="${REPO_ROOT}/website"
WEB_ROOT="/var/www/lanceon"

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root: sudo $0"
  exit 1
fi

ensure_node() {
  if command -v node >/dev/null 2>&1; then
    local major
    major="$(node -p "process.versions.node.split('.')[0]")"
    if [ "${major}" -ge 20 ]; then
      return 0
    fi
    echo "Node $(node -v) is too old; installing Node 22..."
  else
    echo "Installing Node 22..."
  fi
  apt-get update -y
  apt-get install -y ca-certificates curl gnupg
  mkdir -p /etc/apt/keyrings
  curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key \
    | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
  echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_22.x nodistro main" \
    > /etc/apt/sources.list.d/nodesource.list
  apt-get update -y
  apt-get install -y nodejs
}

ensure_node
echo "Using $(node -v) / $(npm -v)"

cd "${WEB_SRC}"

if [ -f .env.production ]; then
  echo "Keeping existing website/.env.production"
elif [ -f .env ]; then
  cp .env .env.production
  echo "Copied website/.env to website/.env.production"
else
  # Same origin: browser calls /api on lanceonpara.com.br
  printf 'VITE_API_URL=\n' > .env.production
fi

echo "Building website with:"
cat .env.production

npm ci
npm run build

mkdir -p "${WEB_ROOT}"
# Preserve /admin if already deployed
if [ -d "${WEB_ROOT}/admin" ]; then
  rsync -a --delete --exclude 'admin' "${WEB_SRC}/dist/" "${WEB_ROOT}/"
else
  rsync -a --delete "${WEB_SRC}/dist/" "${WEB_ROOT}/"
fi
chown -R www-data:www-data "${WEB_ROOT}"

echo ""
echo "Website published to ${WEB_ROOT}"
echo "Open: https://lanceonpara.com.br"
echo "Admin stays at: https://lanceonpara.com.br/admin/"
