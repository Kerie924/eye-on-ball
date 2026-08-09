import { useEffect, useState } from 'react'
import { RefreshCw, Search } from 'lucide-react'
import { api } from '../api/client'
import { PageHeader } from '../components/PageHeader'
import { PaginationBar } from '../components/PaginationBar'
import { LoadingState } from '../components/shared'
import { StatusBadge } from '../components/ui'
import { useToast } from '../context/ToastContext'
import { usePagination } from '../hooks/usePagination'
import type { Court, Device } from '../types'
import { formatDateTime } from '../utils/helpers'

interface DeviceRow extends Device {
  court_name: string
}

export function DevicesPage() {
  const { showToast } = useToast()
  const [devices, setDevices] = useState<DeviceRow[]>([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  async function loadDevices() {
    const courts: Court[] = await api.courts()
    const rows = await Promise.all(
      courts.map(async (court) => {
        const courtDevices = await api.courtDevices(court.id)
        return courtDevices.map((device) => ({
          ...device,
          court_name: court.name,
        }))
      }),
    )
    setDevices(rows.flat())
  }

  useEffect(() => {
    loadDevices()
      .catch((err) => showToast(err.message, 'error'))
      .finally(() => setLoading(false))
  }, [])

  async function handleRefresh() {
    setRefreshing(true)
    try {
      await loadDevices()
      showToast('Dispositivos atualizados', 'success')
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Erro ao atualizar', 'error')
    } finally {
      setRefreshing(false)
    }
  }

  const filtered = devices.filter(
    (device) =>
      device.name.toLowerCase().includes(search.toLowerCase()) ||
      device.court_name.toLowerCase().includes(search.toLowerCase()),
  )
  const pagination = usePagination(filtered, 6, search)

  if (loading) return <LoadingState />

  return (
    <section className="page animate-fade">
      <PageHeader title="Dispositivos" subtitle="Monitore cameras e mini PCs das quadras.">
        <button
          type="button"
          className="btn btn-outline"
          onClick={handleRefresh}
          disabled={refreshing}
        >
          <RefreshCw size={16} className={refreshing ? 'spin' : ''} />
          Atualizar
        </button>
      </PageHeader>

      <div className="toolbar">
        <label className="search-field">
          <Search size={16} />
          <input
            placeholder="Buscar dispositivo..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </label>
      </div>

      <div className="panel table-wrap hover-lift">
        <table className="data-table">
          <thead>
            <tr>
              <th>Nome do Dispositivo</th>
              <th>Quadra</th>
              <th>Tipo</th>
              <th>Status</th>
              <th>Ultima Conexao</th>
            </tr>
          </thead>
          <tbody>
            {pagination.pageItems.length === 0 ? (
              <tr>
                <td colSpan={5} className="empty-cell">
                  Nenhum dispositivo encontrado
                </td>
              </tr>
            ) : (
              pagination.pageItems.map((device) => (
                <tr key={device.id} className="table-row-interactive">
                  <td>{device.name}</td>
                  <td>{device.court_name}</td>
                  <td>Camera</td>
                  <td>
                    <StatusBadge variant={device.is_online ? 'online' : 'offline'}>
                      {device.is_online ? 'Online' : 'Offline'}
                    </StatusBadge>
                  </td>
                  <td>
                    {device.last_heartbeat
                      ? formatDateTime(device.last_heartbeat)
                      : '-'}
                  </td>
                </tr>
              ))
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
          label="dispositivos"
        />
      </div>
    </section>
  )
}
