"""Application workflows for personal capabilities."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from brain_ops.core.events import EventSink
from brain_ops.services.body_metrics_service import body_metrics_status, log_body_metrics
from brain_ops.services.daily_log_service import log_daily_event
from brain_ops.services.daily_status_service import daily_status
from brain_ops.services.personal_review_service import (
    daily_review as _daily_review_svc,
    weekly_review as _weekly_review_svc,
)
from brain_ops.services.diet_service import (
    active_diet,
    create_diet_plan,
    diet_status,
    set_active_diet,
    update_active_diet_meal,
)
from brain_ops.services.expenses_service import log_expense, spending_summary
from brain_ops.services.fitness_service import log_workout, workout_status
from brain_ops.services.goals_service import (
    budget_status,
    habit_target_status,
    macro_status,
    set_budget_target,
    set_habit_target,
    set_macro_targets,
)
from brain_ops.services.life_ops_service import daily_habits, habit_checkin, log_supplement
from brain_ops.services.nutrition_service import daily_macros, log_meal
from .events import publish_result_events


def execute_daily_macros_workflow(*, config_path: Path | None, date: str | None, load_database_path):
    return daily_macros(load_database_path(config_path), date_text=date)


def execute_macro_status_workflow(*, config_path: Path | None, date: str | None, load_database_path):
    return macro_status(load_database_path(config_path), date_text=date)


def execute_active_diet_workflow(*, config_path: Path | None, load_database_path):
    return active_diet(load_database_path(config_path))


def execute_diet_status_workflow(*, config_path: Path | None, date: str | None, load_database_path):
    return diet_status(load_database_path(config_path), date_text=date)


def execute_daily_habits_workflow(*, config_path: Path | None, date: str | None, load_database_path):
    return daily_habits(load_database_path(config_path), date_text=date)


def execute_habit_status_workflow(*, config_path: Path | None, period: str, date: str | None, load_database_path):
    return habit_target_status(load_database_path(config_path), period=period, date_text=date)


def execute_body_metrics_status_workflow(*, config_path: Path | None, date: str | None, load_database_path):
    return body_metrics_status(load_database_path(config_path), date_text=date)


def execute_workout_status_workflow(*, config_path: Path | None, date: str | None, load_database_path):
    return workout_status(load_database_path(config_path), date_text=date)


def execute_spending_summary_workflow(
    *,
    config_path: Path | None,
    date: str | None,
    currency: str,
    load_database_path,
):
    return spending_summary(load_database_path(config_path), date_text=date, currency=currency)


def execute_budget_status_workflow(*, config_path: Path | None, period: str, date: str | None, load_database_path):
    return budget_status(load_database_path(config_path), period=period, date_text=date)


def execute_daily_status_workflow(*, config_path: Path | None, date: str | None, load_database_path):
    return daily_status(load_database_path(config_path), date_text=date)


def execute_daily_review_workflow(*, config_path: Path | None, date: str | None, load_database_path):
    return _daily_review_svc(load_database_path(config_path), date_text=date)


def execute_weekly_review_personal_workflow(*, config_path: Path | None, date: str | None, load_database_path):
    return _weekly_review_svc(load_database_path(config_path), date_text=date)


def execute_log_meal_workflow(
    *,
    config_path: Path | None,
    meal_text: str,
    meal_type: str | None,
    dry_run: bool,
    load_database_path,
    event_sink: EventSink | None = None,
):
    result = log_meal(load_database_path(config_path), meal_text, meal_type=meal_type, dry_run=dry_run)
    return publish_result_events("log-meal", source="application.personal", result=result, event_sink=event_sink)


def execute_log_supplement_workflow(
    *,
    config_path: Path | None,
    supplement_name: str,
    amount: float | None,
    unit: str | None,
    note: str | None,
    dry_run: bool,
    load_database_path,
    event_sink: EventSink | None = None,
):
    result = log_supplement(
        load_database_path(config_path),
        supplement_name,
        amount=amount,
        unit=unit,
        note=note,
        dry_run=dry_run,
    )
    return publish_result_events("log-supplement", source="application.personal", result=result, event_sink=event_sink)


def execute_habit_checkin_workflow(
    *,
    config_path: Path | None,
    habit_name: str,
    status: str,
    note: str | None,
    dry_run: bool,
    load_database_path,
    event_sink: EventSink | None = None,
):
    result = habit_checkin(
        load_database_path(config_path),
        habit_name,
        status=status,
        note=note,
        dry_run=dry_run,
    )
    return publish_result_events("habit-checkin", source="application.personal", result=result, event_sink=event_sink)


def execute_log_body_metrics_workflow(
    *,
    config_path: Path | None,
    weight_kg: float | None,
    body_fat_pct: float | None,
    fat_mass_kg: float | None,
    muscle_mass_kg: float | None,
    visceral_fat: float | None,
    bmr_calories: float | None,
    arm_cm: float | None,
    waist_cm: float | None,
    thigh_cm: float | None,
    calf_cm: float | None,
    logged_at: str | None,
    note: str | None,
    dry_run: bool,
    load_database_path,
    event_sink: EventSink | None = None,
):
    result = log_body_metrics(
        load_database_path(config_path),
        weight_kg=weight_kg,
        body_fat_pct=body_fat_pct,
        fat_mass_kg=fat_mass_kg,
        muscle_mass_kg=muscle_mass_kg,
        visceral_fat=visceral_fat,
        bmr_calories=bmr_calories,
        arm_cm=arm_cm,
        waist_cm=waist_cm,
        thigh_cm=thigh_cm,
        calf_cm=calf_cm,
        note=note,
        logged_at=datetime.fromisoformat(logged_at) if logged_at else None,
        dry_run=dry_run,
    )
    return publish_result_events("log-body-metrics", source="application.personal", result=result, event_sink=event_sink)


def execute_log_workout_workflow(
    *,
    config_path: Path | None,
    workout_text: str,
    routine_name: str | None,
    duration_minutes: int | None,
    note: str | None,
    dry_run: bool,
    load_database_path,
    event_sink: EventSink | None = None,
):
    result = log_workout(
        load_database_path(config_path),
        workout_text,
        routine_name=routine_name,
        duration_minutes=duration_minutes,
        note=note,
        dry_run=dry_run,
    )
    return publish_result_events("log-workout", source="application.personal", result=result, event_sink=event_sink)


def execute_log_expense_workflow(
    *,
    config_path: Path | None,
    amount: float,
    category: str | None,
    merchant: str | None,
    currency: str,
    note: str | None,
    dry_run: bool,
    load_database_path,
    event_sink: EventSink | None = None,
):
    result = log_expense(
        load_database_path(config_path),
        amount,
        category=category,
        merchant=merchant,
        currency=currency,
        note=note,
        dry_run=dry_run,
    )
    return publish_result_events("log-expense", source="application.personal", result=result, event_sink=event_sink)


def execute_daily_log_workflow(
    *,
    config_path: Path | None,
    text: str,
    domain: str,
    dry_run: bool,
    load_database_path,
    event_sink: EventSink | None = None,
):
    result = log_daily_event(load_database_path(config_path), text, domain=domain, dry_run=dry_run)
    return publish_result_events("daily-log", source="application.personal", result=result, event_sink=event_sink)


def execute_set_macro_targets_workflow(
    *,
    config_path: Path | None,
    calories: float | None,
    protein_g: float | None,
    carbs_g: float | None,
    fat_g: float | None,
    dry_run: bool,
    load_database_path,
    event_sink: EventSink | None = None,
):
    result = set_macro_targets(
        load_database_path(config_path),
        calories=calories,
        protein_g=protein_g,
        carbs_g=carbs_g,
        fat_g=fat_g,
        dry_run=dry_run,
    )
    return publish_result_events("set-macro-targets", source="application.personal", result=result, event_sink=event_sink)


def execute_create_diet_plan_workflow(
    *,
    config_path: Path | None,
    name: str,
    meal: list[str],
    notes: str | None,
    activate: bool,
    dry_run: bool,
    load_database_path,
    event_sink: EventSink | None = None,
):
    result = create_diet_plan(
        load_database_path(config_path),
        name=name,
        meals=meal,
        notes=notes,
        activate=activate,
        dry_run=dry_run,
    )
    return publish_result_events("create-diet-plan", source="application.personal", result=result, event_sink=event_sink)


def execute_set_active_diet_workflow(
    *,
    config_path: Path | None,
    name: str,
    dry_run: bool,
    load_database_path,
    event_sink: EventSink | None = None,
):
    result = set_active_diet(load_database_path(config_path), name=name, dry_run=dry_run)
    return publish_result_events("set-active-diet", source="application.personal", result=result, event_sink=event_sink)


def execute_update_diet_meal_workflow(
    *,
    config_path: Path | None,
    meal_type: str,
    items: str,
    mode: str,
    dry_run: bool,
    load_database_path,
    event_sink: EventSink | None = None,
):
    result = update_active_diet_meal(
        load_database_path(config_path),
        meal_type=meal_type,
        items_text=items,
        mode=mode,
        dry_run=dry_run,
    )
    return publish_result_events("update-diet-meal", source="application.personal", result=result, event_sink=event_sink)


def execute_set_habit_target_workflow(
    *,
    config_path: Path | None,
    habit_name: str,
    target_count: int,
    period: str,
    dry_run: bool,
    load_database_path,
    event_sink: EventSink | None = None,
):
    result = set_habit_target(
        load_database_path(config_path),
        habit_name=habit_name,
        target_count=target_count,
        period=period,
        dry_run=dry_run,
    )
    return publish_result_events("set-habit-target", source="application.personal", result=result, event_sink=event_sink)


def execute_set_budget_target_workflow(
    *,
    config_path: Path | None,
    amount: float,
    period: str,
    category: str | None,
    currency: str,
    dry_run: bool,
    load_database_path,
    event_sink: EventSink | None = None,
):
    result = set_budget_target(
        load_database_path(config_path),
        amount=amount,
        period=period,
        category=category,
        currency=currency,
        dry_run=dry_run,
    )
    return publish_result_events("set-budget-target", source="application.personal", result=result, event_sink=event_sink)


__all__ = [
    "execute_active_diet_workflow",
    "execute_body_metrics_status_workflow",
    "execute_budget_status_workflow",
    "execute_create_diet_plan_workflow",
    "execute_daily_habits_workflow",
    "execute_daily_log_workflow",
    "execute_daily_macros_workflow",
    "execute_daily_review_workflow",
    "execute_daily_status_workflow",
    "execute_diet_status_workflow",
    "execute_habit_checkin_workflow",
    "execute_habit_status_workflow",
    "execute_log_body_metrics_workflow",
    "execute_log_expense_workflow",
    "execute_log_meal_workflow",
    "execute_log_supplement_workflow",
    "execute_log_workout_workflow",
    "execute_macro_status_workflow",
    "execute_set_active_diet_workflow",
    "execute_set_budget_target_workflow",
    "execute_set_habit_target_workflow",
    "execute_set_macro_targets_workflow",
    "execute_spending_summary_workflow",
    "execute_update_diet_meal_workflow",
    "execute_weekly_review_personal_workflow",
    "execute_workout_status_workflow",
]
