import { Ionicons } from '@expo/vector-icons'
import { Redirect, Tabs } from 'expo-router'

import { useAuth } from '@/src/auth/AuthContext'
import { BrandLogo } from '@/src/components/BrandLogo'
import { LoadingState } from '@/src/components/LoadingState'
import { colors } from '@/src/theme/colors'

function HeaderLogo() {
  return <BrandLogo variant="wordmark" width={200} />
}

export default function TabLayout() {
  const { user, loading } = useAuth()

  if (loading) {
    return <LoadingState message="Carregando..." />
  }

  if (!user) {
    return <Redirect href="/(auth)/welcome" />
  }

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: colors.grass,
        tabBarInactiveTintColor: colors.textMuted,
        tabBarStyle: {
          backgroundColor: colors.blackSoft,
          borderTopColor: colors.cardBorder,
          height: 64,
          paddingTop: 6,
          paddingBottom: 8,
        },
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '600',
        },
        headerStyle: {
          backgroundColor: colors.black,
        },
        headerTintColor: colors.white,
        headerTitleStyle: {
          fontWeight: '700',
        },
        headerTitleAlign: 'center',
        headerShadowVisible: false,
        sceneStyle: {
          backgroundColor: colors.black,
        },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'Inicio',
          headerShown: false,
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="home" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="recordings"
        options={{
          title: 'Gravacoes',
          headerTitle: HeaderLogo,
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="videocam" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="courts"
        options={{
          title: 'Cidades',
          headerShown: false,
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="football" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Perfil',
          headerTitle: HeaderLogo,
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="person" size={size} color={color} />
          ),
        }}
      />
    </Tabs>
  )
}
