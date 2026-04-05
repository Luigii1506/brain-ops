"""CLI orchestration helpers for personal logging commands."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from brain_ops.application import (
    execute_daily_log_workflow,
    execute_habit_checkin_workflow,
    execute_log_body_metrics_workflow,
    execute_log_expense_workflow,
    execute_log_meal_workflow,
    execute_log_supplement_workflow,
    execute_log_workout_workflow,
)
from brain_ops.interfaces.cli.presenters import print_rendered_with_operations
from brain_ops.interfaces.cli.runtime import load_database_path, load_event_sink
from brain_ops.reporting_personal import (
    render_body_metrics_log,
    render_daily_log,
    render_expense_log,
    render_habit_checkin,
    render_meal_log,
    render_supplement_log,
    render_workout_log,
)


def run_log_meal_command(
    *,
    config_path: Path | None,
    meal_text: str,
    meal_type: str | None,
    dry_run: bool,
):
    return execute_log_meal_workflow(
        config_path=config_path,
        meal_text=meal_text,
        meal_type=meal_type,
        dry_run=dry_run,
        load_database_path=load_database_path,
        event_sink=load_event_sink(),
    )


def present_log_meal_command(
    console: Console,
    *,
    config_path: Path | None,
    meal_text: str,
    meal_type: str | None,
    dry_run: bool,
) -> None:
    result = run_log_meal_command(
        config_path=config_path,
        meal_text=meal_text,
        meal_type=meal_type,
        dry_run=dry_run,
    )
    print_rendered_with_operations(console, result.operations, render_meal_log(result))


def run_log_supplement_command(
    *,
    config_path: Path | None,
    supplement_name: str,
    amount: float | None,
    unit: str | None,
    note: str | None,
    dry_run: bool,
):
    return execute_log_supplement_workflow(
        config_path=config_path,
        supplement_name=supplement_name,
        amount=amount,
        unit=unit,
        note=note,
        dry_run=dry_run,
        load_database_path=load_database_path,
        event_sink=load_event_sink(),
    )


def present_log_supplement_command(
    console: Console,
    *,
    config_path: Path | None,
    supplement_name: str,
    amount: float | None,
    unit: str | None,
    note: str | None,
    dry_run: bool,
) -> None:
    result = run_log_supplement_command(
        config_path=config_path,
        supplement_name=supplement_name,
        amount=amount,
        unit=unit,
        note=note,
        dry_run=dry_run,
    )
    print_rendered_with_operations(console, result.operations, render_supplement_log(result))


def run_habit_checkin_command(
    *,
    config_path: Path | None,
    habit_name: str,
    status: str,
    note: str | None,
    dry_run: bool,
):
    return execute_habit_checkin_workflow(
        config_path=config_path,
        habit_name=habit_name,
        status=status,
        note=note,
        dry_run=dry_run,
        load_database_path=load_database_path,
        event_sink=load_event_sink(),
    )


def present_habit_checkin_command(
    console: Console,
    *,
    config_path: Path | None,
    habit_name: str,
    status: str,
    note: str | None,
    dry_run: bool,
) -> None:
    result = run_habit_checkin_command(
        config_path=config_path,
        habit_name=habit_name,
        status=status,
        note=note,
        dry_run=dry_run,
    )
    print_rendered_with_operations(console, result.operations, render_habit_checkin(result))


def run_log_body_metrics_command(
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
):
    return execute_log_body_metrics_workflow(
        config_path=config_path,
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
        logged_at=logged_at,
        dry_run=dry_run,
        load_database_path=load_database_path,
        event_sink=load_event_sink(),
    )


def present_log_body_metrics_command(
    console: Console,
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
) -> None:
    result = run_log_body_metrics_command(
        config_path=config_path,
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
        logged_at=logged_at,
        note=note,
        dry_run=dry_run,
    )
    print_rendered_with_operations(console, result.operations, render_body_metrics_log(result))


def run_log_workout_command(
    *,
    config_path: Path | None,
    workout_text: str,
    routine_name: str | None,
    duration_minutes: int | None,
    note: str | None,
    dry_run: bool,
):
    return execute_log_workout_workflow(
        config_path=config_path,
        workout_text=workout_text,
        routine_name=routine_name,
        duration_minutes=duration_minutes,
        note=note,
        dry_run=dry_run,
        load_database_path=load_database_path,
        event_sink=load_event_sink(),
    )


def present_log_workout_command(
    console: Console,
    *,
    config_path: Path | None,
    workout_text: str,
    routine_name: str | None,
    duration_minutes: int | None,
    note: str | None,
    dry_run: bool,
) -> None:
    result = run_log_workout_command(
        config_path=config_path,
        workout_text=workout_text,
        routine_name=routine_name,
        duration_minutes=duration_minutes,
        note=note,
        dry_run=dry_run,
    )
    print_rendered_with_operations(console, result.operations, render_workout_log(result))


def run_log_expense_command(
    *,
    config_path: Path | None,
    amount: float,
    category: str | None,
    merchant: str | None,
    currency: str,
    note: str | None,
    dry_run: bool,
):
    return execute_log_expense_workflow(
        config_path=config_path,
        amount=amount,
        category=category,
        merchant=merchant,
        currency=currency,
        note=note,
        dry_run=dry_run,
        load_database_path=load_database_path,
        event_sink=load_event_sink(),
    )


def present_log_expense_command(
    console: Console,
    *,
    config_path: Path | None,
    amount: float,
    category: str | None,
    merchant: str | None,
    currency: str,
    note: str | None,
    dry_run: bool,
) -> None:
    result = run_log_expense_command(
        config_path=config_path,
        amount=amount,
        category=category,
        merchant=merchant,
        currency=currency,
        note=note,
        dry_run=dry_run,
    )
    print_rendered_with_operations(console, result.operations, render_expense_log(result))


def run_daily_log_command(
    *,
    config_path: Path | None,
    text: str,
    domain: str,
    dry_run: bool,
):
    return execute_daily_log_workflow(
        config_path=config_path,
        text=text,
        domain=domain,
        dry_run=dry_run,
        load_database_path=load_database_path,
        event_sink=load_event_sink(),
    )


def present_daily_log_command(
    console: Console,
    *,
    config_path: Path | None,
    text: str,
    domain: str,
    dry_run: bool,
) -> None:
    result = run_daily_log_command(
        config_path=config_path,
        text=text,
        domain=domain,
        dry_run=dry_run,
    )
    print_rendered_with_operations(console, result.operations, render_daily_log(result))


__all__ = [
    "present_daily_log_command",
    "present_habit_checkin_command",
    "present_log_body_metrics_command",
    "present_log_expense_command",
    "present_log_meal_command",
    "present_log_supplement_command",
    "present_log_workout_command",
    "run_daily_log_command",
    "run_habit_checkin_command",
    "run_log_body_metrics_command",
    "run_log_expense_command",
    "run_log_meal_command",
    "run_log_supplement_command",
    "run_log_workout_command",
]
