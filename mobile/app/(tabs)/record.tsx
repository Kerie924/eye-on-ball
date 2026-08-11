import { Ionicons } from '@expo/vector-icons'
import { router, useFocusEffect } from 'expo-router'
import { useCallback, useMemo, useState } from 'react'
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'

import { ApiError, api } from '@/src/api/client'
import { useAuth } from '@/src/auth/AuthContext'
import { AppBrandHeader } from '@/src/components/AppBrandHeader'
import { colors } from '@/src/theme/colors'
import type { CourtAccess } from '@/src/types'
import { showMessage } from '@/src/utils/dialogs'

export default function RecordScreen() {
  const { user } = useAuth()
  const [accesses, setAccesses] = useState<CourtAccess[]>([])
  const [selectedCourtId, setSelectedCourtId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [capturing, setCapturing] = useState(false)

  const loadAccess = useCallback(async () => {
    setLoading(true)
    try {
      const list = await api.myCourtAccess()
      setAccesses(list)
      setSelectedCourtId((current) => {
        if (current && list.some((item) => item.court_id === current)) {
          return current
        }
        return list[0]?.court_id ?? null
      })
    } catch {
      setAccesses([])
      setSelectedCourtId(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useFocusEffect(
    useCallback(() => {
      loadAccess()
    }, [loadAccess]),
  )

  const selectedAccess = useMemo(
    () => accesses.find((item) => item.court_id === selectedCourtId) ?? null,
    [accesses, selectedCourtId],
  )

  async function handleCapture() {
    if (capturing) return

    if (!selectedCourtId) {
      showMessage(
        'Sem acesso',
        'Solicite acesso a uma quadra antes de gravar.',
        { tone: 'warning' },
      )
      router.push('/(tabs)/courts')
      return
    }

    if (user?.role === 'scout' && !user.is_approved) {
      showMessage(
        'Aguardando aprovacao',
        'Sua conta de olheiro ainda nao foi aprovada pelo administrador.',
        { tone: 'warning' },
      )
      return
    }

    setCapturing(true)
    try {
      const result = await api.triggerCapture(selectedCourtId)
      showMessage(
        result.device_online ? 'Gravando!' : 'Comando enviado',
        result.message,
        { tone: result.device_online ? 'success' : 'warning' },
      )
      if (result.device_online) {
        setTimeout(() => router.push('/(tabs)/recordings'), 1200)
      }
    } catch (err) {
      showMessage(
        'Erro',
        err instanceof ApiError ? err.message : 'Nao foi possivel iniciar a gravacao',
        { tone: 'danger' },
      )
    } finally {
      setCapturing(false)
    }
  }

  const canCapture = Boolean(selectedCourtId) && !capturing && !loading

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <AppBrandHeader />
      <View style={styles.content}>
        <Text style={styles.title}>Gravacao</Text>
        <Text style={styles.subtitle}>
          Toque em PRONTO para capturar os ultimos 30 segundos na quadra
          selecionada. O botao fisico da quadra tambem funciona.
        </Text>

        {accesses.length > 1 ? (
          <View style={styles.courtPicker}>
            {accesses.map((access) => {
              const active = access.court_id === selectedCourtId
              return (
                <Pressable
                  key={access.court_id}
                  style={[styles.courtChip, active && styles.courtChipActive]}
                  onPress={() => setSelectedCourtId(access.court_id)}
                >
                  <Text
                    style={[styles.courtChipText, active && styles.courtChipTextActive]}
                    numberOfLines={1}
                  >
                    {access.court?.name ?? `Quadra #${access.court_id}`}
                  </Text>
                </Pressable>
              )
            })}
          </View>
        ) : selectedAccess?.court ? (
          <Text style={styles.courtLabel}>{selectedAccess.court.name}</Text>
        ) : null}

        <Pressable
          style={({ pressed }) => [
            styles.ringOuter,
            pressed && canCapture && styles.pressed,
            !canCapture && styles.disabled,
          ]}
          onPress={handleCapture}
          disabled={!canCapture && Boolean(selectedCourtId)}
        >
          <View style={styles.ringMid}>
            <View style={[styles.readyBtn, capturing && styles.readyBtnBusy]}>
              {capturing ? (
                <ActivityIndicator color={colors.textOnGreen} size="large" />
              ) : (
                <Text style={styles.readyText}>PRONTO</Text>
              )}
            </View>
          </View>
        </Pressable>

        <View style={styles.hint}>
          <Ionicons
            name={selectedCourtId ? 'radio-button-on' : 'alert-circle-outline'}
            size={22}
            color={colors.grass}
          />
          <Text style={styles.hintText}>
            {loading
              ? 'Carregando suas quadras...'
              : selectedCourtId
                ? 'Toque no botao verde para gravar seu lance agora'
                : 'Voce precisa de acesso a uma quadra para gravar'}
          </Text>
        </View>

        {!selectedCourtId && !loading ? (
          <Pressable style={styles.linkBtn} onPress={() => router.push('/(tabs)/courts')}>
            <Text style={styles.linkText}>Ir para Quadras</Text>
          </Pressable>
        ) : null}
      </View>
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.black,
  },
  content: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 28,
    gap: 16,
  },
  title: {
    color: colors.white,
    fontSize: 28,
    fontWeight: '800',
  },
  subtitle: {
    color: colors.textSecondary,
    textAlign: 'center',
    fontSize: 15,
    lineHeight: 22,
    maxWidth: 320,
  },
  courtLabel: {
    color: colors.grassBright,
    fontWeight: '700',
    fontSize: 14,
  },
  courtPicker: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: 8,
    maxWidth: 340,
  },
  courtChip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    backgroundColor: colors.card,
    maxWidth: 160,
  },
  courtChipActive: {
    backgroundColor: colors.grassDeep,
    borderColor: colors.grass,
  },
  courtChipText: {
    color: colors.textSecondary,
    fontWeight: '600',
    fontSize: 13,
  },
  courtChipTextActive: {
    color: colors.grassLight,
  },
  ringOuter: {
    width: 220,
    height: 220,
    borderRadius: 110,
    borderWidth: 2,
    borderColor: 'rgba(34,197,94,0.25)',
    alignItems: 'center',
    justifyContent: 'center',
    marginVertical: 18,
  },
  ringMid: {
    width: 180,
    height: 180,
    borderRadius: 90,
    borderWidth: 2,
    borderColor: 'rgba(34,197,94,0.45)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  readyBtn: {
    width: 140,
    height: 140,
    borderRadius: 70,
    backgroundColor: colors.grass,
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 10,
  },
  readyBtnBusy: {
    backgroundColor: colors.grassDark,
  },
  readyText: {
    color: colors.textOnGreen,
    fontWeight: '900',
    fontSize: 22,
    letterSpacing: 1,
  },
  pressed: {
    opacity: 0.92,
    transform: [{ scale: 0.98 }],
  },
  disabled: {
    opacity: 0.55,
  },
  hint: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: colors.card,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    paddingHorizontal: 16,
    paddingVertical: 14,
    maxWidth: 320,
  },
  hintText: {
    flex: 1,
    color: colors.textSecondary,
    fontSize: 14,
    lineHeight: 20,
  },
  linkBtn: {
    marginTop: 4,
    paddingVertical: 10,
    paddingHorizontal: 16,
  },
  linkText: {
    color: colors.grassBright,
    fontWeight: '700',
    fontSize: 15,
  },
})
