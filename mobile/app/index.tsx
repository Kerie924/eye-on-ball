import { Redirect } from 'expo-router'

import { LoadingState } from '@/src/components/LoadingState'
import { useAuth } from '@/src/auth/AuthContext'

export default function Index() {
  const { user, loading } = useAuth()

  if (loading) {
    return <LoadingState message="Iniciando app..." />
  }

  if (user) {
    return <Redirect href="/(tabs)" />
  }

  return <Redirect href="/(auth)/welcome" />
}
