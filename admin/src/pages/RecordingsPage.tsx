import { useEffect, useState } from 'react'
import { Download, Eye, Search, Trash2 } from 'lucide-react'
import { api } from '../api/client'
import { PageHeader } from '../components/PageHeader'
import { PaginationBar } from '../components/PaginationBar'
import { LoadingState } from '../components/shared'
import { RecordingThumb, StatusBadge } from '../components/ui'
import { useToast } from '../context/ToastContext'
import { usePagination } from '../hooks/usePagination'
import type { Court, Recording } from '../types'
import { downloadCsv, formatDateTime, formatDuration } from '../utils/helpers'

export function RecordingsPage() {
  const { showToast } = useToast()
  const [recordings, setRecordings] = useState<Recording[]>([])
  const [courts, setCourts] = useState<Court[]>([])
  const [courtFilter, setCourtFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState<'available' | 'expired' | 'all'>('all')
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)

  async function loadData() {
    const courtId = courtFilter ? Number(courtFilter) : undefined
    const [recordingData, courtData] = await Promise.all([
      api.recordings(courtId, statusFilter),
      api.courts(),
    ])
    setRecordings(recordingData)
    setCourts(courtData)
  }

  useEffect(() => {
    loadData()
      .catch((err) => showToast(err.message, 'error'))
      .finally(() => setLoading(false))
  }, [courtFilter, statusFilter])

  async function handleDelete(recordingId: number) {
    if (!window.confirm('Excluir esta gravacao?')) return
    try {
      const response = await api.deleteRecording(recordingId)
      showToast(response.message, 'success')
      await loadData()
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Erro ao excluir', 'error')
    }
  }

  function handleExport() {
    downloadCsv(
      `gravacoes-${new Date().toISOString().slice(0, 10)}.csv`,
      ['ID', 'Quadra', 'Camera', 'Data', 'Duracao', 'Status'],
      filtered.map((recording) => [
        String(recording.id),
        recording.court_name ?? '',
        String(recording.camera_index),
        formatDateTime(recording.triggered_at),
        formatDuration(recording.duration_seconds),
        recording.status ?? 'available',
      ]),
    )
    showToast('Gravacoes exportadas', 'success')
  }

  const filtered = recordings.filter((recording) => {
    const term = search.toLowerCase()
    return (
      String(recording.id).includes(term) ||
      (recording.court_name ?? '').toLowerCase().includes(term)
    )
  })
  const pagination = usePagination(
    filtered,
    6,
    `${search}|${courtFilter}|${statusFilter}`,
  )

  if (loading) return <LoadingState />

  return (
    <section className="page animate-fade">
      <PageHeader title="Gravacoes" subtitle="Visualize e gerencie os lances disponiveis.">
        <button type="button" className="btn btn-outline" onClick={handleExport}>
          Exportar
        </button>
      </PageHeader>

      <div className="toolbar filters-row">
        <label className="search-field">
          <Search size={16} />
          <input
            placeholder="Buscar gravacao..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </label>
        <select value={courtFilter} onChange={(e) => setCourtFilter(e.target.value)}>
          <option value="">Todas as Quadras</option>
          {courts.map((court) => (
            <option key={court.id} value={court.id}>
              {court.name}
            </option>
          ))}
        </select>
        <select
          value={statusFilter}
          onChange={(e) =>
            setStatusFilter(e.target.value as 'available' | 'expired' | 'all')
          }
        >
          <option value="all">Todos os Status</option>
          <option value="available">Disponivel</option>
          <option value="expired">Expirado</option>
        </select>
      </div>

      <div className="panel table-wrap hover-lift">
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Miniatura</th>
              <th>Quadra</th>
              <th>Camera</th>
              <th>Data e Hora</th>
              <th>Duracao</th>
              <th>Status</th>
              <th>Acoes</th>
            </tr>
          </thead>
          <tbody>
            {pagination.pageItems.length === 0 ? (
              <tr>
                <td colSpan={8} className="empty-cell">
                  Nenhuma gravacao encontrada
                </td>
              </tr>
            ) : (
              pagination.pageItems.map((recording) => (
                <tr key={recording.id} className="table-row-interactive">
                  <td>#{recording.id}</td>
                  <td>
                    <RecordingThumb duration={recording.duration_seconds} />
                  </td>
                  <td>{recording.court_name}</td>
                  <td>Camera {recording.camera_index}</td>
                  <td>{formatDateTime(recording.triggered_at)}</td>
                  <td>{formatDuration(recording.duration_seconds)}</td>
                  <td>
                    <StatusBadge
                      variant={recording.status === 'expired' ? 'danger' : 'success'}
                    >
                      {recording.status === 'expired' ? 'Expirado' : 'Disponivel'}
                    </StatusBadge>
                  </td>
                  <td>
                    <div className="icon-actions">
                      {recording.download_url && (
                        <a
                          className="icon-btn"
                          href={recording.download_url}
                          target="_blank"
                          rel="noreferrer"
                          title="Visualizar"
                        >
                          <Eye size={16} />
                        </a>
                      )}
                      {recording.download_url && (
                        <a
                          className="icon-btn"
                          href={recording.download_url}
                          download
                          title="Download"
                        >
                          <Download size={16} />
                        </a>
                      )}
                      <button
                        type="button"
                        className="icon-btn danger"
                        title="Excluir"
                        onClick={() => handleDelete(recording.id)}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
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
          label="gravacoes"
        />
      </div>
    </section>
  )
}
