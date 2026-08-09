import { useEffect, useState, type FormEvent } from 'react'
import { Plus, Search, UserCheck, UserX } from 'lucide-react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import { PageHeader } from '../components/PageHeader'
import { PaginationBar } from '../components/PaginationBar'
import { LoadingState, Modal } from '../components/shared'
import { StatusBadge, UserAvatar } from '../components/ui'
import { useToast } from '../context/ToastContext'
import { usePagination } from '../hooks/usePagination'
import type { CourtAccessRequest, User, UserRole } from '../types'

const roleLabels: Record<User['role'], string> = {
  admin: 'Administrador',
  athlete: 'Atleta',
  scout: 'Olheiro',
}

type Tab = 'all' | 'requests' | 'scouts'

function tabFromParams(value: string | null): Tab {
  if (value === 'requests' || value === 'scouts' || value === 'all') return value
  return 'all'
}

export function UsersPage() {
  const { showToast } = useToast()
  const [searchParams, setSearchParams] = useSearchParams()
  const [tab, setTab] = useState<Tab>(() => tabFromParams(searchParams.get('tab')))
  const [users, setUsers] = useState<User[]>([])
  const [requests, setRequests] = useState<CourtAccessRequest[]>([])
  const [scouts, setScouts] = useState<User[]>([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState<UserRole>('athlete')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    setTab(tabFromParams(searchParams.get('tab')))
  }, [searchParams])

  function selectTab(next: Tab) {
    setTab(next)
    setSearchParams(next === 'all' ? {} : { tab: next }, { replace: true })
  }

  async function loadAll() {
    const [usersData, requestsData, scoutsData] = await Promise.all([
      api.users(),
      api.accessRequests(),
      api.pendingScouts(),
    ])
    setUsers(usersData)
    setRequests(requestsData)
    setScouts(scoutsData)
  }

  useEffect(() => {
    loadAll()
      .catch((err) => showToast(err.message, 'error'))
      .finally(() => setLoading(false))
  }, [])

  async function handleCreate(event: FormEvent) {
    event.preventDefault()
    setSubmitting(true)
    try {
      await api.createUser({
        email,
        password,
        full_name: fullName,
        role,
      })
      showToast('Usuario criado com sucesso', 'success')
      setShowCreate(false)
      setFullName('')
      setEmail('')
      setPassword('')
      await loadAll()
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Erro ao criar usuario', 'error')
    } finally {
      setSubmitting(false)
    }
  }

  async function toggleUserActive(user: User) {
    try {
      await api.updateUser(user.id, { is_active: !user.is_active })
      showToast(
        user.is_active ? 'Usuario desativado' : 'Usuario ativado',
        'success',
      )
      await loadAll()
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Erro ao atualizar usuario', 'error')
    }
  }

  const filteredUsers = users.filter(
    (user) =>
      user.full_name.toLowerCase().includes(search.toLowerCase()) ||
      user.email.toLowerCase().includes(search.toLowerCase()),
  )
  const usersPagination = usePagination(filteredUsers, 6, `${search}|${tab}`)
  const requestsPagination = usePagination(requests, 6, `requests|${tab}`)
  const scoutsPagination = usePagination(scouts, 6, `scouts|${tab}`)

  if (loading) return <LoadingState />

  return (
    <section className="page animate-fade">
      <PageHeader title="Usuarios" subtitle="Gerencie atletas, olheiros e administradores.">
        <button type="button" className="btn btn-primary" onClick={() => setShowCreate(true)}>
          <Plus size={16} />
          Novo Usuario
        </button>
      </PageHeader>

      <div className="tabs">
        {([
          ['all', `Todos (${users.length})`],
          ['requests', `Solicitacoes (${requests.length})`],
          ['scouts', `Olheiros (${scouts.length})`],
        ] as const).map(([key, label]) => (
          <button
            key={key}
            type="button"
            className={tab === key ? 'tab active' : 'tab'}
            onClick={() => selectTab(key)}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="toolbar">
        <label className="search-field">
          <Search size={16} />
          <input
            placeholder="Buscar usuario..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </label>
      </div>

      {tab === 'all' && (
        <div className="panel table-wrap hover-lift">
          <table className="data-table">
            <thead>
              <tr>
                <th>Nome</th>
                <th>E-mail</th>
                <th>Tipo</th>
                <th>Status</th>
                <th>Aprovado</th>
                <th>Data de Cadastro</th>
                <th>Acoes</th>
              </tr>
            </thead>
            <tbody>
              {usersPagination.pageItems.length === 0 ? (
                <tr>
                  <td colSpan={7} className="empty-cell">
                    Nenhum usuario encontrado
                  </td>
                </tr>
              ) : (
                usersPagination.pageItems.map((user) => (
                <tr key={user.id} className="table-row-interactive">
                  <td>
                    <div className="table-user">
                      <UserAvatar name={user.full_name} />
                      <strong>{user.full_name}</strong>
                    </div>
                  </td>
                  <td>{user.email}</td>
                  <td>{roleLabels[user.role]}</td>
                  <td>
                    <StatusBadge variant={user.is_active ? 'online' : 'offline'}>
                      {user.is_active ? 'Ativo' : 'Inativo'}
                    </StatusBadge>
                  </td>
                  <td>{user.is_approved ? 'Sim' : 'Nao'}</td>
                  <td>{new Date(user.created_at).toLocaleDateString('pt-BR')}</td>
                  <td>
                    {user.role !== 'admin' && (
                      <button
                        type="button"
                        className="icon-btn"
                        title={user.is_active ? 'Desativar' : 'Ativar'}
                        onClick={() => toggleUserActive(user)}
                      >
                        {user.is_active ? <UserX size={16} /> : <UserCheck size={16} />}
                      </button>
                    )}
                  </td>
                </tr>
              ))
              )}
            </tbody>
          </table>
          <PaginationBar
            from={usersPagination.from}
            to={usersPagination.to}
            total={usersPagination.total}
            page={usersPagination.page}
            totalPages={usersPagination.totalPages}
            onPageChange={usersPagination.setPage}
            label="usuarios"
          />
        </div>
      )}

      {tab === 'requests' && (
        <div className="panel table-wrap hover-lift">
          <table className="data-table">
            <thead>
              <tr>
                <th>Atleta</th>
                <th>E-mail</th>
                <th>Quadra</th>
                <th>Data</th>
                <th>Acoes</th>
              </tr>
            </thead>
            <tbody>
              {requestsPagination.pageItems.length === 0 ? (
                <tr>
                  <td colSpan={5} className="empty-cell">
                    Nenhuma solicitacao pendente
                  </td>
                </tr>
              ) : (
                requestsPagination.pageItems.map((request) => (
                  <tr key={request.id} className="table-row-interactive">
                    <td>{request.user?.full_name}</td>
                    <td>{request.user?.email}</td>
                    <td>{request.court?.name}</td>
                    <td>{new Date(request.created_at).toLocaleDateString('pt-BR')}</td>
                    <td className="actions">
                      <button
                        type="button"
                        className="btn btn-primary btn-sm"
                        onClick={async () => {
                          const res = await api.approveAccessRequest(request.id)
                          showToast(res.message, 'success')
                          await loadAll()
                        }}
                      >
                        Aprovar
                      </button>
                      <button
                        type="button"
                        className="btn btn-danger btn-sm"
                        onClick={async () => {
                          const res = await api.rejectAccessRequest(request.id)
                          showToast(res.message, 'success')
                          await loadAll()
                        }}
                      >
                        Rejeitar
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
          <PaginationBar
            from={requestsPagination.from}
            to={requestsPagination.to}
            total={requestsPagination.total}
            page={requestsPagination.page}
            totalPages={requestsPagination.totalPages}
            onPageChange={requestsPagination.setPage}
            label="solicitacoes"
          />
        </div>
      )}

      {tab === 'scouts' && (
        <div className="panel table-wrap hover-lift">
          <table className="data-table">
            <thead>
              <tr>
                <th>Nome</th>
                <th>E-mail</th>
                <th>Cadastro</th>
                <th>Acoes</th>
              </tr>
            </thead>
            <tbody>
              {scoutsPagination.pageItems.length === 0 ? (
                <tr>
                  <td colSpan={4} className="empty-cell">
                    Nenhum olheiro aguardando aprovacao
                  </td>
                </tr>
              ) : (
                scoutsPagination.pageItems.map((scout) => (
                  <tr key={scout.id} className="table-row-interactive">
                    <td>{scout.full_name}</td>
                    <td>{scout.email}</td>
                    <td>{new Date(scout.created_at).toLocaleDateString('pt-BR')}</td>
                    <td className="actions">
                      <button
                        type="button"
                        className="btn btn-primary btn-sm"
                        onClick={async () => {
                          const res = await api.approveScout(scout.id)
                          showToast(res.message, 'success')
                          await loadAll()
                        }}
                      >
                        Aprovar
                      </button>
                      <button
                        type="button"
                        className="btn btn-danger btn-sm"
                        onClick={async () => {
                          const res = await api.rejectScout(scout.id)
                          showToast(res.message, 'success')
                          await loadAll()
                        }}
                      >
                        Rejeitar
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
          <PaginationBar
            from={scoutsPagination.from}
            to={scoutsPagination.to}
            total={scoutsPagination.total}
            page={scoutsPagination.page}
            totalPages={scoutsPagination.totalPages}
            onPageChange={scoutsPagination.setPage}
            label="olheiros"
          />
        </div>
      )}

      {showCreate && (
        <Modal title="Novo Usuario" onClose={() => setShowCreate(false)}>
          <form className="form-stack" onSubmit={handleCreate}>
            <label>
              Nome completo
              <input value={fullName} onChange={(e) => setFullName(e.target.value)} required />
            </label>
            <label>
              E-mail
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </label>
            <label>
              Senha
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                minLength={8}
                required
              />
            </label>
            <label>
              Tipo
              <select value={role} onChange={(e) => setRole(e.target.value as UserRole)}>
                <option value="athlete">Atleta</option>
                <option value="scout">Olheiro</option>
              </select>
            </label>
            <div className="modal-actions">
              <button type="button" className="btn btn-outline" onClick={() => setShowCreate(false)}>
                Cancelar
              </button>
              <button type="submit" className="btn btn-primary" disabled={submitting}>
                {submitting ? 'Salvando...' : 'Criar usuario'}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </section>
  )
}
