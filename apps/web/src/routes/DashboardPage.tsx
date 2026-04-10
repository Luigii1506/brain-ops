import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { PageHeader } from '../components/PageHeader'
import { QueryState } from '../components/QueryState'
import { StatCard } from '../components/StatCard'
import { api } from '../lib/api'
import { formatMoney } from '../lib/format'

export function DashboardPage() {
  const statusQuery = useQuery({
    queryKey: ['daily-status'],
    queryFn: () => api.getDailyStatus(),
  })
  const tasksQuery = useQuery({
    queryKey: ['tasks', 'focus'],
    queryFn: () => api.getTasks('?focus_today=true'),
  })
  const projectsQuery = useQuery({
    queryKey: ['projects'],
    queryFn: () => api.getProjects(),
  })

  return (
    <section className="page">
      <PageHeader
        eyebrow="Personal"
        title="Panel de hoy"
        description="Estado diario, pendientes con foco y accesos rápidos a lo que más vas a usar."
        actions={
          <>
            <Link className="button button--secondary" to="/tasks">
              Ver tareas
            </Link>
            <Link className="button" to="/projects">
              Abrir proyectos
            </Link>
          </>
        }
      />

      <QueryState
        isLoading={statusQuery.isLoading}
        error={statusQuery.error}
        empty={!statusQuery.data}
      >
        {statusQuery.data ? (
          <>
            <div className="grid grid--cards">
              <StatCard
                label="Calorías"
                value={`${Math.round(statusQuery.data.calories_actual)}`}
                hint={
                  statusQuery.data.calories_target
                    ? `Target ${Math.round(statusQuery.data.calories_target)}`
                    : 'Sin target'
                }
              />
              <StatCard
                label="Proteína"
                value={`${Math.round(statusQuery.data.protein_g_actual)} g`}
                hint={
                  statusQuery.data.protein_g_target
                    ? `Restan ${Math.max(Math.round(statusQuery.data.protein_g_remaining ?? 0), 0)} g`
                    : 'Sin target'
                }
              />
              <StatCard
                label="Gasto"
                value={formatMoney(statusQuery.data.expenses_total, statusQuery.data.expense_currency)}
                hint={`Fecha ${statusQuery.data.date}`}
              />
              <StatCard
                label="Workout"
                value={`${statusQuery.data.workouts_logged}`}
                hint={`${statusQuery.data.total_workout_sets} sets`}
              />
              <StatCard
                label="Hábitos"
                value={`${statusQuery.data.habits_completed.length}`}
                hint={`${statusQuery.data.habit_pending.length} pendientes`}
              />
              <StatCard
                label="Suplementos"
                value={`${statusQuery.data.supplements_logged}`}
                hint={statusQuery.data.supplement_names.join(', ') || 'Sin logs'}
              />
            </div>

            <div className="grid grid--main">
              <article className="card stack">
                <h3>Foco de hoy</h3>
                <QueryState
                  isLoading={tasksQuery.isLoading}
                  error={tasksQuery.error}
                  empty={!tasksQuery.data || tasksQuery.data.items.length === 0}
                  emptyMessage="No hay tareas con focus date activo."
                >
                  <ul className="list">
                    {tasksQuery.data?.items.map((task) => (
                      <li className="list__item" key={task.id}>
                        <p className="list__item-title">{task.title}</p>
                        <div className="pill-row">
                          <span className={`pill pill--${task.priority}`}>{task.priority}</span>
                          <span className="pill">{task.project ?? 'personal'}</span>
                        </div>
                        <p className="list__item-meta">
                          Due {task.due_date ?? 'sin fecha'} · Focus {task.focus_date ?? 'sin fecha'}
                        </p>
                      </li>
                    ))}
                  </ul>
                </QueryState>
              </article>

              <div className="stack">
                <article className="card">
                  <h3>Señales del día</h3>
                  <div className="pill-row">
                    {statusQuery.data.missing_diet_meals.map((item) => (
                      <span className="pill" key={item}>
                        Falta {item}
                      </span>
                    ))}
                    {statusQuery.data.habit_pending.map((item) => (
                      <span className="pill" key={item}>
                        Hábito: {item}
                      </span>
                    ))}
                    {statusQuery.data.missing_diet_meals.length === 0 &&
                    statusQuery.data.habit_pending.length === 0 ? (
                      <span className="pill">Sin gaps importantes detectados</span>
                    ) : null}
                  </div>
                </article>

                <article className="card">
                  <h3>Proyectos activos</h3>
                  <QueryState
                    isLoading={projectsQuery.isLoading}
                    error={projectsQuery.error}
                    empty={!projectsQuery.data || projectsQuery.data.length === 0}
                  >
                    <ul className="list">
                      {projectsQuery.data?.slice(0, 5).map((project) => (
                        <li className="list__item" key={project.name}>
                          <Link className="list__item-title" to={`/projects/${project.name}`}>
                            {project.name}
                          </Link>
                          <p className="list__item-meta">
                            {project.context.phase ?? 'Sin fase'} ·{' '}
                            {(project.context.pending ?? []).length} pendientes
                          </p>
                        </li>
                      ))}
                    </ul>
                  </QueryState>
                </article>
              </div>
            </div>
          </>
        ) : null}
      </QueryState>
    </section>
  )
}
