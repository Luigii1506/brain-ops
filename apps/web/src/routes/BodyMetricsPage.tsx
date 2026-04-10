import { useQuery } from '@tanstack/react-query'

import { PageHeader } from '../components/PageHeader'
import { QueryState } from '../components/QueryState'
import { api } from '../lib/api'

export function BodyMetricsPage() {
  const query = useQuery({
    queryKey: ['body-metrics'],
    queryFn: () => api.getBodyMetrics(),
  })

  return (
    <section className="page">
      <PageHeader
        eyebrow="Personal"
        title="Body Metrics"
        description="Lectura rápida de snapshots corporales recientes."
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
                <th>Peso</th>
                <th>BF %</th>
                <th>Cintura</th>
              </tr>
            </thead>
            <tbody>
              {query.data?.map((row, index) => (
                <tr key={`${row.id ?? index}`}>
                  <td>{String(row.logged_at ?? '')}</td>
                  <td>{String(row.weight_kg ?? '')}</td>
                  <td>{String(row.body_fat_pct ?? '')}</td>
                  <td>{String(row.waist_cm ?? '')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </QueryState>
      </article>
    </section>
  )
}
