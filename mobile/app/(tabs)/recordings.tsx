import { router, useFocusEffect, useLocalSearchParams } from 'expo-router'
import { useCallback, useMemo, useState } from 'react'
import {
  FlatList,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from 'react-native'

import { api } from '@/src/api/client'
import { EmptyState } from '@/src/components/EmptyState'
import { LoadingState } from '@/src/components/LoadingState'
import { RecordingCard } from '@/src/components/RecordingCard'
import { colors } from '@/src/theme/colors'
import type { Recording } from '@/src/types'
import { formatLongDate, recordingInTimeSlot } from '@/src/utils/timeSlots'

function firstParam(value?: string | string[]) {
  const raw = Array.isArray(value) ? value[0] : value
  return raw?.trim() || null
}

export default function RecordingsScreen() {
  const params = useLocalSearchParams<{
    courtId?: string
    courtName?: string
    cityName?: string
    date?: string
    startTime?: string
    endTime?: string
  }>()

  const courtId = useMemo(() => {
    const parsed = Number(firstParam(params.courtId))
    return Number.isFinite(parsed) && parsed > 0 ? parsed : null
  }, [params.courtId])
  const courtName = firstParam(params.courtName)
  const cityName = firstParam(params.cityName)
  const date = firstParam(params.date)
  const startTime = firstParam(params.startTime)
  const endTime = firstParam(params.endTime)
  const hasWindow = Boolean(courtId && date && startTime && endTime)

  const [recordings, setRecordings] = useState<Recording[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState('')

  const load = useCallback(
    async (isRefresh = false) => {
      if (!hasWindow || !courtId || !date || !startTime || !endTime) {
        setRecordings([])
        setLoading(false)
        setRefreshing(false)
        return
      }
      if (isRefresh) setRefreshing(true)
      else setLoading(true)
      setError('')
      try {
        const data = await api.recordings(courtId, date, startTime, endTime)
        setRecordings(
          data.filter((item) => recordingInTimeSlot(item.triggered_at, date, startTime, endTime)),
        )
      } catch (err) {
        setRecordings([])
        setError(err instanceof Error ? err.message : 'Nao foi possivel carregar os videos')
      } finally {
        setLoading(false)
        setRefreshing(false)
      }
    },
    [courtId, date, startTime, endTime, hasWindow],
  )

  useFocusEffect(
    useCallback(() => {
      load()
    }, [load]),
  )

  if (loading) {
    return <LoadingState message="Carregando gravacoes..." />
  }

  if (!hasWindow) {
    return (
      <View style={styles.root}>
        <EmptyState
          title="Escolha cidade, quadra e horario"
          description="Toque em Quadras, selecione a cidade e a quadra, depois a data e o bloco de horario."
        />
        <Pressable style={styles.cta} onPress={() => router.push('/(tabs)/courts')}>
          <Text style={styles.ctaText}>Comecar</Text>
        </Pressable>
      </View>
    )
  }

  return (
    <View style={styles.root}>
      <View style={styles.filterBar}>
        <View style={styles.filterBody}>
          <Text style={styles.filterTitle} numberOfLines={1}>
            {cityName ? `${cityName} · ` : ''}
            {courtName ?? `Quadra #${courtId}`}
          </Text>
          <Text style={styles.filterMeta}>
            {date ? formatLongDate(date) : ''} · {startTime} – {endTime}
          </Text>
        </View>
        <Pressable onPress={() => router.push('/(tabs)/courts')} hitSlop={8}>
          <Text style={styles.filterClear}>Trocar</Text>
        </Pressable>
      </View>

      <FlatList
        contentContainerStyle={styles.content}
        data={recordings}
        keyExtractor={(item) => String(item.id)}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => load(true)}
            tintColor={colors.grass}
          />
        }
        ListEmptyComponent={
          <EmptyState
            title={error ? 'Erro ao carregar' : 'Nenhum video neste horario'}
            description={
              error ||
              'Nao ha lances desta quadra neste bloco. Tente outro horario ou outra data.'
            }
          />
        }
        renderItem={({ item }) => (
          <RecordingCard
            recording={item}
            onPress={() => router.push(`/recording/${item.id}`)}
          />
        )}
        ItemSeparatorComponent={() => <View style={styles.separator} />}
      />
    </View>
  )
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: colors.black,
  },
  filterBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 12,
    marginHorizontal: 16,
    marginTop: 8,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 12,
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  filterBody: {
    flex: 1,
    gap: 2,
  },
  filterTitle: {
    color: colors.white,
    fontWeight: '700',
    fontSize: 14,
  },
  filterMeta: {
    color: colors.textSecondary,
    fontSize: 12,
    textTransform: 'capitalize',
  },
  filterClear: {
    color: colors.grassBright,
    fontWeight: '700',
    fontSize: 13,
  },
  content: {
    paddingHorizontal: 12,
    paddingVertical: 16,
    flexGrow: 1,
    alignItems: 'stretch',
  },
  separator: {
    height: 16,
  },
  cta: {
    alignSelf: 'center',
    marginBottom: 40,
    backgroundColor: colors.grass,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 12,
  },
  ctaText: {
    color: colors.textOnGreen,
    fontWeight: '800',
  },
})
