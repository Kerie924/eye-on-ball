import { Link } from 'react-router-dom'
import { Download, Share2, MapPinned } from 'lucide-react'

import { BrandLogo } from '../components/BrandLogo'
import { Button } from '../components/Button'
import { DownloadApp } from '../components/DownloadApp'
import courtBg from '../assets/bg_court_net.jpg'

export function HowItWorksPage() {
  return (
    <div className="relative min-h-screen">
      <img src={courtBg} alt="" className="absolute inset-0 -z-20 h-full w-full object-cover" />
      <div className="absolute inset-0 -z-10 bg-ink/85" />
      <header className="mx-auto flex max-w-3xl items-center justify-between px-4 py-5">
        <BrandLogo variant="full" className="h-14 md:h-16" />
        <Link to="/">
          <Button variant="ghost" className="px-3 py-2">
            Inicio
          </Button>
        </Link>
      </header>

      <main className="mx-auto max-w-3xl space-y-8 px-4 pb-16">
        <div>
          <h1 className="text-3xl font-bold">Como funciona</h1>
          <p className="mt-2 text-muted">Seguro. Rapido. Confiavel. Seus momentos, sempre com voce.</p>
        </div>

        <div className="space-y-4">
          {[
            {
              icon: MapPinned,
              title: '1. Escolha',
              body: 'Selecione a cidade, a quadra e o bloco de horario do seu jogo.',
            },
            {
              icon: Download,
              title: '2. Assista e baixe',
              body: 'Veja os clips de 30 segundos das cameras e salve na galeria.',
            },
            {
              icon: Share2,
              title: '3. Compartilhe',
              body: 'Mande para amigos, olheiros e redes sociais.',
            },
          ].map((step) => (
            <div key={step.title} className="surface-card flex gap-4 rounded-2xl p-5">
              <div className="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-grass/15 text-grass shadow-[0_0_16px_rgba(30,215,96,0.25)]">
                <step.icon className="h-6 w-6" />
              </div>
              <div>
                <h2 className="text-lg font-semibold">{step.title}</h2>
                <p className="mt-1 text-sm text-muted">{step.body}</p>
              </div>
            </div>
          ))}
        </div>

        <DownloadApp />
        <Link to="/cadastrar">
          <Button className="w-full">Comecar agora</Button>
        </Link>
      </main>
    </div>
  )
}
