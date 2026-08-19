function resolveApiUrl(): string {
  const envUrl = process.env.EXPO_PUBLIC_API_URL
  if (envUrl) {
    return envUrl.replace(/\/$/, '')
  }

  return 'http://13.210.97.155:8000'
}

export const API_URL = resolveApiUrl()

export const APP_NAME = 'Lance On'
export const APP_TAGLINE = 'Seu lance. Gravou. Compartilhou.'

export const GOOGLE_WEB_CLIENT_ID = process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID?.trim() || ''
export const GOOGLE_ANDROID_CLIENT_ID =
  process.env.EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID?.trim() || ''
export const GOOGLE_IOS_CLIENT_ID = process.env.EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID?.trim() || ''
