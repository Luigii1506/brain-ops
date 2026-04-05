from __future__ import annotations

from datetime import datetime
from pathlib import Path

from brain_ops.core.validation import DEFAULT_ALLOWED_PERIODS, normalize_period, resolve_iso_date
from brain_ops.domains.personal.goals import (
    build_date_bounds,
    build_budget_target_result,
    build_period_bounds,
    build_budget_status_summary,
    build_habit_target_result,
    build_habit_target_status_summary,
    build_macro_targets_result,
    build_macro_status_summary,
    normalize_budget_target_inputs,
    normalize_habit_target_inputs,
    normalize_macro_target_inputs,
    resolve_macro_status_targets,
)
from brain_ops.models import BudgetTargetResult, HabitTargetResult, MacroTargetsResult
from brain_ops.services.diet_service import load_active_diet_totals
from brain_ops.storage.db import ensure_database_parent, require_database_file, resolve_database_path
from brain_ops.storage.sqlite import (
    fetch_budget_status_rows,
    fetch_habit_target_status_rows,
    fetch_macro_status_rows,
    replace_budget_target,
    upsert_habit_target,
    upsert_macro_targets,
)

ALLOWED_PERIODS = DEFAULT_ALLOWED_PERIODS


def set_macro_targets(
    database_path: Path,
    *,
    calories: float | None = None,
    protein_g: float | None = None,
    carbs_g: float | None = None,
    fat_g: float | None = None,
    dry_run: bool = False,
) -> MacroTargetsResult:
    normalized = normalize_macro_target_inputs(
        calories=calories,
        protein_g=protein_g,
        carbs_g=carbs_g,
        fat_g=fat_g,
    )

    target = resolve_database_path(database_path)
    updated_at = datetime.now().isoformat(timespec="seconds")
    if not dry_run:
        ensure_database_parent(target)
        upsert_macro_targets(
            target,
            calories=normalized["calories"],
            protein_g=normalized["protein_g"],
            carbs_g=normalized["carbs_g"],
            fat_g=normalized["fat_g"],
            updated_at=updated_at,
        )
    return build_macro_targets_result(
        database_path=target,
        calories=normalized["calories"],
        protein_g=normalized["protein_g"],
        carbs_g=normalized["carbs_g"],
        fat_g=normalized["fat_g"],
    )


def macro_status(database_path: Path, date_text: str | None = None):
    target = require_database_file(database_path)

    resolved_date = resolve_iso_date(date_text)
    start, end = build_date_bounds(resolved_date)
    target_row, actual_row = fetch_macro_status_rows(target, start=start, end=end)

    active_diet = load_active_diet_totals(target)
    target_values = resolve_macro_status_targets(active_diet, target_row)
    calories_actual = float(actual_row[0] or 0)
    protein_actual = float(actual_row[1] or 0)
    carbs_actual = float(actual_row[2] or 0)
    fat_actual = float(actual_row[3] or 0)

    return build_macro_status_summary(
        date=resolved_date,
        database_path=target,
        target_source=target_values["target_source"],
        active_diet_name=target_values["active_diet_name"],
        calories_target=target_values["calories_target"],
        protein_g_target=target_values["protein_g_target"],
        carbs_g_target=target_values["carbs_g_target"],
        fat_g_target=target_values["fat_g_target"],
        calories_actual=calories_actual,
        protein_g_actual=protein_actual,
        carbs_g_actual=carbs_actual,
        fat_g_actual=fat_actual,
    )


def set_budget_target(
    database_path: Path,
    *,
    amount: float,
    period: str,
    currency: str = "MXN",
    category: str | None = None,
    dry_run: bool = False,
) -> BudgetTargetResult:
    normalized = normalize_budget_target_inputs(
        amount=amount,
        period=period,
        currency=currency,
        category=category,
    )
    target = resolve_database_path(database_path)
    updated_at = datetime.now().isoformat(timespec="seconds")
    if not dry_run:
        ensure_database_parent(target)
        replace_budget_target(
            target,
            normalized_period=normalized["period"],
            category=normalized["category"],
            amount=normalized["amount"],
            normalized_currency=normalized["currency"],
            updated_at=updated_at,
        )
    return build_budget_target_result(
        database_path=target,
        period=normalized["period"],
        amount=normalized["amount"],
        currency=normalized["currency"],
        category=normalized["category"],
    )


def budget_status(database_path: Path, *, period: str, date_text: str | None = None):
    target = require_database_file(database_path)

    normalized_period = normalize_period(period, allowed=ALLOWED_PERIODS)
    resolved_date = resolve_iso_date(date_text)
    start, end = build_period_bounds(resolved_date, normalized_period)
    target_rows, actual_amounts_by_target = fetch_budget_status_rows(
        target,
        normalized_period=normalized_period,
        start=start,
        end=end,
    )
    return build_budget_status_summary(
        date=resolved_date,
        period=normalized_period,
        database_path=target,
        target_rows=target_rows,
        actual_amounts_by_target=actual_amounts_by_target,
    )


def set_habit_target(
    database_path: Path,
    *,
    habit_name: str,
    target_count: int,
    period: str = "daily",
    dry_run: bool = False,
) -> HabitTargetResult:
    normalized = normalize_habit_target_inputs(
        habit_name=habit_name,
        target_count=target_count,
        period=period,
    )
    target = resolve_database_path(database_path)
    updated_at = datetime.now().isoformat(timespec="seconds")
    if not dry_run:
        ensure_database_parent(target)
        upsert_habit_target(
            target,
            habit_name=normalized["habit_name"],
            normalized_period=normalized["period"],
            target_count=normalized["target_count"],
            updated_at=updated_at,
        )
    return build_habit_target_result(
        database_path=target,
        habit_name=normalized["habit_name"],
        period=normalized["period"],
        target_count=normalized["target_count"],
    )


def habit_target_status(database_path: Path, *, period: str = "daily", date_text: str | None = None):
    target = require_database_file(database_path)

    normalized_period = normalize_period(period, allowed=ALLOWED_PERIODS)
    resolved_date = resolve_iso_date(date_text)
    start, end = build_period_bounds(resolved_date, normalized_period)

    target_rows, completed_counts_by_habit = fetch_habit_target_status_rows(
        target,
        normalized_period=normalized_period,
        start=start,
        end=end,
    )
    return build_habit_target_status_summary(
        date=resolved_date,
        period=normalized_period,
        database_path=target,
        target_rows=target_rows,
        completed_counts_by_habit=completed_counts_by_habit,
    )
