# Lance On — Website

Public website for Lance On (landing, auth, and athlete/scout video browsing).
Uses the same FastAPI backend as the mobile app and admin panel.

## Stack

- React 19 + TypeScript + Vite
- Tailwind CSS v4
- React Router
- Lucide icons

## Setup

```bash
cd website
cp .env.example .env
npm install
npm run dev
```

Dev server: [http://localhost:5174](http://localhost:5174)

With empty `VITE_API_URL`, Vite proxies `/api` and `/health` to `https://api.lanceonpara.com.br`.

## Production

```bash
VITE_API_URL=https://api.lanceonpara.com.br npm run build
```

Serve the `dist/` folder behind HTTPS. Ensure the API CORS origin allows your website domain.

## Routes

| Path | Description |
|------|-------------|
| `/` | Landing |
| `/entrar` | Login |
| `/cadastrar` | Register |
| `/esqueci-senha` | Forgot password |
| `/sobre` | How it works |
| `/app` | Home (auth) |
| `/app/cidades` → quadras → horarios → gravacoes → video | Browse & play clips |
| `/app/relatar` | Feedback / error report |
| `/app/perfil` | Profile & logout |
