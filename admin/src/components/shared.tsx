import { useEffect, useRef, useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import type { AdminStats } from '../types'

interface NotificationsPanelProps {
  stats: AdminStats | null
}

export function NotificationsPanel({ stats }: NotificationsPanelProps) {
  const [open, setOpen] = useState(false)
  const panelRef = useRef<HTMLDivElement>(null)
  const count =
    (stats?.pending_access_requests ?? 0) +
    (stats?.pending_scouts ?? 0) +
    (stats?.devices_offline ?? 0)

  useEffect(() => {
    function handleClick(event: MouseEvent) {
      if (panelRef.current && !panelRef.current.contains(event.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const items: { label: string; to: string; count: number }[] = [
    {
      label: 'Solicitacoes de acesso',
      to: '/usuarios?tab=requests',
      count: stats?.pending_access_requests ?? 0,
    },
    {
      label: 'Olheiros pendentes',
      to: '/usuarios?tab=scouts',
      count: stats?.pending_scouts ?? 0,
    },
    {
      label: 'Dispositivos offline',
      to: '/dispositivos',
      count: stats?.devices_offline ?? 0,
    },
  ]

  return (
    <div className="notifications-wrap" ref={panelRef}>
      <button
        type="button"
        className="icon-btn notification-btn"
        aria-label="Notificacoes"
        onClick={() => setOpen((value) => !value)}
      >
        {count > 0 && <span className="notification-dot">{count}</span>}
      </button>

      {open && (
        <div className="notifications-panel animate-dropdown">
          <h3>Notificacoes</h3>
          {items.map((item) => (
            <Link
              key={item.label}
              to={item.to}
              className="notification-item"
              onClick={() => setOpen(false)}
            >
              <span>{item.label}</span>
              <strong>{item.count}</strong>
            </Link>
          ))}
          {count === 0 && <p className="empty-state">Nenhuma notificacao pendente</p>}
        </div>
      )}
    </div>
  )
}

export function LoadingState({ label = 'Carregando...' }: { label?: string }) {
  return (
    <div className="loading-state animate-fade">
      <span className="spinner" />
      <p>{label}</p>
    </div>
  )
}

export function Modal({
  title,
  children,
  onClose,
}: {
  title: string
  children: ReactNode
  onClose: () => void
}) {
  return (
    <div className="modal-overlay animate-fade" onClick={onClose}>
      <div className="modal animate-scale" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{title}</h2>
          <button type="button" className="icon-btn" onClick={onClose} aria-label="Fechar">
            ×
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}
