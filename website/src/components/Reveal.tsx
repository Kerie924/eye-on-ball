import { useEffect, useRef, useState, type ReactNode } from 'react'

type Props = {
  children: ReactNode
  from?: 'left' | 'right' | 'up'
  className?: string
  delay?: number
}

export function Reveal({ children, from = 'up', className = '', delay = 0 }: Props) {
  const ref = useRef<HTMLDivElement>(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const node = ref.current
    if (!node) return
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) setVisible(true)
      },
      { threshold: 0.18, rootMargin: '0px 0px -8% 0px' },
    )
    observer.observe(node)
    return () => observer.disconnect()
  }, [])

  return (
    <div
      ref={ref}
      style={{ transitionDelay: `${delay}ms` }}
      className={`reveal reveal-${from} ${visible ? 'reveal-in' : ''} ${className}`}
    >
      {children}
    </div>
  )
}
