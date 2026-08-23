import * as AuthSession from 'expo-auth-session'
import * as Crypto from 'expo-crypto'
import * as WebBrowser from 'expo-web-browser'
import { GoogleAuthProvider, signInWithCredential } from 'firebase/auth'
import { Platform } from 'react-native'

import {
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

export async function isGoogleAuthCancelled(error: unknown): Promise<boolean> {
  if (error instanceof GoogleAuthCancelledError) {
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

async function googleIdTokenNative(): Promise<string> {
  const mod = await loadGoogleSignIn()
  configureGoogleSignIn(mod)
  await mod.GoogleSignin.hasPlayServices({ showPlayServicesUpdateDialog: true })

  const response = await mod.GoogleSignin.signIn()
  if (mod.isSuccessResponse(response) && response.data.idToken) {
    return response.data.idToken
  }
  if (response.type === 'cancelled') {
    throw new GoogleAuthCancelledError()
  }
  throw new Error('Google nao retornou um token')
}

async function googleIdTokenBrowser(): Promise<string> {
  const redirectUri = AuthSession.makeRedirectUri({
    scheme: 'lanceon',
    path: 'redirect',
  })
  const nonce = await Crypto.digestStringAsync(
    Crypto.CryptoDigestAlgorithm.SHA256,
    `${Date.now()}-${Math.random()}`,
  )
  const request = new AuthSession.AuthRequest({
    clientId: GOOGLE_WEB_CLIENT_ID,
    redirectUri,
    responseType: AuthSession.ResponseType.IdToken,
    scopes: ['openid', 'profile', 'email'],
    extraParams: {
      nonce,
      prompt: 'select_account',
    },
    usePKCE: false,
  })

  const result = await request.promptAsync({
    authorizationEndpoint: 'https://accounts.google.com/o/oauth2/v2/auth',
  })

  if (result.type === 'cancel' || result.type === 'dismiss') {
    throw new GoogleAuthCancelledError()
  }
  if (result.type !== 'success') {
    throw new Error('Falha na autenticacao Google')
  }

  const idToken = (result.params as { id_token?: string } | undefined)?.id_token
  if (!idToken) {
    throw new Error('Google nao retornou um token')
  }
  return idToken
}

async function getGoogleIdToken(): Promise<string> {
  if (Platform.OS === 'web') {
    return googleIdTokenBrowser()
  }

  try {
    return await googleIdTokenNative()
  } catch (error) {
    if (await isGoogleAuthCancelled(error)) {
      throw error instanceof GoogleAuthCancelledError
        ? error
        : new GoogleAuthCancelledError()
    }
    if (isNativeModuleMissing(error)) {
      return googleIdTokenBrowser()
    }
    throw error
  }
}

async function exchangeFirebaseIdToken(googleIdToken: string): Promise<string> {
  const credential = GoogleAuthProvider.credential(googleIdToken)
  const { user } = await signInWithCredential(getFirebaseAuth(), credential)
  return user.getIdToken()
}

export async function signInWithGoogle(): Promise<string> {
  if (!isGoogleAuthConfigured()) {
    throw new Error(
      'Firebase Auth nao configurado. Defina EXPO_PUBLIC_FIREBASE_API_KEY, EXPO_PUBLIC_FIREBASE_PROJECT_ID e EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID.',
    )
  }

  const googleIdToken = await getGoogleIdToken()
  return exchangeFirebaseIdToken(googleIdToken)
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
