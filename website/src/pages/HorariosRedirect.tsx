import { Navigate } from 'react-router-dom'

/** Atalho da navegacao: o fluxo de horarios comeca pela escolha de cidade/quadra. */
export function HorariosRedirectPage() {
  return <Navigate to="/app/cidades" replace />
}
