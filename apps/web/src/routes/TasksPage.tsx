import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import { PageHeader } from '../components/PageHeader'
import { QueryState } from '../components/QueryState'
import { api } from '../lib/api'
import { cn } from '../lib/format'

export function TasksPage() {
  const queryClient = useQueryClient()
  const [title, setTitle] = useState('')
  const [project, setProject] = useState('')
  const [priority, setPriority] = useState('medium')
  const [dueDate, setDueDate] = useState('')
  const [focusDate, setFocusDate] = useState('')
  const [note, setNote] = useState('')

  const tasksQuery = useQuery({
    queryKey: ['tasks', 'all'],
    queryFn: () => api.getTasks(''),
  })
  const projectsQuery = useQuery({
    queryKey: ['projects'],
    queryFn: () => api.getProjects(),
  })

  const createTask = useMutation({
    mutationFn: () =>
      api.createTask({
        title,
        project: project || null,
        priority,
        due_date: dueDate || null,
        focus_date: focusDate || null,
        note: note || null,
      }),
    onSuccess: async () => {
      setTitle('')
      setProject('')
      setPriority('medium')
      setDueDate('')
      setFocusDate('')
      setNote('')
      await queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })

  const completeTask = useMutation({
    mutationFn: (taskId: number) => api.completeTask(taskId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })

  return (
    <section className="page">
      <PageHeader
        eyebrow="Personal"
        title="Tasks"
        description="Una sola bandeja para tareas personales y tareas ligadas a proyectos."
      />

      <div className="split">
        <article className="card">
          <h3>Nueva tarea</h3>
          <form
            className="stack"
            onSubmit={(event) => {
              event.preventDefault()
              if (!title.trim()) {
                return
              }
              createTask.mutate()
            }}
          >
            <div className="field">
              <label htmlFor="task-title">Título</label>
              <input
                id="task-title"
                onChange={(event) => setTitle(event.target.value)}
                placeholder="Ej. preparar cierre semanal"
                value={title}
              />
            </div>

            <div className="form-grid">
              <div className="field">
                <label htmlFor="task-project">Proyecto</label>
                <select
                  id="task-project"
                  onChange={(event) => setProject(event.target.value)}
                  value={project}
                >
                  <option value="">Personal</option>
                  {projectsQuery.data?.map((item) => (
                    <option key={item.name} value={item.name}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="field">
                <label htmlFor="task-priority">Prioridad</label>
                <select
                  id="task-priority"
                  onChange={(event) => setPriority(event.target.value)}
                  value={priority}
                >
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>

              <div className="field">
                <label htmlFor="task-due">Due date</label>
                <input
                  id="task-due"
                  onChange={(event) => setDueDate(event.target.value)}
                  type="date"
                  value={dueDate}
                />
              </div>

              <div className="field">
                <label htmlFor="task-focus">Focus date</label>
                <input
                  id="task-focus"
                  onChange={(event) => setFocusDate(event.target.value)}
                  type="date"
                  value={focusDate}
                />
              </div>
            </div>

            <div className="field">
              <label htmlFor="task-note">Nota</label>
              <textarea
                id="task-note"
                onChange={(event) => setNote(event.target.value)}
                placeholder="Contexto o siguiente paso"
                value={note}
              />
            </div>

            <div className="actions">
              <button className="button" disabled={createTask.isPending} type="submit">
                {createTask.isPending ? 'Guardando…' : 'Crear tarea'}
              </button>
            </div>
          </form>
        </article>

        <article className="card">
          <h3>Resumen</h3>
          <QueryState
            isLoading={tasksQuery.isLoading}
            error={tasksQuery.error}
            empty={!tasksQuery.data}
          >
            <div className="grid grid--cards">
              {Object.entries(tasksQuery.data?.counts ?? {}).map(([status, count]) => (
                <div className="list__item" key={status}>
                  <p className="list__item-title">{status}</p>
                  <p className="list__item-meta">{count} tareas</p>
                </div>
              ))}
            </div>
          </QueryState>
        </article>
      </div>

      <article className="card">
        <div className="toolbar">
          <h3>Todas las tareas activas</h3>
        </div>
        <QueryState
          isLoading={tasksQuery.isLoading}
          error={tasksQuery.error}
          empty={!tasksQuery.data || tasksQuery.data.items.length === 0}
          emptyMessage="No hay tareas activas todavía."
        >
          <ul className="list">
            {tasksQuery.data?.items.map((task) => (
              <li className="list__item" key={task.id}>
                <div className="toolbar">
                  <div>
                    <p className="list__item-title">{task.title}</p>
                    <p className="list__item-meta">
                      {task.project ?? 'personal'} · due {task.due_date ?? 'sin fecha'} · focus{' '}
                      {task.focus_date ?? 'sin fecha'}
                    </p>
                  </div>
                  <div className="actions">
                    <span className={cn('pill', `pill--${task.priority}`)}>{task.priority}</span>
                    <button
                      className="button button--secondary"
                      disabled={completeTask.isPending}
                      onClick={() => completeTask.mutate(task.id)}
                      type="button"
                    >
                      Marcar done
                    </button>
                  </div>
                </div>
                {task.note ? <p className="list__item-meta">{task.note}</p> : null}
              </li>
            ))}
          </ul>
        </QueryState>
      </article>
    </section>
  )
}
