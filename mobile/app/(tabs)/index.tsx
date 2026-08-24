import { Ionicons } from '@expo/vector-icons'
import { router, useFocusEffect } from 'expo-router'
import { useCallback, useState } from 'react'
import { Linking, Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'

import { api } from '@/src/api/client'
import { useAuth } from '@/src/auth/AuthContext'
import { AppBrandHeader } from '@/src/components/AppBrandHeader'
import { colors } from '@/src/theme/colors'

const INSTAGRAM_URL = 'https://www.instagram.com/lanceonpara?igsi=NmVsYWloeG93NWV1'

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

        <View style={styles.socialRow}>
          <Pressable
            accessibilityRole="link"
            accessibilityLabel="Instagram Lance On"
            style={({ pressed }) => [styles.socialBtn, pressed && styles.socialPressed]}
            onPress={() => {
              void Linking.openURL(INSTAGRAM_URL)
            }}
          >
            <Ionicons name="logo-instagram" size={28} color={colors.grass} />
          </Pressable>
          <View style={styles.socialBtn}>
            <Ionicons name="logo-facebook" size={28} color={colors.grass} />
          </View>
          <View style={styles.socialBtn}>
            <Ionicons name="globe-outline" size={28} color={colors.grass} />
          </View>
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
  socialRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 16,
    marginTop: 28,
  },
  socialBtn: {
    width: 52,
    height: 52,
    borderRadius: 16,
    backgroundColor: 'rgba(34,197,94,0.15)',
    borderWidth: 1,
    borderColor: colors.cardBorder,
    alignItems: 'center',
    justifyContent: 'center',
  },
  socialPressed: {
    opacity: 0.85,
    borderColor: colors.grass,
  },
})

