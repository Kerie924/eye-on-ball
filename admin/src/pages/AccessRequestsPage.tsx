import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { CourtAccessRequest } from '../types'

export function AccessRequestsPage() {
  const [requests, setRequests] = useState<CourtAccessRequest[]>([])
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  async function loadRequests() {
    const data = await api.accessRequests()
    setRequests(data)
  }

  useEffect(() => {
    loadRequests().catch((err) => setError(err.message))
  }, [])

  async function handleApprove(requestId: number) {
    try {
      const response = await api.approveAccessRequest(requestId)
      setMessage(response.message)
      await loadRequests()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao aprovar')
    }
  }

  async function handleReject(requestId: number) {
    try {
      const response = await api.rejectAccessRequest(requestId)
      setMessage(response.message)
      await loadRequests()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao rejeitar')
    }
  }

  return (
    <section>
      <header className="page-header">
        <div>
          <h1>Solicitacoes de acesso</h1>
          <p>Aprove ou rejeite pedidos de atletas para quadras</p>
        </div>
      </header>

      {message && <p className="success-text">{message}</p>}
      {error && <p className="error-text">{error}</p>}

      <div className="panel table-wrap">
        {requests.length === 0 ? (
          <p className="empty-state">Nenhuma solicitacao pendente.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Atleta</th>
                <th>E-mail</th>
                <th>Quadra</th>
                <th>Horario do jogo</th>
                <th>Solicitado em</th>
                <th>Acoes</th>
              </tr>
            </thead>
            <tbody>
              {requests.map((request) => (
                <tr key={request.id}>
                  <td>{request.user?.full_name}</td>
                  <td>{request.user?.email}</td>
                  <td>{request.court?.name}</td>
                  <td>
                    {request.play_started_at && request.play_ended_at
                      ? `${new Date(request.play_started_at).toLocaleString('pt-BR', {
                          dateStyle: 'short',
                          timeStyle: 'short',
                        })} – ${new Date(request.play_ended_at).toLocaleTimeString('pt-BR', {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}`
                      : '—'}
                  </td>
                  <td>{new Date(request.created_at).toLocaleString('pt-BR')}</td>
                  <td className="actions">
                    <button
                      type="button"
                      className="btn btn-primary"
                      onClick={() => handleApprove(request.id)}
                    >
                      Aprovar
                    </button>
                    <button
                      type="button"
                      className="btn btn-danger"
                      onClick={() => handleReject(request.id)}
                    >
                      Rejeitar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  )
}
