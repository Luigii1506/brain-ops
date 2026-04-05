from __future__ import annotations

from datetime import datetime
from pathlib import Path

from brain_ops.core.validation import resolve_iso_date
from brain_ops.domains.personal.diet.parsing import (
    parse_diet_plan_meals,
    parse_diet_update_items,
    normalize_diet_meal_update_inputs,
    normalize_diet_plan_name,
)
from brain_ops.domains.personal.diet.projections import (
    build_actual_meal_progress,
    build_diet_activation_result,
    build_diet_meal_update_result,
    build_diet_plan_result,
    build_diet_plan_summary,
    build_diet_status_summary,
    remaining,
)
from brain_ops.errors import ConfigError
from brain_ops.models import (
    DietPlanMealItem,
    DietPlanSummary,
    DietStatusSummary,
)
from brain_ops.storage.db import ensure_database_parent, require_database_file, resolve_database_path
from brain_ops.storage.sqlite import (
    activate_diet_plan,
    create_diet_plan_records,
    fetch_active_diet_plan_rows,
    fetch_actual_meal_progress_rows,
    update_active_diet_meal_items,
)


def create_diet_plan(
    database_path: Path,
    *,
    name: str,
    meals: list[str],
    notes: str | None = None,
    activate: bool = False,
    dry_run: bool = False,
) -> DietPlanResult:
    normalized_name = normalize_diet_plan_name(name)
    parsed_meals = parse_diet_plan_meals(meals)

    target = resolve_database_path(database_path)
    created_at = datetime.now().isoformat(timespec="seconds")
    status = "active" if activate else "inactive"

    if not dry_run:
        ensure_database_parent(target)
        if not create_diet_plan_records(
            target,
            normalized_name=normalized_name,
            notes=notes,
            status=status,
            created_at=created_at,
            activate=activate,
            parsed_meals=parsed_meals,
        ):
            raise ConfigError(f"Diet plan already exists: {normalized_name}")
    return build_diet_plan_result(
        database_path=target,
        name=normalized_name,
        status=status,
        meals=[meal.to_model() for meal in parsed_meals],
    )


def set_active_diet(
    database_path: Path,
    *,
    name: str,
    dry_run: bool = False,
) -> DietActivationResult:
    normalized_name = normalize_diet_plan_name(name)

    target = resolve_database_path(database_path)
    activated_at = datetime.now().isoformat(timespec="seconds")
    if not dry_run:
        if not activate_diet_plan(target, normalized_name=normalized_name, activated_at=activated_at):
            raise ConfigError(f"Diet plan not found: {normalized_name}")
    return build_diet_activation_result(database_path=target, name=normalized_name)


def active_diet(database_path: Path) -> DietPlanSummary | None:
    target = require_database_file(database_path)
    plan = _load_active_diet_plan(target)
    if plan is None:
        return None
    return plan


def update_active_diet_meal(
    database_path: Path,
    *,
    meal_type: str,
    items_text: str,
    mode: str = "replace",
    dry_run: bool = False,
) -> DietMealUpdateResult:
    normalized = normalize_diet_meal_update_inputs(meal_type=meal_type, items_text=items_text, mode=mode)

    target = resolve_database_path(database_path)
    plan = _load_active_diet_plan(target)
    if plan is None:
        raise ConfigError("No active diet plan found.")

    parsed_items = parse_diet_update_items(normalized["items_text"])

    if not dry_run:
        if not update_active_diet_meal_items(
            target,
            normalized_meal_type=normalized["meal_type"],
            normalized_mode=normalized["mode"],
            parsed_items=parsed_items,
            updated_at=datetime.now().isoformat(timespec="seconds"),
        ):
            raise ConfigError(f"Active diet does not contain meal type: {normalized['meal_type']}")
    return build_diet_meal_update_result(
        database_path=target,
        diet_name=plan.name,
        meal_type=normalized["meal_type"],
        mode=normalized["mode"],
        items=parsed_items,
    )


def diet_status(database_path: Path, date_text: str | None = None):
    target = require_database_file(database_path)

    resolved_date = resolve_iso_date(date_text)
    plan = _load_active_diet_plan(target)
    if plan is None:
        return DietStatusSummary(date=resolved_date, database_path=target)

    actual_by_meal, actual_totals = _load_actual_meal_progress(target, resolved_date)
    return build_diet_status_summary(
        date=resolved_date,
        database_path=target,
        plan=plan,
        actual_by_meal=actual_by_meal,
        actual_totals=actual_totals,
    )


def load_active_diet_totals(database_path: Path) -> tuple[str, dict[str, float]] | None:
    plan = _load_active_diet_plan(resolve_database_path(database_path))
    if plan is None:
        return None
    return (
        plan.name,
        {
            "calories": plan.calories_target,
            "protein_g": plan.protein_g_target,
            "carbs_g": plan.carbs_g_target,
            "fat_g": plan.fat_g_target,
        },
    )


def _load_active_diet_plan(database_path: Path) -> DietPlanSummary | None:
    plan_row, meal_rows, item_rows_by_meal = fetch_active_diet_plan_rows(database_path)
    if not plan_row:
        return None

    _, name, status, notes = plan_row
    return build_diet_plan_summary(
        name=name,
        status=status,
        notes=notes,
        database_path=database_path,
        meal_rows=meal_rows,
        item_rows_by_meal=item_rows_by_meal,
    )


def _load_actual_meal_progress(database_path: Path, date_text: str) -> tuple[dict[str, dict[str, object]], dict[str, float]]:
    start = f"{date_text}T00:00:00"
    end = f"{date_text}T23:59:59"
    rows = fetch_actual_meal_progress_rows(database_path, start=start, end=end)
    return build_actual_meal_progress(rows)
