import { useQuery } from '@tanstack/react-query'

import { PageHeader } from '../components/PageHeader'
import { QueryState } from '../components/QueryState'
import { api } from '../lib/api'

export function HabitsPage() {
  const habitsQuery = useQuery({
    queryKey: ['habits'],
    queryFn: () => api.getHabits(),
  })
  const supplementsQuery = useQuery({
    queryKey: ['supplements'],
    queryFn: () => api.getSupplements(),
  })

  return (
    <section className="page">
      <PageHeader
        eyebrow="Personal"
        title="Hábitos y suplementos"
        description="Dos vistas rápidas sobre check-ins y suplementos ya registrados."
      />

      <div className="split">
        <article className="card">
          <h3>Hábitos</h3>
          <QueryState
            isLoading={habitsQuery.isLoading}
            error={habitsQuery.error}
            empty={!habitsQuery.data || habitsQuery.data.length === 0}
          >
            <ul className="list">
              {habitsQuery.data?.map((row, index) => (
                <li className="list__item" key={`${row.id ?? index}`}>
                  <p className="list__item-title">{String(row.habit_name ?? '')}</p>
                  <p className="list__item-meta">
                    {String(row.status ?? '')} · {String(row.checked_at ?? '')}
                  </p>
                </li>
              ))}
            </ul>
          </QueryState>
        </article>

        <article className="card">
          <h3>Suplementos</h3>
          <QueryState
            isLoading={supplementsQuery.isLoading}
            error={supplementsQuery.error}
            empty={!supplementsQuery.data || supplementsQuery.data.length === 0}
          >
            <ul className="list">
              {supplementsQuery.data?.map((row, index) => (
                <li className="list__item" key={`${row.id ?? index}`}>
                  <p className="list__item-title">{String(row.supplement_name ?? '')}</p>
                  <p className="list__item-meta">
                    {String(row.amount ?? '')} {String(row.unit ?? '')} · {String(row.logged_at ?? '')}
                  </p>
                </li>
              ))}
            </ul>
          </QueryState>
        </article>
      </div>
    </section>
  )
}
