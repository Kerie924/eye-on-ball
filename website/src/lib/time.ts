export function todayLocalDate() {
  const d = new Date()
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

export function formatLongDate(isoDate: string) {
  const parsed = new Date(`${isoDate}T12:00:00`)
  return parsed.toLocaleDateString('pt-BR', {
    weekday: 'long',
    day: '2-digit',
    month: 'long',
    year: 'numeric',
  })
}

export function formatDateTime(iso: string) {
  return new Date(iso).toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function remainingLabel(expiresAt: string) {
  const ms = new Date(expiresAt).getTime() - Date.now()
  if (ms <= 0) return 'Expirado'
  const mins = Math.round(ms / 60000)
  if (mins < 60) return `${mins}m restantes`
  const hours = Math.round(mins / 60)
  return `${hours}h restantes`
}

export function hourSlots() {
  return Array.from({ length: 16 }, (_, i) => {
    const startHour = 8 + i
    const endHour = startHour === 23 ? 0 : startHour + 1
    const pad = (n: number) => String(n).padStart(2, '0')
    return {
      label: `${pad(startHour)}:00 – ${pad(endHour)}:00`,
      start: `${pad(startHour)}:00`,
      end: `${pad(endHour)}:00`,
    }
  })
}

export function brazilStartIso(date: string, time: string) {
  return `${date}T${time}:00-03:00`
}

export function brazilEndIso(date: string, endTime: string) {
  if (endTime === '00:00') {
    const [year, month, day] = date.split('-').map(Number)
    const next = new Date(Date.UTC(year, month - 1, day))
    next.setUTCDate(next.getUTCDate() + 1)
    const y = next.getUTCFullYear()
    const m = String(next.getUTCMonth() + 1).padStart(2, '0')
    const d = String(next.getUTCDate()).padStart(2, '0')
    return `${y}-${m}-${d}T00:00:00-03:00`
  }
  return `${date}T${endTime}:00-03:00`
}

export function recordingInTimeSlot(
  triggeredAt: string,
  date: string,
  startTime: string,
  endTime: string,
) {
  const triggered = new Date(triggeredAt).getTime()
  if (Number.isNaN(triggered)) return false
  const start = new Date(brazilStartIso(date, startTime)).getTime()
  const end = new Date(brazilEndIso(date, endTime)).getTime()
  return triggered >= start && triggered < end
}

export function roleLabel(role: string) {
  if (role === 'scout') return 'Olheiro'
  if (role === 'admin') return 'Admin'
  return 'Atleta'
}
