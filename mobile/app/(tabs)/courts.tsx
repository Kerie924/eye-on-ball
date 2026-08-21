import { Ionicons } from '@expo/vector-icons'
import { router, useFocusEffect } from 'expo-router'
import { useCallback, useMemo, useState } from 'react'
import {
  FlatList,
  Platform,
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
import { AppBrandHeader } from '@/src/components/AppBrandHeader'
import { EmptyState } from '@/src/components/EmptyState'
import { LoadingState } from '@/src/components/LoadingState'
import { MonthCalendar } from '@/src/components/MonthCalendar'
import { colors } from '@/src/theme/colors'
import type { City, Court } from '@/src/types'
import { showMessage } from '@/src/utils/dialogs'
import {
  formatLongDate,
  hourSlots,
  todayLocalDate,
} from '@/src/utils/timeSlots'

type Step = 'city' | 'court' | 'date' | 'time'

const webNoOutline = { outlineStyle: 'none' } as object

export default function CourtsScreen() {
  const [step, setStep] = useState<Step>('city')
  const [cities, setCities] = useState<City[]>([])
  const [courts, setCourts] = useState<Court[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [searchFocused, setSearchFocused] = useState(false)

  const [selectedCity, setSelectedCity] = useState<City | null>(null)
  const [selectedCourt, setSelectedCourt] = useState<Court | null>(null)
  const [playDate, setPlayDate] = useState(todayLocalDate())

  const loadCities = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true)
    else setLoading(true)
    setError('')
    try {
      setCities(await api.cities())
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : 'Nao foi possivel carregar as cidades'
      setError(message)
      showMessage('Erro', message)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useFocusEffect(
    useCallback(() => {
      if (step === 'city') {
        loadCities()
      }
    }, [loadCities, step]),
  )

  const filteredCities = useMemo(() => {
    const term = search.trim().toLowerCase()
    if (!term) return cities
    return cities.filter((city) => city.name.toLowerCase().includes(term))
  }, [cities, search])

  const filteredCourts = useMemo(() => {
    const term = search.trim().toLowerCase()
    if (!term) return courts
    return courts.filter(
      (court) =>
        court.name.toLowerCase().includes(term) ||
        (court.address ?? '').toLowerCase().includes(term),
    )
  }, [courts, search])

  async function openCity(city: City) {
    setSelectedCity(city)
    setSelectedCourt(null)
    setSearch('')
    setLoading(true)
    try {
      setCourts(await api.courts(city.id))
      setStep('court')
    } catch (err) {
      showMessage(
        'Erro',
        err instanceof ApiError ? err.message : 'Nao foi possivel carregar as quadras',
      )
    } finally {
      setLoading(false)
    }
  }

  function openCourt(court: Court) {
    setSelectedCourt(court)
    setPlayDate(todayLocalDate())
    setStep('date')
  }

  function goBack() {
    setSearch('')
    if (step === 'time') setStep('date')
    else if (step === 'date') setStep('court')
    else if (step === 'court') {
      setSelectedCity(null)
      setCourts([])
      setStep('city')
    }
  }

  function openVideos(start: string, end: string) {
    if (!selectedCity || !selectedCourt) return
    router.push({
      pathname: '/(tabs)/recordings',
      params: {
        cityId: String(selectedCity.id),
        cityName: selectedCity.name,
        courtId: String(selectedCourt.id),
        courtName: selectedCourt.name,
        date: playDate,
        startTime: start,
        endTime: end,
      },
    })
  }

  if (loading) {
    return <LoadingState message="Carregando..." />
  }

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <AppBrandHeader />
      {step === 'city' ? (
        <FlatList
          style={styles.root}
          contentContainerStyle={styles.content}
          data={filteredCities}
          keyExtractor={(item) => String(item.id)}
          keyboardShouldPersistTaps="handled"
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={() => loadCities(true)}
              tintColor={colors.grass}
            />
          }
          ListHeaderComponent={
            <View style={styles.header}>
              <Text style={styles.headerTitle}>Cidades</Text>
              <Text style={styles.headerSub}>
                Escolha a cidade, a quadra, a data e o horario para ver os videos.
              </Text>
              <SearchBox
                value={search}
                focused={searchFocused}
                placeholder="Buscar cidade"
                onChange={setSearch}
                onFocus={() => setSearchFocused(true)}
                onBlur={() => setSearchFocused(false)}
              />
              {error ? <Text style={styles.error}>{error}</Text> : null}
            </View>
          }
          ListEmptyComponent={
            <EmptyState
              title={search ? 'Nenhuma cidade encontrada' : 'Nenhuma cidade cadastrada'}
              description="O administrador pode criar cidades no painel web."
            />
          }
          renderItem={({ item }) => (
            <Pressable
              style={({ pressed }) => [styles.card, pressed && styles.cardPressed]}
              onPress={() => openCity(item)}
            >
              <View style={styles.cardBody}>
                <Text style={styles.cardTitle}>{item.name}</Text>
                <Text style={styles.cardMeta}>
                  {item.court_count} {item.court_count === 1 ? 'quadra' : 'quadras'}
                </Text>
              </View>
              <Ionicons name="chevron-forward" size={18} color={colors.textMuted} />
            </Pressable>
          )}
          ItemSeparatorComponent={() => <View style={styles.separator} />}
        />
      ) : null}

      {step === 'court' && selectedCity ? (
        <FlatList
          style={styles.root}
          contentContainerStyle={styles.content}
          data={filteredCourts}
          keyExtractor={(item) => String(item.id)}
          keyboardShouldPersistTaps="handled"
          ListHeaderComponent={
            <View style={styles.header}>
              <BackRow label="Voltar as cidades" onPress={goBack} />
              <Text style={styles.headerTitle}>{selectedCity.name}</Text>
              <Text style={styles.headerSub}>Escolha a quadra (bloco) desta cidade.</Text>
              <SearchBox
                value={search}
                focused={searchFocused}
                placeholder="Buscar quadra"
                onChange={setSearch}
                onFocus={() => setSearchFocused(true)}
                onBlur={() => setSearchFocused(false)}
              />
            </View>
          }
          ListEmptyComponent={
            <EmptyState
              title={search ? 'Nenhuma quadra encontrada' : 'Nenhuma quadra nesta cidade'}
              description="Cadastre a quadra no painel admin, na cidade correta."
            />
          }
          renderItem={({ item }) => (
            <Pressable
              style={({ pressed }) => [styles.card, pressed && styles.cardPressed]}
              onPress={() => openCourt(item)}
            >
              <View style={styles.cardBody}>
                <Text style={styles.cardTitle}>{item.name}</Text>
                {item.address ? <Text style={styles.cardMeta}>{item.address}</Text> : null}
              </View>
              <Ionicons name="chevron-forward" size={18} color={colors.textMuted} />
            </Pressable>
          )}
          ItemSeparatorComponent={() => <View style={styles.separator} />}
        />
      ) : null}

      {step === 'date' && selectedCourt ? (
        <ScrollView contentContainerStyle={styles.content} style={styles.root}>
          <BackRow label="Voltar as quadras" onPress={goBack} />
          <Text style={styles.headerTitle}>Data do jogo</Text>
          <Text style={styles.headerSub}>
            {selectedCity?.name} · {selectedCourt.name}
          </Text>
          <MonthCalendar value={playDate} onChange={setPlayDate} />
          <Pressable
            style={({ pressed }) => [styles.primaryBtn, pressed && styles.cardPressed]}
            onPress={() => setStep('time')}
          >
            <Text style={styles.primaryBtnText}>Continuar</Text>
          </Pressable>
        </ScrollView>
      ) : null}

      {step === 'time' && selectedCourt ? (
        <ScrollView contentContainerStyle={styles.content} style={styles.root}>
          <BackRow label="Voltar ao calendario" onPress={goBack} />
          <Text style={styles.headerTitle}>Horario</Text>
          <Text style={styles.headerSub}>{formatLongDate(playDate)}</Text>
          <View style={styles.slotList}>
            {hourSlots().map((slot) => (
              <Pressable
                key={slot.start}
                style={({ pressed }) => [styles.slot, pressed && styles.cardPressed]}
                onPress={() => openVideos(slot.start, slot.end)}
              >
                <Text style={styles.slotText}>{slot.label}</Text>
                <Ionicons name="chevron-forward" size={16} color={colors.textMuted} />
              </Pressable>
            ))}
          </View>
        </ScrollView>
      ) : null}
    </SafeAreaView>
  )
}

