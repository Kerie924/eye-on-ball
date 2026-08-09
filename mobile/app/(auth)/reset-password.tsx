import { router, useLocalSearchParams } from 'expo-router'
import { useState } from 'react'
import { StyleSheet, Text, View } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'

import { ApiError, api } from '@/src/api/client'
import { Button } from '@/src/components/Button'
import { Input } from '@/src/components/Input'
import { colors } from '@/src/theme/colors'

export default function ResetPasswordScreen() {
  const params = useLocalSearchParams<{ token?: string }>()
  const [token, setToken] = useState(params.token ?? '')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit() {
    setError('')
    if (password !== confirm) {
      setError('As senhas nao coincidem')
      return
    }
    setLoading(true)
    try {
      await api.resetPassword(token.trim(), password)
      router.replace('/(auth)/login')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Nao foi possivel redefinir')
    } finally {
      setLoading(false)
    }
  }

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.content}>
        <Text style={styles.title}>Nova senha</Text>
        <Text style={styles.subtitle}>Crie uma nova senha para sua conta.</Text>
        {!params.token ? (
          <Input label="Token" value={token} onChangeText={setToken} />
        ) : null}
        <Input
          label="Nova senha"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
        />
        <Input
          label="Confirmar senha"
          value={confirm}
          onChangeText={setConfirm}
          secureTextEntry
        />
        {error ? <Text style={styles.error}>{error}</Text> : null}
        <Button label="Salvar senha" loading={loading} onPress={handleSubmit} />
        <Button label="Voltar" variant="ghost" onPress={() => router.back()} />
      </View>
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.black },
  content: { flex: 1, padding: 24, gap: 14, justifyContent: 'center' },
  title: { color: colors.white, fontSize: 28, fontWeight: '800' },
  subtitle: { color: colors.textSecondary, fontSize: 15, marginBottom: 8 },
  error: { color: '#fca5a5' },
})
