import { Ionicons } from '@expo/vector-icons'
import { Pressable, StyleSheet, Text, View } from 'react-native'

import { colors } from '../theme/colors'
import type { Recording } from '../types'
import { formatDateTime, formatDuration, formatExpiresIn } from '../utils/format'

interface RecordingCardProps {
  recording: Recording
  onPress: () => void
}

export function RecordingCard({ recording, onPress }: RecordingCardProps) {
  return (
    <Pressable
      style={({ pressed }) => [styles.card, pressed && styles.pressed]}
      onPress={onPress}
    >
      <View style={styles.thumb}>
        <Ionicons name="play" size={22} color={colors.white} />
        <Text style={styles.duration}>{formatDuration(recording.duration_seconds)}</Text>
      </View>
      <View style={styles.body}>
        <Text style={styles.title} numberOfLines={1}>
          {recording.court_name ?? `Quadra #${recording.court_id}`}
        </Text>
        <Text style={styles.meta}>Camera {recording.camera_index}</Text>
        <Text style={styles.meta}>{formatDateTime(recording.triggered_at)}</Text>
        <Text style={styles.expires}>{formatExpiresIn(recording.expires_at)}</Text>
      </View>
      <Ionicons name="chevron-forward" size={20} color={colors.textMuted} />
    </Pressable>
  )
}

const styles = StyleSheet.create({
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    backgroundColor: colors.card,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    padding: 14,
  },
  pressed: {
    opacity: 0.92,
    borderColor: colors.grass,
  },
  thumb: {
    width: 78,
    height: 56,
    borderRadius: 12,
    backgroundColor: colors.grassDeep,
    alignItems: 'center',
    justifyContent: 'center',
  },
  duration: {
    position: 'absolute',
    right: 6,
    bottom: 4,
    fontSize: 10,
    color: colors.white,
    backgroundColor: 'rgba(0,0,0,0.55)',
    paddingHorizontal: 4,
    paddingVertical: 2,
    borderRadius: 4,
    overflow: 'hidden',
  },
  body: {
    flex: 1,
    gap: 2,
  },
  title: {
    fontSize: 16,
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
})
