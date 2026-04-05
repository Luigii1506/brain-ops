from __future__ import annotations

from datetime import datetime
from pathlib import Path

from brain_ops.core.validation import resolve_iso_date
from brain_ops.domains.personal.nutrition.meal_parsing import normalize_meal_log_input
from brain_ops.models import DailyMacrosSummary, MealLogResult, OperationRecord, OperationStatus
from brain_ops.storage.db import ensure_database_parent, require_database_file, resolve_database_path
from brain_ops.storage.sqlite import fetch_daily_macro_rows, insert_meal_log


def log_meal(
    database_path: Path,
    meal_text: str,
    *,
    meal_type: str | None = None,
    logged_at: datetime | None = None,
    dry_run: bool = False,
) -> MealLogResult:
    normalized_text, items = normalize_meal_log_input(meal_text)

    logged_at = logged_at or datetime.now()
    target = resolve_database_path(database_path)
    operations: list[OperationRecord] = []

    if not dry_run:
        ensure_database_parent(target)
        insert_meal_log(
            target,
            logged_at=logged_at.isoformat(timespec="seconds"),
            meal_type=meal_type,
            note=normalized_text,
            items=items,
        )

    operations.append(
        OperationRecord(
            action="insert",
            path=target,
            detail=f"logged meal with {len(items)} item(s)",
            status=OperationStatus.CREATED,
        )
    )
    return MealLogResult(
        logged_at=logged_at,
        meal_type=meal_type,
        items=items,
        operations=operations,
        reason="Logged structured meal data into SQLite.",
    )


def daily_macros(database_path: Path, date_text: str | None = None) -> DailyMacrosSummary:
    target = require_database_file(database_path)

    resolved_date = resolve_iso_date(date_text)
    date_start = f"{resolved_date}T00:00:00"
    date_end = f"{resolved_date}T23:59:59"

    meals_logged, row = fetch_daily_macro_rows(target, date_start=date_start, date_end=date_end)

    return DailyMacrosSummary(
        date=resolved_date,
        meals_logged=meals_logged,
        items_logged=int(row[0] or 0),
        calories=float(row[1] or 0),
        protein_g=float(row[2] or 0),
        carbs_g=float(row[3] or 0),
        fat_g=float(row[4] or 0),
        database_path=target,
    )
