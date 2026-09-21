import { Link, NavLink, Outlet } from 'react-router-dom'
import {
  CalendarDays,
  CircleAlert,
  Home,
  MapPinned,
  UserRound,
  Video,
} from 'lucide-react'

import { BrandLogo } from './BrandLogo'
import { useAuth } from '../auth/AuthContext'

const nav = [
  { to: '/app', label: 'Inicio', icon: Home, end: true },
  { to: '/app/cidades', label: 'Cidades', icon: MapPinned },
  { to: '/app/gravacoes', label: 'Videos', icon: Video },
  { to: '/app/horarios', label: 'Horarios', icon: CalendarDays },
  { to: '/app/relatar', label: 'Relatar', icon: CircleAlert },
  { to: '/app/perfil', label: 'Perfil', icon: UserRound },
]

export function AppShell() {
  const { user } = useAuth()
  const first = user?.full_name?.split(' ')[0] ?? 'Atleta'

  return (
    <div className="min-h-screen bg-ink">
      <header className="sticky top-0 z-40 border-b border-line/70 bg-ink/90 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
          <BrandLogo variant="full" className="h-14 md:h-20" to="/app" />
          <nav className="hidden items-center gap-1 md:flex">
            {nav.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `nav-glow inline-flex items-center gap-2 rounded-lg px-3 py-2 text-base transition ${
                    isActive ? 'bg-grass/15 text-grass shadow-[0_0_18px_rgba(30,215,96,0.25)]' : 'text-muted'
                  }`
                }
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </NavLink>
            ))}
          </nav>
          <Link
            to="/app/perfil"
            className="flex items-center gap-2 rounded-full border border-line px-3 py-1.5 text-sm"
          >
            <span className="grid h-8 w-8 place-items-center rounded-full bg-grass/20 text-grass">
              {first.slice(0, 1).toUpperCase()}
            </span>
            <span className="hidden sm:inline">{first}</span>
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-6 pb-24 md:pb-8">
        <Outlet />
      </main>

      <nav className="fixed inset-x-0 bottom-0 z-40 border-t border-line/70 bg-ink/95 backdrop-blur md:hidden">
        <div className="grid grid-cols-5 gap-1 px-2 py-2">
          {nav.slice(0, 5).map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `nav-glow flex flex-col items-center gap-1 rounded-lg px-1 py-2 text-xs ${
                  isActive ? 'text-grass shadow-[0_0_16px_rgba(30,215,96,0.3)]' : 'text-muted'
                }`
              }
            >
              <item.icon className="h-5 w-5" />
              {item.label}
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  )
}
