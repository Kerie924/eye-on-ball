import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  ChevronRight,
  CircleHelp,
  FileText,
  LogOut,
  MapPinned,
  Shield,
  Trash2,
  UserRound,
} from 'lucide-react'

import { ApiError, LEGAL } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { Button } from '../components/Button'
import { Input } from '../components/Input'
import { roleLabel } from '../lib/time'

export function ProfilePage() {
  const { user, logout, deleteAccount, updateProfile } = useAuth()
  const navigate = useNavigate()
  const [editing, setEditing] = useState(false)
  const [fullName, setFullName] = useState(user?.full_name ?? '')
  const [email, setEmail] = useState(user?.email ?? '')
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [error, setError] = useState('')
  const [done, setDone] = useState('')
  const [saving, setSaving] = useState(false)

  async function handleLogout() {
    if (!confirm('Deseja encerrar sua sessao?')) return
    logout()
    navigate('/entrar', { replace: true })
  }

  async function handleDelete() {
    if (
      !confirm(
        'Isso desativa sua conta e remove nome, e-mail e login. Esta acao nao pode ser desfeita.',
      )
    ) {
      return
    }
    try {
      await deleteAccount()
      navigate('/', { replace: true })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Nao foi possivel excluir a conta')
    }
  }

  async function onSave(e: FormEvent) {
    e.preventDefault()
    setError('')
    setDone('')
    setSaving(true)
    try {
      await updateProfile({
        full_name: fullName.trim(),
        email: email.trim(),
        ...(newPassword
          ? { current_password: currentPassword, new_password: newPassword }
          : {}),
      })
      setDone('Perfil atualizado.')
      setCurrentPassword('')
      setNewPassword('')
      setEditing(false)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Nao foi possivel salvar')
    } finally {
      setSaving(false)
    }
  }

  const menu = [
    { label: 'Meu perfil', icon: UserRound, action: () => setEditing(true) },
    { label: 'Minhas quadras', icon: MapPinned, to: '/app/cidades' },
    { label: 'Ajuda e suporte', icon: CircleHelp, to: '/app/relatar' },
    { label: 'Politica de privacidade', icon: Shield, href: LEGAL.privacy },
    { label: 'Termos de uso', icon: FileText, href: LEGAL.terms },
  ]

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="rounded-2xl border border-line bg-card p-6 text-center">
        {user?.avatar_url ? (
          <img
            src={user.avatar_url}
            alt=""
            className="mx-auto h-20 w-20 rounded-full object-cover"
          />
        ) : (
          <div className="mx-auto grid h-20 w-20 place-items-center rounded-full bg-grass/20 text-2xl font-bold text-grass">
            {user?.full_name?.slice(0, 1).toUpperCase() ?? '?'}
          </div>
        )}
        <h1 className="mt-4 text-2xl font-bold">{user?.full_name}</h1>
        <p className="text-sm text-muted">{user?.email}</p>
        <p className="mt-1 text-sm text-grass">{roleLabel(user?.role ?? '')}</p>
        {user?.role === 'scout' && !user.is_approved ? (
          <p className="mt-3 rounded-xl border border-line bg-ink-soft px-3 py-2 text-xs text-muted">
            Sua conta de olheiro aguarda aprovacao do administrador.
          </p>
        ) : null}
        <Button
          variant="outline"
          className="mt-5 px-4 py-2"
          onClick={() => {
            setFullName(user?.full_name ?? '')
            setEmail(user?.email ?? '')
            setEditing((v) => !v)
          }}
        >
          {editing ? 'Fechar edicao' : 'Editar perfil'}
        </Button>
      </div>

      {editing ? (
        <form onSubmit={onSave} className="space-y-4 rounded-2xl border border-line bg-card p-6">
          <Input label="Nome" value={fullName} onChange={(e) => setFullName(e.target.value)} />
          <Input
            label="E-mail"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <Input
            label="Senha atual (para trocar senha)"
            type="password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
          />
          <Input
            label="Nova senha"
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
          />
          {error ? <p className="text-sm text-danger">{error}</p> : null}
          {done ? <p className="text-sm text-grass">{done}</p> : null}
          <Button type="submit" className="w-full" disabled={saving}>
            {saving ? 'Salvando...' : 'Salvar'}
          </Button>
        </form>
      ) : null}

      <div className="overflow-hidden rounded-2xl border border-line bg-card">
        {menu.map((item, index) => {
          const content = (
            <>
              <span className="flex items-center gap-3">
                <item.icon className="h-5 w-5 text-grass" />
                {item.label}
              </span>
              <ChevronRight className="h-4 w-4 text-muted" />
            </>
          )
          const className = `flex w-full items-center justify-between px-5 py-4 text-left text-sm transition hover:bg-white/5 ${
            index < menu.length - 1 ? 'border-b border-line' : ''
          }`
          if (item.to) {
            return (
              <Link key={item.label} to={item.to} className={className}>
                {content}
              </Link>
            )
          }
          if (item.href) {
            return (
              <a
                key={item.label}
                href={item.href}
                target="_blank"
                rel="noreferrer"
                className={className}
              >
                {content}
              </a>
            )
          }
          return (
            <button key={item.label} type="button" onClick={item.action} className={className}>
              {content}
            </button>
          )
        })}
      </div>

      <button
        type="button"
        onClick={() => void handleLogout()}
        className="flex w-full items-center justify-center gap-2 rounded-2xl border border-danger/40 px-5 py-4 text-sm font-semibold text-danger hover:bg-danger/10"
      >
        <LogOut className="h-4 w-4" />
        Sair
      </button>

      <button
        type="button"
        onClick={() => void handleDelete()}
        className="flex w-full items-center justify-center gap-2 px-5 py-2 text-sm text-danger/80 hover:text-danger"
      >
        <Trash2 className="h-4 w-4" />
        Excluir conta
      </button>
    </div>
  )
}
