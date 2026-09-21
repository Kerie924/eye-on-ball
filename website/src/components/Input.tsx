import type { InputHTMLAttributes } from 'react'

type Props = InputHTMLAttributes<HTMLInputElement> & {
  label?: string
}

export function Input({ label, className = '', id, ...props }: Props) {
  const inputId = id || props.name
  return (
    <label className="flex w-full flex-col gap-2 text-sm">
      {label ? <span className="font-medium text-muted">{label}</span> : null}
      <input
        id={inputId}
        className={`w-full rounded-xl border border-line bg-ink-soft px-4 py-3 text-white outline-none transition placeholder:text-white/30 focus:border-grass ${className}`}
        {...props}
      />
    </label>
  )
}
