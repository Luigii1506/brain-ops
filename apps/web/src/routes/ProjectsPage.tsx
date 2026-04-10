import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { PageHeader } from '../components/PageHeader'
import { QueryState } from '../components/QueryState'
import { api } from '../lib/api'

export function ProjectsPage() {
  const projectsQuery = useQuery({
    queryKey: ['projects'],
    queryFn: () => api.getProjects(),
  })

  return (
    <section className="page">
      <PageHeader
        eyebrow="Projects"
        title="Proyectos"
        description="Contexto operativo, pendientes y acceso rápido a logs, sesión y refresh."
      />

      <QueryState
        isLoading={projectsQuery.isLoading}
        error={projectsQuery.error}
        empty={!projectsQuery.data || projectsQuery.data.length === 0}
      >
        <div className="grid">
          {projectsQuery.data?.map((project) => (
            <article className="card" key={project.name}>
              <div className="toolbar">
                <div>
                  <Link className="list__item-title" to={`/projects/${project.name}`}>
                    {project.name}
                  </Link>
                  <p className="list__item-meta">
                    {project.context.phase ?? 'Sin fase definida'} ·{' '}
                    {(project.context.pending ?? []).length} pendientes ·{' '}
                    {(project.context.decisions ?? []).length} decisiones
                  </p>
                </div>
                <Link className="button button--secondary" to={`/projects/${project.name}`}>
                  Abrir
                </Link>
              </div>
            </article>
          ))}
        </div>
      </QueryState>
    </section>
  )
}
