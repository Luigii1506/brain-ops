import type { ReactNode } from 'react'

type QueryStateProps = {
  isLoading: boolean
  error: Error | null
  empty?: boolean
  emptyMessage?: string
  children: ReactNode
}

export function QueryState({
  isLoading,
  error,
  empty = false,
  emptyMessage = 'No hay datos.',
  children,
}: QueryStateProps) {
  if (isLoading) {
    return <div className="loading">Cargando…</div>
  }

  if (error) {
    return <div className="error">{error.message}</div>
  }

  if (empty) {
    return <div className="empty">{emptyMessage}</div>
  }

  return <>{children}</>
}
