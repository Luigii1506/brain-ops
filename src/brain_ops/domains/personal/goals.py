from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from brain_ops.core.validation import DEFAULT_ALLOWED_PERIODS, has_any_non_none, normalize_period
from brain_ops.errors import ConfigError
from brain_ops.models import (
    BudgetTargetResult,
    BudgetStatusItem,
    BudgetStatusSummary,
    HabitTargetResult,
    HabitStatusItem,
    HabitTargetStatusSummary,
    MacroStatusSummary,
    MacroTargetsResult,
    OperationRecord,
    OperationStatus,
)


def normalize_macro_target_inputs(
    *,
    calories: float | None,
    protein_g: float | None,
    carbs_g: float | None,
    fat_g: float | None,
) -> dict[str, float | None]:
    if not has_any_non_none([calories, protein_g, carbs_g, fat_g]):
        raise ConfigError("At least one macro target must be provided.")
    return {
        "calories": calories,
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fat_g": fat_g,
    }


def normalize_budget_target_inputs(
    *,
    amount: float,
    period: str,
    currency: str,
    category: str | None,
) -> dict[str, object]:
    if amount <= 0:
        raise ConfigError("Budget amount must be greater than zero.")
    return {
        "amount": amount,
        "period": normalize_period(period, allowed=DEFAULT_ALLOWED_PERIODS),
        "currency": (currency or "MXN").upper(),
        "category": category,
    }


def normalize_habit_target_inputs(
    *,
    habit_name: str,
    target_count: int,
    period: str,
) -> dict[str, object]:
    normalized_habit_name = habit_name.strip()
    if not normalized_habit_name:
        raise ConfigError("Habit name cannot be empty.")
    if target_count <= 0:
        raise ConfigError("Habit target count must be greater than zero.")
    return {
        "habit_name": normalized_habit_name,
        "target_count": target_count,
        "period": normalize_period(period, allowed=DEFAULT_ALLOWED_PERIODS),
    }


def build_macro_status_summary(
    *,
    date: str,
    database_path: Path,
    target_source: str | None,
    active_diet_name: str | None,
    calories_target: float | None,
    protein_g_target: float | None,
    carbs_g_target: float | None,
    fat_g_target: float | None,
    calories_actual: float,
    protein_g_actual: float,
    carbs_g_actual: float,
    fat_g_actual: float,
) -> MacroStatusSummary:
    return MacroStatusSummary(
        date=date,
        target_source=target_source,
        active_diet_name=active_diet_name,
        calories_target=calories_target,
        protein_g_target=protein_g_target,
        carbs_g_target=carbs_g_target,
        fat_g_target=fat_g_target,
        calories_actual=calories_actual,
        protein_g_actual=protein_g_actual,
        carbs_g_actual=carbs_g_actual,
        fat_g_actual=fat_g_actual,
        calories_remaining=remaining(calories_target, calories_actual),
        protein_g_remaining=remaining(protein_g_target, protein_g_actual),
        carbs_g_remaining=remaining(carbs_g_target, carbs_g_actual),
        fat_g_remaining=remaining(fat_g_target, fat_g_actual),
        database_path=database_path,
    )


def build_budget_status_summary(
    *,
    date: str,
    period: str,
    database_path: Path,
    target_rows: list[tuple[str | None, object, str]],
    actual_amounts_by_target: dict[tuple[str | None, str], float],
) -> BudgetStatusSummary:
    items: list[BudgetStatusItem] = []
    for category, amount, currency in target_rows:
        target_amount = float(amount)
        actual_amount = actual_amounts_by_target[(category, currency)]
        items.append(
            BudgetStatusItem(
                period=period,
                category=category,
                target_amount=target_amount,
                actual_amount=actual_amount,
                remaining_amount=target_amount - actual_amount,
                currency=currency,
            )
        )

    return BudgetStatusSummary(
        date=date,
        period=period,
        items=items,
        database_path=database_path,
    )


