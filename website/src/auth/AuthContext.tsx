import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import { api, setToken } from '../api/client'
import type { User, UserRole } from '../types'

type AuthContextValue = {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (payload: {
    email: string
    password: string
    full_name: string
    role: Extract<UserRole, 'athlete' | 'scout'>
  }) => Promise<void>
  logout: () => void
  refresh: () => Promise<void>
  updateProfile: (payload: {
    full_name?: string
    email?: string
    avatar_url?: string | null
    current_password?: string
    new_password?: string
  }) => Promise<void>
  deleteAccount: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async () => {
    const token = localStorage.getItem('lanceon_token')
    if (!token) {
      setUser(null)
      setLoading(false)
      return
    }
    try {
      const me = await api.me()
      setUser(me)
    } catch {
      setToken(null)
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const login = useCallback(async (email: string, password: string) => {
    const { access_token } = await api.login(email, password)
    setToken(access_token)
    const me = await api.me()
    setUser(me)
  }, [])

  const register = useCallback(
    async (payload: {
      email: string
      password: string
      full_name: string
      role: Extract<UserRole, 'athlete' | 'scout'>
    }) => {
      await api.register(payload)
      await login(payload.email, payload.password)
    },
    [login],
  )

  const logout = useCallback(() => {
    setToken(null)
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

  const deleteAccount = useCallback(async () => {
    await api.deleteAccount()
    setToken(null)
    setUser(null)
  }, [])

  const value = useMemo(
    () => ({
      user,
      loading,
      login,
      register,
      logout,
      refresh,
      updateProfile,
      deleteAccount,
    }),
    [user, loading, login, register, logout, refresh, updateProfile, deleteAccount],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
