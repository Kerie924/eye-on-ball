import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronRight, Search } from 'lucide-react'

import { ApiError, api } from '../api/client'
import type { City } from '../types'

export function CitiesPage() {
  const [cities, setCities] = useState<City[]>([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      setLoading(true)
      setError('')
      try {
        const data = await api.cities()
        if (!cancelled) setCities(data)
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'Nao foi possivel carregar as cidades')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase()
    if (!term) return cities
    return cities.filter((city) => city.name.toLowerCase().includes(term))
  }, [cities, search])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Cidades</h1>
        <p className="mt-1 text-sm text-muted">
          Escolha a cidade, a quadra, a data e o horario para ver os videos.
        </p>
      </div>

      <label className="flex items-center gap-3 rounded-xl border border-line bg-ink-soft px-4 py-3">
        <Search className="h-4 w-4 text-muted" />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Buscar cidade"
          className="w-full bg-transparent text-sm outline-none placeholder:text-white/30"
        />
      </label>

      {loading ? <p className="text-muted">Carregando...</p> : null}
      {error ? <p className="text-sm text-danger">{error}</p> : null}

      {!loading && !error && filtered.length === 0 ? (
        <p className="rounded-2xl border border-line bg-card p-6 text-sm text-muted">
          {search ? 'Nenhuma cidade encontrada.' : 'Nenhuma cidade cadastrada.'}
        </p>
      ) : null}

      <div className="grid gap-3 sm:grid-cols-2">
        {filtered.map((city) => (
          <Link
            key={city.id}
            to={`/app/cidades/${city.id}`}
            state={{ cityName: city.name }}
            className="flex items-center justify-between rounded-2xl border border-line bg-card px-5 py-4 transition hover:border-grass/40"
          >
            <div>
              <div className="font-semibold">{city.name}</div>
              <div className="mt-1 text-sm text-muted">
                {city.court_count} {city.court_count === 1 ? 'quadra' : 'quadras'}
              </div>
            </div>
            <ChevronRight className="h-5 w-5 text-grass" />
          </Link>
        ))}
      </div>
    </div>
  )
}
