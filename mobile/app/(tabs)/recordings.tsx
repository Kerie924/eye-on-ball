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
import { useAuth } from '@/src/auth/AuthContext'
import { EmptyState } from '@/src/components/EmptyState'
import { LoadingState } from '@/src/components/LoadingState'
import { RecordingCard } from '@/src/components/RecordingCard'
import { colors } from '@/src/theme/colors'
import type { Recording } from '@/src/types'

type TabKey = 'all' | 'available' | 'expired'

export default function RecordingsScreen() {
  const { user } = useAuth()
  const params = useLocalSearchParams<{ courtId?: string; courtName?: string }>()
  const courtId = useMemo(() => {
    const raw = Array.isArray(params.courtId) ? params.courtId[0] : params.courtId
    const parsed = raw ? Number(raw) : NaN
    return Number.isFinite(parsed) && parsed > 0 ? parsed : null
  }, [params.courtId])
  const courtNameParam = useMemo(() => {
    const raw = Array.isArray(params.courtName) ? params.courtName[0] : params.courtName
    return raw?.trim() || null
  }, [params.courtName])

  const [recordings, setRecordings] = useState<Recording[]>([])
  const [tab, setTab] = useState<TabKey>('all')
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const load = useCallback(
    async (isRefresh = false) => {
      if (isRefresh) setRefreshing(true)
      else setLoading(true)
      try {
        const data = await api.recordings(courtId ?? undefined)
        setRecordings(data)
      } finally {
        setLoading(false)
        setRefreshing(false)
      }
    },
    [courtId],
  )

  useFocusEffect(
    useCallback(() => {
      load()
    }, [load]),
  )

  const courtName = useMemo(() => {
    if (!courtId) return null
    return (
      courtNameParam ??
      recordings.find((item) => item.court_id === courtId)?.court_name ??
      null
    )
  }, [courtId, courtNameParam, recordings])

  const filtered = useMemo(() => {
    const now = Date.now()
    if (tab === 'available') {
      return recordings.filter((r) => new Date(r.expires_at).getTime() > now)
    }
    if (tab === 'expired') {
      return []
    }
    return recordings
  }, [recordings, tab])

  function clearCourtFilter() {
    router.replace('/(tabs)/recordings')
  }

  if (loading) {
    return <LoadingState message="Carregando gravacoes..." />
  }

  const emptyMessage =
    user?.role === 'athlete'
      ? 'Solicite acesso a uma quadra para ver os lances.'
      : user?.role === 'scout' && !user.is_approved
        ? 'Sua conta de olheiro aguarda aprovacao.'
        : courtId
          ? 'Nenhum lance desta quadra nas ultimas 48h.'
          : 'Quando um botao for pressionado, o lance aparece aqui por 48h.'

  return (
    <View style={styles.root}>
      {courtId ? (
        <View style={styles.filterBar}>
          <Text style={styles.filterText} numberOfLines={1}>
            Quadra: {courtName ?? `#${courtId}`}
          </Text>
          <Pressable onPress={clearCourtFilter} hitSlop={8}>
            <Text style={styles.filterClear}>Ver todas</Text>
          </Pressable>
        </View>
      ) : null}

      <View style={styles.tabs}>
        {(
          [
            ['all', 'Todas'],
            ['available', 'Disponiveis'],
            ['expired', 'Expiradas'],
          ] as const
        ).map(([key, label]) => (
          <Pressable
            key={key}
            style={[styles.tab, tab === key && styles.tabActive]}
            onPress={() => setTab(key)}
          >
            <Text style={[styles.tabText, tab === key && styles.tabTextActive]}>
              {label}
            </Text>
          </Pressable>
        ))}
      </View>

      <FlatList
        contentContainerStyle={styles.content}
        data={filtered}
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
            title={tab === 'expired' ? 'Nenhuma expirada' : 'Nenhuma gravacao'}
            description={
              tab === 'expired'
                ? 'Gravacoes expiradas sao removidas automaticamente apos 48h.'
                : emptyMessage
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
  filterText: {
    flex: 1,
    color: colors.white,
    fontWeight: '700',
    fontSize: 14,
  },
  filterClear: {
    color: colors.grassBright,
    fontWeight: '700',
    fontSize: 13,
  },
  tabs: {
    flexDirection: 'row',
    gap: 8,
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 4,
  },
  tab: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 999,
    backgroundColor: colors.blackMuted,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.cardBorder,
  },
  tabActive: {
    backgroundColor: colors.grass,
    borderColor: colors.grass,
  },
  tabText: {
    color: colors.textSecondary,
    fontWeight: '700',
    fontSize: 13,
  },
  tabTextActive: {
    color: colors.textOnGreen,
  },
  content: {
    padding: 16,
    flexGrow: 1,
    gap: 12,
  },
  separator: {
    height: 12,
  },
})
