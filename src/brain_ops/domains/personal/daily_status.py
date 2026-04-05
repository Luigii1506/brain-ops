from __future__ import annotations

from pathlib import Path

from brain_ops.models import (
    BodyMetricsSummary,
    DailyStatusSummary,
    DietStatusSummary,
    HabitTargetStatusSummary,
    MacroStatusSummary,
    SpendingSummary,
    WorkoutStatusSummary,
)


def build_daily_status_summary(
    *,
    macro: MacroStatusSummary,
    diet: DietStatusSummary,
    workout: WorkoutStatusSummary,
    spending: SpendingSummary,
    habits: HabitTargetStatusSummary,
    body: BodyMetricsSummary,
    supplements_logged: int,
    supplement_names: list[str],
    daily_logs_count: int,
    database_path: Path,
) -> DailyStatusSummary:
    return DailyStatusSummary(
        date=macro.date,
        active_diet_name=diet.active_diet_name,
        calories_actual=macro.calories_actual,
        calories_target=macro.calories_target,
        calories_remaining=macro.calories_remaining,
        protein_g_actual=macro.protein_g_actual,
        protein_g_target=macro.protein_g_target,
        protein_g_remaining=macro.protein_g_remaining,
        carbs_g_actual=macro.carbs_g_actual,
        carbs_g_target=macro.carbs_g_target,
        carbs_g_remaining=macro.carbs_g_remaining,
        fat_g_actual=macro.fat_g_actual,
        fat_g_target=macro.fat_g_target,
        fat_g_remaining=macro.fat_g_remaining,
        missing_diet_meals=[meal.label for meal in diet.meals if not meal.logged],
        workouts_logged=workout.workouts_logged,
        total_workout_sets=workout.total_sets,
        expenses_total=spending.total_amount,
        expense_currency=spending.currency,
        supplements_logged=supplements_logged,
        supplement_names=supplement_names,
        habit_pending=[item.habit_name for item in habits.items if item.remaining_count > 0],
        habits_completed=[item.habit_name for item in habits.items if item.remaining_count <= 0],
        body_weight_kg=body.latest_weight_kg,
        body_fat_pct=body.latest_body_fat_pct,
        waist_cm=body.latest_waist_cm,
        daily_logs_count=daily_logs_count,
        database_path=database_path,
    )
