import { Ionicons } from '@expo/vector-icons'
import { router, useFocusEffect } from 'expo-router'
import { useCallback, useMemo, useState } from 'react'
import {
  FlatList,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
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

function todayLocalDate(): string {
  const now = new Date()
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function toIsoLocal(date: string, time: string): string {
  const parsed = new Date(`${date}T${time}:00`)
  if (Number.isNaN(parsed.getTime())) {
    throw new Error('Horario invalido')
  }
  return parsed.toISOString()
}

function formatPlayWindow(start?: string | null, end?: string | null): string {
  if (!start || !end) return ''
  const a = new Date(start)
  const b = new Date(end)
  const date = a.toLocaleDateString('pt-BR')
  const t1 = a.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
  const t2 = b.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
  return `${date} · ${t1} – ${t2}`
}

export default function CourtsScreen() {
  const { user } = useAuth()
  const [courts, setCourts] = useState<Court[]>([])
  const [accesses, setAccesses] = useState<CourtAccess[]>([])
  const [requests, setRequests] = useState<CourtAccessRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [requesting, setRequesting] = useState(false)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [searchFocused, setSearchFocused] = useState(false)

  const [selectedCourt, setSelectedCourt] = useState<Court | null>(null)
  const [playDate, setPlayDate] = useState(todayLocalDate())
  const [startTime, setStartTime] = useState('19:00')
  const [endTime, setEndTime] = useState('20:00')

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
            setAccesses(await api.myCourtAccess())
          } else {
            setAccesses([])
          }
          setRequests([])
        } else if (user?.role === 'admin') {
          setAccesses(await api.myCourtAccess())
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

  const pendingByCourt = useMemo(() => {
    const map = new Map<number, CourtAccessRequest>()
    for (const item of requests) {
      if (item.status === 'pending') map.set(item.court_id, item)
    }
    return map
  }, [requests])

  const approvedWindows = useMemo(() => {
    return requests.filter((item) => item.status === 'approved')
  }, [requests])

  const filteredCourts = useMemo(() => {
    const term = search.trim().toLowerCase()
    if (!term) return courts
    return courts.filter(
      (court) =>
        court.name.toLowerCase().includes(term) ||
        (court.address ?? '').toLowerCase().includes(term),
    )
  }, [courts, search])

  function openCourtVideos(courtId: number, courtName?: string | null) {
    router.push({
      pathname: '/(tabs)/recordings',
      params: {
        courtId: String(courtId),
        ...(courtName ? { courtName } : {}),
      },
    })
  }

  function openRequestForm(court: Court) {
    setSelectedCourt(court)
    setPlayDate(todayLocalDate())
    setStartTime('19:00')
    setEndTime('20:00')
  }

  async function handleSubmitRequest() {
    if (!selectedCourt) return
    setRequesting(true)
    try {
      const started = toIsoLocal(playDate, startTime)
      const ended = toIsoLocal(playDate, endTime)
      await api.requestCourtAccess(selectedCourt.id, started, ended)
      showMessage(
        'Solicitacao enviada',
        'O administrador revisara seu pedido. Depois da aprovacao, voce vera so os videos do horario informado.',
      )
      setSelectedCourt(null)
      await loadData(true)
    } catch (err) {
      showMessage(
        'Erro',
        err instanceof ApiError ? err.message : 'Nao foi possivel solicitar acesso',
      )
    } finally {
      setRequesting(false)
    }
  }

  if (loading) {
    return <LoadingState message="Carregando quadras..." />
  }

  if (selectedCourt && user?.role === 'athlete') {
    return (
      <SafeAreaView style={styles.safe} edges={['top']}>
        <AppBrandHeader />
        <ScrollView contentContainerStyle={styles.formContent} keyboardShouldPersistTaps="handled">
          <Pressable style={styles.backRow} onPress={() => setSelectedCourt(null)}>
            <Ionicons name="arrow-back" size={20} color={colors.grassBright} />
            <Text style={styles.backText}>Voltar a busca</Text>
          </Pressable>

          <Text style={styles.headerTitle}>Solicitar acesso</Text>
          <Text style={styles.headerSub}>
            Informe quando voce jogou nesta quadra. Apos a aprovacao, voce vera apenas os videos
            desse horario.
          </Text>

          <View style={styles.card}>
            <Text style={styles.cardTitle}>{selectedCourt.name}</Text>
            {selectedCourt.address ? (
              <Text style={styles.cardMeta}>{selectedCourt.address}</Text>
            ) : null}
          </View>

          <View style={styles.field}>
            <Text style={styles.label}>Data do jogo</Text>
            <TextInput
              style={styles.input}
              value={playDate}
              onChangeText={setPlayDate}
              placeholder="AAAA-MM-DD"
              placeholderTextColor={colors.textMuted}
              autoCapitalize="none"
            />
          </View>
          <View style={styles.timeRow}>
            <View style={[styles.field, styles.timeField]}>
              <Text style={styles.label}>Inicio</Text>
              <TextInput
                style={styles.input}
                value={startTime}
                onChangeText={setStartTime}
                placeholder="19:00"
                placeholderTextColor={colors.textMuted}
                autoCapitalize="none"
              />
            </View>
            <View style={[styles.field, styles.timeField]}>
              <Text style={styles.label}>Fim</Text>
              <TextInput
                style={styles.input}
                value={endTime}
                onChangeText={setEndTime}
                placeholder="20:00"
                placeholderTextColor={colors.textMuted}
                autoCapitalize="none"
              />
            </View>
          </View>

          <Button
            label="Enviar solicitacao"
            loading={requesting}
            onPress={handleSubmitRequest}
          />
        </ScrollView>
      </SafeAreaView>
    )
  }

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <AppBrandHeader />
      <FlatList
        style={styles.root}
        contentContainerStyle={styles.content}
        data={filteredCourts}
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
                ? 'Busque a quadra pelo nome, informe o horario do jogo e solicite acesso.'
                : user?.role === 'admin' || user?.is_approved
                  ? 'Toque em uma quadra para ver os videos.'
                  : 'Sua conta de olheiro aguarda aprovacao do administrador.'}
            </Text>
            <View style={[styles.searchBox, searchFocused && styles.searchBoxFocused]}>
              <Ionicons
                name="search"
                size={18}
                color={searchFocused ? colors.grass : colors.textMuted}
              />
              <TextInput
                style={styles.searchInput}
                value={search}
                onChangeText={setSearch}
                onFocus={() => setSearchFocused(true)}
                onBlur={() => setSearchFocused(false)}
                placeholder="Buscar quadra por nome ou endereco"
                placeholderTextColor={colors.textMuted}
                autoCapitalize="none"
                autoCorrect={false}
                underlineColorAndroid="transparent"
                selectionColor={colors.grass}
                cursorColor={colors.grass}
              />
              {search ? (
                <Pressable onPress={() => setSearch('')}>
                  <Ionicons name="close-circle" size={18} color={colors.textMuted} />
                </Pressable>
              ) : null}
            </View>
            {error ? <Text style={styles.error}>{error}</Text> : null}
          </View>
        }
        ListEmptyComponent={
          <EmptyState
            title={search ? 'Nenhuma quadra encontrada' : 'Nenhuma quadra cadastrada'}
            description={
              search
                ? 'Tente outro nome ou parte do endereco.'
                : 'Quando o administrador cadastrar uma quadra, ela aparecera aqui.'
            }
          />
        }
        renderItem={({ item }) => {
          const hasAccess = accessCourtIds.has(item.id)
          const pending = pendingByCourt.get(item.id)
          const scoutCanView = user?.role === 'scout' && user.is_approved
          const adminCanView = user?.role === 'admin'
          const canOpenVideos = hasAccess || scoutCanView || adminCanView
          const showRequest = user?.role === 'athlete' && !pending
          const windows = approvedWindows.filter((req) => req.court_id === item.id)

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
                ) : pending ? (
                  <Text style={styles.badgePending}>
                    Solicitacao pendente
                    {formatPlayWindow(pending.play_started_at, pending.play_ended_at)
                      ? `\n${formatPlayWindow(pending.play_started_at, pending.play_ended_at)}`
                      : ''}
                  </Text>
                ) : user?.role === 'scout' ? (
                  <Text style={styles.badgePending}>Conta aguardando aprovacao</Text>
                ) : user?.role === 'athlete' ? (
                  <Text style={styles.badgeMuted}>Sem acesso — busque e solicite abaixo</Text>
                ) : null}
                {user?.role === 'athlete' && windows.length > 0 ? (
                  <Text style={styles.windowHint}>
                    Horarios aprovados:{' '}
                    {windows
                      .slice(0, 2)
                      .map((w) => formatPlayWindow(w.play_started_at, w.play_ended_at))
                      .join(' · ')}
                    {windows.length > 2 ? '…' : ''}
                  </Text>
                ) : null}
              </View>
              {showRequest ? (
                <Button
                  label={hasAccess ? 'Solicitar outro horario' : 'Solicitar acesso'}
                  variant="outline"
                  onPress={() => openRequestForm(item)}
                />
              ) : null}
            </>
          )

          if (canOpenVideos) {
            return (
              <View style={styles.card}>
                <Pressable
                  style={({ pressed }) => [pressed && styles.cardPressed]}
                  onPress={() => openCourtVideos(item.id, item.name)}
                >
                  <View style={styles.cardBody}>
                    <View style={styles.titleRow}>
                      <Text style={styles.cardTitle}>{item.name}</Text>
                      <Ionicons name="chevron-forward" size={18} color={colors.textMuted} />
                    </View>
                    {item.address ? <Text style={styles.cardMeta}>{item.address}</Text> : null}
                    <Text style={styles.badgeSuccess}>
                      {adminCanView
                        ? 'Acesso de administrador — toque para ver videos'
                        : scoutCanView && !hasAccess
                          ? 'Acesso de olheiro — toque para ver videos'
                          : 'Acesso liberado — toque para ver videos'}
                    </Text>
                    {user?.role === 'athlete' && windows.length > 0 ? (
                      <Text style={styles.windowHint}>
                        Horarios aprovados:{' '}
                        {windows
                          .slice(0, 2)
                          .map((w) => formatPlayWindow(w.play_started_at, w.play_ended_at))
                          .join(' · ')}
                        {windows.length > 2 ? '…' : ''}
                      </Text>
                    ) : null}
                  </View>
                </Pressable>
                {showRequest ? (
                  <Button
                    label="Solicitar outro horario"
                    variant="outline"
                    onPress={() => openRequestForm(item)}
                  />
                ) : null}
              </View>
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
  formContent: {
    padding: 16,
    gap: 14,
    paddingBottom: 40,
  },
  header: {
    gap: 8,
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
  searchBox: {
    marginTop: 4,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  searchBoxFocused: {
    borderColor: colors.grass,
  },
  searchInput: {
    flex: 1,
    color: colors.white,
    fontSize: 15,
    padding: 0,
    // Kill default browser/Android focus outline; green border is on the container.
    outlineStyle: 'none' as const,
  },
  backRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 4,
  },
  backText: {
    color: colors.grassBright,
    fontWeight: '700',
    fontSize: 14,
  },
  field: {
    gap: 6,
  },
  timeRow: {
    flexDirection: 'row',
    gap: 12,
  },
  timeField: {
    flex: 1,
  },
  label: {
    color: colors.textSecondary,
    fontSize: 13,
    fontWeight: '600',
  },
  input: {
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    borderRadius: 12,
    color: colors.white,
    fontSize: 16,
    paddingHorizontal: 14,
    paddingVertical: 12,
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
  windowHint: {
    marginTop: 4,
    color: colors.textSecondary,
    fontSize: 12,
    lineHeight: 17,
  },
  separator: {
    height: 12,
  },
})
