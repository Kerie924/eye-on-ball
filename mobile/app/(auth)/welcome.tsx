import { LinearGradient } from 'expo-linear-gradient'
import { Redirect, router } from 'expo-router'
import { StyleSheet, Text, View } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'

import { useAuth } from '@/src/auth/AuthContext'
import { BrandLogo } from '@/src/components/BrandLogo'
import { Button } from '@/src/components/Button'
import { LegalLinks } from '@/src/components/LegalLinks'
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
      <LinearGradient
        colors={['#0a0a0a', '#0f1117', '#14532d']}
        start={{ x: 0.15, y: 0 }}
        end={{ x: 0.9, y: 1 }}
        style={styles.bg}
      >
        <SafeAreaView style={styles.safe}>
          <View style={styles.brand}>
            <BrandLogo variant="full" width={340} />
            <Text style={styles.subtitle}>Seu lance. Gravou. Compartilhou.</Text>
          </View>

          <View style={styles.actions}>
            <Button label="Entrar" onPress={() => router.push('/(auth)/login')} />
            <Button
              label="Criar conta"
              variant="outline"
              onPress={() => router.push('/(auth)/register')}
            />
            <LegalLinks />
          </View>
        </SafeAreaView>
      </LinearGradient>
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
