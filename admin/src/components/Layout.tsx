import { useEffect, useState } from 'react'
import {
  BarChart3,
  Cpu,
  FileText,
  Grid3X3,
  HelpCircle,
  LayoutGrid,
  LogOut,
  Menu,
  Settings,
  Users,
  Video,
  X,
} from 'lucide-react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { useToast } from '../context/ToastContext'
import { BrandLogo } from './BrandLogo'
import { NotificationsPanel } from './shared'
import { UserAvatar } from './ui'
import type { AdminStats } from '../types'
import { downloadCsv } from '../utils/helpers'

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutGrid, end: true },
  { to: '/quadras', label: 'Quadras', icon: Grid3X3 },
  { to: '/gravacoes', label: 'Gravacoes', icon: Video },
  { to: '/usuarios', label: 'Usuarios', icon: Users },
  { to: '/dispositivos', label: 'Dispositivos', icon: Cpu },
  { to: '/relatorios', label: 'Relatorios', icon: BarChart3 },
  { to: '/configuracoes', label: 'Configuracoes', icon: Settings },
  { to: '/suporte', label: 'Suporte', icon: HelpCircle },
]

export function Layout() {
  const { user, logout } = useAuth()
  const { showToast } = useToast()
  const navigate = useNavigate()
  const location = useLocation()
  const [stats, setStats] = useState<AdminStats | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)

  useEffect(() => {
    api.stats().then(setStats).catch(() => undefined)
  }, [])

  useEffect(() => {
    setSidebarOpen(false)
  }, [location.pathname])

  useEffect(() => {
    document.body.style.overflow = sidebarOpen ? 'hidden' : ''
    return () => {
      document.body.style.overflow = ''
    }
  }, [sidebarOpen])

  async function handleExport() {
    try {
      const [recordings, users, courts] = await Promise.all([
        api.recordings(undefined, 'all'),
        api.users(),
        api.courts(),
      ])

      downloadCsv(
        `relatorio-olho-no-lance-${new Date().toISOString().slice(0, 10)}.csv`,
        ['Tipo', 'Nome', 'Detalhe', 'Status', 'Data'],
        [
          ...recordings.map((recording) => [
            'Gravacao',
            recording.court_name ?? '',
            `#${recording.id} Camera ${recording.camera_index}`,
            recording.status ?? 'available',
            new Date(recording.triggered_at).toLocaleString('pt-BR'),
          ]),
          ...users.map((item) => [
            'Usuario',
            item.full_name,
            item.email,
            item.is_active ? 'Ativo' : 'Inativo',
            new Date(item.created_at).toLocaleDateString('pt-BR'),
          ]),
          ...courts.map((court) => [
            'Quadra',
            court.name,
            court.address ?? '',
            court.is_active ? 'Ativa' : 'Inativa',
            new Date(court.created_at).toLocaleDateString('pt-BR'),
          ]),
        ],
      )
      showToast('Relatorio exportado com sucesso', 'success')
    } catch {
      showToast('Erro ao exportar relatorio', 'error')
    }
  }

  return (
    <div className={`app-shell ${sidebarOpen ? 'sidebar-open' : ''}`}>
      <div
        className="sidebar-backdrop"
        onClick={() => setSidebarOpen(false)}
        aria-hidden={!sidebarOpen}
      />

      <aside className="sidebar">
        <div className="sidebar-top">
          <div className="brand">
            <BrandLogo variant="full" className="brand-logo-sidebar" />
          </div>
          <button
            type="button"
            className="sidebar-close"
            onClick={() => setSidebarOpen(false)}
            aria-label="Fechar menu"
          >
            <X size={20} />
          </button>
        </div>

        <nav className="nav">
          {navItems.map((item) => {
            const Icon = item.icon
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  isActive ? 'nav-link active' : 'nav-link'
                }
              >
                <Icon size={18} />
                {item.label}
              </NavLink>
            )
          })}
        </nav>

        <div className="sidebar-footer">
          <button
            type="button"
            className="sidebar-user sidebar-user-btn"
            onClick={() => navigate('/configuracoes')}
          >
            <UserAvatar name={user?.full_name ?? 'Admin'} />
            <div>
              <strong>{user?.full_name ?? 'Admin'}</strong>
              <span>Super Administrador</span>
            </div>
          </button>
          <button type="button" className="nav-link logout-btn" onClick={logout}>
            <LogOut size={18} />
            Sair
          </button>
        </div>
      </aside>

      <div className="main-area">
        <header className="topbar">
          <div className="topbar-left">
            <button
              type="button"
              className="menu-toggle"
              onClick={() => setSidebarOpen(true)}
              aria-label="Abrir menu"
            >
              <Menu size={22} />
            </button>
            <div className="topbar-date">
              <FileText size={16} />
              <span>{new Date().toLocaleDateString('pt-BR')}</span>
            </div>
          </div>
          <div className="topbar-actions">
            <button type="button" className="btn btn-outline btn-sm" onClick={handleExport}>
              Exportar Relatorio
            </button>
            <NotificationsPanel stats={stats} />
            <div className="topbar-profile">
              <UserAvatar name={user?.full_name ?? 'Admin'} />
            </div>
          </div>
        </header>

        <main className="content page-enter">
          <Outlet context={{ refreshStats: () => api.stats().then(setStats) }} />
        </main>
      </div>
    </div>
  )
}
