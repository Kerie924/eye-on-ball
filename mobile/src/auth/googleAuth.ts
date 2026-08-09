import type { AuthSessionResult } from 'expo-auth-session'
import * as Google from 'expo-auth-session/providers/google'
import * as WebBrowser from 'expo-web-browser'
import { Platform } from 'react-native'

import {
  GOOGLE_ANDROID_CLIENT_ID,
  GOOGLE_IOS_CLIENT_ID,
  GOOGLE_WEB_CLIENT_ID,
} from '../config'

WebBrowser.maybeCompleteAuthSession()

/** Prevents expo-auth-session from crashing when env vars are empty. */
const PLACEHOLDER_CLIENT_ID = '000000000000-placeholder.apps.googleusercontent.com'

export function isGoogleAuthConfigured(): boolean {
  return Boolean(GOOGLE_WEB_CLIENT_ID || GOOGLE_ANDROID_CLIENT_ID || GOOGLE_IOS_CLIENT_ID)
}

export function useGoogleIdToken() {
  const webClientId = GOOGLE_WEB_CLIENT_ID || PLACEHOLDER_CLIENT_ID
  // Expo Go on native uses the web client; native client IDs are for standalone builds.
  const androidClientId = GOOGLE_ANDROID_CLIENT_ID || GOOGLE_WEB_CLIENT_ID || PLACEHOLDER_CLIENT_ID
  const iosClientId = GOOGLE_IOS_CLIENT_ID || GOOGLE_WEB_CLIENT_ID || PLACEHOLDER_CLIENT_ID

  const [request, response, promptAsync] = Google.useIdTokenAuthRequest({
    webClientId,
    androidClientId,
    iosClientId,
    clientId: webClientId,
    selectAccount: true,
  })

  return {
    ready: Boolean(request) && isGoogleAuthConfigured(),
    response,
    promptAsync,
    platformHint:
      Platform.OS === 'web'
        ? 'Configure EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID'
        : 'Configure os Client IDs do Google no mobile/.env',
  }
}

export function extractGoogleIdToken(response: AuthSessionResult | null): string | null {
  if (!response || response.type !== 'success') {
    return null
  }
  const fromParams = (response.params as { id_token?: string } | undefined)?.id_token
  if (typeof fromParams === 'string' && fromParams.length > 20) {
    return fromParams
  }
  const fromAuth = response.authentication?.idToken
  if (typeof fromAuth === 'string' && fromAuth.length > 20) {
    return fromAuth
  }
  return null
}
