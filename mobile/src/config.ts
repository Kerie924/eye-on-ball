import { Platform } from 'react-native'

function resolveApiUrl(): string {
  const envUrl = process.env.EXPO_PUBLIC_API_URL
  if (envUrl) {
    return envUrl.replace(/\/$/, '')
  }

  if (Platform.OS === 'android') {
    return 'http://10.0.2.2:8000'
  }

  return 'http://localhost:8000'
}

export const API_URL = resolveApiUrl()

export const APP_NAME = 'Olho no Lance'
export const APP_TAGLINE = 'E Lance Gravou'

export const GOOGLE_WEB_CLIENT_ID = process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID?.trim() || ''
export const GOOGLE_ANDROID_CLIENT_ID =
  process.env.EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID?.trim() || ''
export const GOOGLE_IOS_CLIENT_ID = process.env.EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID?.trim() || ''
