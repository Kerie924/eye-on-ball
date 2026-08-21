import { cacheDirectory, downloadAsync } from 'expo-file-system/legacy'
import * as Sharing from 'expo-sharing'
import { useVideoPlayer, VideoView } from 'expo-video'
import { useLocalSearchParams } from 'expo-router'
import { useEffect, useMemo, useRef, useState } from 'react'
import {
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native'
import { Ionicons } from '@expo/vector-icons'

import { ApiError, api, getAuthToken } from '@/src/api/client'
import { Button } from '@/src/components/Button'
import { LoadingState } from '@/src/components/LoadingState'
import { colors } from '@/src/theme/colors'
import type { Recording } from '@/src/types'
import { showMessage } from '@/src/utils/dialogs'
import { formatDateTime, formatDuration, formatExpiresIn } from '@/src/utils/format'

function RecordingPlayer({ uri }: { uri: string }) {
  const videoRef = useRef<VideoView>(null)
  const player = useVideoPlayer(uri, (instance) => {
    instance.loop = false
  })

  return (
    <View style={styles.playerWrap}>
      <VideoView
        ref={videoRef}
        player={player}
        style={styles.video}
        contentFit="contain"
        nativeControls
        fullscreenOptions={{ enable: true }}
        allowsPictureInPicture
      />
      {Platform.OS !== 'web' ? (
        <Pressable
          style={styles.fullscreenBtn}
          onPress={() => {
            void videoRef.current?.enterFullscreen()
          }}
        >
          <Ionicons name="expand" size={18} color={colors.white} />
          <Text style={styles.fullscreenBtnText}>Tela cheia</Text>
        </Pressable>
      ) : null}
    </View>
  )
}

export default function RecordingDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>()
  const [recording, setRecording] = useState<Recording | null>(null)
  const [loading, setLoading] = useState(true)
  const [downloading, setDownloading] = useState(false)
  const [sharing, setSharing] = useState(false)

  const mediaUrl = useMemo(() => {
    if (!recording) return null
    const token = getAuthToken()
    if (!token) return recording.download_url ?? null
    return `${api.recordingStreamUrl(recording.id)}?token=${encodeURIComponent(token)}`
  }, [recording])

  useEffect(() => {
    async function loadRecording() {
      try {
        const data = await api.recording(Number(id))
        setRecording(data)
      } catch (err) {
        showMessage(
          'Erro',
          err instanceof ApiError ? err.message : 'Nao foi possivel carregar a gravacao',
        )
      } finally {
        setLoading(false)
      }
    }

    loadRecording()
  }, [id])

  async function getLocalFile(): Promise<string | null> {
    if (!recording || !cacheDirectory) {
      return null
    }
    const token = getAuthToken()
    const fileName = `lance-${recording.id}.mp4`
    const target = `${cacheDirectory}${fileName}`

    // Prefer query-token URL — more reliable than auth headers on some Android builds.
    if (token) {
      const url = `${api.recordingStreamUrl(recording.id)}?token=${encodeURIComponent(token)}&download=true`
      const result = await downloadAsync(url, target)
      return result.uri
    }

    if (recording.download_url) {
      const result = await downloadAsync(recording.download_url, target)
      return result.uri
    }

    return null
  }

  async function handleShare() {
    setSharing(true)
    try {
      const uri = await getLocalFile()
      if (!uri) {
        showMessage('Indisponivel', 'Link do video nao encontrado.')
        return
      }
      if (await Sharing.isAvailableAsync()) {
        await Sharing.shareAsync(uri, {
          mimeType: 'video/mp4',
          UTI: 'public.movie',
        })
      } else {
        showMessage('Compartilhar', 'Compartilhamento nao disponivel neste dispositivo.')
      }
    } catch (err) {
      showMessage(
        'Erro',
        err instanceof Error ? err.message : 'Nao foi possivel compartilhar o video.',
      )
    } finally {
      setSharing(false)
    }
  }

  async function handleDownload() {
    setDownloading(true)
    try {
      const uri = await getLocalFile()
      if (!uri) {
        showMessage('Indisponivel', 'Link de download nao encontrado.')
        return
      }
      if (await Sharing.isAvailableAsync()) {
        await Sharing.shareAsync(uri, {
          dialogTitle: 'Salvar video',
          mimeType: 'video/mp4',
          UTI: 'public.movie',
        })
        showMessage('Pronto', 'Escolha “Salvar” ou “Arquivos” para guardar o video.')
      } else if (Platform.OS === 'web') {
        // Web: open authenticated stream so the browser can save it.
        const token = getAuthToken()
        const url = token
          ? `${api.recordingStreamUrl(recording!.id)}?token=${encodeURIComponent(token)}&download=true`
          : recording!.download_url
        if (url) {
          window.open(url, '_blank')
        }
      } else {
        showMessage('Download', `Arquivo salvo em cache: ${uri}`)
      }
    } catch (err) {
      showMessage(
        'Erro',
        err instanceof Error ? err.message : 'Nao foi possivel baixar o video.',
      )
    } finally {
      setDownloading(false)
    }
  }

  if (loading) {
    return <LoadingState message="Carregando video..." />
  }

  if (!recording) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>Gravacao nao encontrada</Text>
      </View>
    )
  }

  return (
    <ScrollView contentContainerStyle={styles.content} style={styles.root}>
      {mediaUrl ? (
        <RecordingPlayer uri={mediaUrl} />
      ) : (
        <View style={styles.videoPlaceholder}>
          <Text style={styles.placeholderText}>Video indisponivel</Text>
        </View>
      )}

      <View style={styles.metaCard}>
        <Text style={styles.title}>{recording.court_name ?? `Quadra #${recording.court_id}`}</Text>
        <Text style={styles.meta}>Camera {recording.camera_index}</Text>
        <Text style={styles.meta}>{formatDateTime(recording.triggered_at)}</Text>
        <Text style={styles.meta}>Duracao: {formatDuration(recording.duration_seconds)}</Text>
        <Text style={styles.expires}>{formatExpiresIn(recording.expires_at)}</Text>
      </View>

      <View style={styles.actions}>
        <Button
          label="Compartilhar"
          variant="outline"
          loading={sharing}
          onPress={handleShare}
          style={styles.actionBtn}
        />
        <Button
          label="Download"
          loading={downloading}
          onPress={handleDownload}
          style={styles.actionBtn}
        />
      </View>
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: colors.black,
  },
  content: {
    padding: 16,
    gap: 16,
    paddingBottom: 40,
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.black,
  },
  playerWrap: {
    gap: 8,
  },
  video: {
    width: '100%',
    aspectRatio: 16 / 9,
    borderRadius: 14,
    backgroundColor: '#000',
  },
  fullscreenBtn: {
    alignSelf: 'flex-end',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  fullscreenBtnText: {
    color: colors.white,
    fontSize: 13,
    fontWeight: '700',
  },
  videoPlaceholder: {
    width: '100%',
    aspectRatio: 16 / 9,
    borderRadius: 14,
    backgroundColor: colors.blackMuted,
    alignItems: 'center',
    justifyContent: 'center',
  },
  placeholderText: {
    color: colors.textMuted,
  },
  metaCard: {
    backgroundColor: colors.card,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    padding: 16,
    gap: 4,
  },
  title: {
    fontSize: 20,
    fontWeight: '800',
    color: colors.white,
  },
  meta: {
    fontSize: 14,
    color: colors.textSecondary,
  },
  expires: {
    marginTop: 6,
    fontSize: 13,
    fontWeight: '700',
    color: colors.grassBright,
  },
  actions: {
    flexDirection: 'row',
    gap: 12,
  },
  actionBtn: {
    flex: 1,
  },
  errorText: {
    color: colors.danger,
    fontSize: 16,
  },
})
