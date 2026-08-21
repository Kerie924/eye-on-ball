#!/usr/bin/env bash
# Build the Lance On admin SPA and publish it for Nginx.
# Usage:
#   sudo ./install-admin.sh
#   sudo ./install-admin.sh https://lanceonpara.com.br
set -euo pipefail

API_URL="${1:-}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ADMIN_SRC="${REPO_ROOT}/admin"
ADMIN_ROOT="/var/www/lanceon-admin"

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root: sudo $0 [https://your-domain]"
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

cd "${ADMIN_SRC}"

if [ -n "${API_URL}" ]; then
  printf 'VITE_API_URL=%s\n' "${API_URL}" > .env.production
else
  # Same origin: browser calls /api on lanceonpara.com.br
  printf 'VITE_API_URL=\n' > .env.production
fi

echo "Building admin with:"
cat .env.production

npm ci
npm run build

mkdir -p "${ADMIN_ROOT}"
rsync -a --delete "${ADMIN_SRC}/dist/" "${ADMIN_ROOT}/"
chown -R www-data:www-data "${ADMIN_ROOT}"

echo ""
echo "Admin published to ${ADMIN_ROOT}"
echo "Next: sudo nginx -t && sudo systemctl reload nginx"
echo "Open: https://lanceonpara.com.br"
