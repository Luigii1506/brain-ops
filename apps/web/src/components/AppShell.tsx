import type { PropsWithChildren } from 'react'
import { NavLink } from 'react-router-dom'

type NavItem = {
  to: string
  label: string
}

const personalLinks: NavItem[] = [
  { to: '/', label: 'Hoy' },
  { to: '/tasks', label: 'Tasks' },
  { to: '/expenses', label: 'Gastos' },
  { to: '/meals', label: 'Comidas' },
  { to: '/workouts', label: 'Workouts' },
  { to: '/habits', label: 'Hábitos' },
  { to: '/body-metrics', label: 'Body Metrics' },
  { to: '/reviews', label: 'Reviews' },
]

const projectLinks: NavItem[] = [{ to: '/projects', label: 'Proyectos' }]

function renderLink(item: NavItem) {
  return (
    <NavLink
      key={item.to}
      className={({ isActive }) =>
        `sidebar__link${isActive ? ' sidebar__link--active' : ''}`
      }
      to={item.to}
      end={item.to === '/'}
    >
      {item.label}
    </NavLink>
  )
}

export function AppShell({ children }: PropsWithChildren) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar__brand">
          <h1>brain-ops</h1>
          <p>UI local-first para operar Personal y Projects sin depender del terminal.</p>
        </div>

        <section className="sidebar__group">
          <span className="sidebar__group-label">Personal</span>
          <nav className="sidebar__nav">{personalLinks.map(renderLink)}</nav>
        </section>

        <section className="sidebar__group">
          <span className="sidebar__group-label">Projects</span>
          <nav className="sidebar__nav">{projectLinks.map(renderLink)}</nav>
        </section>
      </aside>

      <main className="content">{children}</main>
    </div>
  )
}
