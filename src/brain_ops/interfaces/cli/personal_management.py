"""CLI orchestration helpers for personal target and diet management commands."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from brain_ops.application import (
    execute_create_diet_plan_workflow,
    execute_set_active_diet_workflow,
    execute_set_budget_target_workflow,
    execute_set_habit_target_workflow,
    execute_set_macro_targets_workflow,
    execute_update_diet_meal_workflow,
)
from brain_ops.interfaces.cli.presenters import print_rendered_with_operations
from brain_ops.interfaces.cli.runtime import load_database_path, load_event_sink
from brain_ops.reporting_personal import (
    render_budget_target,
    render_diet_activation,
    render_diet_meal_update,
    render_diet_plan,
    render_habit_target,
    render_macro_targets,
)


def run_set_macro_targets_command(
    *,
    config_path: Path | None,
    calories: float | None,
    protein_g: float | None,
    carbs_g: float | None,
    fat_g: float | None,
    dry_run: bool,
):
    return execute_set_macro_targets_workflow(
        config_path=config_path,
        calories=calories,
        protein_g=protein_g,
        carbs_g=carbs_g,
        fat_g=fat_g,
        dry_run=dry_run,
        load_database_path=load_database_path,
        event_sink=load_event_sink(),
    )


def present_set_macro_targets_command(
    console: Console,
    *,
    config_path: Path | None,
    calories: float | None,
    protein_g: float | None,
    carbs_g: float | None,
    fat_g: float | None,
    dry_run: bool,
) -> None:
    result = run_set_macro_targets_command(
        config_path=config_path,
        calories=calories,
        protein_g=protein_g,
        carbs_g=carbs_g,
        fat_g=fat_g,
        dry_run=dry_run,
    )
    print_rendered_with_operations(console, result.operations, render_macro_targets(result))


def run_create_diet_plan_command(
    *,
    config_path: Path | None,
    name: str,
    meal: list[str],
    notes: str | None,
    activate: bool,
    dry_run: bool,
):
    return execute_create_diet_plan_workflow(
        config_path=config_path,
        name=name,
        meal=meal,
        notes=notes,
        activate=activate,
        dry_run=dry_run,
        load_database_path=load_database_path,
        event_sink=load_event_sink(),
    )


def present_create_diet_plan_command(
    console: Console,
    *,
    config_path: Path | None,
    name: str,
    meal: list[str],
    notes: str | None,
    activate: bool,
    dry_run: bool,
) -> None:
    result = run_create_diet_plan_command(
        config_path=config_path,
        name=name,
        meal=meal,
        notes=notes,
        activate=activate,
        dry_run=dry_run,
    )
    print_rendered_with_operations(console, result.operations, render_diet_plan(result))


def run_set_active_diet_command(
    *,
    config_path: Path | None,
    name: str,
    dry_run: bool,
):
    return execute_set_active_diet_workflow(
        config_path=config_path,
        name=name,
        dry_run=dry_run,
        load_database_path=load_database_path,
        event_sink=load_event_sink(),
    )


def present_set_active_diet_command(
    console: Console,
    *,
    config_path: Path | None,
    name: str,
    dry_run: bool,
) -> None:
    result = run_set_active_diet_command(
        config_path=config_path,
        name=name,
        dry_run=dry_run,
    )
    print_rendered_with_operations(console, result.operations, render_diet_activation(result))


def run_update_diet_meal_command(
    *,
    config_path: Path | None,
    meal_type: str,
    items: str,
    mode: str,
    dry_run: bool,
):
    return execute_update_diet_meal_workflow(
        config_path=config_path,
        meal_type=meal_type,
        items=items,
        mode=mode,
        dry_run=dry_run,
        load_database_path=load_database_path,
        event_sink=load_event_sink(),
    )


def present_update_diet_meal_command(
    console: Console,
    *,
    config_path: Path | None,
    meal_type: str,
    items: str,
    mode: str,
    dry_run: bool,
) -> None:
    result = run_update_diet_meal_command(
        config_path=config_path,
        meal_type=meal_type,
        items=items,
        mode=mode,
        dry_run=dry_run,
    )
    print_rendered_with_operations(console, result.operations, render_diet_meal_update(result))


def run_set_habit_target_command(
    *,
    config_path: Path | None,
    habit_name: str,
    target_count: int,
    period: str,
    dry_run: bool,
):
    return execute_set_habit_target_workflow(
        config_path=config_path,
        habit_name=habit_name,
        target_count=target_count,
        period=period,
        dry_run=dry_run,
        load_database_path=load_database_path,
        event_sink=load_event_sink(),
    )


def present_set_habit_target_command(
    console: Console,
    *,
    config_path: Path | None,
    habit_name: str,
    target_count: int,
    period: str,
    dry_run: bool,
) -> None:
    result = run_set_habit_target_command(
        config_path=config_path,
        habit_name=habit_name,
        target_count=target_count,
        period=period,
        dry_run=dry_run,
    )
    print_rendered_with_operations(console, result.operations, render_habit_target(result))


def run_set_budget_target_command(
    *,
    config_path: Path | None,
    amount: float,
    period: str,
    category: str | None,
    currency: str,
    dry_run: bool,
):
    return execute_set_budget_target_workflow(
        config_path=config_path,
        amount=amount,
        period=period,
        category=category,
        currency=currency,
        dry_run=dry_run,
        load_database_path=load_database_path,
        event_sink=load_event_sink(),
    )


def present_set_budget_target_command(
    console: Console,
    *,
    config_path: Path | None,
    amount: float,
    period: str,
    category: str | None,
    currency: str,
    dry_run: bool,
) -> None:
    result = run_set_budget_target_command(
        config_path=config_path,
        amount=amount,
        period=period,
        category=category,
        currency=currency,
        dry_run=dry_run,
    )
    print_rendered_with_operations(console, result.operations, render_budget_target(result))


__all__ = [
    "present_create_diet_plan_command",
    "present_set_active_diet_command",
    "present_set_budget_target_command",
    "present_set_habit_target_command",
    "present_set_macro_targets_command",
    "present_update_diet_meal_command",
    "run_create_diet_plan_command",
    "run_set_active_diet_command",
    "run_set_budget_target_command",
    "run_set_habit_target_command",
    "run_set_macro_targets_command",
    "run_update_diet_meal_command",
]
