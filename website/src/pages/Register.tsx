import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'

import { ApiError, LEGAL } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { BrandLogo } from '../components/BrandLogo'
import { Button } from '../components/Button'
import { Input } from '../components/Input'
import type { UserRole } from '../types'
import stadiumBg from '../assets/bg_stadium_dark.jpg'

export function RegisterPage() {
  const { user, loading, register } = useAuth()
  const navigate = useNavigate()
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState<Extract<UserRole, 'athlete' | 'scout'>>('athlete')
  const [accepted, setAccepted] = useState(false)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (!loading && user) return <Navigate to="/app" replace />

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    if (!accepted) {
      setError('Aceite a Politica de privacidade e os Termos de uso.')
      return
    }
    if (fullName.trim().length < 2) {
      setError('Informe seu nome completo.')
      return
    }
    if (!email.trim()) {
      setError('Informe um e-mail valido.')
      return
    }
    if (password.length < 8) {
      setError('A senha deve ter pelo menos 8 caracteres.')
      return
    }
    setSubmitting(true)
    try {
      await register({
        email: email.trim(),
        password,
        full_name: fullName.trim(),
        role,
      })
      navigate('/app', { replace: true })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Nao foi possivel cadastrar')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="relative grid min-h-screen place-items-center px-4 py-10">
      <img
        src={stadiumBg}
        alt=""
        className="absolute inset-0 -z-10 h-full w-full object-cover opacity-30"
      />
      <div className="absolute inset-0 -z-10 bg-ink/80" />
      <div className="w-full max-w-md rounded-2xl border border-line bg-card/95 p-6 shadow-xl backdrop-blur md:p-8">
        <BrandLogo variant="full" className="mx-auto h-16 md:h-20" />
        <h1 className="mt-6 text-center text-2xl font-bold">Criar conta</h1>
        <p className="mt-1 text-center text-sm text-muted">Comece a assistir seus lances</p>

        <form className="mt-8 space-y-4" onSubmit={onSubmit}>
          <Input
            label="Nome completo"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="Seu nome"
            autoComplete="name"
          />
          <Input
            label="E-mail"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="seu@email.com"
            autoComplete="email"
          />
          <Input
            label="Senha"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Minimo 8 caracteres"
            autoComplete="new-password"
          />

          <div>
            <span className="mb-2 block text-sm font-medium text-muted">Tipo de conta</span>
            <div className="grid grid-cols-2 gap-2 rounded-xl border border-line bg-ink-soft p-1">
              {(
                [
                  ['athlete', 'Atleta'],
                  ['scout', 'Olheiro'],
                ] as const
              ).map(([value, label]) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setRole(value)}
                  className={`rounded-lg px-3 py-2.5 text-sm font-semibold transition ${
                    role === value ? 'bg-grass text-on-grass' : 'text-muted hover:text-white'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          <label className="flex items-start gap-3 text-sm text-muted">
            <input
              type="checkbox"
              checked={accepted}
              onChange={(e) => setAccepted(e.target.checked)}
              className="mt-1 accent-grass"
            />
            <span>
              Li e aceito a{' '}
              <a href={LEGAL.privacy} target="_blank" rel="noreferrer" className="text-grass">
                Politica de privacidade
              </a>{' '}
              e os{' '}
              <a href={LEGAL.terms} target="_blank" rel="noreferrer" className="text-grass">
                Termos de uso
              </a>
              .
            </span>
          </label>

          {error ? <p className="text-sm text-danger">{error}</p> : null}
          <Button type="submit" className="w-full" disabled={submitting}>
            {submitting ? 'Cadastrando...' : 'Cadastrar'}
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-muted">
          Ja tem conta?{' '}
          <Link to="/entrar" className="font-semibold text-grass hover:underline">
            Entrar
          </Link>
        </p>
      </div>
    </div>
  )
}
