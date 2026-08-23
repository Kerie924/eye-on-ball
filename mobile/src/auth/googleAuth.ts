import * as Linking from 'expo-linking'
import * as WebBrowser from 'expo-web-browser'
import {
  GoogleAuthProvider,
  signInWithCredential,
  signInWithPopup,
} from 'firebase/auth'
import { Platform } from 'react-native'

import {
  API_URL,
  FIREBASE_API_KEY,
  FIREBASE_PROJECT_ID,
  GOOGLE_WEB_CLIENT_ID,
} from '../config'
import { getFirebaseAuth } from './firebase'

WebBrowser.maybeCompleteAuthSession()

type GoogleSignInModule = typeof import('@react-native-google-signin/google-signin')

let googleConfigured = false
let googleModulePromise: Promise<GoogleSignInModule> | null = null

export class GoogleAuthCancelledError extends Error {
  constructor() {
    super('Login Google cancelado')
    this.name = 'GoogleAuthCancelledError'
  }
}

export function isGoogleAuthConfigured(): boolean {
  return Boolean(GOOGLE_WEB_CLIENT_ID && FIREBASE_API_KEY && FIREBASE_PROJECT_ID)
}

function loadGoogleSignIn(): Promise<GoogleSignInModule> {
  if (!googleModulePromise) {
    googleModulePromise = import('@react-native-google-signin/google-signin')
  }
  return googleModulePromise
}

function isFirebaseCancelled(error: unknown): boolean {
  const code =
    typeof error === 'object' && error && 'code' in error
      ? String((error as { code?: string }).code)
      : ''
  return code === 'auth/popup-closed-by-user' || code === 'auth/cancelled-popup-request'
}

export async function isGoogleAuthCancelled(error: unknown): Promise<boolean> {
  if (error instanceof GoogleAuthCancelledError || isFirebaseCancelled(error)) {
    return true
  }
  try {
    const { isErrorWithCode, statusCodes } = await loadGoogleSignIn()
    return isErrorWithCode(error) && error.code === statusCodes.SIGN_IN_CANCELLED
  } catch {
    return false
  }
}

function configureGoogleSignIn(mod: GoogleSignInModule) {
  if (googleConfigured || !GOOGLE_WEB_CLIENT_ID) {
    return
  }

  mod.GoogleSignin.configure({
    webClientId: GOOGLE_WEB_CLIENT_ID,
    offlineAccess: false,
  })
  googleConfigured = true
}

function isNativeModuleMissing(error: unknown): boolean {
  const message = error instanceof Error ? error.message : String(error)
  return /native module|RNGoogleSignin|null is not an object|hasPlayServices/i.test(message)
}

async function isDeveloperError(error: unknown): Promise<boolean> {
  try {
    const { isErrorWithCode, statusCodes } = await loadGoogleSignIn()
    return isErrorWithCode(error) && error.code === statusCodes.DEVELOPER_ERROR
  } catch {
    return false
  }
}

function idTokenFromUrl(url: string): string | null {
  const parsed = Linking.parse(url)
  const token = parsed.queryParams?.id_token
  if (typeof token === 'string' && token.length > 20) {
    return token
  }
  return null
}

async function signInWithGoogleNative(): Promise<string> {
  const mod = await loadGoogleSignIn()
  configureGoogleSignIn(mod)
  await mod.GoogleSignin.hasPlayServices({ showPlayServicesUpdateDialog: true })

  const response = await mod.GoogleSignin.signIn()
  if (mod.isSuccessResponse(response) && response.data.idToken) {
    const credential = GoogleAuthProvider.credential(response.data.idToken)
    const { user } = await signInWithCredential(getFirebaseAuth(), credential)
    return user.getIdToken()
  }
  if (response.type === 'cancelled') {
    throw new GoogleAuthCancelledError()
  }
  throw new Error('Google nao retornou um token')
}

async function signInWithGoogleWeb(): Promise<string> {
  const provider = new GoogleAuthProvider()
  provider.addScope('email')
  provider.addScope('profile')
  provider.setCustomParameters({ prompt: 'select_account' })

  try {
    const { user } = await signInWithPopup(getFirebaseAuth(), provider)
    return user.getIdToken()
  } catch (error) {
    if (isFirebaseCancelled(error)) {
      throw new GoogleAuthCancelledError()
    }
    throw error
  }
}

async function signInWithGoogleHosted(): Promise<string> {
  const redirectUrl = Linking.createURL('google-auth')
  const authUrl = `${API_URL}/api/auth/google-app?continue=${encodeURIComponent(redirectUrl)}`
  const result = await WebBrowser.openAuthSessionAsync(authUrl, redirectUrl)

  if (result.type === 'cancel' || result.type === 'dismiss') {
    throw new GoogleAuthCancelledError()
  }
  if (result.type !== 'success' || !('url' in result)) {
    throw new Error('Falha na autenticacao Google')
  }

  const idToken = idTokenFromUrl(result.url)
  if (!idToken) {
    throw new Error('Google nao retornou um token')
  }
  return idToken
}

export async function signInWithGoogle(): Promise<string> {
  if (!isGoogleAuthConfigured()) {
    throw new Error(
      'Firebase Auth nao configurado. Defina EXPO_PUBLIC_FIREBASE_API_KEY, EXPO_PUBLIC_FIREBASE_PROJECT_ID e EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID.',
    )
  }

  if (Platform.OS === 'web') {
    return signInWithGoogleWeb()
  }

  try {
    return await signInWithGoogleNative()
  } catch (error) {
    if (await isGoogleAuthCancelled(error)) {
      throw error instanceof GoogleAuthCancelledError
        ? error
        : new GoogleAuthCancelledError()
    }
    if (isNativeModuleMissing(error) || (await isDeveloperError(error))) {
      return signInWithGoogleHosted()
    }
    throw error
  }
}

export async function signOutGoogle(): Promise<void> {
  try {
    const { GoogleSignin } = await loadGoogleSignIn()
    await GoogleSignin.signOut()
  } catch {
    // Expo Go and already-signed-out sessions are fine.
  }

  if (!isGoogleAuthConfigured()) {
    return
  }

  try {
    await getFirebaseAuth().signOut()
  } catch {
    // Ignore if Firebase was never initialized.
  }
}
