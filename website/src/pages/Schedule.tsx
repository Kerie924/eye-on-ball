import { useMemo, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, ChevronRight } from 'lucide-react'

import { MonthCalendar } from '../components/MonthCalendar'
import { formatLongDate, hourSlots, todayLocalDate } from '../lib/time'

export function SchedulePage() {
  const { cityId, courtId } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const state = (location.state as {
    cityName?: string
    courtName?: string
    courtAddress?: string
  } | null) ?? {}

  const [playDate, setPlayDate] = useState(todayLocalDate())
  const slots = useMemo(() => hourSlots(), [])

  function openVideos(start: string, end: string) {
    const params = new URLSearchParams({
      courtId: String(courtId),
      cityId: String(cityId),
      date: playDate,
      startTime: start,
      endTime: end,
    })
    if (state.cityName) params.set('cityName', state.cityName)
    if (state.courtName) params.set('courtName', state.courtName)
    navigate(`/app/gravacoes?${params.toString()}`)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start gap-3">
        <Link
          to={`/app/cidades/${cityId}`}
          state={{ cityName: state.cityName }}
          className="mt-1 rounded-lg border border-line p-2 text-muted hover:text-white"
        >
          <ArrowLeft className="h-4 w-4" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold">Horarios</h1>
          <p className="mt-1 text-sm text-muted">
            {state.courtName ?? `Quadra #${courtId}`} · {formatLongDate(playDate)}
          </p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_1fr]">
        <div className="space-y-2">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-muted">
            Bloco de horario
          </h2>
          <div className="max-h-[28rem] space-y-2 overflow-y-auto pr-1">
            {slots.map((slot) => (
              <button
                key={slot.label}
                type="button"
                onClick={() => openVideos(slot.start, slot.end)}
                className="flex w-full items-center justify-between rounded-2xl border border-line bg-card px-4 py-3.5 text-left transition hover:border-grass/50"
              >
                <span className="font-medium">{slot.label}</span>
                <ChevronRight className="h-4 w-4 text-grass" />
              </button>
            ))}
          </div>
        </div>

        <div>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted">
            Data do jogo
          </h2>
          <MonthCalendar value={playDate} onChange={setPlayDate} />
          {(state.courtName || state.courtAddress) && (
            <div className="mt-4 rounded-2xl border border-line bg-card p-4 text-sm">
              <div className="font-semibold">{state.courtName}</div>
              {state.courtAddress ? (
                <div className="mt-1 text-muted">{state.courtAddress}</div>
              ) : null}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
