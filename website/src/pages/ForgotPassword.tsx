import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'

import { ApiError, api } from '../api/client'
import { BrandLogo } from '../components/BrandLogo'
import { Button } from '../components/Button'
import { Input } from '../components/Input'
import stadiumBg from '../assets/bg_stadium_dark.jpg'

export function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [done, setDone] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setDone('')
    if (!email.trim()) {
      setError('Informe seu e-mail.')
      return
    }
    setSubmitting(true)
    try {
      const res = await api.forgotPassword(email.trim())
      setDone(res.message || 'Se o e-mail existir, enviaremos o link de redefinicao.')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Nao foi possivel enviar o e-mail')
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
        <h1 className="mt-6 text-center text-2xl font-bold">Esqueci a senha</h1>
        <p className="mt-1 text-center text-sm text-muted">
          Enviaremos um link para redefinir sua senha.
        </p>

        <form className="mt-8 space-y-4" onSubmit={onSubmit}>
          <Input
            label="E-mail"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="seu@email.com"
            autoComplete="email"
          />
          {error ? <p className="text-sm text-danger">{error}</p> : null}
          {done ? <p className="text-sm text-grass">{done}</p> : null}
          <Button type="submit" className="w-full" disabled={submitting}>
            {submitting ? 'Enviando...' : 'Enviar link'}
          </Button>
        </form>

        <p className="mt-6 text-center text-sm">
          <Link to="/entrar" className="text-grass hover:underline">
            Voltar ao login
          </Link>
        </p>
      </div>
    </div>
  )
}
