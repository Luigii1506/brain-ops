import { useQuery } from '@tanstack/react-query'

import { PageHeader } from '../components/PageHeader'
import { QueryState } from '../components/QueryState'
import { api } from '../lib/api'

export function MealsPage() {
  const query = useQuery({
    queryKey: ['meals'],
    queryFn: () => api.getMeals(),
  })

  return (
    <section className="page">
      <PageHeader
        eyebrow="Personal"
        title="Comidas"
        description="Historial de comidas registradas. La siguiente fase agrega alta manual desde formulario."
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
                <th>Tipo</th>
                <th>Nota</th>
              </tr>
            </thead>
            <tbody>
              {query.data?.map((row, index) => (
                <tr key={`${row.id ?? index}`}>
                  <td>{String(row.logged_at ?? '')}</td>
                  <td>{String(row.meal_type ?? '')}</td>
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
