import type { ReactNode } from 'react'

interface StatCardProps {
  label: string
  value: string | number
  hint?: string
  icon: ReactNode
  tone?: 'green' | 'purple' | 'yellow' | 'blue'
}

export function StatCard({ label, value, hint, icon, tone = 'green' }: StatCardProps) {
  return (
    <article className={`stat-card stat-card-${tone} hover-lift`}>
      <div className="stat-card-icon">{icon}</div>
      <div className="stat-card-body">
        <span>{label}</span>
        <strong>{value}</strong>
        {hint && <small>{hint}</small>}
      </div>
    </article>
  )
}
