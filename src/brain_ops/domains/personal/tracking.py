from __future__ import annotations

from pathlib import Path

from brain_ops.errors import ConfigError
from brain_ops.models import (
    BodyMetricsLogResult,
    BodyMetricsSummary,
    DailyHabitsSummary,
    ExpenseLogResult,
    HabitCheckinResult,
    OperationRecord,
    OperationStatus,
    SpendingSummary,
    SupplementLogResult,
    WorkoutLogResult,
    WorkoutStatusSummary,
)

ALLOWED_HABIT_STATUSES = frozenset({"done", "skipped", "partial"})


def normalize_supplement_log_inputs(
    *,
    supplement_name: str,
    amount: float | None,
    unit: str | None,
    note: str | None,
) -> dict[str, object]:
    normalized_name = supplement_name.strip()
    if not normalized_name:
        raise ConfigError("Supplement name cannot be empty.")
    return {
        "supplement_name": normalized_name,
        "amount": amount,
        "unit": unit,
        "note": note,
    }


def normalize_habit_checkin_inputs(
    *,
    habit_name: str,
    status: str,
    note: str | None,
) -> dict[str, object]:
    normalized_habit_name = habit_name.strip()
    if not normalized_habit_name:
        raise ConfigError("Habit name cannot be empty.")
    normalized_status = status.strip().lower()
    if normalized_status not in ALLOWED_HABIT_STATUSES:
        raise ConfigError(
            f"Habit status must be one of: {', '.join(sorted(ALLOWED_HABIT_STATUSES))}."
        )
    return {
        "habit_name": normalized_habit_name,
        "status": normalized_status,
        "note": note,
    }


def normalize_daily_log_inputs(*, text: str, domain: str) -> dict[str, str]:
    normalized_text = text.strip()
    if not normalized_text:
        raise ConfigError("Daily log text cannot be empty.")
    return {
        "text": normalized_text,
        "domain": domain.strip().lower(),
    }


def normalize_body_metrics_inputs(
    *,
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
    note: str | None,
) -> dict[str, object]:
    if (
        weight_kg is None
        and body_fat_pct is None
        and fat_mass_kg is None
        and muscle_mass_kg is None
        and visceral_fat is None
        and bmr_calories is None
        and arm_cm is None
        and waist_cm is None
        and thigh_cm is None
        and calf_cm is None
    ):
        raise ConfigError("At least one body metric must be provided.")
    if weight_kg is not None and weight_kg <= 0:
        raise ConfigError("Weight must be greater than zero.")
    if body_fat_pct is not None and not 0 <= body_fat_pct <= 100:
        raise ConfigError("Body fat percentage must be between 0 and 100.")
    for label, value in {
        "Fat mass": fat_mass_kg,
        "Muscle mass": muscle_mass_kg,
        "Visceral fat": visceral_fat,
        "BMR calories": bmr_calories,
        "Arm circumference": arm_cm,
        "Waist": waist_cm,
        "Thigh circumference": thigh_cm,
        "Calf circumference": calf_cm,
    }.items():
        if value is not None and value <= 0:
            raise ConfigError(f"{label} must be greater than zero.")
    return {
        "weight_kg": weight_kg,
        "body_fat_pct": body_fat_pct,
        "fat_mass_kg": fat_mass_kg,
        "muscle_mass_kg": muscle_mass_kg,
        "visceral_fat": visceral_fat,
        "bmr_calories": bmr_calories,
        "arm_cm": arm_cm,
        "waist_cm": waist_cm,
        "thigh_cm": thigh_cm,
        "calf_cm": calf_cm,
        "note": note,
    }


def normalize_expense_log_inputs(
    *,
    amount: float,
    category: str | None,
    merchant: str | None,
    currency: str | None,
    note: str | None,
) -> dict[str, object]:
    if amount <= 0:
        raise ConfigError("Expense amount must be greater than zero.")
    return {
        "amount": amount,
        "category": category,
        "merchant": merchant,
        "currency": (currency or "MXN").upper(),
        "note": note,
    }


def build_spending_summary(
    *,
    date: str,
    database_path: Path,
    total_amount: float,
    transaction_count: int,
    category_rows: list[tuple[str, float]],
    currency: str,
) -> SpendingSummary:
    return SpendingSummary(
        date=date,
        total_amount=total_amount,
        transaction_count=transaction_count,
        by_category={category: total for category, total in category_rows},
        currency=currency,
        database_path=database_path,
    )


def build_body_metrics_summary(
    *,
    date: str,
    database_path: Path,
    count_row: tuple[object, ...] | list[object] | None,
    latest_row: tuple[object, ...] | list[object] | None,
) -> BodyMetricsSummary:
    return BodyMetricsSummary(
        date=date,
        entries_logged=int((count_row or [0])[0] or 0),
        latest_logged_at=latest_row[0] if latest_row else None,
        latest_weight_kg=float(latest_row[1]) if latest_row and latest_row[1] is not None else None,
        latest_body_fat_pct=float(latest_row[2]) if latest_row and latest_row[2] is not None else None,
        latest_fat_mass_kg=float(latest_row[3]) if latest_row and latest_row[3] is not None else None,
        latest_muscle_mass_kg=float(latest_row[4]) if latest_row and latest_row[4] is not None else None,
        latest_visceral_fat=float(latest_row[5]) if latest_row and latest_row[5] is not None else None,
        latest_bmr_calories=float(latest_row[6]) if latest_row and latest_row[6] is not None else None,
        latest_arm_cm=float(latest_row[7]) if latest_row and latest_row[7] is not None else None,
        latest_waist_cm=float(latest_row[8]) if latest_row and latest_row[8] is not None else None,
        latest_thigh_cm=float(latest_row[9]) if latest_row and latest_row[9] is not None else None,
        latest_calf_cm=float(latest_row[10]) if latest_row and latest_row[10] is not None else None,
        database_path=database_path,
    )


