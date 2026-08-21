import { Ionicons } from '@expo/vector-icons'
import { File, Paths } from 'expo-file-system'
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

function streamUrl(recordingId: number, download = false) {
  const token = getAuthToken()
  const params = new URLSearchParams()
  if (token) params.set('token', token)
  if (download) params.set('download', 'true')
  const query = params.toString()
  return `${api.recordingStreamUrl(recordingId)}${query ? `?${query}` : ''}`
}

async function saveOnWeb(recording: Recording) {
  const token = getAuthToken()
  const url = streamUrl(recording.id, true) || recording.download_url
  if (!url) {
    throw new Error('Link de download nao encontrado.')
  }

  const response = await fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  })
  if (!response.ok) {
    throw new Error('Nao foi possivel baixar o video.')
  }

  const blob = await response.blob()
  const objectUrl = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = objectUrl
  anchor.download = `lance-${recording.id}.mp4`
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(objectUrl)
}

async function saveOnDevice(recording: Recording): Promise<string> {
  const token = getAuthToken()
  const url = token ? streamUrl(recording.id, true) : recording.download_url
  if (!url) {
    throw new Error('Link de download nao encontrado.')
  }

  const dest = new File(Paths.cache, `lance-${recording.id}.mp4`)
  const downloaded = await File.downloadFileAsync(url, dest, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    idempotent: true,
  })
  return downloaded.uri
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
    if (!token && recording.download_url) return recording.download_url
    if (!token) return null
    return streamUrl(recording.id)
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

  async function handleShare() {
    if (!recording) return
    setSharing(true)
    try {
      if (Platform.OS === 'web') {
        await saveOnWeb(recording)
        showMessage('Pronto', 'O download do video foi iniciado.')
        return
      }
      const uri = await saveOnDevice(recording)
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
    if (!recording) return
    setDownloading(true)
    try {
      if (Platform.OS === 'web') {
        await saveOnWeb(recording)
        showMessage('Pronto', 'O download do video foi iniciado.')
        return
      }
      const uri = await saveOnDevice(recording)
      if (await Sharing.isAvailableAsync()) {
        await Sharing.shareAsync(uri, {
          dialogTitle: 'Salvar video',
          mimeType: 'video/mp4',
          UTI: 'public.movie',
        })
        showMessage('Pronto', 'Escolha “Salvar” ou “Arquivos” para guardar o video.')
      } else {
        showMessage('Download', 'Video salvo no cache do aplicativo.')
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
