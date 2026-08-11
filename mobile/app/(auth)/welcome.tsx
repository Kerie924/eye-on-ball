import { Redirect, router } from 'expo-router'
import { ImageBackground, StyleSheet, Text, View } from 'react-native'
import { LinearGradient } from 'expo-linear-gradient'
import { SafeAreaView } from 'react-native-safe-area-context'

import { useAuth } from '@/src/auth/AuthContext'
import { BrandLogo } from '@/src/components/BrandLogo'
import { Button } from '@/src/components/Button'
import { LoadingState } from '@/src/components/LoadingState'
import { colors } from '@/src/theme/colors'

export default function WelcomeScreen() {
  const { user, loading } = useAuth()

  if (loading) {
    return <LoadingState />
  }

  if (user) {
    return <Redirect href="/(tabs)" />
  }

  return (
    <View style={styles.root}>
      <ImageBackground
        source={{
          uri: 'https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=1200&q=80',
        }}
        style={styles.bg}
        resizeMode="cover"
      >
        <LinearGradient
          colors={['rgba(15,17,23,0.35)', 'rgba(15,17,23,0.92)', '#0f1117']}
          style={styles.overlay}
        >
          <SafeAreaView style={styles.safe}>
            <View style={styles.brand}>
              <BrandLogo variant="full" width={340} />
              <Text style={styles.subtitle}>
                Seu lance. Gravou. Compartilhou.
              </Text>
            </View>

            <View style={styles.actions}>
              <Button label="Entrar" onPress={() => router.push('/(auth)/login')} />
              <Button
                label="Criar conta"
                variant="outline"
                onPress={() => router.push('/(auth)/register')}
              />
            </View>
          </SafeAreaView>
        </LinearGradient>
      </ImageBackground>
    </View>
  )
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: colors.black,
  },
  bg: {
    flex: 1,
  },
  overlay: {
    flex: 1,
  },
  safe: {
    flex: 1,
    justifyContent: 'space-between',
    padding: 28,
    paddingBottom: 40,
  },
  brand: {
    marginTop: 72,
    alignItems: 'center',
    gap: 14,
  },
  subtitle: {
    color: colors.textSecondary,
    fontSize: 16,
    textAlign: 'center',
    lineHeight: 24,
    maxWidth: 280,
  },
  actions: {
    gap: 12,
  },
})
