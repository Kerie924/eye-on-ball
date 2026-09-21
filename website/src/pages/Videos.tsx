import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Play } from 'lucide-react'

import { ApiError, api } from '../api/client'
import {
  formatDateTime,
  formatLongDate,
  recordingInTimeSlot,
  remainingLabel,
} from '../lib/time'
import type { Recording } from '../types'
import { Badge } from '../components/Badge'

export function VideosPage() {
  const [params] = useSearchParams()
  const courtId = Number(params.get('courtId'))
  const date = params.get('date')
  const startTime = params.get('startTime')
  const endTime = params.get('endTime')
  const cityName = params.get('cityName')
  const courtName = params.get('courtName')
  const cityId = params.get('cityId')

  const hasWindow =
    Number.isFinite(courtId) &&
    courtId > 0 &&
    Boolean(date && startTime && endTime)

  const [recordings, setRecordings] = useState<Recording[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!hasWindow || !date || !startTime || !endTime) {
      setRecordings([])
      setLoading(false)
      return
    }
    let cancelled = false
    ;(async () => {
      setLoading(true)
      setError('')
      try {
        const data = await api.recordings(courtId, date, startTime, endTime)
        if (!cancelled) {
          setRecordings(
            data.filter((item) =>
              recordingInTimeSlot(item.triggered_at, date, startTime, endTime),
            ),
          )
        }
      } catch (err) {
        if (!cancelled) {
          setRecordings([])
          setError(err instanceof ApiError ? err.message : 'Nao foi possivel carregar os videos')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [courtId, date, startTime, endTime, hasWindow])

  const title = useMemo(() => {
    if (!hasWindow) return 'Gravacoes'
    return `${cityName ? `${cityName} · ` : ''}${courtName ?? `Quadra #${courtId}`}`
  }, [hasWindow, cityName, courtName, courtId])

  if (!hasWindow) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">Videos</h1>
        <div className="rounded-2xl border border-line bg-card p-8 text-center">
          <p className="text-muted">
            Escolha cidade, quadra e horario para ver os videos desse bloco.
          </p>
          <Link
            to="/app/cidades"
            className="mt-5 inline-flex rounded-xl bg-grass px-5 py-3 text-sm font-semibold text-on-grass"
          >
            Comecar
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">{title}</h1>
          <p className="mt-1 text-sm text-muted">
            {date ? formatLongDate(date) : ''} · {startTime} – {endTime}
          </p>
        </div>
        <Link
          to={cityId ? `/app/cidades/${cityId}/quadras/${courtId}/horarios` : '/app/cidades'}
          state={{ cityName, courtName }}
          className="text-sm font-medium text-grass hover:underline"
        >
          Trocar
        </Link>
      </div>

      {loading ? <p className="text-muted">Carregando gravacoes...</p> : null}

      {!loading && recordings.length === 0 ? (
        <div className="rounded-2xl border border-line bg-card p-8 text-center text-sm text-muted">
          {error ||
            'Nao ha lances desta quadra neste bloco. Tente outro horario ou outra data.'}
        </div>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {recordings.map((rec) => (
          <Link
            key={rec.id}
            to={`/app/video/${rec.id}`}
            state={{ recordings }}
            className="group overflow-hidden rounded-2xl border border-line bg-card transition hover:border-grass/40"
          >
            <div className="relative aspect-video bg-gradient-to-br from-grass/15 via-ink-soft to-ink">
              <div className="absolute inset-0 grid place-items-center">
                <span className="grid h-12 w-12 place-items-center rounded-full bg-grass/90 text-on-grass shadow-lg transition group-hover:scale-105">
                  <Play className="h-5 w-5 fill-current" />
                </span>
              </div>
              <span className="absolute bottom-2 right-2">
                <Badge tone="live" className="bg-black/70 backdrop-blur">
                  {remainingLabel(rec.expires_at)}
                </Badge>
              </span>
            </div>
            <div className="p-4">
              <div className="font-semibold">
                Camera {rec.camera_index} · {rec.duration_seconds}s
              </div>
              <div className="mt-1 text-xs text-muted">{formatDateTime(rec.triggered_at)}</div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}
