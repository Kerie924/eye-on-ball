import { Ionicons } from '@expo/vector-icons'
import { router, useFocusEffect } from 'expo-router'
import { useCallback, useState } from 'react'
import { Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'

import { api } from '@/src/api/client'
import { useAuth } from '@/src/auth/AuthContext'
import { AppBrandHeader } from '@/src/components/AppBrandHeader'
import { colors } from '@/src/theme/colors'
import type { City } from '@/src/types'

export default function HomeScreen() {
  const { user } = useAuth()
  const [cityCount, setCityCount] = useState(0)
  const [refreshing, setRefreshing] = useState(false)

  const load = useCallback(async () => {
    try {
      const cities = await api.cities()
      setCityCount(cities.length)
    } catch {
      setCityCount(0)
    }
  }, [])

  useFocusEffect(
    useCallback(() => {
      void load()
    }, [load]),
  )

  const firstName = user?.full_name?.split(' ')[0] ?? 'Atleta'

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <AppBrandHeader />
      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={async () => {
              setRefreshing(true)
              await load()
              setRefreshing(false)
            }}
            tintColor={colors.grass}
          />
        }
      >
        <View style={styles.greetingRow}>
          <View>
            <Text style={styles.greeting}>Ola, {firstName}!</Text>
            <Text style={styles.greetingSub}>Encontre seus lances por cidade e horario</Text>
          </View>
          <Pressable style={styles.avatar} onPress={() => router.push('/(tabs)/profile')}>
            <Text style={styles.avatarText}>
              {user?.full_name?.slice(0, 1).toUpperCase() ?? '?'}
            </Text>
          </Pressable>
        </View>

        <Pressable
          style={({ pressed }) => [styles.hero, pressed && styles.pressed]}
          onPress={() => router.push('/(tabs)/courts')}
        >
          <View style={styles.heroIcon}>
            <Ionicons name="football" size={26} color={colors.grass} />
          </View>
          <View style={styles.heroBody}>
            <Text style={styles.heroTitle}>Ver videos</Text>
            <Text style={styles.heroMeta}>
              Cidade, quadra, data e horario — so os lances do seu jogo.
            </Text>
            {cityCount > 0 ? (
              <Text style={styles.heroHint}>
                {cityCount} {cityCount === 1 ? 'cidade disponivel' : 'cidades disponiveis'}
              </Text>
            ) : null}
          </View>
          <Ionicons name="chevron-forward" size={20} color={colors.textMuted} />
        </Pressable>

        <View style={styles.steps}>
          <Text style={styles.stepsTitle}>Como funciona</Text>
          {[
            'Escolha a cidade',
            'Escolha a quadra',
            'Escolha a data no calendario',
            'Escolha o horario (ex: 19:00 – 20:00)',
          ].map((label, index) => (
            <View key={label} style={styles.stepRow}>
              <View style={styles.stepNum}>
                <Text style={styles.stepNumText}>{index + 1}</Text>
              </View>
              <Text style={styles.stepText}>{label}</Text>
            </View>
          ))}
        </View>
      </ScrollView>
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
    gap: 20,
    paddingBottom: 40,
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
    maxWidth: 240,
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
  hero: {
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
  heroIcon: {
    width: 48,
    height: 48,
    borderRadius: 12,
    backgroundColor: 'rgba(34,197,94,0.15)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  heroBody: {
    flex: 1,
    gap: 4,
  },
  heroTitle: {
    color: colors.white,
    fontSize: 18,
    fontWeight: '800',
  },
  heroMeta: {
    color: colors.textSecondary,
    fontSize: 14,
    lineHeight: 20,
  },
  heroHint: {
    color: colors.grassBright,
    fontSize: 12,
    fontWeight: '700',
    marginTop: 2,
  },
  steps: {
    gap: 10,
  },
  stepsTitle: {
    color: colors.white,
    fontSize: 16,
    fontWeight: '700',
  },
  stepRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  stepNum: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: colors.grassDeep,
    alignItems: 'center',
    justifyContent: 'center',
  },
  stepNumText: {
    color: colors.grassLight,
    fontWeight: '800',
  },
  stepText: {
    color: colors.textSecondary,
    fontSize: 15,
  },
})

