import type { ButtonHTMLAttributes, ReactNode } from 'react'

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'outline' | 'ghost' | 'danger'
  children: ReactNode
}

const styles = {
  primary:
    'bg-grass text-on-grass hover:bg-grass-bright shadow-[0_0_28px_rgba(30,215,96,0.35)]',
  outline: 'border-2 border-grass text-grass hover:bg-grass/10',
  ghost: 'text-white/80 hover:bg-white/5',
  danger: 'border border-danger text-danger hover:bg-danger/10',
}

export function Button({
  variant = 'primary',
  className = '',
  children,
  ...props
}: Props) {
  return (
    <button
      className={`btn-shine inline-flex items-center justify-center gap-2 rounded-lg px-5 py-3 text-lg font-semibold transition duration-200 hover:-translate-y-0.5 active:translate-y-0 disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:translate-y-0 ${styles[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}
