import { useQuery } from '@tanstack/react-query'

import { PageHeader } from '../components/PageHeader'
import { QueryState } from '../components/QueryState'
import { api } from '../lib/api'

export function ReviewsPage() {
  const dailyQuery = useQuery({
    queryKey: ['daily-review'],
    queryFn: () => api.getDailyReview(),
  })
  const weeklyQuery = useQuery({
    queryKey: ['weekly-review'],
    queryFn: () => api.getWeeklyReview(),
  })

  return (
    <section className="page">
      <PageHeader
        eyebrow="Personal"
        title="Reviews"
        description="Daily y weekly review expuestos en la web para consulta rápida."
      />

      <div className="split">
        <article className="card">
          <h3>Daily review</h3>
          <QueryState
            isLoading={dailyQuery.isLoading}
            error={dailyQuery.error}
            empty={!dailyQuery.data}
          >
            <div className="stack">
              <div className="pill-row">
                <span className="pill">Score {dailyQuery.data?.score}</span>
                <span className="pill">Fecha {dailyQuery.data?.date}</span>
              </div>
              <div>
                <strong>Highlights</strong>
                <ul className="list">
                  {dailyQuery.data?.highlights.map((item) => (
                    <li className="list__item" key={item}>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <strong>Gaps</strong>
                <ul className="list">
                  {dailyQuery.data?.gaps.map((item) => (
                    <li className="list__item" key={item}>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </QueryState>
        </article>

        <article className="card">
          <h3>Weekly review</h3>
          <QueryState
            isLoading={weeklyQuery.isLoading}
            error={weeklyQuery.error}
            empty={!weeklyQuery.data}
          >
            <div className="stack">
              <div className="pill-row">
                <span className="pill">Score {weeklyQuery.data?.score}</span>
                <span className="pill">
                  {weeklyQuery.data?.start_date} → {weeklyQuery.data?.end_date}
                </span>
              </div>
              <ul className="list">
                <li className="list__item">Días con data: {weeklyQuery.data?.days_with_data}</li>
                <li className="list__item">Workout days: {weeklyQuery.data?.workout_days}</li>
                <li className="list__item">Total sets: {weeklyQuery.data?.total_sets}</li>
                <li className="list__item">Gasto total: {weeklyQuery.data?.total_spending}</li>
              </ul>
              <div>
                <strong>Trends</strong>
                <ul className="list">
                  {weeklyQuery.data?.trends.map((item) => (
                    <li className="list__item" key={item}>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </QueryState>
        </article>
      </div>
    </section>
  )
}
