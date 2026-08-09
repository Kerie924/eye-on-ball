import { Ionicons } from '@expo/vector-icons'
import { router, useFocusEffect } from 'expo-router'
import { useCallback, useState } from 'react'
import {
  FlatList,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'

import { api } from '@/src/api/client'
import { useAuth } from '@/src/auth/AuthContext'
import { EmptyState } from '@/src/components/EmptyState'
import { LoadingState } from '@/src/components/LoadingState'
import { RecordingCard } from '@/src/components/RecordingCard'
import { colors } from '@/src/theme/colors'
import type { CourtAccess, Recording } from '@/src/types'

export default function HomeScreen() {
  const { user } = useAuth()
  const [recordings, setRecordings] = useState<Recording[]>([])
  const [accesses, setAccesses] = useState<CourtAccess[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true)
    else setLoading(true)

    try {
      const [recs, accessList] = await Promise.all([
        api.recordings(),
        api.myCourtAccess().catch(() => [] as CourtAccess[]),
      ])
      setRecordings(recs.slice(0, 8))
      setAccesses(accessList)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useFocusEffect(
    useCallback(() => {
      load()
    }, [load]),
  )

  function openCourtVideos(courtId: number, courtName?: string | null) {
    router.push({
      pathname: '/(tabs)/recordings',
      params: {
        courtId: String(courtId),
        ...(courtName ? { courtName } : {}),
      },
    })
  }

  if (loading) {
    return <LoadingState message="Carregando inicio..." />
  }

  const firstName = user?.full_name?.split(' ')[0] ?? 'Atleta'
  const primaryAccess = accesses[0]
  const primaryCourt = primaryAccess?.court

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
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
        ListHeaderComponent={
          <View style={styles.headerBlock}>
            <View style={styles.greetingRow}>
              <View>
                <Text style={styles.greeting}>Ola, {firstName}!</Text>
                <Text style={styles.greetingSub}>Seus lances estao aqui</Text>
              </View>
              <Pressable
                style={styles.avatar}
                onPress={() => router.push('/(tabs)/profile')}
              >
                <Text style={styles.avatarText}>
                  {user?.full_name?.slice(0, 1).toUpperCase() ?? '?'}
                </Text>
              </Pressable>
            </View>

            {primaryCourt && primaryAccess ? (
              <Pressable
                style={({ pressed }) => [styles.courtCard, pressed && styles.pressed]}
                onPress={() => openCourtVideos(primaryAccess.court_id, primaryCourt.name)}
              >
                <View style={styles.courtIcon}>
                  <Ionicons name="football" size={22} color={colors.grass} />
                </View>
                <View style={styles.courtBody}>
                  <Text style={styles.courtLabel}>Quadra atual</Text>
                  <Text style={styles.courtName}>{primaryCourt.name}</Text>
                  {primaryCourt.address ? (
                    <Text style={styles.courtMeta}>{primaryCourt.address}</Text>
                  ) : null}
                  <Text style={styles.courtAction}>Toque para ver os videos</Text>
                </View>
                <Ionicons name="chevron-forward" size={18} color={colors.textMuted} />
              </Pressable>
            ) : (
              <Pressable
                style={styles.courtCard}
                onPress={() => router.push('/(tabs)/courts')}
              >
                <View style={styles.courtIcon}>
                  <Ionicons name="add-circle" size={22} color={colors.grass} />
                </View>
                <View style={styles.courtBody}>
                  <Text style={styles.courtName}>Solicitar acesso</Text>
                  <Text style={styles.courtMeta}>
                    Escolha uma quadra para ver os lances
                  </Text>
                </View>
                <Ionicons name="chevron-forward" size={18} color={colors.textMuted} />
              </Pressable>
            )}

            <View style={styles.sectionRow}>
              <Text style={styles.sectionTitle}>Ultimas gravacoes</Text>
              <Pressable onPress={() => router.push('/(tabs)/recordings')}>
                <Text style={styles.sectionLink}>Ver todas</Text>
              </Pressable>
            </View>
          </View>
        }
        ListEmptyComponent={
          <EmptyState
            title="Nenhuma gravacao ainda"
            description="Quando o botao fisico for pressionado, o lance aparece aqui."
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
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.black,
  },
  content: {
    padding: 20,
    flexGrow: 1,
    gap: 12,
    paddingBottom: 32,
  },
  headerBlock: {
    gap: 16,
    marginBottom: 4,
  },
  greetingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  greeting: {
    color: colors.white,
    fontSize: 28,
    fontWeight: '800',
  },
  greetingSub: {
    color: colors.textSecondary,
    marginTop: 2,
  },
  avatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: colors.grassDeep,
    borderWidth: 2,
    borderColor: colors.grass,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    color: colors.grassLight,
    fontWeight: '800',
    fontSize: 18,
  },
  courtCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: colors.card,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    padding: 16,
  },
  pressed: {
    opacity: 0.92,
    borderColor: colors.grass,
  },
  courtIcon: {
    width: 44,
    height: 44,
    borderRadius: 12,
    backgroundColor: 'rgba(34,197,94,0.15)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  courtBody: {
    flex: 1,
    gap: 2,
  },
  courtLabel: {
    color: colors.textMuted,
    fontSize: 12,
    fontWeight: '600',
  },
  courtName: {
    color: colors.white,
    fontSize: 16,
    fontWeight: '700',
  },
  courtMeta: {
    color: colors.textSecondary,
    fontSize: 13,
  },
  courtAction: {
    marginTop: 4,
    color: colors.grassBright,
    fontSize: 12,
    fontWeight: '700',
  },
  sectionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 4,
  },
  sectionTitle: {
    color: colors.white,
    fontSize: 18,
    fontWeight: '700',
  },
  sectionLink: {
    color: colors.grass,
    fontWeight: '700',
    fontSize: 14,
  },
  separator: {
    height: 12,
  },
})
