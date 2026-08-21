#!/usr/bin/env bash
# Enable HTTPS for Lance On (admin SPA + API) on Ubuntu EC2.
# Usage: sudo ./setup-https.sh lanceonpara.com.br you@email.com
set -euo pipefail

DOMAIN="${1:-}"
EMAIL="${2:-admin@lanceon.com.br}"

if [ -z "$DOMAIN" ]; then
  echo "Usage: sudo $0 lanceonpara.com.br [email@example.com]"
  echo ""
  echo "Before running:"
  echo "  1. A records for @, www, and api -> EC2 Elastic IP"
  echo "  2. Open AWS security group ports 80 and 443"
  echo "  3. Build the admin: sudo ./install-admin.sh"
  exit 1
fi

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root: sudo $0 $DOMAIN"
  exit 1
fi

echo "Installing Nginx + Certbot..."
apt-get update -y
apt-get install -y nginx certbot python3-certbot-nginx

mkdir -p /var/www/lanceon-admin
if [ ! -f /var/www/lanceon-admin/index.html ]; then
  echo "<!doctype html><title>Lance On</title><p>Admin not built yet. Run deploy/install-admin.sh</p>" \
    > /var/www/lanceon-admin/index.html
  chown -R www-data:www-data /var/www/lanceon-admin
fi

CONF_SRC="$(cd "$(dirname "$0")" && pwd)/nginx-lanceon.conf"
CONF_DST="/etc/nginx/sites-available/lanceon"

sed "s/DOMAIN_NAME/${DOMAIN}/g" "$CONF_SRC" > "$CONF_DST"
ln -sfn "$CONF_DST" /etc/nginx/sites-enabled/lanceon
rm -f /etc/nginx/sites-enabled/default
rm -f /etc/nginx/sites-enabled/lanceon-api

nginx -t
systemctl enable nginx
systemctl restart nginx

echo "Requesting Let's Encrypt certificates for ${DOMAIN}, www, and api..."
certbot --nginx \
  -d "$DOMAIN" \
  -d "www.${DOMAIN}" \
  -d "api.${DOMAIN}" \
  --non-interactive --agree-tos -m "$EMAIL" --redirect

systemctl reload nginx

echo ""
echo "HTTPS ready:"
echo "  Admin:  https://${DOMAIN}"
echo "  API:    https://api.${DOMAIN}/health"
echo "  Same-origin API via admin host: https://${DOMAIN}/api/..."
echo ""
echo "Keep API on localhost only (recommended):"
echo "  Edit /etc/systemd/system/lanceon-api.service"
echo "  Change: --host 127.0.0.1 --port 8000"
echo "  Then: systemctl daemon-reload && systemctl restart lanceon-api"
echo ""
echo "Update clients to: https://api.${DOMAIN}"
echo "  mobile/.env  EXPO_PUBLIC_API_URL"
echo "  Pi config    api_url"
echo "Then rebuild the mobile APK."
