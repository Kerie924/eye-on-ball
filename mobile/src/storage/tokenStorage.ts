import * as SecureStore from 'expo-secure-store'
import { Platform } from 'react-native'

/**
 * Token storage that works on native (SecureStore) and web (localStorage).
 * expo-secure-store is not fully implemented on web.
 */
export async function getToken(key: string): Promise<string | null> {
  if (Platform.OS === 'web') {
    try {
      return localStorage.getItem(key)
    } catch {
      return null
    }
  }

  try {
    return await SecureStore.getItemAsync(key)
  } catch {
    return null
  }
}

export async function setToken(key: string, value: string): Promise<void> {
  if (Platform.OS === 'web') {
    localStorage.setItem(key, value)
    return
  }

  await SecureStore.setItemAsync(key, value)
}

export async function deleteToken(key: string): Promise<void> {
  if (Platform.OS === 'web') {
    try {
      localStorage.removeItem(key)
    } catch {
      // ignore
    }
    return
  }

  try {
    await SecureStore.deleteItemAsync(key)
  } catch {
    // ignore missing native methods / empty keys
  }
}
