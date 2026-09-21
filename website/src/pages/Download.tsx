import { useEffect } from 'react'
import { Link } from 'react-router-dom'

import { DownloadApp } from '../components/DownloadApp'
import { BrandLogo } from '../components/BrandLogo'
import { APP_STORE_URL, deviceKind, PLAY_STORE_URL } from '../lib/stores'
import stadium from '../assets/bg_stadium_dark.jpg'

export function DownloadPage() {
  useEffect(() => {
    const kind = deviceKind()
    if (kind === 'android') {
      window.location.replace(PLAY_STORE_URL)
      return
    }
    if (kind === 'ios' && APP_STORE_URL) {
      window.location.replace(APP_STORE_URL)
    }
  }, [])

  return (
    <div className="relative grid min-h-screen place-items-center px-4 py-16">
      <img src={stadium} alt="" className="absolute inset-0 -z-20 h-full w-full object-cover" />
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_top,rgba(30,215,96,0.22),transparent_45%),linear-gradient(180deg,rgba(13,17,23,0.82),rgba(13,17,23,0.94))]" />
      <div className="surface-card w-full max-w-lg rounded-3xl p-8">
        <BrandLogo variant="full" className="mx-auto h-16" />
        <h1 className="mt-6 text-center text-2xl font-bold">Baixar o app</h1>
        <p className="mt-2 text-center text-sm text-muted">
          No celular, este link abre a loja certa. No computador, escolha abaixo.
        </p>
        <div className="mt-8">
          <DownloadApp />
        </div>
        <p className="mt-8 text-center text-sm">
          <Link to="/" className="text-grass hover:underline">
            Voltar ao site
          </Link>
        </p>
      </div>
    </div>
  )
}
