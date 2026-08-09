import type { ReactNode } from 'react'

type BadgeVariant = 'online' | 'offline' | 'warning' | 'success' | 'danger' | 'neutral'

interface StatusBadgeProps {
  variant: BadgeVariant
  children: ReactNode
}

const labels: Record<BadgeVariant, string> = {
  online: 'Online',
  offline: 'Offline',
  warning: 'Manutencao',
  success: 'Disponivel',
  danger: 'Expirado',
  neutral: 'Neutro',
}

export function StatusBadge({ variant, children }: StatusBadgeProps) {
  return <span className={`badge badge-${variant}`}>{children ?? labels[variant]}</span>
}

export function UserAvatar({ name }: { name: string }) {
  const initials = name
    .split(' ')
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? '')
    .join('')

  return <span className="user-avatar">{initials || 'U'}</span>
}

export function CourtThumb({ name }: { name: string }) {
  return (
    <span className="court-thumb" aria-hidden="true">
      {name.slice(0, 1).toUpperCase()}
    </span>
  )
}

export function RecordingThumb({ duration }: { duration: number }) {
  const mins = Math.floor(duration / 60)
  const secs = duration % 60
  const label = `${mins}:${secs.toString().padStart(2, '0')}`

  return (
    <span className="recording-thumb">
      <span className="recording-thumb-play">▶</span>
      <span className="recording-thumb-duration">{label}</span>
    </span>
  )
}
