export type Task = {
  id: number
  created_at: string
  updated_at: string
  completed_at?: string | null
  project?: string | null
  title: string
  priority: 'high' | 'medium' | 'low' | string
  status: 'pending' | 'active' | 'done' | 'cancelled' | string
  due_date?: string | null
  focus_date?: string | null
  note?: string | null
  source: string
  tags: string[]
}

export type TaskListResponse = {
  items: Task[]
  counts: Record<string, number>
}

export type DailyStatus = {
  date: string
  active_diet_name?: string | null
  calories_actual: number
  calories_target?: number | null
  calories_remaining?: number | null
  protein_g_actual: number
  protein_g_target?: number | null
  protein_g_remaining?: number | null
  carbs_g_actual: number
  carbs_g_target?: number | null
  carbs_g_remaining?: number | null
  fat_g_actual: number
  fat_g_target?: number | null
  fat_g_remaining?: number | null
  missing_diet_meals: string[]
  workouts_logged: number
  total_workout_sets: number
  expenses_total: number
  expense_currency: string
  supplements_logged: number
  supplement_names: string[]
  habit_pending: string[]
  habits_completed: string[]
  body_weight_kg?: number | null
  body_fat_pct?: number | null
  waist_cm?: number | null
  daily_logs_count: number
  database_path: string
}

export type DailyReview = {
  date: string
  score: number
  calories_pct: number
  protein_pct: number
  carbs_pct: number
  fat_pct: number
  highlights: string[]
  gaps: string[]
  suggestions: string[]
  summary: DailyStatus
}

export type WeeklyReview = {
  start_date: string
  end_date: string
  days_with_data: number
  score: number
  avg_calories: number
  avg_protein: number
  avg_carbs: number
  avg_fat: number
  total_spending: number
  spending_currency: string
  workout_days: number
  total_sets: number
  trends: string[]
}

export type ExpenseMeta = {
  categories: string[]
  merchants: string[]
  currencies: string[]
  periods: string[]
}

export type SpendingSummary = {
  date: string
  total_amount: number
  transaction_count: number
  by_category: Record<string, number>
  currency: string
  database_path: string
}

export type BudgetStatusItem = {
  period: string
  category?: string | null
  target_amount: number
  actual_amount: number
  remaining_amount: number
  currency: string
}

export type BudgetStatus = {
  date: string
  period: string
  items: BudgetStatusItem[]
  database_path: string
}

export type ProjectContext = {
  phase?: string | null
  pending?: string[]
  decisions?: string[]
  notes?: string | null
  commands?: Record<string, string>
}

export type Project = {
  name: string
  path: string
  stack?: string[]
  description?: string | null
  context: ProjectContext
}

export type ProjectLog = {
  id?: number
  logged_at?: string
  project_name?: string
  entry_type?: string
  entry_text?: string
  source?: string
}

export type ProjectSession = {
  project: Project
  recent_logs: ProjectLog[]
  recent_commits: string[]
  vault_status?: string | null
  vault_decisions: string[]
  vault_bugs: string[]
  vault_path?: string | null
}

export type ProjectAudit = {
  project_name: string
  issues: string[]
  score: number
}

export type PersonalRecord = Record<string, string | number | null>
