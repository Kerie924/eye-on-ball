export type TimeSlot = {
  start: string
  end: string
  label: string
}

export function hourSlots(): TimeSlot[] {
  const slots: TimeSlot[] = []
  for (let hour = 8; hour <= 23; hour += 1) {
    const start = `${String(hour).padStart(2, '0')}:00`
    const endHour = hour === 23 ? 0 : hour + 1
    const end = `${String(endHour).padStart(2, '0')}:00`
    slots.push({ start, end, label: `${start} – ${end}` })
  }
  return slots
}

export function brazilStartIso(date: string, time: string): string {
  return `${date}T${time}:00-03:00`
}

export function brazilEndIso(date: string, endTime: string): string {
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
): boolean {
  const triggered = new Date(triggeredAt).getTime()
  if (Number.isNaN(triggered)) return false
  const start = new Date(brazilStartIso(date, startTime)).getTime()
  const end = new Date(brazilEndIso(date, endTime)).getTime()
  return triggered >= start && triggered < end
}

export function todayLocalDate(): string {
  const now = new Date()
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

export function formatLongDate(date: string): string {
  const parsed = new Date(`${date}T12:00:00`)
  return parsed.toLocaleDateString('pt-BR', {
    weekday: 'long',
    day: '2-digit',
    month: 'long',
    year: 'numeric',
  })
}
