from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class BaseIntent(BaseModel):
    intent: str
    intent_version: str = "1"
    domain: str
    command: str
    routing_source: str = "heuristic"
    confidence: float = 0.0


class QueryIntent(BaseIntent):
    date: str | None = None


class LogMealIntent(BaseIntent):
    intent: Literal["log_meal"] = "log_meal"
    domain: str = "nutrition"
    command: str = "log-meal"
    meal_text: str
    meal_type: str | None = None


class LogSupplementIntent(BaseIntent):
    intent: Literal["log_supplement"] = "log_supplement"
    domain: str = "supplements"
    command: str = "log-supplement"
    supplement_name: str
    amount: float | None = None
    unit: str | None = None
    note: str | None = None


class HabitCheckinIntent(BaseIntent):
    intent: Literal["habit_checkin"] = "habit_checkin"
    domain: str = "habits"
    command: str = "habit-checkin"
    habit_name: str
    status: str = "done"
    note: str | None = None


class LogBodyMetricsIntent(BaseIntent):
    intent: Literal["log_body_metrics"] = "log_body_metrics"
    domain: str = "body_metrics"
    command: str = "log-body-metrics"
    weight_kg: float | None = None
    body_fat_pct: float | None = None
    waist_cm: float | None = None
    note: str | None = None


class LogWorkoutIntent(BaseIntent):
    intent: Literal["log_workout"] = "log_workout"
    domain: str = "fitness"
    command: str = "log-workout"
    workout_text: str
    routine_name: str | None = None


class LogExpenseIntent(BaseIntent):
    intent: Literal["log_expense"] = "log_expense"
    domain: str = "expenses"
    command: str = "log-expense"
    amount: float
    currency: str = "MXN"
    category: str | None = None
    merchant: str | None = None
    note: str | None = None


class SetMacroTargetsIntent(BaseIntent):
    intent: Literal["set_macro_targets"] = "set_macro_targets"
    domain: str = "nutrition_goals"
    command: str = "set-macro-targets"
    calories: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None


class SetBudgetTargetIntent(BaseIntent):
    intent: Literal["set_budget_target"] = "set_budget_target"
    domain: str = "budget_goals"
    command: str = "set-budget-target"
    amount: float
    period: str = "daily"
    category: str | None = None
    currency: str = "MXN"


class SetHabitTargetIntent(BaseIntent):
    intent: Literal["set_habit_target"] = "set_habit_target"
    domain: str = "habit_goals"
    command: str = "set-habit-target"
    habit_name: str
    target_count: int
    period: str = "daily"


class CreateDietPlanIntent(BaseIntent):
    intent: Literal["create_diet_plan"] = "create_diet_plan"
    domain: str = "diet"
    command: str = "create-diet-plan"
    name: str
    meals: list[str] = Field(default_factory=list)
    notes: str | None = None
    activate: bool = True


class SetActiveDietIntent(BaseIntent):
    intent: Literal["set_active_diet"] = "set_active_diet"
    domain: str = "diet"
    command: str = "set-active-diet"
    name: str


class UpdateDietMealIntent(BaseIntent):
    intent: Literal["update_diet_meal"] = "update_diet_meal"
    domain: str = "diet"
    command: str = "update-diet-meal"
    meal_type: str
    items_text: str
    mode: str = "replace"


class MacroStatusIntent(QueryIntent):
    intent: Literal["macro_status"] = "macro_status"
    domain: str = "nutrition_status"
    command: str = "macro-status"
    metric: str | None = None


class BudgetStatusIntent(QueryIntent):
    intent: Literal["budget_status"] = "budget_status"
    domain: str = "budget_status"
    command: str = "budget-status"
    period: str = "daily"
    category: str | None = None


class HabitStatusIntent(QueryIntent):
    intent: Literal["habit_status"] = "habit_status"
    domain: str = "habit_status"
    command: str = "habit-status"
    period: str = "daily"


class DietStatusIntent(QueryIntent):
    intent: Literal["diet_status"] = "diet_status"
    domain: str = "diet"
    command: str = "diet-status"
    meal_focus: str | None = None


class ActiveDietIntent(QueryIntent):
    intent: Literal["active_diet"] = "active_diet"
    domain: str = "diet"
    command: str = "active-diet"


class DailyStatusIntent(QueryIntent):
    intent: Literal["daily_status"] = "daily_status"
    domain: str = "daily_status"
    command: str = "daily-status"


class CaptureNoteIntent(BaseIntent):
    intent: Literal["capture_note"] = "capture_note"
    domain: str = "knowledge"
    command: str = "capture-note"
    force_type: str
    text: str


class DailyLogIntent(BaseIntent):
    intent: Literal["daily_log"] = "daily_log"
    domain: str = "daily"
    command: str = "daily-log"
    text: str
    log_domain: str = "daily"


class ParseFailure(BaseModel):
    input_text: str
    reason: str
    follow_up: str | None = None
    routing_source: str = "fallback"


IntentModel = (
    LogMealIntent
    | LogSupplementIntent
    | HabitCheckinIntent
    | LogBodyMetricsIntent
    | LogWorkoutIntent
    | LogExpenseIntent
    | SetMacroTargetsIntent
    | SetBudgetTargetIntent
    | SetHabitTargetIntent
    | CreateDietPlanIntent
    | SetActiveDietIntent
    | UpdateDietMealIntent
    | MacroStatusIntent
    | BudgetStatusIntent
    | HabitStatusIntent
    | DietStatusIntent
    | ActiveDietIntent
    | DailyStatusIntent
    | CaptureNoteIntent
    | DailyLogIntent
)


INTENT_VERSION = "1"
