import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { AuthProvider } from './auth/AuthContext'
import { AppShell } from './components/AppShell'
import { ProtectedRoute } from './components/ProtectedRoute'
import { CitiesPage } from './pages/Cities'
import { CourtsPage } from './pages/Courts'
import { ForgotPasswordPage } from './pages/ForgotPassword'
import { HomePage } from './pages/Home'
import { HorariosRedirectPage } from './pages/HorariosRedirect'
import { HowItWorksPage } from './pages/HowItWorks'
import { LandingPage } from './pages/Landing'
import { DownloadPage } from './pages/Download'
import { LoginPage } from './pages/Login'
import { PlayerPage } from './pages/Player'
import { ProfilePage } from './pages/Profile'
import { RegisterPage } from './pages/Register'
import { ReportPage } from './pages/Report'
import { SchedulePage } from './pages/Schedule'
import { VideosPage } from './pages/Videos'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/entrar" element={<LoginPage />} />
          <Route path="/cadastrar" element={<RegisterPage />} />
          <Route path="/esqueci-senha" element={<ForgotPasswordPage />} />
          <Route path="/sobre" element={<HowItWorksPage />} />
          <Route path="/baixar" element={<DownloadPage />} />

          <Route element={<ProtectedRoute />}>
            <Route path="/app" element={<AppShell />}>
              <Route index element={<HomePage />} />
              <Route path="cidades" element={<CitiesPage />} />
              <Route path="cidades/:cityId" element={<CourtsPage />} />
              <Route path="cidades/:cityId/quadras/:courtId/horarios" element={<SchedulePage />} />
              <Route path="horarios" element={<HorariosRedirectPage />} />
              <Route path="gravacoes" element={<VideosPage />} />
              <Route path="video/:id" element={<PlayerPage />} />
              <Route path="relatar" element={<ReportPage />} />
              <Route path="perfil" element={<ProfilePage />} />
            </Route>
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
