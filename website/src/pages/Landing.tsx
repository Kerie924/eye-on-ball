import { Link } from 'react-router-dom'
import { Camera, ShieldCheck, Zap } from 'lucide-react'

import { BrandLogo } from '../components/BrandLogo'
import { Button } from '../components/Button'
import { DownloadApp } from '../components/DownloadApp'
import { Reveal } from '../components/Reveal'
import heroBg from '../assets/bg_stadium.jpg'
import sectionBg from '../assets/bg_stadium_dark.jpg'
import courtBg from '../assets/bg_court_net.jpg'
import player from '../assets/player_illus.png'

const INSTAGRAM = 'https://www.instagram.com/lanceonpara'

const features = [
  { icon: Camera, label: 'Grave seus momentos' },
  { icon: Zap, label: 'Acesso rapido' },
  { icon: ShieldCheck, label: 'Seguro e confiavel' },
]

export function LandingPage() {
  return (
    <div className="min-h-screen overflow-x-hidden bg-ink text-white">
      <div className="relative isolate min-h-[100svh]">
        <img
          src={heroBg}
          alt=""
          className="absolute inset-0 -z-30 h-full w-full object-cover object-center"
        />
        <div
          className="page-glow absolute inset-0 -z-20 bg-[linear-gradient(105deg,rgba(13,17,23,0.94)_0%,rgba(13,17,23,0.82)_42%,rgba(13,17,23,0.35)_100%)]"
          aria-hidden
        />

        <header className="relative z-30 mx-auto flex max-w-7xl items-center justify-between gap-3 px-4 py-3 md:py-4">
          <BrandLogo
            variant="full"
            className="h-16 w-auto drop-shadow-[0_0_18px_rgba(30,215,96,0.35)] sm:h-20 md:h-24"
          />
          <nav className="hidden items-center gap-1 text-base font-semibold uppercase tracking-[0.06em] text-white/85 xl:flex">
            <a href="#como-funciona" className="nav-glow px-3 py-2">
              Como funciona
            </a>
            <a href="#recursos" className="nav-glow px-3 py-2">
              Recursos
            </a>
            <a href="#baixar" className="nav-glow px-3 py-2">
              Baixar app
            </a>
            <a href="#contato" className="nav-glow px-3 py-2">
              Contato
            </a>
          </nav>
          <div className="flex items-center gap-2">
            <Link to="/entrar" className="hidden sm:block">
              <Button variant="outline" className="px-4 py-2.5 text-base uppercase tracking-wide sm:text-lg">
                Entrar
              </Button>
            </Link>
            <Link to="/cadastrar">
              <Button className="px-4 py-2.5 text-base uppercase tracking-wide sm:px-5 sm:text-lg">
                Criar conta
              </Button>
            </Link>
          </div>
        </header>
        <nav className="relative z-30 flex gap-2 overflow-x-auto px-4 pb-3 text-sm font-semibold uppercase tracking-wide text-white/80 xl:hidden">
          <a href="#como-funciona" className="nav-glow shrink-0 px-3 py-2">
            Como funciona
          </a>
          <a href="#recursos" className="nav-glow shrink-0 px-3 py-2">
            Recursos
          </a>
          <a href="#baixar" className="nav-glow shrink-0 px-3 py-2">
            Baixar app
          </a>
          <a href="#contato" className="nav-glow shrink-0 px-3 py-2">
            Contato
          </a>
          <Link to="/entrar" className="nav-glow shrink-0 px-3 py-2 sm:hidden">
            Entrar
          </Link>
        </nav>

        <section className="relative z-10 mx-auto grid max-w-7xl items-center gap-6 px-4 pb-10 pt-2 md:gap-8 lg:min-h-[calc(100svh-9rem)] lg:grid-cols-[minmax(0,0.78fr)_minmax(0,1.22fr)] lg:gap-2 lg:pb-6">
          <div className="relative z-20 order-1 max-w-2xl space-y-6 md:space-y-7">
            <h1 className="text-4xl font-extrabold italic uppercase leading-[0.95] tracking-tight drop-shadow-[0_8px_30px_rgba(0,0,0,0.55)] sm:text-5xl lg:text-6xl xl:text-7xl">
              Seu lance.
              <br />
              <span className="text-grass [text-shadow:0_0_28px_rgba(30,215,96,0.45)]">Gravou.</span>
              <br />
              Compartilhou.
            </h1>
            <p className="max-w-lg text-lg text-white/85 md:text-xl">
              A plataforma n° 1 para gravacao de jogos em quadras esportivas.
            </p>

            <ul className="flex flex-col gap-3 sm:gap-4">
              {features.map(({ icon: Icon, label }) => (
                <li
                  key={label}
                  className="flex items-center gap-3 text-base font-semibold uppercase tracking-wide md:text-lg"
                >
                  <span className="grid h-11 w-11 shrink-0 place-items-center rounded-full border border-grass text-grass shadow-[0_0_18px_rgba(30,215,96,0.35)] sm:h-12 sm:w-12">
                    <Icon className="h-5 w-5" />
                  </span>
                  {label}
                </li>
              ))}
            </ul>

            <div className="flex flex-col gap-3 pt-1 sm:flex-row sm:flex-wrap">
              <Link to="/cadastrar" className="sm:w-auto">
                <Button className="w-full px-8 py-4 text-lg uppercase tracking-wide sm:w-auto sm:text-xl">
                  Comecar agora
                </Button>
              </Link>
              <a href="#baixar" className="sm:w-auto">
                <Button variant="outline" className="w-full px-8 py-4 text-lg sm:w-auto sm:text-xl">
                  Baixar o app
                </Button>
              </a>
            </div>
          </div>

          <div className="relative z-0 order-2 -mx-4 flex min-h-[42vh] items-end justify-center overflow-visible sm:min-h-[48vh] md:-mx-2 lg:min-h-[78vh] lg:justify-end lg:self-end">
            <div
              className="pointer-events-none absolute bottom-[8%] left-1/2 h-[70%] w-[70%] -translate-x-1/2 rounded-full bg-grass/20 blur-3xl lg:left-auto lg:right-[8%] lg:translate-x-0"
              aria-hidden
            />
            <img
              src={player}
              alt="Atleta Lance On"
              className="pointer-events-none relative z-10 h-[48vh] w-auto max-w-none object-contain object-bottom drop-shadow-[0_20px_40px_rgba(0,0,0,0.45)] sm:h-[56vh] md:h-[62vh] lg:h-[min(90vh,960px)] lg:max-w-[135%] lg:translate-x-[6%] lg:scale-[1.0] xl:scale-[1.0]"
            />
          </div>
        </section>
      </div>

      <section className="border-y border-line bg-card/70 backdrop-blur">
        <div className="mx-auto grid max-w-6xl grid-cols-2 gap-6 px-4 py-10 md:grid-cols-4">
          {[
            ['+1M', 'Lances gravados'],
            ['+10K', 'Quadras ativas'],
            ['+500K', 'Atletas'],
            ['24/7', 'Gravacao'],
          ].map(([value, label], index) => (
            <Reveal key={label} from={index % 2 === 0 ? 'left' : 'right'} delay={index * 80}>
              <div className="text-center">
                <div className="text-4xl font-extrabold text-grass drop-shadow-[0_0_16px_rgba(30,215,96,0.4)] md:text-5xl">
                  {value}
                </div>
                <div className="mt-2 text-sm font-semibold uppercase tracking-[0.14em] text-muted">
                  {label}
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      <section id="baixar" className="relative overflow-hidden py-20">
        <img src={courtBg} alt="" className="absolute inset-0 -z-10 h-full w-full object-cover" />
        <div className="absolute inset-0 -z-10 bg-[linear-gradient(180deg,rgba(13,17,23,0.88),rgba(13,17,23,0.78))]" />
        <div className="mx-auto grid max-w-6xl items-center gap-10 px-4 md:grid-cols-2">
          <Reveal from="left">
            <h2 className="text-4xl font-bold md:text-5xl">Leve o Lance On no bolso</h2>
            <p className="mt-4 max-w-lg text-lg text-muted">
              Baixe o app, escolha a quadra e o horario, e assista seus clips de 30 segundos.
            </p>
            <div className="mt-8">
              <DownloadApp />
            </div>
          </Reveal>
          <Reveal from="right">
            <div className="surface-card rounded-3xl p-8">
              <p className="text-base text-muted">Tambem no navegador</p>
              <h3 className="mt-2 text-2xl font-semibold">Ja tem conta?</h3>
              <p className="mt-2 text-base text-muted">
                Entre aqui e veja os videos da sua cidade sem instalar nada.
              </p>
              <Link to="/entrar" className="mt-6 inline-block">
                <Button>Entrar no site</Button>
              </Link>
            </div>
          </Reveal>
        </div>
      </section>

      <section id="como-funciona" className="relative overflow-hidden py-20">
        <img src={sectionBg} alt="" className="absolute inset-0 -z-10 h-full w-full object-cover opacity-40" />
        <div className="absolute inset-0 -z-10 bg-ink/80" />
        <div className="mx-auto max-w-6xl px-4">
          <Reveal from="left">
            <h2 className="text-4xl font-bold md:text-5xl">Como funciona</h2>
            <p className="mt-3 max-w-xl text-lg text-muted">Tres passos. Sem complicacao.</p>
          </Reveal>
          <div className="mt-10 grid gap-6 md:grid-cols-3">
            {[
              ['1', 'Escolha', 'Cidade, quadra, data e bloco de horario do seu jogo.', 'left'],
              ['2', 'Assista e baixe', 'Veja os clips de 30s e salve na galeria.', 'up'],
              ['3', 'Compartilhe', 'Mande para amigos, olheiros e redes sociais.', 'right'],
            ].map(([n, title, body, from], index) => (
              <Reveal key={n} from={from as 'left' | 'right' | 'up'} delay={index * 120}>
                <div className="surface-card h-full rounded-2xl p-6">
                  <div className="grid h-12 w-12 place-items-center rounded-full bg-grass text-lg font-bold text-on-grass shadow-[0_0_18px_rgba(30,215,96,0.4)]">
                    {n}
                  </div>
                  <h3 className="mt-4 text-2xl font-semibold">{title}</h3>
                  <p className="mt-2 text-base text-muted">{body}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section id="recursos" className="relative border-t border-line py-20">
        <div className="page-glow absolute inset-0 -z-10" />
        <div className="mx-auto max-w-6xl px-4">
          <Reveal from="right">
            <h2 className="text-4xl font-bold md:text-5xl">Feito para a quadra</h2>
          </Reveal>
          <div className="mt-8 grid gap-4 md:grid-cols-3">
            {[
              ['Botao na quadra', 'Pressione e o lance dos ultimos 30 segundos e gravado.', 'left'],
              ['Varias cameras', 'Ate 6 angulos por quadra, no mesmo horario.', 'up'],
              ['App e site', 'Assista no celular Lance On ou aqui no navegador.', 'right'],
            ].map(([title, body, from], index) => (
              <Reveal key={title} from={from as 'left' | 'right' | 'up'} delay={index * 100}>
                <div className="surface-card h-full rounded-2xl p-6">
                  <h3 className="text-xl font-semibold text-grass">{title}</h3>
                  <p className="mt-2 text-base text-muted">{body}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <footer id="contato" className="border-t border-line bg-ink py-10">
        <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 md:flex-row md:items-center md:justify-between">
          <BrandLogo variant="full" className="h-12" />
          <div className="flex flex-wrap items-center gap-5 text-base text-muted">
            <a href={INSTAGRAM} target="_blank" rel="noreferrer" className="rounded-full border border-grass/40 p-2 text-grass shadow-[0_0_16px_rgba(30,215,96,0.2)] hover:bg-grass/10" aria-label="Instagram">
              <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" aria-hidden>
                <rect x="3" y="3" width="18" height="18" rx="5" stroke="currentColor" strokeWidth="1.8" />
                <circle cx="12" cy="12" r="4" stroke="currentColor" strokeWidth="1.8" />
                <circle cx="17.5" cy="6.5" r="1.1" fill="currentColor" />
              </svg>
            </a>
            <Link to="/baixar" className="hover:text-white">
              Baixar app
            </Link>
            <Link to="/sobre" className="hover:text-white">
              Sobre
            </Link>
            <a
              href="https://api.lanceonpara.com.br/api/legal/privacy"
              target="_blank"
              rel="noreferrer"
              className="hover:text-white"
            >
              Privacidade
            </a>
            <a
              href="https://api.lanceonpara.com.br/api/legal/terms"
              target="_blank"
              rel="noreferrer"
              className="hover:text-white"
            >
              Termos
            </a>
          </div>
        </div>
      </footer>
    </div>
  )
}
