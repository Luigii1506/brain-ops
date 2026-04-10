import { useQuery } from '@tanstack/react-query'

import { PageHeader } from '../components/PageHeader'
import { QueryState } from '../components/QueryState'
import { api } from '../lib/api'

export function WorkoutsPage() {
  const query = useQuery({
    queryKey: ['workouts'],
    queryFn: () => api.getWorkouts(),
  })

  return (
    <section className="page">
      <PageHeader
        eyebrow="Personal"
        title="Workouts"
        description="Historial de sesiones de entrenamiento almacenadas en SQLite."
      />
      <article className="card">
        <QueryState
          isLoading={query.isLoading}
          error={query.error}
          empty={!query.data || query.data.length === 0}
        >
          <table className="table">
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Rutina</th>
                <th>Duración</th>
                <th>Nota</th>
              </tr>
            </thead>
            <tbody>
              {query.data?.map((row, index) => (
                <tr key={`${row.id ?? index}`}>
                  <td>{String(row.logged_at ?? '')}</td>
                  <td>{String(row.routine_name ?? '')}</td>
                  <td>{String(row.duration_minutes ?? '')}</td>
                  <td>{String(row.note ?? '')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </QueryState>
      </article>
    </section>
  )
}
