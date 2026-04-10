import { Navigate, Route, Routes } from 'react-router-dom'

import { AppShell } from '../components/AppShell'
import { BodyMetricsPage } from '../routes/BodyMetricsPage'
import { DashboardPage } from '../routes/DashboardPage'
import { ExpensesPage } from '../routes/ExpensesPage'
import { HabitsPage } from '../routes/HabitsPage'
import { MealsPage } from '../routes/MealsPage'
import { ProjectDetailPage } from '../routes/ProjectDetailPage'
import { ProjectsPage } from '../routes/ProjectsPage'
import { ReviewsPage } from '../routes/ReviewsPage'
import { TasksPage } from '../routes/TasksPage'
import { WorkoutsPage } from '../routes/WorkoutsPage'

export function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/tasks" element={<TasksPage />} />
        <Route path="/expenses" element={<ExpensesPage />} />
        <Route path="/meals" element={<MealsPage />} />
        <Route path="/workouts" element={<WorkoutsPage />} />
        <Route path="/habits" element={<HabitsPage />} />
        <Route path="/body-metrics" element={<BodyMetricsPage />} />
        <Route path="/reviews" element={<ReviewsPage />} />
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/projects/:projectName" element={<ProjectDetailPage />} />
        <Route path="*" element={<Navigate replace to="/" />} />
      </Routes>
    </AppShell>
  )
}
