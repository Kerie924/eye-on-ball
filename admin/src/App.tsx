import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './auth/AuthContext'
import { ToastContainer } from './components/ToastContainer'
import { Layout } from './components/Layout'
import { ProtectedRoute } from './components/ProtectedRoute'
import { ToastProvider } from './context/ToastContext'
import { CourtsPage } from './pages/CourtsPage'
import { DashboardPage } from './pages/DashboardPage'
import { DevicesPage } from './pages/DevicesPage'
import { LoginPage } from './pages/LoginPage'
import { RecordingsPage } from './pages/RecordingsPage'
import { ReportsPage } from './pages/ReportsPage'
import { SettingsPage } from './pages/SettingsPage'
import { SupportPage } from './pages/SupportPage'
import { UsersPage } from './pages/UsersPage'

export default function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route element={<ProtectedRoute />}>
              <Route element={<Layout />}>
                <Route index element={<DashboardPage />} />
                <Route path="quadras" element={<CourtsPage />} />
                <Route path="gravacoes" element={<RecordingsPage />} />
                <Route path="usuarios" element={<UsersPage />} />
                <Route path="dispositivos" element={<DevicesPage />} />
                <Route path="relatorios" element={<ReportsPage />} />
                <Route path="configuracoes" element={<SettingsPage />} />
                <Route path="suporte" element={<SupportPage />} />
              </Route>
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
          <ToastContainer />
        </BrowserRouter>
      </AuthProvider>
    </ToastProvider>
  )
}
