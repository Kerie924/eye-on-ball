import { Stack } from 'expo-router'
import * as SplashScreen from 'expo-splash-screen'
import { useEffect } from 'react'
import { StatusBar } from 'expo-status-bar'
import 'react-native-reanimated'

import { AuthProvider } from '@/src/auth/AuthContext'
import { DialogProvider } from '@/src/ui/DialogContext'
import { colors } from '@/src/theme/colors'

export { ErrorBoundary } from 'expo-router'

SplashScreen.preventAutoHideAsync()

export default function RootLayout() {
  useEffect(() => {
    SplashScreen.hideAsync()
  }, [])

  return (
    <AuthProvider>
      <DialogProvider>
        <StatusBar style="light" />
        <Stack
          screenOptions={{
            headerStyle: { backgroundColor: colors.black },
            headerTintColor: colors.white,
            headerTitleStyle: { fontWeight: '700' },
            contentStyle: { backgroundColor: colors.black },
            headerShadowVisible: false,
          }}
        >
          <Stack.Screen name="index" options={{ headerShown: false }} />
          <Stack.Screen name="(auth)" options={{ headerShown: false }} />
          <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
          <Stack.Screen
            name="recording/[id]"
            options={{
              title: 'Gravacao',
              presentation: 'card',
            }}
          />
          <Stack.Screen
            name="edit-profile"
            options={{
              title: 'Editar perfil',
              presentation: 'card',
            }}
          />
        </Stack>
      </DialogProvider>
    </AuthProvider>
  )
}
