import { Ionicons } from '@expo/vector-icons'
import * as ImagePicker from 'expo-image-picker'
import { useState } from 'react'
import {
  Image,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'

import { ApiError, api } from '@/src/api/client'
import { AppBrandHeader } from '@/src/components/AppBrandHeader'
import { Button } from '@/src/components/Button'
import { colors } from '@/src/theme/colors'
import { showMessage } from '@/src/utils/dialogs'

const MAX_PHOTOS = 4
const MIN_MESSAGE = 10

interface PickedPhoto {
  uri: string
  name: string
  type: string
  base64?: string
}

export default function ReportScreen() {
  const [message, setMessage] = useState('')
  const [photos, setPhotos] = useState<PickedPhoto[]>([])
  const [submitting, setSubmitting] = useState(false)

  async function pickPhotos() {
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync()
    if (!permission.granted) {
      showMessage('Permissao', 'Permita o acesso as fotos para anexar imagens.')
      return
    }

    const remaining = MAX_PHOTOS - photos.length
    if (remaining <= 0) {
      showMessage('Limite', `Voce pode anexar no maximo ${MAX_PHOTOS} fotos.`)
      return
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images'],
      quality: 0.6,
      allowsMultipleSelection: true,
      selectionLimit: remaining,
      base64: Platform.OS !== 'web',
    })

    if (result.canceled) return

    const next = result.assets.slice(0, remaining).map((asset, index) => {
      const mime = asset.mimeType ?? 'image/jpeg'
      const ext = mime.includes('png') ? 'png' : mime.includes('webp') ? 'webp' : 'jpg'
      return {
        uri: asset.uri,
        name: asset.fileName ?? `foto-${Date.now()}-${index}.${ext}`,
        type: mime,
        base64: asset.base64 ?? undefined,
      }
    })
    setPhotos((current) => [...current, ...next].slice(0, MAX_PHOTOS))
  }

  function removePhoto(uri: string) {
    setPhotos((current) => current.filter((photo) => photo.uri !== uri))
  }

  async function handleSubmit() {
    const text = message.trim()
    if (text.length < MIN_MESSAGE) {
      showMessage('Mensagem', `Escreva pelo menos ${MIN_MESSAGE} caracteres.`)
      return
    }

    setSubmitting(true)
    try {
      await api.submitFeedback(
        text,
        photos.map((photo) => ({
          uri: photo.uri,
          name: photo.name,
          type: photo.type,
          base64: photo.base64,
        })),
      )
      setMessage('')
      setPhotos([])
      showMessage(
        'Enviado',
        'Obrigado. Seu relato foi enviado para a equipe Lance On.',
        { tone: 'success' },
      )
    } catch (err) {
      showMessage(
        'Erro',
        err instanceof ApiError ? err.message : 'Nao foi possivel enviar o relato.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <AppBrandHeader />
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView
          contentContainerStyle={styles.content}
          keyboardShouldPersistTaps="handled"
        >
          <Text style={styles.title}>Reportar um erro</Text>
          <Text style={styles.subtitle}>
            Conte o que aconteceu. Voce pode anexar fotos para a equipe entender melhor.
          </Text>

          <View style={styles.field}>
            <Text style={styles.label}>Sua mensagem</Text>
            <TextInput
              value={message}
              onChangeText={setMessage}
              placeholder="Ex: o video nao abriu na quadra X apos o botao..."
              placeholderTextColor={colors.textMuted}
              style={styles.textarea}
              multiline
              textAlignVertical="top"
              maxLength={2000}
            />
            <Text style={styles.counter}>{message.trim().length}/2000</Text>
          </View>

          <View style={styles.field}>
            <Text style={styles.label}>Fotos (opcional)</Text>
            <View style={styles.photos}>
              {photos.map((photo) => (
                <View key={photo.uri} style={styles.thumbWrap}>
                  <Image source={{ uri: photo.uri }} style={styles.thumb} />
                  <Pressable
                    style={styles.removeBtn}
                    onPress={() => removePhoto(photo.uri)}
                    hitSlop={8}
                  >
                    <Ionicons name="close-circle" size={22} color={colors.white} />
                  </Pressable>
                </View>
              ))}
              {photos.length < MAX_PHOTOS ? (
                <Pressable
                  style={({ pressed }) => [styles.addPhoto, pressed && styles.pressed]}
                  onPress={() => void pickPhotos()}
                >
                  <Ionicons name="camera-outline" size={26} color={colors.grass} />
                  <Text style={styles.addPhotoText}>Anexar</Text>
                </Pressable>
              ) : null}
            </View>
            <Text style={styles.hint}>Ate {MAX_PHOTOS} imagens, JPG ou PNG.</Text>
          </View>

          <Button
            label="Enviar relato"
            loading={submitting}
            onPress={() => void handleSubmit()}
          />
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
    padding: 20,
    gap: 18,
    paddingBottom: 40,
  },
  title: {
    color: colors.white,
    fontSize: 26,
    fontWeight: '800',
  },
  subtitle: {
    color: colors.textSecondary,
    fontSize: 15,
    lineHeight: 22,
    marginTop: -8,
  },
  field: {
    gap: 8,
  },
  label: {
    color: colors.textSecondary,
    fontSize: 14,
    fontWeight: '700',
  },
  textarea: {
    minHeight: 140,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    backgroundColor: colors.blackMuted,
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 16,
    color: colors.textPrimary,
  },
  counter: {
    alignSelf: 'flex-end',
    color: colors.textMuted,
    fontSize: 12,
  },
  photos: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  thumbWrap: {
    width: 84,
    height: 84,
  },
  thumb: {
    width: 84,
    height: 84,
    borderRadius: 12,
    backgroundColor: colors.card,
  },
  removeBtn: {
    position: 'absolute',
    top: -6,
    right: -6,
  },
  addPhoto: {
    width: 84,
    height: 84,
    borderRadius: 12,
    borderWidth: 1.5,
    borderStyle: 'dashed',
    borderColor: colors.grass,
    backgroundColor: 'rgba(34,197,94,0.08)',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
  },
  addPhotoText: {
    color: colors.grass,
    fontSize: 12,
    fontWeight: '700',
  },
  pressed: {
    opacity: 0.85,
  },
  hint: {
    color: colors.textMuted,
    fontSize: 12,
  },
})
