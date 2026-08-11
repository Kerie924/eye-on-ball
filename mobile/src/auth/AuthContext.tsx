import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import { api, setAuthToken } from '../api/client'
import { deleteToken, getToken, setToken } from '../storage/tokenStorage'
import type { User, UserRole } from '../types'

const TOKEN_KEY = 'lanceon_token'

interface AuthContextValue {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  loginWithGoogle: (idToken: string, role?: UserRole) => Promise<void>
  register: (payload: {
    email: string
    password: string
    full_name: string
    role: UserRole
  }) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
  updateProfile: (payload: {
    full_name?: string
    email?: string
    avatar_url?: string | null
    current_password?: string
    new_password?: string
  }) => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const refreshUser = useCallback(async () => {
    const profile = await api.me()
    setUser(profile)
  }, [])

  useEffect(() => {
    async function bootstrap() {
      try {
        const token = await getToken(TOKEN_KEY)
        if (!token) {
          return
        }
        setAuthToken(token)
        await refreshUser()
      } catch {
        await deleteToken(TOKEN_KEY)
        setAuthToken(null)
        setUser(null)
      } finally {
        setLoading(false)
      }
    }

    bootstrap()
  }, [refreshUser])

  const applyToken = useCallback(
    async (accessToken: string) => {
      await setToken(TOKEN_KEY, accessToken)
      setAuthToken(accessToken)
      await refreshUser()
    },
    [refreshUser],
  )

  const login = useCallback(
    async (email: string, password: string) => {
      const { access_token } = await api.login(email, password)
      await applyToken(access_token)
    },
    [applyToken],
  )

  const loginWithGoogle = useCallback(
    async (idToken: string, role: UserRole = 'athlete') => {
      const { access_token } = await api.googleLogin(idToken, role)
      await applyToken(access_token)
    },
    [applyToken],
  )

  const register = useCallback(
    async (payload: {
      email: string
      password: string
      full_name: string
      role: UserRole
    }) => {
      await api.register(payload)
      await login(payload.email, payload.password)
    },
    [login],
  )

  const logout = useCallback(async () => {
    await deleteToken(TOKEN_KEY)
    setAuthToken(null)
    setUser(null)
  }, [])

  const updateProfile = useCallback(
    async (payload: {
      full_name?: string
      email?: string
      avatar_url?: string | null
      current_password?: string
      new_password?: string
    }) => {
      const updated = await api.updateProfile(payload)
      setUser(updated)
    },
    [],
  )

  const value = useMemo(
    () => ({
      user,
      loading,
      login,
      loginWithGoogle,
      register,
      logout,
      refreshUser,
      updateProfile,
    }),
    [user, loading, login, loginWithGoogle, register, logout, refreshUser, updateProfile],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
