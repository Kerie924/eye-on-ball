import { useEffect, useMemo, useState } from 'react'

interface UsePaginationResult<T> {
  page: number
  setPage: (page: number) => void
  pageSize: number
  total: number
  totalPages: number
  pageItems: T[]
  from: number
  to: number
}

export function usePagination<T>(
  items: T[],
  pageSize = 6,
  resetKey?: string | number,
): UsePaginationResult<T> {
  const [page, setPage] = useState(1)

  const total = items.length
  const totalPages = Math.max(1, Math.ceil(total / pageSize) || 1)

  useEffect(() => {
    setPage(1)
  }, [resetKey, pageSize])

  useEffect(() => {
    if (page > totalPages) {
      setPage(totalPages)
    }
  }, [page, totalPages])

  const safePage = Math.min(page, totalPages)

  const pageItems = useMemo(() => {
    const start = (safePage - 1) * pageSize
    return items.slice(start, start + pageSize)
  }, [items, safePage, pageSize])

  const from = total === 0 ? 0 : (safePage - 1) * pageSize + 1
  const to = Math.min(safePage * pageSize, total)

  return {
    page: safePage,
    setPage,
    pageSize,
    total,
    totalPages,
    pageItems,
    from,
    to,
  }
}
