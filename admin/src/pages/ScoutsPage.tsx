import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { User } from '../types'

export function ScoutsPage() {
  const [scouts, setScouts] = useState<User[]>([])
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  async function loadScouts() {
    const data = await api.pendingScouts()
    setScouts(data)
  }

  useEffect(() => {
    loadScouts().catch((err) => setError(err.message))
  }, [])

  async function handleApprove(userId: number) {
    try {
      const response = await api.approveScout(userId)
      setMessage(response.message)
      await loadScouts()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao aprovar olheiro')
    }
  }

  async function handleReject(userId: number) {
    try {
      const response = await api.rejectScout(userId)
      setMessage(response.message)
      await loadScouts()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao rejeitar olheiro')
    }
  }

  return (
    <section>
      <header className="page-header">
        <div>
          <h1>Olheiros pendentes</h1>
          <p>Apos aprovacao, o olheiro tera acesso a todas as quadras</p>
        </div>
      </header>

      {message && <p className="success-text">{message}</p>}
      {error && <p className="error-text">{error}</p>}

      <div className="panel table-wrap">
        {scouts.length === 0 ? (
          <p className="empty-state">Nenhum olheiro aguardando aprovacao.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Nome</th>
                <th>E-mail</th>
                <th>Cadastro</th>
                <th>Acoes</th>
              </tr>
            </thead>
            <tbody>
              {scouts.map((scout) => (
                <tr key={scout.id}>
                  <td>{scout.full_name}</td>
                  <td>{scout.email}</td>
                  <td>{new Date(scout.created_at).toLocaleString('pt-BR')}</td>
                  <td className="actions">
                    <button
                      type="button"
                      className="btn btn-primary"
                      onClick={() => handleApprove(scout.id)}
                    >
                      Aprovar
                    </button>
                    <button
                      type="button"
                      className="btn btn-danger"
                      onClick={() => handleReject(scout.id)}
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
