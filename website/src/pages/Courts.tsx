import { useEffect, useMemo, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { ArrowLeft, ChevronRight, Search } from 'lucide-react'

import { ApiError, api } from '../api/client'
import type { Court } from '../types'
import netCourt from '../assets/bg_court_net.jpg'
import { Badge } from '../components/Badge'

export function CourtsPage() {
  const { cityId } = useParams()
  const location = useLocation()
  const cityName = (location.state as { cityName?: string } | null)?.cityName
  const numericId = Number(cityId)

  const [courts, setCourts] = useState<Court[]>([])
  const [selected, setSelected] = useState<Court | null>(null)
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!Number.isFinite(numericId) || numericId <= 0) return
    let cancelled = false
    ;(async () => {
      setLoading(true)
      setError('')
      try {
        const data = await api.courts(numericId)
        if (!cancelled) {
          setCourts(data)
          setSelected(data[0] ?? null)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'Nao foi possivel carregar as quadras')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [numericId])

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase()
    if (!term) return courts
    return courts.filter(
      (court) =>
        court.name.toLowerCase().includes(term) ||
        (court.address ?? '').toLowerCase().includes(term),
    )
  }, [courts, search])

  return (
    <div className="space-y-6">
      <div className="flex items-start gap-3">
        <Link
          to="/app/cidades"
          className="mt-1 rounded-lg border border-line p-2 text-muted hover:text-white"
        >
          <ArrowLeft className="h-4 w-4" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold">Quadras</h1>
          <p className="mt-1 text-sm text-muted">
            {cityName ?? courts[0]?.city_name ?? `Cidade #${cityId}`}
          </p>
        </div>
      </div>

      <label className="flex items-center gap-3 rounded-xl border border-line bg-ink-soft px-4 py-3">
        <Search className="h-4 w-4 text-muted" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Buscar quadra"
          className="w-full bg-transparent text-sm outline-none placeholder:text-white/30"
        />
      </label>

      {loading ? <p className="text-muted">Carregando...</p> : null}
      {error ? <p className="text-sm text-danger">{error}</p> : null}

      <div className="grid gap-6 lg:grid-cols-[1fr_1.1fr]">
        <div className="space-y-2">
          {filtered.map((court) => (
            <button
              key={court.id}
              type="button"
              onClick={() => setSelected(court)}
              className={`flex w-full items-center justify-between rounded-2xl border px-4 py-4 text-left transition ${
                selected?.id === court.id
                  ? 'border-grass bg-grass/10'
                  : 'border-line bg-card hover:border-grass/40'
              }`}
            >
              <div>
                <div className="font-semibold">{court.name}</div>
                {court.address ? (
                  <div className="mt-1 text-sm text-muted">{court.address}</div>
                ) : null}
              </div>
              <ChevronRight className="h-4 w-4 text-muted" />
            </button>
          ))}
          {!loading && filtered.length === 0 ? (
            <p className="rounded-2xl border border-line bg-card p-6 text-sm text-muted">
              Nenhuma quadra nesta cidade.
            </p>
          ) : null}
        </div>

        {selected ? (
          <div className="rounded-2xl border border-line bg-card p-6">
            <div className="aspect-video overflow-hidden rounded-xl">
              <img src={netCourt} alt="" className="h-full w-full object-cover" />
            </div>
            <h2 className="mt-5 text-xl font-bold uppercase tracking-wide">{selected.name}</h2>
            {selected.address ? (
              <p className="mt-2 text-sm text-muted">{selected.address}</p>
            ) : null}
            <div className="mt-4 flex flex-wrap gap-2">
              <Badge>Grama sintetica</Badge>
              <Badge>Cameras Lance On</Badge>
              <Badge>Clips 30s</Badge>
            </div>
            <Link
              to={`/app/cidades/${cityId}/quadras/${selected.id}/horarios`}
              state={{
                cityName: cityName ?? selected.city_name,
                courtName: selected.name,
                courtAddress: selected.address,
              }}
              className="mt-6 inline-flex w-full items-center justify-center rounded-lg bg-grass px-5 py-3 text-sm font-semibold text-on-grass shadow-[0_0_24px_rgba(30,215,96,0.3)] transition hover:bg-grass-bright"
            >
              Selecionar quadra
            </Link>
          </div>
        ) : null}
      </div>
    </div>
  )
}
