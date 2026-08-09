import { router } from 'expo-router'
import { useState } from 'react'
import { StyleSheet, Text, View } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'

import { ApiError, api } from '@/src/api/client'
import { Button } from '@/src/components/Button'
import { Input } from '@/src/components/Input'
import { colors } from '@/src/theme/colors'

export default function ForgotPasswordScreen() {
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit() {
    setError('')
    setMessage('')
    setLoading(true)
    try {
      const result = await api.forgotPassword(email.trim())
      setMessage(result.message)
      if (result.reset_token) {
        router.push({
          pathname: '/(auth)/reset-password',
          params: { token: result.reset_token },
        })
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Nao foi possivel enviar')
    } finally {
      setLoading(false)
    }
  }

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.content}>
        <Text style={styles.title}>Esqueceu a senha?</Text>
        <Text style={styles.subtitle}>
          Informe seu e-mail para receber o link de redefinicao.
        </Text>
        <Input
          label="E-mail"
          value={email}
          onChangeText={setEmail}
          autoCapitalize="none"
          keyboardType="email-address"
        />
        {error ? <Text style={styles.error}>{error}</Text> : null}
        {message ? <Text style={styles.success}>{message}</Text> : null}
        <Button label="Enviar" loading={loading} onPress={handleSubmit} />
        <Button label="Voltar" variant="ghost" onPress={() => router.back()} />
      </View>
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.black },
  content: { flex: 1, padding: 24, gap: 14, justifyContent: 'center' },
  title: { color: colors.white, fontSize: 28, fontWeight: '800' },
  subtitle: { color: colors.textSecondary, fontSize: 15, lineHeight: 22, marginBottom: 8 },
  error: { color: '#fca5a5' },
  success: { color: colors.grassBright },
})