def build_habit_target_status_summary(
    *,
    date: str,
    period: str,
    database_path: Path,
    target_rows: list[tuple[str, object]],
    completed_counts_by_habit: dict[str, int],
) -> HabitTargetStatusSummary:
    items: list[HabitStatusItem] = []
    for habit_name, target_count in target_rows:
        normalized_target = int(target_count)
        completed_count = completed_counts_by_habit[str(habit_name)]
        items.append(
            HabitStatusItem(
                habit_name=habit_name,
                period=period,
                target_count=normalized_target,
                completed_count=completed_count,
                remaining_count=max(normalized_target - completed_count, 0),
            )
        )

    return HabitTargetStatusSummary(
        date=date,
        period=period,
        items=items,
        database_path=database_path,
    )


def build_macro_targets_result(
    *,
    database_path: Path,
    calories: float | None,
    protein_g: float | None,
    carbs_g: float | None,
    fat_g: float | None,
) -> MacroTargetsResult:
    operation = OperationRecord(
        action="upsert",
        path=database_path,
        detail="updated macro targets",
        status=OperationStatus.UPDATED,
    )
    return MacroTargetsResult(
        calories=calories,
        protein_g=protein_g,
        carbs_g=carbs_g,
        fat_g=fat_g,
        operations=[operation],
        reason="Stored macro targets in SQLite.",
    )


def build_budget_target_result(
    *,
    database_path: Path,
    period: str,
    amount: float,
    currency: str,
    category: str | None,
) -> BudgetTargetResult:
    operation = OperationRecord(
        action="insert",
        path=database_path,
        detail=f"stored {period} budget target",
        status=OperationStatus.CREATED,
    )
    return BudgetTargetResult(
        period=period,
        amount=amount,
        currency=currency,
        category=category,
        operations=[operation],
        reason="Stored budget target in SQLite.",
    )


def build_habit_target_result(
    *,
    database_path: Path,
    habit_name: str,
    period: str,
    target_count: int,
) -> HabitTargetResult:
    operation = OperationRecord(
        action="upsert",
        path=database_path,
        detail=f"stored {period} habit target for `{habit_name}`",
        status=OperationStatus.UPDATED,
    )
    return HabitTargetResult(
        habit_name=habit_name,
        period=period,
        target_count=target_count,
        operations=[operation],
        reason="Stored habit target in SQLite.",
    )


def resolve_macro_status_targets(
    active_diet: tuple[str, dict[str, float]] | None,
    target_row: tuple[object, object, object, object] | None,
) -> dict[str, object]:
    if active_diet is not None:
        active_diet_name, totals = active_diet
        return {
            "target_source": "active_diet",
            "active_diet_name": active_diet_name,
            "calories_target": totals["calories"],
            "protein_g_target": totals["protein_g"],
            "carbs_g_target": totals["carbs_g"],
            "fat_g_target": totals["fat_g"],
        }

    if target_row:
        return {
            "target_source": "manual",
            "active_diet_name": None,
            "calories_target": _to_float(target_row[0]),
            "protein_g_target": _to_float(target_row[1]),
            "carbs_g_target": _to_float(target_row[2]),
            "fat_g_target": _to_float(target_row[3]),
        }

    return {
        "target_source": None,
        "active_diet_name": None,
        "calories_target": None,
        "protein_g_target": None,
        "carbs_g_target": None,
        "fat_g_target": None,
    }


def build_date_bounds(date_text: str) -> tuple[str, str]:
    return (f"{date_text}T00:00:00", f"{date_text}T23:59:59")


def build_period_bounds(date_text: str, period: str) -> tuple[str, str]:
    base = datetime.fromisoformat(date_text)
    if period == "daily":
        start = base
        end = base
    elif period == "weekly":
        start = base - timedelta(days=base.weekday())
        end = start + timedelta(days=6)
    else:
        start = base.replace(day=1)
        if start.month == 12:
            next_month = start.replace(year=start.year + 1, month=1, day=1)
        else:
            next_month = start.replace(month=start.month + 1, day=1)
        end = next_month - timedelta(days=1)
    return (
        f"{start.date().isoformat()}T00:00:00",
        f"{end.date().isoformat()}T23:59:59",
    )


def remaining(target_value: float | None, actual_value: float) -> float | None:
    if target_value is None:
        return None
    return target_value - actual_value


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)
