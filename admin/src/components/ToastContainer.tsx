import { useToast } from '../context/ToastContext'

export function ToastContainer() {
  const { toasts, dismissToast } = useToast()

  return (
    <div className="toast-container" aria-live="polite">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`toast toast-${toast.type} animate-in`}
          role="status"
        >
          <span>{toast.message}</span>
          <button type="button" onClick={() => dismissToast(toast.id)} aria-label="Fechar">
            ×
          </button>
        </div>
      ))}
    </div>
  )
}
