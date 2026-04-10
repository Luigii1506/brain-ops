import type {
  BudgetStatus,
  DailyReview,
  DailyStatus,
  ExpenseMeta,
  PersonalRecord,
  Project,
  ProjectAudit,
  ProjectLog,
  ProjectSession,
  SpendingSummary,
  Task,
  TaskListResponse,
  WeeklyReview,
} from '../types/api'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api'

class ApiError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
  })

  if (!response.ok) {
    let detail = response.statusText
    try {
      const data = (await response.json()) as { detail?: string }
      detail = data.detail ?? detail
    } catch {
      // ignore invalid json
    }
    throw new ApiError(detail)
  }

  return (await response.json()) as T
}

export const api = {
  getDailyStatus(date?: string) {
    const query = date ? `?date_str=${encodeURIComponent(date)}` : ''
    return request<DailyStatus>(`/personal/daily-status${query}`)
  },
  getDailyReview(date?: string) {
    const query = date ? `?date_str=${encodeURIComponent(date)}` : ''
    return request<DailyReview>(`/personal/daily-review${query}`)
  },
  getWeeklyReview(date?: string) {
    const query = date ? `?date_str=${encodeURIComponent(date)}` : ''
    return request<WeeklyReview>(`/personal/week-review${query}`)
  },
  getTasks(query = '') {
    return request<TaskListResponse>(`/personal/tasks${query}`)
  },
  createTask(payload: {
    title: string
    project?: string | null
    priority?: string
    due_date?: string | null
    focus_date?: string | null
    tags?: string[]
    note?: string | null
  }) {
    return request<Task>('/personal/tasks', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  completeTask(taskId: number) {
    return request<Task>(`/personal/tasks/${taskId}/done`, {
      method: 'POST',
    })
  },
  updateTask(
    taskId: number,
    payload: {
      status?: string
      priority?: string
      note?: string | null
      due_date?: string | null
      focus_date?: string | null
      project?: string | null
    },
  ) {
    return request<Task>(`/personal/tasks/${taskId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    })
  },
  getExpenses() {
    return request<PersonalRecord[]>('/personal/expenses')
  },
  getExpenseMeta() {
    return request<ExpenseMeta>('/personal/expenses/meta')
  },
  createExpense(payload: {
    amount: number
    category?: string | null
    merchant?: string | null
    currency?: string
    note?: string | null
    logged_at?: string | null
  }) {
    return request<{ result: object; expense: PersonalRecord | null }>('/personal/expenses', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  deleteExpense(expenseId: number) {
    return request<{ deleted: number }>(`/personal/expenses/${expenseId}`, {
      method: 'DELETE',
    })
  },
  getSpendingSummary(date?: string, currency = 'MXN') {
    const params = new URLSearchParams()
    if (date) {
      params.set('date_str', date)
    }
    params.set('currency', currency)
    const query = params.toString()
    return request<SpendingSummary>(`/personal/spending-summary?${query}`)
  },
  getBudgetStatus(period = 'weekly', date?: string) {
    const params = new URLSearchParams()
    params.set('period', period)
    if (date) {
      params.set('date_str', date)
    }
    return request<BudgetStatus>(`/personal/budget-status?${params.toString()}`)
  },
  createBudgetTarget(payload: {
    amount: number
    period: string
    category?: string | null
    currency?: string
  }) {
    return request('/personal/budget-target', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  getMeals() {
    return request<PersonalRecord[]>('/personal/meals')
  },
  getWorkouts() {
    return request<PersonalRecord[]>('/personal/workouts')
  },
  getHabits() {
    return request<PersonalRecord[]>('/personal/habits')
  },
  getSupplements() {
    return request<PersonalRecord[]>('/personal/supplements')
  },
  getBodyMetrics() {
    return request<PersonalRecord[]>('/personal/body-metrics')
  },
  getProjects() {
    return request<Project[]>('/projects')
  },
  getProject(name: string) {
    return request<Project>(`/projects/${encodeURIComponent(name)}`)
  },
  getProjectTasks(name: string) {
    return request<{ items: Task[] }>(`/projects/${encodeURIComponent(name)}/tasks`)
  },
  createProjectTask(
    name: string,
    payload: {
      title: string
      priority?: string
      due_date?: string | null
      focus_date?: string | null
      tags?: string[]
      note?: string | null
    },
  ) {
    return request<Task>(`/projects/${encodeURIComponent(name)}/tasks`, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  getProjectLogs(name: string) {
    return request<ProjectLog[]>(`/projects/${encodeURIComponent(name)}/logs`)
  },
  createProjectLog(name: string, text: string) {
    return request<ProjectLog>(`/projects/${encodeURIComponent(name)}/logs`, {
      method: 'POST',
      body: JSON.stringify({ text }),
    })
  },
  getProjectSession(name: string) {
    return request<ProjectSession>(`/projects/${encodeURIComponent(name)}/session`)
  },
  getProjectAudit(name: string) {
    return request<ProjectAudit>(`/projects/${encodeURIComponent(name)}/audit`)
  },
  refreshProject(name: string) {
    return request<{ refreshed: string[]; skipped: string[] }>(
      `/projects/${encodeURIComponent(name)}/refresh`,
      { method: 'POST' },
    )
  },
}
