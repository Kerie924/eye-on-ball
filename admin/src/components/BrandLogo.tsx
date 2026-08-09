import companyLogo from '../assets/brand/company-logo.png'
import mark from '../assets/brand/mark.png'
import wordmark from '../assets/brand/wordmark.png'

type BrandVariant = 'full' | 'mark' | 'wordmark'

interface BrandLogoProps {
  variant?: BrandVariant
  className?: string
  alt?: string
}

const SOURCES: Record<BrandVariant, string> = {
  full: companyLogo,
  mark: mark,
  wordmark: wordmark,
}

export function BrandLogo({
  variant = 'full',
  className = '',
  alt = 'Olho no Lance',
}: BrandLogoProps) {
  return (
    <img
      src={SOURCES[variant]}
      alt={alt}
      className={`brand-logo brand-logo-${variant} ${className}`.trim()}
    />
  )
}
