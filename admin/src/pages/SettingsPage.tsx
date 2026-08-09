import { useEffect, useState, type FormEvent } from 'react'
import { api } from '../api/client'
import { PageHeader } from '../components/PageHeader'
import { LoadingState } from '../components/shared'
import { useToast } from '../context/ToastContext'
import type { PlatformSettings } from '../types'

type SettingsTab = 'general' | 'storage' | 'retention'

export function SettingsPage() {
  const { showToast } = useToast()
  const [tab, setTab] = useState<SettingsTab>('general')
  const [settings, setSettings] = useState<PlatformSettings | null>(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    api.settings()
      .then(setSettings)
      .catch((err) => showToast(err.message, 'error'))
      .finally(() => setLoading(false))
  }, [])

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!settings) return

    setSubmitting(true)
    try {
      const updated = await api.updateSettings(settings)
      setSettings(updated)
      showToast('Configuracoes salvas com sucesso', 'success')
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Erro ao salvar', 'error')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading || !settings) return <LoadingState />

  return (
    <section className="page settings-page animate-fade">
      <PageHeader title="Configuracoes" subtitle="Ajustes gerais da plataforma." />

      <div className="settings-layout">
        <aside className="panel settings-nav">
          {([
            ['general', 'Geral'],
            ['storage', 'Armazenamento'],
            ['retention', 'Retencao de Videos'],
          ] as const).map(([key, label]) => (
            <button
              key={key}
              type="button"
              className={tab === key ? 'settings-nav-item active' : 'settings-nav-item'}
              onClick={() => setTab(key)}
            >
              {label}
            </button>
          ))}
        </aside>

        <form className="panel settings-form hover-lift" onSubmit={handleSubmit}>
          {tab === 'general' && (
            <>
              <label>
                Nome da Plataforma
                <input
                  value={settings.platform_name}
                  onChange={(e) =>
                    setSettings({ ...settings, platform_name: e.target.value })
                  }
                  required
                />
              </label>
              <label>
                E-mail de Suporte
                <input
                  type="email"
                  value={settings.support_email}
                  onChange={(e) =>
                    setSettings({ ...settings, support_email: e.target.value })
                  }
                  required
                />
              </label>
              <label>
                Fuso Horario
                <select
                  value={settings.timezone}
                  onChange={(e) => setSettings({ ...settings, timezone: e.target.value })}
                >
                  <option value="America/Sao_Paulo">UTC-03:00 Brasilia</option>
                </select>
              </label>
              <label>
                Idioma
                <select
                  value={settings.language}
                  onChange={(e) => setSettings({ ...settings, language: e.target.value })}
                >
                  <option value="pt-BR">Portugues (Brasil)</option>
                </select>
              </label>
            </>
          )}

          {tab === 'storage' && (
            <label>
              Limite de armazenamento (TB)
              <input
                type="number"
                min="0.1"
                step="0.1"
                value={settings.storage_limit_tb}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    storage_limit_tb: Number(e.target.value),
                  })
                }
              />
            </label>
          )}

          {tab === 'retention' && (
            <label>
              Retencao de videos (horas)
              <input
                type="number"
                min="1"
                max="720"
                value={settings.retention_hours}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    retention_hours: Number(e.target.value),
                  })
                }
              />
              <small className="field-hint">
                Videos serao removidos automaticamente apos este periodo.
              </small>
            </label>
          )}

          <div className="form-footer">
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? 'Salvando...' : 'Salvar Alteracoes'}
            </button>
          </div>
        </form>
      </div>
    </section>
  )
}
