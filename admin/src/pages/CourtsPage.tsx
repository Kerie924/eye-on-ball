import { useEffect, useState, type FormEvent } from 'react'
import { Copy, Pencil, Plus, Radio, Search, Trash2 } from 'lucide-react'
import { api } from '../api/client'
import { PageHeader } from '../components/PageHeader'
import { PaginationBar } from '../components/PaginationBar'
import { LoadingState, Modal } from '../components/shared'
import { CourtThumb, StatusBadge } from '../components/ui'
import { useToast } from '../context/ToastContext'
import { usePagination } from '../hooks/usePagination'
import type { City, Court, Device } from '../types'
import { formatDateTime } from '../utils/helpers'

type TabKey = 'courts' | 'cities'

export function CourtsPage() {
  const { showToast } = useToast()
  const [tab, setTab] = useState<TabKey>('courts')
  const [courts, setCourts] = useState<Court[]>([])
  const [cities, setCities] = useState<City[]>([])
  const [devicesByCourt, setDevicesByCourt] = useState<Record<number, Device[]>>({})
  const [search, setSearch] = useState('')
  const [cityFilter, setCityFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [modalMode, setModalMode] = useState<'create' | 'edit' | null>(null)
  const [editingCourt, setEditingCourt] = useState<Court | null>(null)
  const [name, setName] = useState('')
  const [address, setAddress] = useState('')
  const [cityId, setCityId] = useState('')
  const [cameraCount, setCameraCount] = useState(2)
  const [submitting, setSubmitting] = useState(false)
  const [triggeringId, setTriggeringId] = useState<number | null>(null)

  const [cityModal, setCityModal] = useState<'create' | 'edit' | null>(null)
  const [editingCity, setEditingCity] = useState<City | null>(null)
  const [cityName, setCityName] = useState('')

  async function loadData() {
    const [courtData, cityData] = await Promise.all([
      api.courts(),
      api.cities(true),
    ])
    setCourts(courtData)
    setCities(cityData)
    const deviceEntries = await Promise.all(
      courtData.map(async (court) => [court.id, await api.courtDevices(court.id)] as const),
    )
    setDevicesByCourt(Object.fromEntries(deviceEntries))
  }

  useEffect(() => {
    loadData()
      .catch((err) => showToast(err.message, 'error'))
      .finally(() => setLoading(false))
  }, [])

  function openCreate() {
    setEditingCourt(null)
    setName('')
    setAddress('')
    setCityId(cityFilter || String(cities.find((c) => c.is_active)?.id ?? ''))
    setCameraCount(2)
    setModalMode('create')
  }

  function openEdit(court: Court) {
    setEditingCourt(court)
    setName(court.name)
    setAddress(court.address ?? '')
    setCityId(court.city_id ? String(court.city_id) : '')
    setCameraCount(devicesByCourt[court.id]?.length || 2)
    setModalMode('edit')
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!cityId) {
      showToast('Selecione a cidade', 'error')
      return
    }
    setSubmitting(true)
    try {
      if (modalMode === 'create') {
        await api.createCourt(name.trim(), address.trim(), cameraCount, Number(cityId))
        showToast('Quadra criada com sucesso', 'success')
      } else if (editingCourt) {
        await api.updateCourt(editingCourt.id, {
          name: name.trim(),
          address: address.trim() || null,
          camera_count: cameraCount,
          city_id: Number(cityId),
        })
        showToast('Quadra atualizada com sucesso', 'success')
      }
      setModalMode(null)
      await loadData()
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Erro ao salvar quadra', 'error')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleRotateKey(court: Court) {
    try {
      const updated = await api.rotateCourtKey(court.id)
      await navigator.clipboard.writeText(updated.device_api_key ?? '')
      showToast('Nova chave gerada e copiada', 'success')
      await loadData()
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Erro ao gerar chave', 'error')
    }
  }

  async function handleTrigger(court: Court) {
    if (triggeringId != null) return
    setTriggeringId(court.id)
    try {
      const result = await api.triggerCapture(court.id)
      showToast(result.message, result.device_online ? 'success' : 'error')
      await loadData()
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Erro ao disparar gravacao', 'error')
    } finally {
      setTriggeringId(null)
    }
  }

  async function handleDeactivate(court: Court) {
    if (!window.confirm(`Desativar a quadra ${court.name}?`)) return
    try {
      await api.deactivateCourt(court.id)
      showToast('Quadra desativada', 'success')
      await loadData()
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Erro ao desativar', 'error')
    }
  }

  async function handleCitySubmit(event: FormEvent) {
    event.preventDefault()
    setSubmitting(true)
    try {
      if (cityModal === 'create') {
        await api.createCity(cityName.trim())
        showToast('Cidade criada com sucesso', 'success')
      } else if (editingCity) {
        await api.updateCity(editingCity.id, { name: cityName.trim() })
        showToast('Cidade atualizada com sucesso', 'success')
      }
      setCityModal(null)
      await loadData()
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Erro ao salvar cidade', 'error')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDeactivateCity(city: City) {
    if (!window.confirm(`Desativar a cidade ${city.name}?`)) return
    try {
      await api.deactivateCity(city.id)
      showToast('Cidade desativada', 'success')
      await loadData()
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Erro ao desativar', 'error')
    }
  }

  const filteredCourts = courts.filter((court) => {
    const term = search.toLowerCase()
    const matchesTerm =
      court.name.toLowerCase().includes(term) ||
      (court.address ?? '').toLowerCase().includes(term) ||
      (court.city_name ?? '').toLowerCase().includes(term)
    const matchesCity = cityFilter ? String(court.city_id) === cityFilter : true
    return matchesTerm && matchesCity
  })
  const courtPagination = usePagination(filteredCourts, 6, `${search}|${cityFilter}`)

  const filteredCities = cities.filter((city) =>
    city.name.toLowerCase().includes(search.toLowerCase()),
  )
  const cityPagination = usePagination(filteredCities, 8, `${search}|cities`)

  if (loading) return <LoadingState />

  return (
    <section className="page animate-fade">
      <PageHeader
        title="Quadras e cidades"
        subtitle="Cadastre cidades e, em cada uma, as quadras da plataforma."
      >
        {tab === 'courts' ? (
          <button type="button" className="btn btn-primary" onClick={openCreate}>
            <Plus size={16} />
            Nova Quadra
          </button>
        ) : (
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => {
              setEditingCity(null)
              setCityName('')
              setCityModal('create')
            }}
          >
            <Plus size={16} />
            Nova Cidade
          </button>
        )}
      </PageHeader>

      <div className="tabs">
        {(
          [
            ['courts', `Quadras (${courts.length})`],
            ['cities', `Cidades (${cities.filter((c) => c.is_active).length})`],
          ] as const
        ).map(([key, label]) => (
          <button
            key={key}
            type="button"
            className={tab === key ? 'tab active' : 'tab'}
            onClick={() => {
              setTab(key)
              setSearch('')
            }}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="toolbar filters-row">
        <label className="search-field">
          <Search size={16} />
          <input
            placeholder={tab === 'courts' ? 'Buscar quadra...' : 'Buscar cidade...'}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </label>
        {tab === 'courts' ? (
          <select value={cityFilter} onChange={(e) => setCityFilter(e.target.value)}>
            <option value="">Todas as cidades</option>
            {cities
              .filter((city) => city.is_active)
              .map((city) => (
                <option key={city.id} value={city.id}>
                  {city.name}
                </option>
              ))}
          </select>
        ) : null}
      </div>

      {tab === 'cities' ? (
        <div className="panel table-wrap hover-lift">
          <table className="data-table">
            <thead>
              <tr>
                <th>Cidade</th>
                <th>Quadras</th>
                <th>Status</th>
                <th>Acoes</th>
              </tr>
            </thead>
            <tbody>
              {cityPagination.pageItems.length === 0 ? (
                <tr>
                  <td colSpan={4} className="empty-cell">
                    Nenhuma cidade encontrada
                  </td>
                </tr>
              ) : (
                cityPagination.pageItems.map((city) => (
                  <tr key={city.id}>
                    <td>
                      <strong>{city.name}</strong>
                    </td>
                    <td>{city.court_count}</td>
                    <td>
                      <StatusBadge variant={city.is_active ? 'success' : 'danger'}>
                        {city.is_active ? 'Ativa' : 'Inativa'}
                      </StatusBadge>
                    </td>
                    <td>
                      <div className="icon-actions">
                        <button
                          type="button"
                          className="icon-btn"
                          title="Editar"
                          onClick={() => {
                            setEditingCity(city)
                            setCityName(city.name)
                            setCityModal('edit')
                          }}
                        >
                          <Pencil size={16} />
                        </button>
                        {city.is_active ? (
                          <button
                            type="button"
                            className="icon-btn danger"
                            title="Desativar"
                            onClick={() => handleDeactivateCity(city)}
                          >
                            <Trash2 size={16} />
                          </button>
                        ) : null}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
          <PaginationBar
            from={cityPagination.from}
            to={cityPagination.to}
            total={cityPagination.total}
            page={cityPagination.page}
            totalPages={cityPagination.totalPages}
            onPageChange={cityPagination.setPage}
            label="cidades"
          />
        </div>
      ) : (
        <div className="panel table-wrap hover-lift">
          <table className="data-table">
            <thead>
              <tr>
                <th>Nome da Quadra</th>
                <th>Cidade</th>
                <th>Localizacao</th>
                <th>Status</th>
                <th>Dispositivos</th>
                <th>Ultima Conexao</th>
                <th>Acoes</th>
              </tr>
            </thead>
            <tbody>
              {courtPagination.pageItems.length === 0 ? (
                <tr>
                  <td colSpan={7} className="empty-cell">
                    Nenhuma quadra encontrada
                  </td>
                </tr>
              ) : (
                courtPagination.pageItems.map((court) => {
                  const devices = devicesByCourt[court.id] ?? []
                  const online = devices.some((device) => device.is_online)
                  const lastHeartbeat = devices
                    .map((device) => device.last_heartbeat)
                    .filter(Boolean)
                    .sort()
                    .pop()
                  const isTriggering = triggeringId === court.id

                  return (
                    <tr key={court.id} className="table-row-interactive">
                      <td>
                        <div className="table-user">
                          <CourtThumb name={court.name} />
                          <div>
                            <strong>{court.name}</strong>
                            <span>ID #{court.id}</span>
                          </div>
                        </div>
                      </td>
                      <td>{court.city_name || '-'}</td>
                      <td>{court.address || '-'}</td>
                      <td>
                        <StatusBadge variant={online ? 'online' : 'offline'}>
                          {online ? 'Online' : 'Offline'}
                        </StatusBadge>
                      </td>
                      <td>{devices.length} cameras</td>
                      <td>{lastHeartbeat ? formatDateTime(lastHeartbeat) : '-'}</td>
                      <td>
                        <div className="icon-actions">
                          <button
                            type="button"
                            className="icon-btn trigger-btn"
                            title="Gravar lance (PRONTO)"
                            disabled={triggeringId != null}
                            onClick={() => handleTrigger(court)}
                          >
                            <Radio size={16} className={isTriggering ? 'spin' : undefined} />
                          </button>
                          <button
                            type="button"
                            className="icon-btn"
                            title="Editar"
                            onClick={() => openEdit(court)}
                          >
                            <Pencil size={16} />
                          </button>
                          <button
                            type="button"
                            className="icon-btn"
                            title="Copiar chave"
                            onClick={() => handleRotateKey(court)}
                          >
                            <Copy size={16} />
                          </button>
                          <button
                            type="button"
                            className="icon-btn danger"
                            title="Desativar"
                            onClick={() => handleDeactivate(court)}
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
          <PaginationBar
            from={courtPagination.from}
            to={courtPagination.to}
            total={courtPagination.total}
            page={courtPagination.page}
            totalPages={courtPagination.totalPages}
            onPageChange={courtPagination.setPage}
            label="quadras"
          />
        </div>
      )}

      {modalMode && (
        <Modal
          title={modalMode === 'create' ? 'Nova Quadra' : 'Editar Quadra'}
          onClose={() => setModalMode(null)}
        >
          <form className="form-stack" onSubmit={handleSubmit}>
            <label>
              Cidade
              <select value={cityId} onChange={(e) => setCityId(e.target.value)} required>
                <option value="">Selecione</option>
                {cities
                  .filter((city) => city.is_active)
                  .map((city) => (
                    <option key={city.id} value={city.id}>
                      {city.name}
                    </option>
                  ))}
              </select>
            </label>
            <label>
              Nome
              <input value={name} onChange={(e) => setName(e.target.value)} required />
            </label>
            <label>
              Endereco
              <input value={address} onChange={(e) => setAddress(e.target.value)} />
            </label>
            <label>
              Cameras (1 a 6)
              <select
                value={cameraCount}
                onChange={(e) => setCameraCount(Number(e.target.value))}
              >
                {[1, 2, 3, 4, 5, 6].map((count) => (
                  <option key={count} value={count}>
                    {count} {count === 1 ? 'camera' : 'cameras'}
                  </option>
                ))}
              </select>
            </label>
            {editingCourt?.device_api_key && (
              <label>
                Chave do dispositivo
                <input value={editingCourt.device_api_key} readOnly />
              </label>
            )}
            <div className="modal-actions">
              <button type="button" className="btn btn-outline" onClick={() => setModalMode(null)}>
                Cancelar
              </button>
              <button type="submit" className="btn btn-primary" disabled={submitting}>
                {submitting ? 'Salvando...' : 'Salvar'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {cityModal && (
        <Modal
          title={cityModal === 'create' ? 'Nova Cidade' : 'Editar Cidade'}
          onClose={() => setCityModal(null)}
        >
          <form className="form-stack" onSubmit={handleCitySubmit}>
            <label>
              Nome
              <input value={cityName} onChange={(e) => setCityName(e.target.value)} required />
            </label>
            <div className="modal-actions">
              <button type="button" className="btn btn-outline" onClick={() => setCityModal(null)}>
                Cancelar
              </button>
              <button type="submit" className="btn btn-primary" disabled={submitting}>
                {submitting ? 'Salvando...' : 'Salvar'}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </section>
  )
}
