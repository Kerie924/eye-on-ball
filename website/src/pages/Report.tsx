import { useState, type FormEvent } from 'react'
import { Paperclip, X } from 'lucide-react'

import { ApiError, api } from '../api/client'
import { Button } from '../components/Button'

const MAX_PHOTOS = 4
const MIN_MESSAGE = 10

export function ReportPage() {
  const [message, setMessage] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const [previews, setPreviews] = useState<string[]>([])
  const [error, setError] = useState('')
  const [done, setDone] = useState('')
  const [submitting, setSubmitting] = useState(false)

  function onFiles(list: FileList | null) {
    if (!list) return
    const remaining = MAX_PHOTOS - files.length
    const next = Array.from(list)
      .filter((f) => f.type.startsWith('image/'))
      .slice(0, remaining)
    const urls = next.map((f) => URL.createObjectURL(f))
    setFiles((cur) => [...cur, ...next])
    setPreviews((cur) => [...cur, ...urls])
  }

  function removeFile(index: number) {
    URL.revokeObjectURL(previews[index])
    setFiles((cur) => cur.filter((_, i) => i !== index))
    setPreviews((cur) => cur.filter((_, i) => i !== index))
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setDone('')
    const text = message.trim()
    if (text.length < MIN_MESSAGE) {
      setError(`Escreva pelo menos ${MIN_MESSAGE} caracteres.`)
      return
    }
    setSubmitting(true)
    try {
      const res = await api.submitFeedback(text, files)
      setDone(res.message)
      setMessage('')
      previews.forEach((url) => URL.revokeObjectURL(url))
      setFiles([])
      setPreviews([])
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Nao foi possivel enviar o relato')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Reportar um erro</h1>
        <p className="mt-1 text-sm text-muted">
          Conte o que aconteceu. Voce pode anexar ate {MAX_PHOTOS} imagens.
        </p>
      </div>

      <form onSubmit={onSubmit} className="space-y-4 rounded-2xl border border-line bg-card p-6">
        <label className="block text-sm">
          <span className="mb-2 block font-medium text-muted">Sua mensagem</span>
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            rows={6}
            maxLength={2000}
            placeholder="Descreva o problema..."
            className="w-full rounded-xl border border-line bg-ink-soft px-4 py-3 text-white outline-none focus:border-grass"
          />
          <span className="mt-1 block text-right text-xs text-muted">
            {message.trim().length}/2000
          </span>
        </label>

        <div>
          <label className="inline-flex cursor-pointer items-center gap-2 rounded-xl border border-dashed border-line px-4 py-3 text-sm text-muted hover:border-grass hover:text-white">
            <Paperclip className="h-4 w-4" />
            Anexar imagens (JPG/PNG)
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              multiple
              className="hidden"
              onChange={(e) => {
                onFiles(e.target.files)
                e.target.value = ''
              }}
            />
          </label>
          {previews.length > 0 ? (
            <div className="mt-3 flex flex-wrap gap-3">
              {previews.map((src, index) => (
                <div key={src} className="relative h-20 w-20 overflow-hidden rounded-lg border border-line">
                  <img src={src} alt="" className="h-full w-full object-cover" />
                  <button
                    type="button"
                    onClick={() => removeFile(index)}
                    className="absolute right-1 top-1 rounded-full bg-black/70 p-0.5"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </div>
              ))}
            </div>
          ) : null}
        </div>

        {error ? <p className="text-sm text-danger">{error}</p> : null}
        {done ? <p className="text-sm text-grass">{done}</p> : null}

        <Button type="submit" className="w-full" disabled={submitting}>
          {submitting ? 'Enviando...' : 'Enviar relato'}
        </Button>
      </form>
    </div>
  )
}