def build_body_metrics_log_result(
    *,
    database_path: Path,
    logged_at,
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
) -> BodyMetricsLogResult:
    pieces = []
    if weight_kg is not None:
        pieces.append(f"weight={weight_kg:g}kg")
    if body_fat_pct is not None:
        pieces.append(f"body_fat={body_fat_pct:g}%")
    if fat_mass_kg is not None:
        pieces.append(f"fat_mass={fat_mass_kg:g}kg")
    if muscle_mass_kg is not None:
        pieces.append(f"muscle_mass={muscle_mass_kg:g}kg")
    if visceral_fat is not None:
        pieces.append(f"visceral_fat={visceral_fat:g}")
    if bmr_calories is not None:
        pieces.append(f"bmr={bmr_calories:g}cal")
    if arm_cm is not None:
        pieces.append(f"arm={arm_cm:g}cm")
    if waist_cm is not None:
        pieces.append(f"waist={waist_cm:g}cm")
    if thigh_cm is not None:
        pieces.append(f"thigh={thigh_cm:g}cm")
    if calf_cm is not None:
        pieces.append(f"calf={calf_cm:g}cm")

    operation = OperationRecord(
        action="insert",
        path=database_path,
        detail=f"logged body metrics ({', '.join(pieces)})",
        status=OperationStatus.CREATED,
    )
    return BodyMetricsLogResult(
        logged_at=logged_at,
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
        operations=[operation],
        reason="Logged body metrics into SQLite.",
    )


def build_expense_log_result(
    *,
    database_path: Path,
    logged_at,
    amount: float,
    currency: str,
    category: str | None,
    merchant: str | None,
) -> ExpenseLogResult:
    operation = OperationRecord(
        action="insert",
        path=database_path,
        detail=f"logged expense {amount:.2f} {currency}",
        status=OperationStatus.CREATED,
    )
    return ExpenseLogResult(
        logged_at=logged_at,
        amount=amount,
        currency=currency,
        category=category,
        merchant=merchant,
        operations=[operation],
        reason="Logged expense into SQLite.",
    )


def build_supplement_log_result(
    *,
    database_path: Path,
    logged_at,
    supplement_name: str,
    amount: float | None,
    unit: str | None,
) -> SupplementLogResult:
    operation = OperationRecord(
        action="insert",
        path=database_path,
        detail=f"logged supplement `{supplement_name}`",
        status=OperationStatus.CREATED,
    )
    return SupplementLogResult(
        logged_at=logged_at,
        supplement_name=supplement_name,
        amount=amount,
        unit=unit,
        operations=[operation],
        reason="Logged supplement intake into SQLite.",
    )


def build_habit_checkin_result(
    *,
    database_path: Path,
    checked_at,
    habit_name: str,
    status: str,
) -> HabitCheckinResult:
    operation = OperationRecord(
        action="insert",
        path=database_path,
        detail=f"logged habit `{habit_name}` as `{status}`",
        status=OperationStatus.CREATED,
    )
    return HabitCheckinResult(
        checked_at=checked_at,
        habit_name=habit_name,
        status=status,
        operations=[operation],
        reason="Logged habit check-in into SQLite.",
    )


def build_workout_log_result(
    *,
    database_path: Path,
    logged_at,
    routine_name: str | None,
    exercises: list,
) -> WorkoutLogResult:
    operation = OperationRecord(
        action="insert",
        path=database_path,
        detail=f"logged workout with {len(exercises)} exercise(s)",
        status=OperationStatus.CREATED,
    )
    return WorkoutLogResult(
        logged_at=logged_at,
        routine_name=routine_name,
        exercises=[exercise.model_copy(deep=True) for exercise in exercises],
        operations=[operation],
        reason="Logged workout session into SQLite.",
    )


def build_workout_status_summary(
    *,
    date: str,
    database_path: Path,
    workouts_logged: int,
    rows: list[tuple[str, int]],
) -> WorkoutStatusSummary:
    total_sets = sum(int(count) for _, count in rows)
    unique_exercises = [name for name, _ in rows]
    return WorkoutStatusSummary(
        date=date,
        workouts_logged=workouts_logged,
        total_sets=total_sets,
        unique_exercises=unique_exercises,
        database_path=database_path,
    )


def build_daily_habits_summary(
    *,
    date: str,
    database_path: Path,
    rows: list[tuple[str, str, int]],
) -> DailyHabitsSummary:
    by_status: dict[str, int] = {}
    habits: list[str] = []
    total = 0
    for habit_name, status, count in rows:
        total += int(count)
        by_status[status] = by_status.get(status, 0) + int(count)
        if habit_name not in habits:
            habits.append(habit_name)

    return DailyHabitsSummary(
        date=date,
        total_checkins=total,
        by_status=by_status,
        habits=habits,
        database_path=database_path,
    )
