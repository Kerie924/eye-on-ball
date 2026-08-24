import { Ionicons } from '@expo/vector-icons'
import { router, type Href } from 'expo-router'
import { Image, Pressable, StyleSheet, Text, View } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'

import { useAuth } from '@/src/auth/AuthContext'
import { colors } from '@/src/theme/colors'
import { confirmAction } from '@/src/utils/dialogs'
import { roleLabel } from '@/src/utils/format'

const MENU = [
  { key: 'edit', label: 'Meu perfil', icon: 'person-outline' as const },
  { key: 'courts', label: 'Minhas quadras', icon: 'football-outline' as const },
  { key: 'help', label: 'Ajuda e suporte', icon: 'help-circle-outline' as const },
]

export default function ProfileScreen() {
  const { user, logout } = useAuth()

  async function handleLogout() {
    const confirmed = await confirmAction('Sair', 'Deseja encerrar sua sessao?', {
      destructive: true,
      confirmLabel: 'Sair',
      cancelLabel: 'Cancelar',
      tone: 'danger',
    })
    if (!confirmed) return
    await logout()
    router.replace('/(auth)/welcome')
  }

  function handleMenu(key: string) {
    if (key === 'edit') {
      router.push('/edit-profile')
      return
    }
    if (key === 'courts') {
      router.push('/(tabs)/courts')
      return
    }
    if (key === 'help') {
      router.push('/(tabs)/report' as Href)
      return
    }
  }

  return (
    <SafeAreaView style={styles.safe} edges={['bottom']}>
      <View style={styles.content}>
        <View style={styles.card}>
          {user?.avatar_url ? (
            <Image source={{ uri: user.avatar_url }} style={styles.avatarImage} />
          ) : (
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>
                {user?.full_name?.slice(0, 1).toUpperCase() ?? '?'}
              </Text>
            </View>
          )}
          <Text style={styles.name}>{user?.full_name}</Text>
          <Text style={styles.email}>{user?.email}</Text>
          <Text style={styles.role}>{roleLabel(user?.role ?? '')}</Text>

          {user?.role === 'scout' && !user.is_approved ? (
            <View style={styles.notice}>
              <Text style={styles.noticeText}>
                Sua conta de olheiro aguarda aprovacao do administrador.
              </Text>
            </View>
          ) : null}

          <Pressable style={styles.editBtn} onPress={() => router.push('/edit-profile')}>
            <Text style={styles.editBtnText}>Editar perfil</Text>
          </Pressable>
        </View>

        <View style={styles.menu}>
          {MENU.map((item) => (
            <Pressable
              key={item.key}
              style={({ pressed }) => [styles.menuItem, pressed && styles.menuPressed]}
              onPress={() => handleMenu(item.key)}
            >
              <View style={styles.menuLeft}>
                <Ionicons name={item.icon} size={20} color={colors.grass} />
                <Text style={styles.menuLabel}>{item.label}</Text>
              </View>
              <Ionicons name="chevron-forward" size={18} color={colors.textMuted} />
            </Pressable>
          ))}
        </View>

        <Pressable
          style={({ pressed }) => [styles.logout, pressed && styles.menuPressed]}
          onPress={handleLogout}
        >
          <Ionicons name="log-out-outline" size={20} color={colors.danger} />
          <Text style={styles.logoutText}>Sair</Text>
        </Pressable>
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
    padding: 20,
    gap: 16,
  },
  card: {
    backgroundColor: colors.card,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    padding: 20,
    alignItems: 'center',
    gap: 6,
  },
  avatar: {
    width: 76,
    height: 76,
    borderRadius: 38,
    backgroundColor: colors.grassDeep,
    borderWidth: 2,
    borderColor: colors.grass,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  avatarImage: {
    width: 76,
    height: 76,
    borderRadius: 38,
    borderWidth: 2,
    borderColor: colors.grass,
    marginBottom: 8,
  },
  avatarText: {
    fontSize: 30,
    fontWeight: '800',
    color: colors.grassLight,
  },
  name: {
    fontSize: 20,
    fontWeight: '800',
    color: colors.white,
  },
  email: {
    fontSize: 14,
    color: colors.textSecondary,
  },
  role: {
    marginTop: 4,
    fontSize: 14,
    fontWeight: '700',
    color: colors.grassBright,
  },
  notice: {
    marginTop: 12,
    backgroundColor: colors.warningSoft,
    borderRadius: 10,
    padding: 12,
  },
  noticeText: {
    color: '#fbbf24',
    textAlign: 'center',
    fontSize: 14,
    lineHeight: 20,
  },
  editBtn: {
    marginTop: 12,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 999,
    backgroundColor: 'rgba(34,197,94,0.15)',
  },
  editBtnText: {
    color: colors.grassBright,
    fontWeight: '700',
  },
  menu: {
    backgroundColor: colors.card,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    overflow: 'hidden',
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: colors.cardBorder,
  },
  menuPressed: {
    backgroundColor: colors.blackMuted,
  },
  menuLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  menuLabel: {
    color: colors.white,
    fontSize: 15,
    fontWeight: '600',
  },
  logout: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: colors.card,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: colors.cardBorder,
    paddingVertical: 16,
  },
  logoutText: {
    color: colors.danger,
    fontWeight: '700',
    fontSize: 16,
  },
})
