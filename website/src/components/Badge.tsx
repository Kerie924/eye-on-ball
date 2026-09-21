import type { ReactNode } from 'react'

type Props = {
  children: ReactNode
  tone?: 'live' | 'info' | 'danger'
  className?: string
}

const tones = {
  live: 'border-grass text-grass',
  info: 'border-grass/70 text-grass',
  danger: 'border-danger text-danger',
}

export function Badge({ children, tone = 'info', className = '' }: Props) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold tracking-wide ${tones[tone]} ${className}`}
    >
      {children}
    </span>
  )
}
