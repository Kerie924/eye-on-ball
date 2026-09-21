import { Navigate, Outlet } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'

export function ProtectedRoute() {
  const { user, loading } = useAuth()
  if (loading) {
    return (
      <div className="grid min-h-screen place-items-center bg-ink text-muted">
        Carregando...
      </div>
    )
  }
  if (!user) return <Navigate to="/entrar" replace />
  return <Outlet />
}
