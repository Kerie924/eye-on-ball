function resolveApiUrl(): string {
  const envUrl = process.env.EXPO_PUBLIC_API_URL
  if (envUrl) {
    return envUrl.replace(/\/$/, '')
  }

  return 'https://api.lanceonpara.com.br'
}

export const API_URL = resolveApiUrl()
export const PRIVACY_URL = `${API_URL}/api/legal/privacy`
export const TERMS_URL = `${API_URL}/api/legal/terms`

export const APP_NAME = 'Lance On'
export const APP_TAGLINE = 'Seu lance. Gravou. Compartilhou.'

// Set to true when we start the App Store / TestFlight submission.
export const IOS_APP_STORE_ENABLED = false

export const GOOGLE_WEB_CLIENT_ID = process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID?.trim() || ''
export const GOOGLE_ANDROID_CLIENT_ID =
  process.env.EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID?.trim() || ''
export const GOOGLE_IOS_CLIENT_ID = process.env.EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID?.trim() || ''

export const FIREBASE_API_KEY = process.env.EXPO_PUBLIC_FIREBASE_API_KEY?.trim() || ''
export const FIREBASE_AUTH_DOMAIN = process.env.EXPO_PUBLIC_FIREBASE_AUTH_DOMAIN?.trim() || ''
export const FIREBASE_PROJECT_ID = process.env.EXPO_PUBLIC_FIREBASE_PROJECT_ID?.trim() || ''
export const FIREBASE_APP_ID = process.env.EXPO_PUBLIC_FIREBASE_APP_ID?.trim() || ''
export const FIREBASE_MESSAGING_SENDER_ID =
  process.env.EXPO_PUBLIC_FIREBASE_MESSAGING_SENDER_ID?.trim() || ''
