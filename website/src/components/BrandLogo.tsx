import { Link } from 'react-router-dom'

import mark from '../assets/brand/mark.png'
import wordmark from '../assets/brand/wordmark.png'
import companyLogo from '../assets/brand/company-logo.png'

type Props = {
  variant?: 'mark' | 'wordmark' | 'full'
  className?: string
  to?: string
}

const sources = {
  mark,
  wordmark,
  full: companyLogo,
} as const

export function BrandLogo({ variant = 'full', className = '', to = '/' }: Props) {
  const hasSize = /\bh-/.test(className)
  const defaults = variant === 'mark' ? 'h-12 w-12' : 'h-14 md:h-16'

  return (
    <Link to={to} className="inline-flex shrink-0 items-center" aria-label="Lance On">
      <img
        src={sources[variant]}
        alt="Lance On"
        className={`w-auto object-contain object-left ${hasSize ? '' : defaults} ${className}`}
      />
    </Link>
  )
}
