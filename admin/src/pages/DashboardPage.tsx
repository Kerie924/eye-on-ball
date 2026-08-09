import { useEffect, useState } from 'react'
import { Camera, Cloud, LayoutGrid, Users } from 'lucide-react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { PageHeader } from '../components/PageHeader'
import { LoadingState } from '../components/shared'
import { StatCard } from '../components/StatCard'
import { RecordingThumb, StatusBadge } from '../components/ui'
import type { ActivityItem, AdminStats, Recording } from '../types'
import { formatDateTime, formatDuration, storageTb } from '../utils/helpers'

const dayLabels = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sab']

export function DashboardPage() {
  const [stats, setStats] = useState<AdminStats | null>(null)
  const [activity, setActivity] = useState<ActivityItem[]>([])
  const [recordings, setRecordings] = useState<Recording[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      api.stats(),
      api.activity(),
      api.recordings(undefined, 'available'),
    ])
      .then(([statsData, activityData, recordingsData]) => {
        setStats(statsData)
        setActivity(activityData)
        setRecordings(recordingsData.slice(0, 5))
      })
      .catch((err) => setError(err.message))
  }, [])

  if (error) {
    return <p className="error-text">{error}</p>
  }

  if (!stats) {
    return <LoadingState label="Carregando painel..." />
  }

  const chartPoints = stats.recordings_by_day
  const chartMax = Math.max(...chartPoints.map((point) => point.count), 1)
  const storagePercent = Math.min(
    Math.round((stats.storage_used_gb / stats.storage_limit_gb) * 100),
    100,
  )

  return (
    <section className="page animate-fade">
      <PageHeader title="Dashboard" subtitle="Visao geral da plataforma." />

      <div className="stats-grid stats-grid-4">
        <StatCard
          label="Quadras Ativas"
          value={stats.courts}
          hint={`${stats.courts_online} online agora`}
          icon={<LayoutGrid size={22} />}
          tone="green"
        />
        <StatCard
          label="Gravacoes Hoje"
          value={stats.recordings_today}
          hint={`${stats.recordings} no total`}
          icon={<Camera size={22} />}
          tone="purple"
        />
        <StatCard
          label="Usuarios Ativos"
          value={stats.active_users}
          hint={`${stats.users} cadastrados`}
          icon={<Users size={22} />}
          tone="yellow"
        />
        <StatCard
          label="Armazenamento Usado"
          value={`${storageTb(stats.storage_used_gb)} TB`}
          hint={`de ${stats.storage_limit_tb} TB`}
          icon={<Cloud size={22} />}
          tone="blue"
        />
      </div>

      <div className="dashboard-grid">
        <article className="panel panel-chart hover-lift">
          <div className="panel-title-row">
            <h2>Gravacoes por Dia</h2>
          </div>
          <div className="line-chart">
            {chartPoints.map((point) => {
              const day = new Date(point.date)
              return (
                <div key={point.date} className="line-chart-bar-wrap">
                  <div
                    className="line-chart-bar"
                    style={{ height: `${(point.count / chartMax) * 100}%` }}
                    title={`${point.count} gravacoes`}
                  />
                  <span>{dayLabels[day.getDay()]}</span>
                </div>
              )
            })}
          </div>
        </article>

        <article className="panel hover-lift">
          <div className="panel-title-row">
            <h2>Atividade Recente</h2>
          </div>
          <ul className="activity-list">
            {activity.length === 0 ? (
              <li>Nenhuma atividade recente</li>
            ) : (
              activity.map((item) => (
                <li key={`${item.kind}-${item.created_at}-${item.message}`}>
                  <span>{item.message}</span>
                  <time>{formatDateTime(item.created_at)}</time>
                </li>
              ))
            )}
          </ul>
        </article>

        <article className="panel hover-lift">
          <div className="panel-title-row">
            <h2>Status das Quadras</h2>
          </div>
          <div className="status-summary">
            <div>
              <strong>{stats.courts_online}</strong>
              <StatusBadge variant="online">Online</StatusBadge>
            </div>
            <div>
              <strong>{stats.courts_offline}</strong>
              <StatusBadge variant="offline">Offline</StatusBadge>
            </div>
            <div>
              <strong>0</strong>
              <StatusBadge variant="warning">Manutencao</StatusBadge>
            </div>
          </div>
          <ul className="court-status-list">
            {stats.court_status.map((court) => (
              <li key={court.id}>
                <span>{court.name}</span>
                <StatusBadge variant={court.online ? 'online' : 'offline'}>
                  {court.online ? 'Online' : 'Offline'}
                </StatusBadge>
              </li>
            ))}
          </ul>
        </article>
      </div>

      <div className="dashboard-grid dashboard-grid-bottom">
        <article className="panel storage-panel hover-lift">
          <div className="panel-title-row">
            <h2>Armazenamento</h2>
          </div>
          <div className="donut-chart">
            <div
              className="donut-chart-ring"
              style={{
                background: `conic-gradient(var(--grass) 0 ${storagePercent}%, var(--grass-mist) 0)`,
              }}
            >
              <div className="donut-chart-hole">
                <strong>{storagePercent}%</strong>
              </div>
            </div>
          </div>
          <p>
            {storageTb(stats.storage_used_gb)} TB usados ·{' '}
            {(stats.storage_limit_tb - Number(storageTb(stats.storage_used_gb))).toFixed(2)}{' '}
            TB livres
          </p>
        </article>

        <article className="panel panel-wide hover-lift">
          <div className="panel-title-row">
            <h2>Gravacoes Recentes</h2>
            <Link to="/gravacoes" className="link-muted">
              Ver todas
            </Link>
          </div>
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Miniatura</th>
                  <th>Quadra</th>
                  <th>Data</th>
                  <th>Duracao</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {recordings.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="empty-cell">
                      Nenhuma gravacao recente
                    </td>
                  </tr>
                ) : (
                  recordings.map((recording) => (
                    <tr key={recording.id} className="table-row-interactive">
                      <td>#{recording.id}</td>
                      <td>
                        <RecordingThumb duration={recording.duration_seconds} />
                      </td>
                      <td>{recording.court_name}</td>
                      <td>{formatDateTime(recording.triggered_at)}</td>
                      <td>{formatDuration(recording.duration_seconds)}</td>
                      <td>
                        <StatusBadge variant="success">Disponivel</StatusBadge>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </article>

        <article className="panel hover-lift">
          <div className="panel-title-row">
            <h2>Dispositivos</h2>
            <Link to="/dispositivos" className="link-muted">
              Ver todos
            </Link>
          </div>
          <p className="devices-summary">
            <strong>{stats.devices_total}</strong> dispositivos conectados
          </p>
          <div className="progress-bar">
            <span
              className="progress-bar-fill online"
              style={{
                width: `${
                  stats.devices_total
                    ? (stats.devices_online / stats.devices_total) * 100
                    : 0
                }%`,
              }}
            />
          </div>
          <div className="device-legend">
            <span>
              <i className="dot online" /> {stats.devices_online} Online
            </span>
            <span>
              <i className="dot offline" /> {stats.devices_offline} Offline
            </span>
          </div>
        </article>
      </div>
    </section>
  )
}
