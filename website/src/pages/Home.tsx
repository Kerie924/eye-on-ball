import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { CalendarDays, ChevronRight, CircleAlert, MapPinned, Video } from 'lucide-react'

import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { Badge } from '../components/Badge'
import { DownloadApp } from '../components/DownloadApp'
import mark from '../assets/brand/mark.png'

export function HomePage() {
  const { user } = useAuth()
  const [cityCount, setCityCount] = useState(0)
  const first = user?.full_name?.split(' ')[0] ?? 'Atleta'

  useEffect(() => {
    void api
      .cities()
      .then((cities) => setCityCount(cities.length))
      .catch(() => setCityCount(0))
  }, [])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Ola, {first}!</h1>
        <p className="mt-1 text-muted">Encontre seus lances por cidade e horario</p>
      </div>

      <Link
        to="/app/cidades"
        className="flex items-center gap-4 rounded-2xl border border-grass/30 bg-gradient-to-br from-grass/20 to-card p-5 transition hover:border-grass"
      >
        <img src={mark} alt="" className="h-12 w-12 object-contain drop-shadow-[0_0_12px_rgba(30,215,96,0.4)]" />
        <div className="flex-1">
          <div className="text-lg font-semibold">Ver videos</div>
          <p className="text-sm text-muted">
            Cidade, quadra, data e horario — so os lances do seu jogo.
          </p>
          {cityCount > 0 ? (
            <Badge className="mt-2" tone="info">
              {cityCount} {cityCount === 1 ? 'cidade disponivel' : 'cidades disponiveis'}
            </Badge>
          ) : null}
        </div>
        <ChevronRight className="h-5 w-5 text-muted" />
      </Link>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {[
          { to: '/app/cidades', label: 'Cidades', icon: MapPinned },
          { to: '/app/cidades', label: 'Quadras', icon: Video },
          { to: '/app/horarios', label: 'Horarios', icon: CalendarDays },
          { to: '/app/relatar', label: 'Relatar erro', icon: CircleAlert },
        ].map((item) => (
          <Link
            key={item.label}
            to={item.to}
            className="surface-card flex flex-col items-center gap-3 rounded-2xl p-5 text-center"
          >
            <item.icon className="h-7 w-7 text-grass" />
            <span className="text-sm font-medium">{item.label}</span>
          </Link>
        ))}
      </div>

      <a
        href="https://www.instagram.com/lanceonpara"
        target="_blank"
        rel="noreferrer"
        className="inline-flex items-center gap-2 text-sm text-muted hover:text-grass"
      >
        <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" aria-hidden>
          <rect x="3" y="3" width="18" height="18" rx="5" stroke="currentColor" strokeWidth="1.8" />
          <circle cx="12" cy="12" r="4" stroke="currentColor" strokeWidth="1.8" />
          <circle cx="17.5" cy="6.5" r="1.1" fill="currentColor" />
        </svg>
        @lanceonpara
      </a>
      <DownloadApp compact />
    </div>
  )
}
