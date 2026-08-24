import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { PageHeader } from '../components/PageHeader'
import { LoadingState } from '../components/shared'
import { useToast } from '../context/ToastContext'
import type { FeedbackReport } from '../types'

export function SupportPage() {
  const { showToast } = useToast()
  const [supportEmail, setSupportEmail] = useState('suporte@lanceon.com.br')
  const [reports, setReports] = useState<FeedbackReport[]>([])
  const [loading, setLoading] = useState(true)

  async function load() {
    try {
      const [settings, items] = await Promise.all([api.settings(), api.feedbackReports()])
      setSupportEmail(settings.support_email)
      setReports(items)
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Erro ao carregar relatos', 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  async function markRead(reportId: number) {
    try {
      const updated = await api.markFeedbackRead(reportId)
      setReports((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      )
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Erro ao atualizar', 'error')
    }
  }

  if (loading) return <LoadingState />

  return (
    <section className="page animate-fade">
      <PageHeader
        title="Suporte"
        subtitle="Relatos enviados pelo app e contato da equipe."
      />
      <div className="panel support-panel hover-lift">
        <h2>Precisa de ajuda?</h2>
        <p>Os atletas enviam relatos pela aba Reportar no aplicativo.</p>
        <ul>
          <li>
            E-mail:{' '}
            <a href={`mailto:${supportEmail}`} className="link-accent">
              {supportEmail}
            </a>
          </li>
          <li>Horario: Segunda a Sexta, 9h as 18h</li>
        </ul>
      </div>

      <div className="feedback-list">
        {reports.length === 0 ? (
          <div className="panel empty-panel">
            <h2>Nenhum relato ainda</h2>
            <p>Quando um usuario enviar um erro pelo app, ele aparece aqui.</p>
          </div>
        ) : (
          reports.map((report) => (
            <article key={report.id} className="panel feedback-card">
              <div className="feedback-card-head">
                <div>
                  <strong>{report.user_name ?? 'Usuario'}</strong>
                  <p>{report.user_email}</p>
                </div>
                <span className={`feedback-status ${report.status}`}>
                  {report.status === 'new' ? 'Novo' : 'Lido'}
                </span>
              </div>
              <p className="feedback-message">{report.message}</p>
              {report.images.length > 0 ? (
                <div className="feedback-thumbs">
                  {report.images.map((image) => (
                    <a
                      key={image.id}
                      href={image.url}
                      target="_blank"
                      rel="noreferrer"
                      title="Abrir foto"
                    >
                      <img src={image.url} alt={`Foto do relato ${report.id}`} />
                    </a>
                  ))}
                </div>
              ) : null}
              <div className="feedback-card-foot">
                <span>
                  {new Date(report.created_at).toLocaleString('pt-BR')}
                </span>
                {report.status === 'new' ? (
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={() => void markRead(report.id)}
                  >
                    Marcar como lido
                  </button>
                ) : null}
              </div>
            </article>
          ))
        )}
      </div>
    </section>
  )
}
