import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { PageHeader } from '../components/PageHeader'
import { LoadingState } from '../components/shared'
import { StatCard } from '../components/StatCard'
import { useToast } from '../context/ToastContext'
import type { AdminStats } from '../types'
import { downloadCsv, storageTb } from '../utils/helpers'
import { Camera, Cloud, LayoutGrid, Users } from 'lucide-react'

export function ReportsPage() {
  const { showToast } = useToast()
  const [stats, setStats] = useState<AdminStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.stats()
      .then(setStats)
      .catch((err) => showToast(err.message, 'error'))
      .finally(() => setLoading(false))
  }, [])

  async function exportFullReport() {
    try {
      const [recordings, users, courts] = await Promise.all([
        api.recordings(undefined, 'all'),
        api.users(),
        api.courts(),
      ])

      downloadCsv(
        `relatorio-completo-${new Date().toISOString().slice(0, 10)}.csv`,
        ['Secao', 'Item', 'Detalhe', 'Valor', 'Data'],
        [
          ...recordings.map((item) => [
            'Gravacao',
            item.court_name ?? '',
            `#${item.id}`,
            item.status ?? '',
            new Date(item.triggered_at).toLocaleString('pt-BR'),
          ]),
          ...users.map((item) => [
            'Usuario',
            item.full_name,
            item.email,
            item.role,
            new Date(item.created_at).toLocaleDateString('pt-BR'),
          ]),
          ...courts.map((item) => [
            'Quadra',
            item.name,
            item.address ?? '',
            item.is_active ? 'Ativa' : 'Inativa',
            new Date(item.created_at).toLocaleDateString('pt-BR'),
          ]),
        ],
      )
      showToast('Relatorio completo exportado', 'success')
    } catch {
      showToast('Erro ao exportar relatorio', 'error')
    }
  }

  if (loading || !stats) return <LoadingState />

  return (
    <section className="page animate-fade">
      <PageHeader title="Relatorios" subtitle="Resumo e exportacao de dados da plataforma.">
        <button type="button" className="btn btn-primary" onClick={exportFullReport}>
          Exportar Relatorio Completo
        </button>
      </PageHeader>

      <div className="stats-grid stats-grid-4">
        <StatCard
          label="Quadras"
          value={stats.courts}
          hint={`${stats.courts_online} online`}
          icon={<LayoutGrid size={22} />}
          tone="green"
        />
        <StatCard
          label="Gravacoes"
          value={stats.recordings}
          hint={`${stats.recordings_today} hoje`}
          icon={<Camera size={22} />}
          tone="purple"
        />
        <StatCard
          label="Usuarios"
          value={stats.users}
          hint={`${stats.active_users} ativos`}
          icon={<Users size={22} />}
          tone="yellow"
        />
        <StatCard
          label="Armazenamento"
          value={`${storageTb(stats.storage_used_gb)} TB`}
          hint={`de ${stats.storage_limit_tb} TB`}
          icon={<Cloud size={22} />}
          tone="blue"
        />
      </div>

      <div className="panel hover-lift">
        <h2>Resumo operacional</h2>
        <ul className="report-list">
          <li>Solicitacoes pendentes: {stats.pending_access_requests}</li>
          <li>Olheiros pendentes: {stats.pending_scouts}</li>
          <li>Dispositivos online: {stats.devices_online}</li>
          <li>Dispositivos offline: {stats.devices_offline}</li>
        </ul>
      </div>
    </section>
  )
}
