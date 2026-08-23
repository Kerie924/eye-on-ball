import { getApp, getApps, initializeApp, type FirebaseApp } from 'firebase/app'
import { getAuth, type Auth } from 'firebase/auth'

import {
  FIREBASE_API_KEY,
  FIREBASE_APP_ID,
  FIREBASE_AUTH_DOMAIN,
  FIREBASE_MESSAGING_SENDER_ID,
  FIREBASE_PROJECT_ID,
} from '../config'

function getFirebaseApp(): FirebaseApp {
  if (getApps().length > 0) {
    return getApp()
  }

  return initializeApp({
    apiKey: FIREBASE_API_KEY,
    authDomain: FIREBASE_AUTH_DOMAIN || `${FIREBASE_PROJECT_ID}.firebaseapp.com`,
    projectId: FIREBASE_PROJECT_ID,
    appId: FIREBASE_APP_ID || undefined,
    messagingSenderId: FIREBASE_MESSAGING_SENDER_ID || undefined,
  })
}

export function getFirebaseAuth(): Auth {
  return getAuth(getFirebaseApp())
}
