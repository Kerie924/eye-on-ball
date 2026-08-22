import { Pressable, StyleSheet, Text, View } from 'react-native'
import { useVideoPlayer, VideoView } from 'expo-video'

import { api, getAuthToken } from '../api/client'
import { colors } from '../theme/colors'
import type { Recording } from '../types'
import { formatDateTime, formatDuration, formatExpiresIn } from '../utils/format'

interface RecordingCardProps {
  recording: Recording
  onPress: () => void
}

function PreviewPlayer({ uri }: { uri: string }) {
  const player = useVideoPlayer(uri, (instance) => {
    instance.loop = false
    instance.muted = true
  })

  return (
    <VideoView
      player={player}
      style={styles.video}
      contentFit="contain"
      nativeControls
    />
  )
}

export function RecordingCard({ recording, onPress }: RecordingCardProps) {
  const token = getAuthToken()
  const previewUrl = token
    ? `${api.recordingStreamUrl(recording.id)}?token=${encodeURIComponent(token)}`
    : recording.download_url ?? null

  return (
    <View style={styles.card}>
      <View style={styles.playerWrap}>
        {previewUrl ? (
          <PreviewPlayer uri={previewUrl} />
        ) : (
          <View style={styles.videoPlaceholder}>
            <Text style={styles.placeholderText}>Video indisponivel</Text>
          </View>
        )}
      </View>
      <Pressable onPress={onPress} style={({ pressed }) => [styles.body, pressed && styles.pressed]}>
        <Text style={styles.title} numberOfLines={1}>
          {recording.court_name ?? `Quadra #${recording.court_id}`}
        </Text>
        <Text style={styles.meta}>
          Camera {recording.camera_index} · {formatDuration(recording.duration_seconds)}
        </Text>
        <Text style={styles.meta}>{formatDateTime(recording.triggered_at)}</Text>
        <Text style={styles.expires}>{formatExpiresIn(recording.expires_at)}</Text>
        <Text style={styles.detailsLink}>Download e tela cheia</Text>
      </Pressable>
    </View>
  )
}

const styles = StyleSheet.create({
  card: {
    width: '100%',
    alignSelf: 'center',
    backgroundColor: colors.card,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    overflow: 'hidden',
  },
  playerWrap: {
    width: '100%',
    backgroundColor: '#000',
  },
  video: {
    width: '100%',
    aspectRatio: 16 / 9,
    backgroundColor: '#000',
  },
  videoPlaceholder: {
    width: '100%',
    aspectRatio: 16 / 9,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.blackMuted,
  },
  placeholderText: {
    color: colors.textMuted,
  },
  body: {
    paddingHorizontal: 14,
    paddingVertical: 12,
    gap: 3,
  },
  pressed: {
    opacity: 0.9,
  },
  title: {
    fontSize: 17,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  meta: {
    fontSize: 13,
    color: colors.textSecondary,
  },
  expires: {
    fontSize: 12,
    color: colors.grassBright,
    fontWeight: '600',
    marginTop: 2,
  },
  detailsLink: {
    marginTop: 6,
    fontSize: 13,
    fontWeight: '700',
    color: colors.grassBright,
  },
})
