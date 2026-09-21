import { Smartphone } from 'lucide-react'

import { APP_STORE_URL, PLAY_STORE_URL, storeHref } from '../lib/stores'
import appIcon from '../assets/brand/icon.png'

function AppleBadge() {
  return (
    <svg viewBox="0 0 24 24" className="h-6 w-6 fill-current" aria-hidden>
      <path d="M16.7 12.6c0-2.3 1.9-3.4 2-3.5-1.1-1.6-2.8-1.8-3.4-1.8-1.4-.2-2.8.8-3.5.8s-1.8-.8-3-.8c-1.5 0-3 .9-3.8 2.3-1.6 2.8-.4 7 1.2 9.3.8 1.1 1.7 2.3 2.9 2.3 1.2 0 1.6-.7 3-.7s1.8.7 3 .7 2-.1 2.9-2.2c.7-1 1.2-2 1.5-3.1-3.9-1.5-3.8-5.5-3.8-5.3zM14.5 5.8c.6-.8 1.1-1.9.9-3-.9 0-2 .6-2.6 1.4-.6.7-1.1 1.8-.9 2.9 1 .1 2-.5 2.6-1.3z" />
    </svg>
  )
}

function PlayBadge() {
  return (
    <svg viewBox="0 0 24 24" className="h-6 w-6" aria-hidden>
      <path fill="#34A853" d="M3.5 20.5 14.2 12 3.5 3.5z" />
      <path fill="#FBBC04" d="m14.2 12 2.6 2.4L20.5 13z" />
      <path fill="#EA4335" d="M3.5 3.5 14.2 12l2.6-2.4L5.2 2.2z" />
      <path fill="#4285F4" d="M3.5 20.5 16.8 14.4 14.2 12z" />
    </svg>
  )
}

export function DownloadApp({ compact = false }: { compact?: boolean }) {
  return (
    <div className={compact ? 'flex flex-wrap items-center gap-3' : 'space-y-4'}>
      {!compact ? (
        <div className="flex items-center gap-4">
          <img
            src={appIcon}
            alt=""
            className="h-16 w-16 rounded-2xl border border-grass/30 shadow-[0_0_24px_rgba(30,215,96,0.35)]"
          />
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.16em] text-grass">
              App Lance On
            </p>
            <p className="text-sm text-muted">Baixe no celular e veja seus lances na hora.</p>
          </div>
        </div>
      ) : null}

      <div className="flex flex-wrap gap-3">
        <a
          href={storeHref('android')}
          onClick={(e) => {
            if (!/Android/i.test(navigator.userAgent)) {
              e.preventDefault()
              window.open(PLAY_STORE_URL, '_blank', 'noopener,noreferrer')
            }
          }}
          className="store-btn"
        >
          <PlayBadge />
          <span className="text-left leading-tight">
            <span className="block text-[10px] uppercase tracking-wide text-white/60">
              Disponível no
            </span>
            <span className="block text-sm font-semibold">Google Play</span>
          </span>
        </a>

        {APP_STORE_URL ? (
          <a href={APP_STORE_URL} target="_blank" rel="noreferrer" className="store-btn">
            <AppleBadge />
            <span className="text-left leading-tight">
              <span className="block text-[10px] uppercase tracking-wide text-white/60">
                Baixar na
              </span>
              <span className="block text-sm font-semibold">App Store</span>
            </span>
          </a>
        ) : (
          <span className="store-btn cursor-not-allowed opacity-60" title="App Store em breve">
            <AppleBadge />
            <span className="text-left leading-tight">
              <span className="block text-[10px] uppercase tracking-wide text-white/60">
                Em breve na
              </span>
              <span className="block text-sm font-semibold">App Store</span>
            </span>
          </span>
        )}

        {compact ? (
          <span className="inline-flex items-center gap-2 text-xs text-muted">
            <Smartphone className="h-4 w-4 text-grass" />
            Android e iPhone
          </span>
        ) : null}
      </div>
    </div>
  )
}
