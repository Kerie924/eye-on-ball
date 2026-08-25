import * as AppleAuthentication from 'expo-apple-authentication'
import { Platform } from 'react-native'

import { IOS_APP_STORE_ENABLED } from '../config'

export class AppleAuthCancelledError extends Error {
  constructor() {
    super('Login Apple cancelado')
    this.name = 'AppleAuthCancelledError'
  }
}

export async function isAppleAuthAvailable(): Promise<boolean> {
  if (!IOS_APP_STORE_ENABLED || Platform.OS !== 'ios') {
    return false
  }
  try {
    return await AppleAuthentication.isAvailableAsync()
  } catch {
    return false
  }
}

export function isAppleAuthCancelled(error: unknown): boolean {
  if (error instanceof AppleAuthCancelledError) {
    return true
  }
  const code =
    typeof error === 'object' && error && 'code' in error
      ? String((error as { code?: string }).code)
      : ''
  return code === 'ERR_REQUEST_CANCELED' || code === 'ERR_CANCELED'
}

export async function signInWithApple(): Promise<{
  identityToken: string
  fullName: string | null
}> {
  if (!(await isAppleAuthAvailable())) {
    throw new Error('Sign in with Apple nao esta disponivel neste dispositivo.')
  }

  try {
    const credential = await AppleAuthentication.signInAsync({
      requestedScopes: [
        AppleAuthentication.AppleAuthenticationScope.FULL_NAME,
        AppleAuthentication.AppleAuthenticationScope.EMAIL,
      ],
    })

    if (!credential.identityToken) {
      throw new Error('Apple nao retornou um token.')
    }

    const parts = [
      credential.fullName?.givenName,
      credential.fullName?.familyName,
    ].filter(Boolean)

    return {
      identityToken: credential.identityToken,
      fullName: parts.length ? parts.join(' ') : null,
    }
  } catch (error) {
    if (isAppleAuthCancelled(error)) {
      throw new AppleAuthCancelledError()
    }
    throw error
  }
}
