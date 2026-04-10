import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'

import { PageHeader } from '../components/PageHeader'
import { QueryState } from '../components/QueryState'
import { api } from '../lib/api'

export function ProjectDetailPage() {
  const { projectName = '' } = useParams()
  const queryClient = useQueryClient()
  const [taskTitle, setTaskTitle] = useState('')
  const [taskPriority, setTaskPriority] = useState('medium')
  const [taskDueDate, setTaskDueDate] = useState('')
  const [logText, setLogText] = useState('')

  const projectQuery = useQuery({
    queryKey: ['project', projectName],
    queryFn: () => api.getProject(projectName),
    enabled: Boolean(projectName),
  })
  const tasksQuery = useQuery({
    queryKey: ['project', projectName, 'tasks'],
    queryFn: () => api.getProjectTasks(projectName),
    enabled: Boolean(projectName),
  })
  const logsQuery = useQuery({
    queryKey: ['project', projectName, 'logs'],
    queryFn: () => api.getProjectLogs(projectName),
    enabled: Boolean(projectName),
  })
  const sessionQuery = useQuery({
    queryKey: ['project', projectName, 'session'],
    queryFn: () => api.getProjectSession(projectName),
    enabled: Boolean(projectName),
  })
  const auditQuery = useQuery({
    queryKey: ['project', projectName, 'audit'],
    queryFn: () => api.getProjectAudit(projectName),
    enabled: Boolean(projectName),
  })

  const createTask = useMutation({
    mutationFn: () =>
      api.createProjectTask(projectName, {
        title: taskTitle,
        priority: taskPriority,
        due_date: taskDueDate || null,
      }),
    onSuccess: async () => {
      setTaskTitle('')
      setTaskPriority('medium')
      setTaskDueDate('')
      await queryClient.invalidateQueries({ queryKey: ['project', projectName, 'tasks'] })
      await queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })

  const createLog = useMutation({
    mutationFn: () => api.createProjectLog(projectName, logText),
    onSuccess: async () => {
      setLogText('')
      await queryClient.invalidateQueries({ queryKey: ['project', projectName, 'logs'] })
      await queryClient.invalidateQueries({ queryKey: ['project', projectName, 'session'] })
      await queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })

  const refreshProject = useMutation({
    mutationFn: () => api.refreshProject(projectName),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['project', projectName, 'session'] })
      await queryClient.invalidateQueries({ queryKey: ['project', projectName, 'audit'] })
      await queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })

  const pendingItems = useMemo(
    () => projectQuery.data?.context.pending ?? [],
    [projectQuery.data?.context.pending],
  )

  return (
    <section className="page">
      <PageHeader
        eyebrow="Projects"
        title={projectName}
        description="Tareas, logs, contexto y operaciones del proyecto desde la UI local."
        actions={
          <button
            className="button"
            disabled={refreshProject.isPending}
            onClick={() => refreshProject.mutate()}
            type="button"
          >
            {refreshProject.isPending ? 'Refrescando…' : 'Refresh project'}
          </button>
        }
      />

      <QueryState isLoading={projectQuery.isLoading} error={projectQuery.error} empty={!projectQuery.data}>
        {projectQuery.data ? (
          <>
            <div className="grid grid--cards">
              <div className="card">
                <div className="stat-card__label">Fase</div>
                <div className="stat-card__value">{projectQuery.data.context.phase ?? 'N/D'}</div>
              </div>
              <div className="card">
                <div className="stat-card__label">Pendientes</div>
                <div className="stat-card__value">{pendingItems.length}</div>
              </div>
              <div className="card">
                <div className="stat-card__label">Score audit</div>
                <div className="stat-card__value">{auditQuery.data?.score ?? '—'}</div>
              </div>
            </div>

            <div className="grid grid--main">
              <div className="stack">
                <article className="card">
                  <h3>Tareas del proyecto</h3>
                  <form
                    className="stack"
                    onSubmit={(event) => {
                      event.preventDefault()
                      if (!taskTitle.trim()) {
                        return
                      }
                      createTask.mutate()
                    }}
                  >
                    <div className="form-grid">
                      <div className="field">
                        <label htmlFor="project-task-title">Título</label>
                        <input
                          id="project-task-title"
                          onChange={(event) => setTaskTitle(event.target.value)}
                          value={taskTitle}
                        />
                      </div>
                      <div className="field">
                        <label htmlFor="project-task-priority">Prioridad</label>
                        <select
                          id="project-task-priority"
                          onChange={(event) => setTaskPriority(event.target.value)}
                          value={taskPriority}
                        >
                          <option value="high">High</option>
                          <option value="medium">Medium</option>
                          <option value="low">Low</option>
                        </select>
                      </div>
                      <div className="field">
                        <label htmlFor="project-task-due">Due date</label>
                        <input
                          id="project-task-due"
                          onChange={(event) => setTaskDueDate(event.target.value)}
                          type="date"
                          value={taskDueDate}
                        />
                      </div>
                    </div>

                    <div className="actions">
                      <button className="button" disabled={createTask.isPending} type="submit">
                        {createTask.isPending ? 'Guardando…' : 'Agregar tarea'}
                      </button>
                    </div>
                  </form>

                  <QueryState
                    isLoading={tasksQuery.isLoading}
                    error={tasksQuery.error}
                    empty={!tasksQuery.data || tasksQuery.data.items.length === 0}
                    emptyMessage="Todavía no hay tareas ligadas a este proyecto."
                  >
                    <ul className="list">
                      {tasksQuery.data?.items.map((task) => (
                        <li className="list__item" key={task.id}>
                          <p className="list__item-title">{task.title}</p>
                          <p className="list__item-meta">
                            {task.priority} · due {task.due_date ?? 'sin fecha'}
                          </p>
                        </li>
                      ))}
                    </ul>
                  </QueryState>
                </article>

                <article className="card">
                  <h3>Project log</h3>
                  <form
                    className="stack"
                    onSubmit={(event) => {
                      event.preventDefault()
                      if (!logText.trim()) {
                        return
                      }
                      createLog.mutate()
                    }}
                  >
                    <div className="field">
                      <label htmlFor="project-log-text">Texto</label>
                      <textarea
                        id="project-log-text"
                        onChange={(event) => setLogText(event.target.value)}
                        placeholder='Ej. next: conectar capture con frontend'
                        value={logText}
                      />
                    </div>
                    <div className="actions">
                      <button className="button" disabled={createLog.isPending} type="submit">
                        {createLog.isPending ? 'Guardando…' : 'Agregar log'}
                      </button>
                    </div>
                  </form>

                  <QueryState
                    isLoading={logsQuery.isLoading}
                    error={logsQuery.error}
                    empty={!logsQuery.data || logsQuery.data.length === 0}
                  >
                    <ul className="list">
                      {logsQuery.data?.map((log, index) => (
                        <li className="list__item" key={`${log.logged_at ?? 'log'}-${index}`}>
                          <p className="list__item-title">{log.entry_text ?? 'Sin texto'}</p>
                          <p className="list__item-meta">
                            {log.entry_type ?? 'update'} · {log.logged_at ?? 'sin fecha'}
                          </p>
                        </li>
                      ))}
                    </ul>
                  </QueryState>
                </article>
              </div>

              <div className="stack">
                <article className="card">
                  <h3>Contexto</h3>
                  <div className="stack">
                    <div>
                      <strong>Decisiones</strong>
                      <ul className="list">
                        {(projectQuery.data.context.decisions ?? []).slice(-4).map((item) => (
                          <li className="list__item" key={item}>
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <strong>Pendientes</strong>
                      <ul className="list">
                        {pendingItems.slice(-4).map((item) => (
                          <li className="list__item" key={item}>
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </article>

                <article className="card">
                  <h3>Sesión</h3>
                  <QueryState
                    isLoading={sessionQuery.isLoading}
                    error={sessionQuery.error}
                    empty={!sessionQuery.data}
                  >
                    <pre className="code-block">
                      {JSON.stringify(
                        {
                          recent_commits: sessionQuery.data?.recent_commits.slice(0, 5),
                          recent_logs: sessionQuery.data?.recent_logs.slice(0, 5),
                          vault_status: sessionQuery.data?.vault_status,
                        },
                        null,
                        2,
                      )}
                    </pre>
                  </QueryState>
                </article>

                <article className="card">
                  <h3>Audit</h3>
                  <QueryState
                    isLoading={auditQuery.isLoading}
                    error={auditQuery.error}
                    empty={!auditQuery.data}
                  >
                    <div className="pill-row">
                      <span className="pill">Score {auditQuery.data?.score}</span>
                    </div>
                    <ul className="list">
                      {(auditQuery.data?.issues ?? []).map((issue) => (
                        <li className="list__item" key={issue}>
                          {issue}
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
