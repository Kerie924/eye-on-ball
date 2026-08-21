# HTTPS for Lance On API (AWS EC2)

Let's Encrypt needs a **domain name**. A raw IP (`13.210.97.155`) cannot get a normal free HTTPS certificate.

## 1. Point a domain at the EC2 IP

Example: `api.lanceon.com.br` → Elastic IP `13.210.97.155`

In your DNS provider (Registro.br, Cloudflare, Route53, etc.):

| Type | Name | Value |
|------|------|--------|
| A | `api` (or `@`) | `13.210.97.155` |

Wait until it resolves:

```bash
dig +short api.lanceon.com.br
# should print 13.210.97.155
```

## 2. Open ports in AWS Security Group

Inbound:

| Port | Source | Use |
|------|--------|-----|
| 22 | your IP | SSH |
| 80 | 0.0.0.0/0 | Certbot + HTTP redirect |
| 443 | 0.0.0.0/0 | HTTPS |

You can close public **8000** after Nginx is working (API stays on `127.0.0.1:8000`).

## 3. On the EC2 instance

Copy the updated `deploy/` folder to the server, then:

```bash
cd /opt/lance-on/deploy   # or ~/Streaming-Project/deploy
sudo chmod +x setup-https.sh
sudo ./setup-https.sh api.lanceon.com.br admin@lanceon.com.br
```

Replace with your real domain and email.

Test:

```bash
curl https://api.lanceon.com.br/health
```

## 4. Bind API to localhost (recommended)

```bash
sudo nano /etc/systemd/system/lanceon-api.service
```

Change ExecStart to:

```text
--host 127.0.0.1 --port 8000
```

```bash
sudo systemctl daemon-reload
sudo systemctl restart lanceon-api
sudo systemctl reload nginx
```

## 5. Update all clients

| Client | Setting |
|--------|---------|
| Mobile `EXPO_PUBLIC_API_URL` | `https://api.lanceon.com.br` |
| Admin `VITE_API_URL` | `https://api.lanceon.com.br` |
| Pi `/etc/lance-on/config.yaml` `api_url` | `https://api.lanceon.com.br` |

Then:

```bash
# Mini PC
sudo systemctl restart lanceon-capture

# Mobile — rebuild APK (required)
cd mobile
npx eas-cli build --platform android --profile preview
```

After HTTPS works, you can remove `usesCleartextTraffic` later for stricter Android security.

## Certificate renewal

Certbot installs a timer. Check:

```bash
sudo certbot renew --dry-run
```

## If you have no domain yet

Options:

1. Buy a cheap domain (`.com.br` / `.com`) — recommended  
2. Use a free DNS name (e.g. DuckDNS) pointing to the Elastic IP, then run the same script  

Do **not** use a self-signed certificate for the mobile app — Android will reject it.
