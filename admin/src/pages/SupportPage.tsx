import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { PageHeader } from '../components/PageHeader'
import { LoadingState } from '../components/shared'

export function SupportPage() {
  const [supportEmail, setSupportEmail] = useState('suporte@olhonolance.com.br')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.settings()
      .then((settings) => setSupportEmail(settings.support_email))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingState />

  return (
    <section className="page animate-fade">
      <PageHeader title="Suporte" subtitle="Central de ajuda e contato." />
      <div className="panel support-panel hover-lift">
        <h2>Precisa de ajuda?</h2>
        <p>Entre em contato com a equipe tecnica para suporte da plataforma Olho no Lance.</p>
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
    </section>
  )
}
