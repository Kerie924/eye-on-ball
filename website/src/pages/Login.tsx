import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'

import { ApiError } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { BrandLogo } from '../components/BrandLogo'
import { Button } from '../components/Button'
import { Input } from '../components/Input'
import stadiumBg from '../assets/bg_stadium_dark.jpg'

export function LoginPage() {
  const { user, loading, login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (!loading && user) return <Navigate to="/app" replace />

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    if (!email.trim() || !password) {
      setError('Informe e-mail e senha.')
      return
    }
    setSubmitting(true)
    try {
      await login(email.trim(), password)
      navigate('/app', { replace: true })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Nao foi possivel entrar')
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
        <h1 className="mt-6 text-center text-2xl font-bold">Entrar</h1>
        <p className="mt-1 text-center text-sm text-muted">Acesse seus lances gravados</p>

        <form className="mt-8 space-y-4" onSubmit={onSubmit}>
          <Input
            label="E-mail"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="seu@email.com"
          />
          <Input
            label="Senha"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
          />
          <div className="text-right text-sm">
            <Link to="/esqueci-senha" className="text-grass hover:underline">
              Esqueci a senha
            </Link>
          </div>
          {error ? <p className="text-sm text-danger">{error}</p> : null}
          <Button type="submit" className="w-full" disabled={submitting}>
            {submitting ? 'Entrando...' : 'Entrar'}
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-muted">
          Nao tem conta?{' '}
          <Link to="/cadastrar" className="font-semibold text-grass hover:underline">
            Criar conta
          </Link>
        </p>
        <p className="mt-3 text-center text-sm">
          <Link to="/" className="text-muted hover:text-white">
            Voltar ao inicio
          </Link>
        </p>
      </div>
    </div>
  )
}
