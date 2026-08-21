export function matchesDateQuery(isoDate: string, query: string): boolean {
  const term = query.trim().toLowerCase()
  if (!term) return true

  const date = new Date(isoDate)
  if (Number.isNaN(date.getTime())) return false

  const isoDay = date.toISOString().slice(0, 10)
  const brDay = date.toLocaleDateString('pt-BR')
  const formatted = formatDateTime(isoDate).toLowerCase()
  const normalized = term.replaceAll('-', '/')

  return (
    formatted.includes(term) ||
    isoDay.includes(term) ||
    brDay.toLowerCase().includes(term) ||
    brDay.includes(normalized) ||
    isoDay.replaceAll('-', '/').includes(normalized)
  )
}

export function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

export function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  if (mins === 0) {
    return `${secs}s`
  }
  return `${mins}:${String(secs).padStart(2, '0')}`
}

export function formatExpiresIn(expiresAt: string): string {
  const diffMs = new Date(expiresAt).getTime() - Date.now()
  if (diffMs <= 0) {
    return 'Expirado'
  }

  const hours = Math.floor(diffMs / (1000 * 60 * 60))
  const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60))

  if (hours >= 24) {
    const days = Math.floor(hours / 24)
    return `${days}d restantes`
  }
  if (hours > 0) {
    return `${hours}h ${minutes}m restantes`
  }
  return `${minutes}m restantes`
}

export function roleLabel(role: string): string {
  switch (role) {
    case 'athlete':
      return 'Atleta'
    case 'scout':
      return 'Olheiro'
    case 'admin':
      return 'Administrador'
    default:
      return role
  }
}
