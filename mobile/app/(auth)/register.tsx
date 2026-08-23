import { Link, router } from 'expo-router'
import { useState } from 'react'
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
  describeAuthError,
  isGoogleAuthCancelled,
  isGoogleAuthConfigured,
  signInWithGoogle,
} from '@/src/auth/googleAuth'
import { Button } from '@/src/components/Button'
import { BrandLogo } from '@/src/components/BrandLogo'
import { Input } from '@/src/components/Input'
import { colors } from '@/src/theme/colors'
import type { UserRole } from '@/src/types'

export default function RegisterScreen() {
  const { register, loginWithGoogle } = useAuth()
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState<UserRole>('athlete')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [googleLoading, setGoogleLoading] = useState(false)

  async function handleRegister() {
    setError('')
    setLoading(true)
    try {
      await register({
        email: email.trim(),
        password,
        full_name: fullName.trim(),
        role,
      })
      router.replace('/(tabs)')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Nao foi possivel cadastrar')
    } finally {
      setLoading(false)
    }
  }

  async function handleGoogle() {
    setError('')
    if (!isGoogleAuthConfigured()) {
      setError(
        'Firebase Auth nao configurado. Defina EXPO_PUBLIC_FIREBASE_API_KEY, EXPO_PUBLIC_FIREBASE_PROJECT_ID e EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID.',
      )
      return
    }
    setGoogleLoading(true)
    try {
      const idToken = await signInWithGoogle()
      await loginWithGoogle(idToken, role)
      router.replace('/(tabs)')
    } catch (err) {
      if (!(await isGoogleAuthCancelled(err))) {
        setError(describeAuthError(err, 'Falha no cadastro Google'))
      }
    } finally {
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
            <BrandLogo variant="full" width={280} />
            <Text style={styles.title}>Criar conta</Text>
            <Text style={styles.subtitle}>
              Atletas solicitam acesso por quadra. Olheiros precisam de aprovacao.
            </Text>
          </View>

          <View style={styles.form}>
            <Input label="Nome completo" value={fullName} onChangeText={setFullName} />
            <Input
              label="E-mail"
              value={email}
              onChangeText={setEmail}
              autoCapitalize="none"
              keyboardType="email-address"
            />
            <Input
              label="Senha"
              value={password}
              onChangeText={setPassword}
              secureTextEntry
            />

            <View style={styles.roleGroup}>
              <Text style={styles.roleLabel}>Tipo de conta</Text>
              <View style={styles.roleRow}>
                <RoleOption
                  label="Atleta"
                  selected={role === 'athlete'}
                  onPress={() => setRole('athlete')}
                />
                <RoleOption
                  label="Olheiro"
                  selected={role === 'scout'}
                  onPress={() => setRole('scout')}
                />
              </View>
            </View>

            {error ? <Text style={styles.error}>{error}</Text> : null}
            <Button label="Cadastrar" loading={loading} onPress={handleRegister} />

            <View style={styles.dividerRow}>
              <View style={styles.divider} />
              <Text style={styles.dividerText}>ou continue com</Text>
              <View style={styles.divider} />
            </View>

            <Button
              label="Cadastrar com Google"
              variant="outline"
              loading={googleLoading}
              onPress={handleGoogle}
            />

            <Text style={styles.footer}>
              Ja tem conta?{' '}
              <Link href="/(auth)/login" style={styles.link}>
                Entrar
              </Link>
            </Text>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  )
}

function RoleOption({
  label,
  selected,
  onPress,
}: {
  label: string
  selected: boolean
  onPress: () => void
}) {
  return (
    <Pressable
      style={[styles.roleOption, selected && styles.roleOptionSelected]}
      onPress={onPress}
    >
      <Text style={[styles.roleOptionText, selected && styles.roleOptionTextSelected]}>
        {label}
      </Text>
    </Pressable>
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
    padding: 24,
    gap: 24,
  },
  header: {
    gap: 8,
    marginTop: 12,
    alignItems: 'center',
  },
  title: {
    marginTop: 8,
    color: colors.white,
    fontSize: 28,
    fontWeight: '800',
    alignSelf: 'stretch',
  },
  subtitle: {
    color: colors.textSecondary,
    fontSize: 15,
    lineHeight: 22,
    alignSelf: 'stretch',
  },
  form: {
    gap: 14,
  },
  roleGroup: {
    gap: 8,
  },
  roleLabel: {
    color: colors.textSecondary,
    fontSize: 14,
    fontWeight: '600',
  },
  roleRow: {
    flexDirection: 'row',
    gap: 10,
  },
  roleOption: {
    flex: 1,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    borderRadius: 12,
    paddingVertical: 12,
    alignItems: 'center',
    backgroundColor: colors.blackMuted,
  },
  roleOptionSelected: {
    backgroundColor: colors.grassDeep,
    borderColor: colors.grass,
  },
  roleOptionText: {
    color: colors.textMuted,
    fontWeight: '600',
  },
  roleOptionTextSelected: {
    color: colors.grassLight,
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
    marginTop: 4,
  },
  link: {
    color: colors.grassBright,
    fontWeight: '700',
  },
})
