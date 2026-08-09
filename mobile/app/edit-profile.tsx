import * as ImagePicker from 'expo-image-picker'
import { router } from 'expo-router'
import { useState } from 'react'
import {
  Image,
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
import { Button } from '@/src/components/Button'
import { Input } from '@/src/components/Input'
import { colors } from '@/src/theme/colors'

export default function EditProfileScreen() {
  const { user, updateProfile } = useAuth()
  const [fullName, setFullName] = useState(user?.full_name ?? '')
  const [email, setEmail] = useState(user?.email ?? '')
  const [avatarUrl, setAvatarUrl] = useState(user?.avatar_url ?? '')
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(false)

  async function pickAvatar() {
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync()
    if (!permission.granted) {
      setError('Permissao de galeria necessaria para alterar o avatar')
      return
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images'],
      quality: 0.5,
      base64: true,
      allowsEditing: true,
      aspect: [1, 1],
    })

    if (!result.canceled && result.assets[0]?.base64) {
      const mime = result.assets[0].mimeType ?? 'image/jpeg'
      setAvatarUrl(`data:${mime};base64,${result.assets[0].base64}`)
    }
  }

  async function handleSave() {
    setError('')
    setSuccess('')
    setLoading(true)
    try {
      await updateProfile({
        full_name: fullName.trim(),
        email: email.trim(),
        avatar_url: avatarUrl || null,
        current_password: newPassword ? currentPassword : undefined,
        new_password: newPassword || undefined,
      })
      setSuccess('Perfil atualizado com sucesso')
      setCurrentPassword('')
      setNewPassword('')
      setTimeout(() => router.back(), 700)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Nao foi possivel salvar')
    } finally {
      setLoading(false)
    }
  }

  return (
    <SafeAreaView style={styles.safe} edges={['bottom']}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
          <Pressable style={styles.avatarWrap} onPress={pickAvatar}>
            {avatarUrl ? (
              <Image source={{ uri: avatarUrl }} style={styles.avatarImage} />
            ) : (
              <View style={styles.avatar}>
                <Text style={styles.avatarText}>
                  {fullName.slice(0, 1).toUpperCase() || '?'}
                </Text>
              </View>
            )}
            <Text style={styles.changePhoto}>Alterar foto</Text>
          </Pressable>

          <Input label="Nome completo" value={fullName} onChangeText={setFullName} />
          <Input
            label="E-mail"
            value={email}
            onChangeText={setEmail}
            autoCapitalize="none"
            keyboardType="email-address"
          />
          <Input
            label="Senha atual (para trocar senha)"
            value={currentPassword}
            onChangeText={setCurrentPassword}
            secureTextEntry
          />
          <Input
            label="Nova senha"
            value={newPassword}
            onChangeText={setNewPassword}
            secureTextEntry
          />

          {error ? <Text style={styles.error}>{error}</Text> : null}
          {success ? <Text style={styles.success}>{success}</Text> : null}

          <Button label="Salvar alteracoes" loading={loading} onPress={handleSave} />
          <Button label="Cancelar" variant="ghost" onPress={() => router.back()} />
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.black },
  flex: { flex: 1 },
  content: { padding: 20, gap: 14 },
  avatarWrap: { alignItems: 'center', gap: 8, marginBottom: 8 },
  avatar: {
    width: 96,
    height: 96,
    borderRadius: 48,
    backgroundColor: colors.grassDeep,
    borderWidth: 2,
    borderColor: colors.grass,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarImage: {
    width: 96,
    height: 96,
    borderRadius: 48,
    borderWidth: 2,
    borderColor: colors.grass,
  },
  avatarText: { color: colors.grassLight, fontSize: 36, fontWeight: '800' },
  changePhoto: { color: colors.grassBright, fontWeight: '700' },
  error: { color: '#fca5a5' },
  success: { color: colors.grassBright },
})
