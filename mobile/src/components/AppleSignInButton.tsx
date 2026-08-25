import * as AppleAuthentication from 'expo-apple-authentication'
import { useEffect, useState } from 'react'
import { Platform, StyleSheet, View } from 'react-native'

import { isAppleAuthAvailable } from '../auth/appleAuth'
import { IOS_APP_STORE_ENABLED } from '../config'

export function AppleSignInButton({
  onPress,
  disabled = false,
  type = 'continue',
}: {
  onPress: () => void
  disabled?: boolean
  type?: 'continue' | 'signUp'
}) {
  const [available, setAvailable] = useState(false)

  useEffect(() => {
    if (!IOS_APP_STORE_ENABLED || Platform.OS !== 'ios') {
      return
    }
    void isAppleAuthAvailable().then(setAvailable)
  }, [])

  if (!available) {
    return null
  }

  return (
    <View pointerEvents={disabled ? 'none' : 'auto'} style={[styles.wrap, disabled && styles.disabled]}>
      <AppleAuthentication.AppleAuthenticationButton
        buttonType={
          type === 'signUp'
            ? AppleAuthentication.AppleAuthenticationButtonType.SIGN_UP
            : AppleAuthentication.AppleAuthenticationButtonType.CONTINUE
        }
        buttonStyle={AppleAuthentication.AppleAuthenticationButtonStyle.WHITE}
        cornerRadius={14}
        style={styles.button}
        onPress={onPress}
      />
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: {
    width: '100%',
    height: 48,
  },
  disabled: {
    opacity: 0.55,
  },
  button: {
    width: '100%',
    height: 48,
  },
})
