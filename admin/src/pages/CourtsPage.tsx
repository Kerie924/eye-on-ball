import { useEffect, useState, type FormEvent } from 'react'
import { Copy, Pencil, Plus, Radio, Search, Trash2 } from 'lucide-react'
import { api } from '../api/client'
import { PageHeader } from '../components/PageHeader'
import { PaginationBar } from '../components/PaginationBar'
import { LoadingState, Modal } from '../components/shared'
import { CourtThumb, StatusBadge } from '../components/ui'
import { useToast } from '../context/ToastContext'
import { usePagination } from '../hooks/usePagination'
import type { Court, Device } from '../types'
import { formatDateTime } from '../utils/helpers'

export function CourtsPage() {
  const { showToast } = useToast()
  const [courts, setCourts] = useState<Court[]>([])
  const [devicesByCourt, setDevicesByCourt] = useState<Record<number, Device[]>>({})
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [modalMode, setModalMode] = useState<'create' | 'edit' | null>(null)
  const [editingCourt, setEditingCourt] = useState<Court | null>(null)
  const [name, setName] = useState('')
  const [address, setAddress] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [triggeringId, setTriggeringId] = useState<number | null>(null)

  async function loadCourts() {
    const data = await api.courts()
    setCourts(data)
    const deviceEntries = await Promise.all(
      data.map(async (court) => [court.id, await api.courtDevices(court.id)] as const),
    )
    setDevicesByCourt(Object.fromEntries(deviceEntries))
  }

  useEffect(() => {
    loadCourts()
      .catch((err) => showToast(err.message, 'error'))
      .finally(() => setLoading(false))
  }, [])

  function openCreate() {
    setEditingCourt(null)
    setName('')
    setAddress('')
    setModalMode('create')
  }

  function openEdit(court: Court) {
    setEditingCourt(court)
    setName(court.name)
    setAddress(court.address ?? '')
    setModalMode('edit')
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setSubmitting(true)
    try {
      if (modalMode === 'create') {
        await api.createCourt(name.trim(), address.trim())
        showToast('Quadra criada com sucesso', 'success')
      } else if (editingCourt) {
        await api.updateCourt(editingCourt.id, {
          name: name.trim(),
          address: address.trim() || null,
        })
        showToast('Quadra atualizada com sucesso', 'success')
      }
      setModalMode(null)
      await loadCourts()
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
      await loadCourts()
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
      await loadCourts()
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
      await loadCourts()
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Erro ao desativar', 'error')
    }
  }

  const filtered = courts.filter(
    (court) =>
      court.name.toLowerCase().includes(search.toLowerCase()) ||
      (court.address ?? '').toLowerCase().includes(search.toLowerCase()),
  )
  const pagination = usePagination(filtered, 6, search)

  if (loading) return <LoadingState />

  return (
    <section className="page animate-fade">
      <PageHeader title="Quadras" subtitle="Gerencie as quadras cadastradas na plataforma.">
        <button type="button" className="btn btn-primary" onClick={openCreate}>
          <Plus size={16} />
          Nova Quadra
        </button>
      </PageHeader>

      <div className="toolbar">
        <label className="search-field">
          <Search size={16} />
          <input
            placeholder="Buscar quadra..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </label>
      </div>

      <div className="panel table-wrap hover-lift">
        <table className="data-table">
          <thead>
            <tr>
              <th>Nome da Quadra</th>
              <th>Localizacao</th>
              <th>Status</th>
              <th>Dispositivos</th>
              <th>Ultima Conexao</th>
              <th>Acoes</th>
            </tr>
          </thead>
          <tbody>
            {pagination.pageItems.length === 0 ? (
              <tr>
                <td colSpan={6} className="empty-cell">
                  Nenhuma quadra encontrada
                </td>
              </tr>
            ) : (
              pagination.pageItems.map((court) => {
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
          from={pagination.from}
          to={pagination.to}
          total={pagination.total}
          page={pagination.page}
          totalPages={pagination.totalPages}
          onPageChange={pagination.setPage}
          label="quadras"
        />
      </div>

      {modalMode && (
        <Modal
          title={modalMode === 'create' ? 'Nova Quadra' : 'Editar Quadra'}
          onClose={() => setModalMode(null)}
        >
          <form className="form-stack" onSubmit={handleSubmit}>
            <label>
              Nome
              <input value={name} onChange={(e) => setName(e.target.value)} required />
            </label>
            <label>
              Endereco
              <input value={address} onChange={(e) => setAddress(e.target.value)} />
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
    </section>
  )
}
