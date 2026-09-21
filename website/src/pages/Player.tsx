import { useEffect, useMemo, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { ArrowLeft, Download, Play } from 'lucide-react'

import { ApiError, api } from '../api/client'
import { Button } from '../components/Button'
import { formatDateTime, remainingLabel } from '../lib/time'
import type { Recording } from '../types'

export function PlayerPage() {
  const { id } = useParams()
  const location = useLocation()
  const sibling = (location.state as { recordings?: Recording[] } | null)?.recordings

  const recordingId = Number(id)
  const [recording, setRecording] = useState<Recording | null>(null)
  const [others, setOthers] = useState<Recording[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [downloading, setDownloading] = useState(false)

  const streamUrl = useMemo(
    () => (Number.isFinite(recordingId) ? api.recordingStreamUrl(recordingId) : ''),
    [recordingId],
  )

  useEffect(() => {
    if (!Number.isFinite(recordingId) || recordingId <= 0) return
    let cancelled = false
    ;(async () => {
      setLoading(true)
      setError('')
      try {
        const data = await api.recording(recordingId)
        if (cancelled) return
        setRecording(data)
        if (sibling && sibling.length > 0) {
          setOthers(sibling.filter((item) => item.id !== data.id))
        } else {
          const related = await api.recordings(data.court_id)
          if (!cancelled) {
            setOthers(
              related.filter(
                (item) =>
                  item.id !== data.id &&
                  Math.abs(
                    new Date(item.triggered_at).getTime() -
                      new Date(data.triggered_at).getTime(),
                  ) < 5 * 60 * 1000,
              ),
            )
          }
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'Nao foi possivel abrir o video')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
    // sibling intentionally omitted: only use initial navigation state
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recordingId])

  async function handleDownload() {
    if (!recording) return
    setDownloading(true)
    try {
      const url = api.recordingStreamUrl(recording.id, true)
      const token = localStorage.getItem('lanceon_token')
      const response = await fetch(url, {
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      })
      if (!response.ok) throw new Error('Nao foi possivel baixar o video.')
      const blob = await response.blob()
      const objectUrl = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = objectUrl
      anchor.download = `lance-${recording.id}.mp4`
      document.body.appendChild(anchor)
      anchor.click()
      anchor.remove()
      URL.revokeObjectURL(objectUrl)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha no download')
    } finally {
      setDownloading(false)
    }
  }

  if (loading) {
    return <p className="text-muted">Carregando player...</p>
  }

  if (!recording) {
    return (
      <div className="space-y-4">
        <p className="text-danger">{error || 'Video nao encontrado.'}</p>
        <Link to="/app/gravacoes" className="text-grass hover:underline">
          Voltar
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => history.back()}
            className="rounded-lg border border-line p-2 text-muted hover:text-white"
          >
            <ArrowLeft className="h-4 w-4" />
          </button>
          <div>
            <h1 className="text-xl font-bold">
              Camera {recording.camera_index}
              {recording.court_name ? ` · ${recording.court_name}` : ''}
            </h1>
            <p className="text-sm text-muted">
              {formatDateTime(recording.triggered_at)} · {remainingLabel(recording.expires_at)}
            </p>
          </div>
        </div>
        <Button
          variant="outline"
          onClick={() => void handleDownload()}
          disabled={downloading}
          className="px-4 py-2"
        >
          <Download className="h-4 w-4" />
          {downloading ? 'Baixando...' : 'Download'}
        </Button>
      </div>

      {error ? <p className="text-sm text-danger">{error}</p> : null}

      <div className="grid gap-6 lg:grid-cols-[1.6fr_0.8fr]">
        <div className="overflow-hidden rounded-2xl border border-line bg-black">
          <video
            key={streamUrl}
            src={streamUrl}
            controls
            playsInline
            className="aspect-video w-full bg-black"
          />
        </div>

        <div className="space-y-3">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-muted">
            Outras cameras
          </h2>
          {others.length === 0 ? (
            <p className="rounded-2xl border border-line bg-card p-4 text-sm text-muted">
              Nenhuma outra camera neste momento.
            </p>
          ) : (
            others.map((item) => (
              <Link
                key={item.id}
                to={`/app/video/${item.id}`}
                state={{ recordings: [recording, ...others, item] }}
                className="flex items-center gap-3 rounded-2xl border border-line bg-card p-3 transition hover:border-grass/40"
              >
                <span className="grid h-10 w-10 place-items-center rounded-lg bg-grass/15 text-grass">
                  <Play className="h-4 w-4 fill-current" />
                </span>
                <div>
                  <div className="text-sm font-semibold">Camera {item.camera_index}</div>
                  <div className="text-xs text-muted">{formatDateTime(item.triggered_at)}</div>
                </div>
              </Link>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
