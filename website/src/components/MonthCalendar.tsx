type Props = {
  value: string
  onChange: (date: string) => void
}

const WEEKDAYS = ['D', 'S', 'T', 'Q', 'Q', 'S', 'S']

function daysInMonth(year: number, monthIndex: number) {
  return new Date(year, monthIndex + 1, 0).getDate()
}

function toDateString(year: number, monthIndex: number, day: number) {
  return `${year}-${String(monthIndex + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
}

export function MonthCalendar({ value, onChange }: Props) {
  const selected = value ? new Date(`${value}T12:00:00`) : new Date()
  const year = selected.getFullYear()
  const monthIndex = selected.getMonth()
  const firstWeekday = new Date(year, monthIndex, 1).getDay()
  const totalDays = daysInMonth(year, monthIndex)
  const today = toDateString(
    new Date().getFullYear(),
    new Date().getMonth(),
    new Date().getDate(),
  )

  const cells: Array<number | null> = [
    ...Array.from({ length: firstWeekday }, () => null),
    ...Array.from({ length: totalDays }, (_, index) => index + 1),
  ]

  const title = selected.toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' })

  function shiftMonth(delta: number) {
    const next = new Date(year, monthIndex + delta, 1)
    onChange(toDateString(next.getFullYear(), next.getMonth(), 1))
  }

  return (
    <div className="rounded-2xl border border-line bg-card p-4">
      <div className="mb-3 flex items-center justify-between">
        <button
          type="button"
          onClick={() => shiftMonth(-1)}
          className="px-2 text-2xl text-grass hover:text-grass-bright"
          aria-label="Mes anterior"
        >
          ‹
        </button>
        <div className="text-sm font-bold capitalize">{title}</div>
        <button
          type="button"
          onClick={() => shiftMonth(1)}
          className="px-2 text-2xl text-grass hover:text-grass-bright"
          aria-label="Proximo mes"
        >
          ›
        </button>
      </div>
      <div className="mb-2 grid grid-cols-7 text-center text-xs font-semibold text-muted">
        {WEEKDAYS.map((label, index) => (
          <div key={`${label}-${index}`}>{label}</div>
        ))}
      </div>
      <div className="grid grid-cols-7 gap-1">
        {cells.map((day, index) => {
          if (!day) return <div key={`empty-${index}`} className="aspect-square" />
          const date = toDateString(year, monthIndex, day)
          const isSelected = date === value
          const isToday = date === today
          return (
            <button
              key={date}
              type="button"
              onClick={() => onChange(date)}
              className={`aspect-square rounded-full text-sm transition ${
                isSelected
                  ? 'bg-grass font-bold text-on-grass'
                  : isToday
                    ? 'border border-grass/50 text-white'
                    : 'text-white/80 hover:bg-white/5'
              }`}
            >
              {day}
            </button>
          )
        })}
      </div>
    </div>
  )
}
