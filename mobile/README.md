# Lance On — Mobile App

Cross-platform app (Android/iOS) for athletes and scouts to view and download court recordings.

## Stack

- Expo + React Native + TypeScript
- expo-router (navigation)
- expo-secure-store (JWT storage)
- expo-av (video playback)
- expo-file-system + expo-sharing (download/share)

## Features

- Register as **Atleta** or **Olheiro**
- Login / logout
- List recordings (30s clips, 48h availability)
- Video playback and download/share
- Browse courts and request access (athletes)
- Profile screen with account status

## Run locally

1. Start the backend on port 8000
2. Install dependencies:

```bash
cd mobile
npm install
```

3. Copy env and set API URL if needed:

```bash
cp .env.example .env
```

4. Start Expo:

```bash
npm start
```

Then press `a` for Android emulator, `i` for iOS simulator, or scan the QR code with Expo Go on your phone.

## API URL notes

| Environment | URL |
|-------------|-----|
| iOS simulator | `http://localhost:8000` |
| Android emulator | `http://10.0.2.2:8000` (default) |
| Physical device | `http://<your-pc-lan-ip>:8000` |

Set `EXPO_PUBLIC_API_URL` in `.env` for physical devices.

## Test flow

1. Register an athlete account in the app
2. In admin panel, create a court if needed
3. Athlete requests court access in **Quadras** tab
4. Admin approves the request
5. Upload a test recording (capture agent or `scripts/test_upload.py`)
6. Recording appears in **Gravacoes** tab
