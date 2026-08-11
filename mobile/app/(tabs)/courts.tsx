import { Ionicons } from '@expo/vector-icons'
import { router, useFocusEffect } from 'expo-router'
import { useCallback, useMemo, useState } from 'react'
import {
  FlatList,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'

import { ApiError, api } from '@/src/api/client'
import { useAuth } from '@/src/auth/AuthContext'
import { AppBrandHeader } from '@/src/components/AppBrandHeader'
import { Button } from '@/src/components/Button'
import { EmptyState } from '@/src/components/EmptyState'
import { LoadingState } from '@/src/components/LoadingState'
import { colors } from '@/src/theme/colors'
import type { Court, CourtAccess, CourtAccessRequest } from '@/src/types'
import { showMessage } from '@/src/utils/dialogs'

export default function CourtsScreen() {
  const { user } = useAuth()
  const [courts, setCourts] = useState<Court[]>([])
  const [accesses, setAccesses] = useState<CourtAccess[]>([])
  const [requests, setRequests] = useState<CourtAccessRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [requestingId, setRequestingId] = useState<number | null>(null)
  const [error, setError] = useState('')

  const loadData = useCallback(
    async (isRefresh = false) => {
      if (isRefresh) setRefreshing(true)
      else setLoading(true)
      setError('')

      try {
        const courtList = await api.courts()
        setCourts(courtList)

        if (user?.role === 'athlete') {
          const [accessList, requestList] = await Promise.all([
            api.myCourtAccess(),
            api.myAccessRequests(),
          ])
          setAccesses(accessList)
          setRequests(requestList)
        } else if (user?.role === 'scout') {
          if (user.is_approved) {
            const accessList = await api.myCourtAccess()
            setAccesses(accessList)
          } else {
            setAccesses([])
          }
          setRequests([])
        } else if (user?.role === 'admin') {
          const accessList = await api.myCourtAccess()
          setAccesses(accessList)
          setRequests([])
        }
      } catch (err) {
        const message =
          err instanceof ApiError ? err.message : 'Nao foi possivel carregar as quadras'
        setError(message)
        showMessage('Erro', message)
      } finally {
        setLoading(false)
        setRefreshing(false)
      }
    },
    [user?.role, user?.is_approved],
  )

  useFocusEffect(
    useCallback(() => {
      loadData()
    }, [loadData]),
  )

  const accessCourtIds = useMemo(
    () => new Set(accesses.map((item) => item.court_id)),
    [accesses],
  )

  const pendingCourtIds = useMemo(
    () =>
      new Set(
        requests.filter((item) => item.status === 'pending').map((item) => item.court_id),
      ),
    [requests],
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

  async function handleRequestAccess(courtId: number) {
    setRequestingId(courtId)
    try {
      await api.requestCourtAccess(courtId)
      showMessage('Solicitacao enviada', 'O administrador revisara seu pedido em breve.')
      await loadData(true)
    } catch (err) {
      showMessage(
        'Erro',
        err instanceof ApiError ? err.message : 'Nao foi possivel solicitar acesso',
      )
    } finally {
      setRequestingId(null)
    }
  }

  if (loading) {
    return <LoadingState message="Carregando quadras..." />
  }

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <AppBrandHeader />
      <FlatList
        style={styles.root}
        contentContainerStyle={styles.content}
        data={courts}
        keyExtractor={(item) => String(item.id)}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => loadData(true)}
            tintColor={colors.grass}
          />
        }
        ListHeaderComponent={
          <View style={styles.header}>
            <Text style={styles.headerTitle}>Quadras</Text>
            <Text style={styles.headerSub}>
              {user?.role === 'athlete'
                ? 'Toque em uma quadra liberada para ver os videos.'
                : user?.role === 'admin' || user?.is_approved
                  ? 'Toque em uma quadra para ver os videos.'
                  : 'Sua conta de olheiro aguarda aprovacao do administrador.'}
            </Text>
            {error ? <Text style={styles.error}>{error}</Text> : null}
          </View>
        }
        ListEmptyComponent={
          <EmptyState
            title="Nenhuma quadra cadastrada"
            description="Quando o administrador cadastrar uma quadra, ela aparecera aqui."
          />
        }
        renderItem={({ item }) => {
          const hasAccess = accessCourtIds.has(item.id)
          const isPending = pendingCourtIds.has(item.id)
          const scoutCanView = user?.role === 'scout' && user.is_approved
          const adminCanView = user?.role === 'admin'
          const canOpenVideos = hasAccess || scoutCanView || adminCanView
          const showRequest = user?.role === 'athlete' && !hasAccess && !isPending

          const cardBody = (
            <>
              <View style={styles.cardBody}>
                <View style={styles.titleRow}>
                  <Text style={styles.cardTitle}>{item.name}</Text>
                  {canOpenVideos ? (
                    <Ionicons name="chevron-forward" size={18} color={colors.textMuted} />
                  ) : null}
                </View>
                {item.address ? <Text style={styles.cardMeta}>{item.address}</Text> : null}
                {canOpenVideos ? (
                  <Text style={styles.badgeSuccess}>
                    {adminCanView
                      ? 'Acesso de administrador — toque para ver videos'
                      : scoutCanView && !hasAccess
                        ? 'Acesso de olheiro — toque para ver videos'
                        : 'Acesso liberado — toque para ver videos'}
                  </Text>
                ) : isPending ? (
                  <Text style={styles.badgePending}>Solicitacao pendente</Text>
                ) : user?.role === 'scout' ? (
                  <Text style={styles.badgePending}>Conta aguardando aprovacao</Text>
                ) : user?.role === 'athlete' ? (
                  <Text style={styles.badgeMuted}>Sem acesso — solicite abaixo</Text>
                ) : null}
              </View>
              {showRequest ? (
                <Button
                  label="Solicitar acesso"
                  variant="outline"
                  loading={requestingId === item.id}
                  onPress={() => handleRequestAccess(item.id)}
                />
              ) : null}
            </>
          )

          if (canOpenVideos) {
            return (
              <Pressable
                style={({ pressed }) => [styles.card, pressed && styles.cardPressed]}
                onPress={() => openCourtVideos(item.id, item.name)}
              >
                {cardBody}
              </Pressable>
            )
          }

          return <View style={styles.card}>{cardBody}</View>
        }}
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
  root: {
    flex: 1,
    backgroundColor: colors.black,
  },
  content: {
    padding: 16,
    flexGrow: 1,
    gap: 12,
  },
  header: {
    gap: 6,
    marginBottom: 4,
  },
  headerTitle: {
    color: colors.white,
    fontSize: 22,
    fontWeight: '800',
  },
  headerSub: {
    color: colors.textSecondary,
    fontSize: 14,
    lineHeight: 20,
  },
  error: {
    color: '#fca5a5',
    fontSize: 13,
    marginTop: 4,
  },
  card: {
    backgroundColor: colors.card,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    padding: 16,
    gap: 12,
  },
  cardPressed: {
    opacity: 0.92,
    borderColor: colors.grass,
  },
  cardBody: {
    gap: 4,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 8,
  },
  cardTitle: {
    flex: 1,
    fontSize: 17,
    fontWeight: '700',
    color: colors.white,
  },
  cardMeta: {
    fontSize: 14,
    color: colors.textSecondary,
  },
  badgeSuccess: {
    marginTop: 6,
    color: colors.grassBright,
    fontWeight: '700',
    fontSize: 13,
  },
  badgePending: {
    marginTop: 6,
    color: colors.warning,
    fontWeight: '700',
    fontSize: 13,
  },
  badgeMuted: {
    marginTop: 6,
    color: colors.textMuted,
    fontWeight: '600',
    fontSize: 13,
  },
  separator: {
    height: 12,
  },
})
