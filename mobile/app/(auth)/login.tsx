import { Link, router } from 'expo-router'
import { useEffect, useState } from 'react'
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'

import { ApiError } from '@/src/api/client'
import { useAuth } from '@/src/auth/AuthContext'
import {
  extractGoogleIdToken,
  isGoogleAuthConfigured,
  useGoogleIdToken,
} from '@/src/auth/googleAuth'
import { Button } from '@/src/components/Button'
import { BrandLogo } from '@/src/components/BrandLogo'
import { Input } from '@/src/components/Input'
import { colors } from '@/src/theme/colors'

export default function LoginScreen() {
  const { login, loginWithGoogle } = useAuth()
  const { ready, response, promptAsync } = useGoogleIdToken()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [googleLoading, setGoogleLoading] = useState(false)

  useEffect(() => {
    async function finishGoogle() {
      const idToken = extractGoogleIdToken(response)
      if (!idToken) {
        if (response?.type === 'error') {
          setError('Falha na autenticacao Google')
          setGoogleLoading(false)
        } else if (response?.type === 'dismiss' || response?.type === 'cancel') {
          setGoogleLoading(false)
        }
        return
      }

      setGoogleLoading(true)
      try {
        await loginWithGoogle(idToken, 'athlete')
        router.replace('/(tabs)')
      } catch (err) {
        setError(err instanceof ApiError ? err.message : 'Falha no login Google')
      } finally {
        setGoogleLoading(false)
      }
    }

    if (response) {
      finishGoogle()
    }
  }, [response, loginWithGoogle])

  async function handleLogin() {
    setError('')
    setLoading(true)
    try {
      await login(email.trim(), password)
      router.replace('/(tabs)')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Nao foi possivel entrar')
    } finally {
      setLoading(false)
    }
  }

  async function handleGoogle() {
    setError('')
    if (!isGoogleAuthConfigured()) {
      setError(
        'Google OAuth nao configurado. Defina EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID no mobile/.env e reinicie o Expo.',
      )
      return
    }
    setGoogleLoading(true)
    try {
      await promptAsync()
    } catch {
      setError('Nao foi possivel abrir o login Google')
      setGoogleLoading(false)
    }
  }

  return (
    <SafeAreaView style={styles.safe}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
          <View style={styles.header}>
            <BrandLogo variant="full" width={300} />
            <Text style={styles.title}>Entrar</Text>
            <Text style={styles.subtitle}>Acesse seus lances gravados</Text>
          </View>

          <View style={styles.form}>
            <Input
              label="E-mail"
              value={email}
              onChangeText={setEmail}
              autoCapitalize="none"
              keyboardType="email-address"
              autoComplete="email"
              placeholder="seu@email.com"
            />
            <Input
              label="Senha"
              value={password}
              onChangeText={setPassword}
              secureTextEntry
              autoComplete="password"
              placeholder="••••••••"
            />
            <Pressable onPress={() => router.push('/(auth)/forgot-password')}>
              <Text style={styles.forgot}>Esqueceu a senha?</Text>
            </Pressable>
            {error ? <Text style={styles.error}>{error}</Text> : null}
            <Button label="Entrar" loading={loading} onPress={handleLogin} />

            <View style={styles.dividerRow}>
              <View style={styles.divider} />
              <Text style={styles.dividerText}>ou continue com</Text>
              <View style={styles.divider} />
            </View>

            <Button
              label="Continuar com Google"
              variant="outline"
              loading={googleLoading}
              disabled={!ready && isGoogleAuthConfigured()}
              onPress={handleGoogle}
            />

            <Text style={styles.footer}>
              Nao tem conta?{' '}
              <Link href="/(auth)/register" style={styles.link}>
                Criar agora
              </Link>
            </Text>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.black,
  },
  flex: {
    flex: 1,
  },
  content: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 24,
    gap: 28,
  },
  header: {
    alignItems: 'center',
    gap: 8,
  },
  title: {
    marginTop: 8,
    color: colors.white,
    fontSize: 30,
    fontWeight: '800',
  },
  subtitle: {
    color: colors.textSecondary,
    fontSize: 15,
  },
  form: {
    gap: 14,
  },
  forgot: {
    color: colors.grassBright,
    fontWeight: '700',
    textAlign: 'right',
    marginTop: -4,
  },
  error: {
    color: '#fca5a5',
    fontSize: 14,
  },
  dividerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginVertical: 4,
  },
  divider: {
    flex: 1,
    height: 1,
    backgroundColor: colors.cardBorder,
  },
  dividerText: {
    color: colors.textMuted,
    fontSize: 12,
  },
  footer: {
    color: colors.textMuted,
    textAlign: 'center',
    marginTop: 8,
  },
  link: {
    color: colors.grassBright,
    fontWeight: '700',
  },
})

