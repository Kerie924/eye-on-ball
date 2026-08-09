interface PaginationBarProps {
  from: number
  to: number
  total: number
  page: number
  totalPages: number
  onPageChange: (page: number) => void
  label?: string
}

export function PaginationBar({
  from,
  to,
  total,
  page,
  totalPages,
  onPageChange,
  label = 'itens',
}: PaginationBarProps) {
  const pages = Array.from({ length: totalPages }, (_, index) => index + 1).slice(
    Math.max(0, page - 3),
    Math.max(0, page - 3) + 5,
  )

  return (
    <div className="pagination-bar">
      <span className="pagination-info">
        Mostrando {from} a {to} de {total} {label}
      </span>
      <div className="pagination-controls">
        <button
          type="button"
          className="pagination-btn"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          ‹
        </button>
        {pages.map((item) => (
          <button
            key={item}
            type="button"
            className={item === page ? 'pagination-btn active' : 'pagination-btn'}
            onClick={() => onPageChange(item)}
          >
            {item}
          </button>
        ))}
        <button
          type="button"
          className="pagination-btn"
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
        >
          ›
        </button>
      </div>
    </div>
  )
}
