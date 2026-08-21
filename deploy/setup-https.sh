#!/usr/bin/env bash
# Enable HTTPS for Lance On API on Ubuntu EC2 (Nginx + Let's Encrypt).
# Usage: sudo ./setup-https.sh api.yourdomain.com
set -euo pipefail

DOMAIN="${1:-}"
EMAIL="${2:-admin@lanceon.com.br}"

if [ -z "$DOMAIN" ]; then
  echo "Usage: sudo $0 api.yourdomain.com [email@example.com]"
  echo ""
  echo "Before running:"
  echo "  1. Buy/use a domain"
  echo "  2. Create an A record: api.yourdomain.com -> EC2 Elastic IP"
  echo "  3. Open AWS security group ports 80 and 443"
  exit 1
fi

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root: sudo $0 $DOMAIN"
  exit 1
fi

echo "Installing Nginx + Certbot..."
apt-get update -y
apt-get install -y nginx certbot python3-certbot-nginx

CONF_SRC="$(cd "$(dirname "$0")" && pwd)/nginx-lanceon-api.conf"
CONF_DST="/etc/nginx/sites-available/lanceon-api"

sed "s/DOMAIN_NAME/${DOMAIN}/g" "$CONF_SRC" > "$CONF_DST"
ln -sfn "$CONF_DST" /etc/nginx/sites-enabled/lanceon-api
rm -f /etc/nginx/sites-enabled/default

nginx -t
systemctl enable nginx
systemctl restart nginx

echo "Requesting Let's Encrypt certificate for ${DOMAIN}..."
certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "$EMAIL" --redirect

systemctl reload nginx

echo ""
echo "HTTPS ready: https://${DOMAIN}/health"
echo "Keep API on localhost only (recommended):"
echo "  Edit /etc/systemd/system/lanceon-api.service"
echo "  Change: --host 127.0.0.1 --port 8000"
echo "  Then: systemctl daemon-reload && systemctl restart lanceon-api"
echo ""
echo "Update clients to: https://${DOMAIN}"
echo "  mobile/.env  EXPO_PUBLIC_API_URL"
echo "  admin/.env   VITE_API_URL"
echo "  Pi config    api_url"
echo "Then rebuild the mobile APK."