function BackRow({ label, onPress }: { label: string; onPress: () => void }) {
  return (
    <Pressable style={styles.backRow} onPress={onPress}>
      <Ionicons name="arrow-back" size={20} color={colors.grassBright} />
      <Text style={styles.backText}>{label}</Text>
    </Pressable>
  )
}

function SearchBox({
  value,
  focused,
  placeholder,
  onChange,
  onFocus,
  onBlur,
}: {
  value: string
  focused: boolean
  placeholder: string
  onChange: (value: string) => void
  onFocus: () => void
  onBlur: () => void
}) {
  return (
    <View style={[styles.searchBox, focused && styles.searchBoxFocused]}>
      <Ionicons name="search" size={18} color={focused ? colors.grass : colors.textMuted} />
      <TextInput
        style={[styles.searchInput, Platform.OS === 'web' ? webNoOutline : null]}
        value={value}
        onChangeText={onChange}
        onFocus={onFocus}
        onBlur={onBlur}
        placeholder={placeholder}
        placeholderTextColor={colors.textMuted}
        autoCapitalize="none"
        autoCorrect={false}
        underlineColorAndroid="transparent"
        selectionColor={colors.grass}
        cursorColor={colors.grass}
      />
      {value ? (
        <Pressable onPress={() => onChange('')}>
          <Ionicons name="close-circle" size={18} color={colors.textMuted} />
        </Pressable>
      ) : null}
    </View>
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
  },
  error: {
    color: '#fca5a5',
    fontSize: 13,
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
  card: {
    backgroundColor: colors.card,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  cardPressed: {
    opacity: 0.92,
    borderColor: colors.grass,
  },
  cardBody: {
    flex: 1,
    gap: 4,
  },
  cardTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: colors.white,
  },
  cardMeta: {
    fontSize: 14,
    color: colors.textSecondary,
  },
  separator: {
    height: 12,
  },
  primaryBtn: {
    marginTop: 8,
    backgroundColor: colors.grass,
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
  },
  primaryBtnText: {
    color: colors.textOnGreen,
    fontWeight: '800',
    fontSize: 16,
  },
  slotList: {
    gap: 8,
  },
  slot: {
    backgroundColor: colors.card,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    paddingHorizontal: 16,
    paddingVertical: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  slotText: {
    color: colors.white,
    fontWeight: '700',
    fontSize: 16,
  },
})
