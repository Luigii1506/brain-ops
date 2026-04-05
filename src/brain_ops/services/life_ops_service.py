from __future__ import annotations

from datetime import datetime
from pathlib import Path

from brain_ops.core.validation import resolve_iso_date
from brain_ops.domains.personal.tracking import (
    normalize_habit_checkin_inputs,
    normalize_supplement_log_inputs,
    build_daily_habits_summary,
    build_habit_checkin_result,
    build_supplement_log_result,
)
from brain_ops.models import HabitCheckinResult, SupplementLogResult
from brain_ops.storage.db import ensure_database_parent, require_database_file, resolve_database_path
from brain_ops.storage.sqlite import fetch_daily_habit_rows, insert_habit_checkin, insert_supplement_log


def log_supplement(
    database_path: Path,
    supplement_name: str,
    *,
    amount: float | None = None,
    unit: str | None = None,
    note: str | None = None,
    logged_at: datetime | None = None,
    dry_run: bool = False,
) -> SupplementLogResult:
    normalized = normalize_supplement_log_inputs(
        supplement_name=supplement_name,
        amount=amount,
        unit=unit,
        note=note,
    )

    logged_at = logged_at or datetime.now()
    target = resolve_database_path(database_path)
    if not dry_run:
        ensure_database_parent(target)
        insert_supplement_log(
            target,
            logged_at=logged_at.isoformat(timespec="seconds"),
            supplement_name=normalized["supplement_name"],
            amount=normalized["amount"],
            unit=normalized["unit"],
            note=normalized["note"],
            source="chat",
        )
    return build_supplement_log_result(
        database_path=target,
        logged_at=logged_at,
        supplement_name=normalized["supplement_name"],
        amount=normalized["amount"],
        unit=normalized["unit"],
    )


def habit_checkin(
    database_path: Path,
    habit_name: str,
    *,
    status: str = "done",
    note: str | None = None,
    checked_at: datetime | None = None,
    dry_run: bool = False,
) -> HabitCheckinResult:
    normalized = normalize_habit_checkin_inputs(
        habit_name=habit_name,
        status=status,
        note=note,
    )

    checked_at = checked_at or datetime.now()
    target = resolve_database_path(database_path)
    if not dry_run:
        ensure_database_parent(target)
        insert_habit_checkin(
            target,
            checked_at=checked_at.isoformat(timespec="seconds"),
            habit_name=normalized["habit_name"],
            status=normalized["status"],
            note=normalized["note"],
            source="chat",
        )
    return build_habit_checkin_result(
        database_path=target,
        checked_at=checked_at,
        habit_name=normalized["habit_name"],
        status=normalized["status"],
    )


def daily_habits(database_path: Path, date_text: str | None = None):
    target = require_database_file(database_path)

    resolved_date = resolve_iso_date(date_text)
    start = f"{resolved_date}T00:00:00"
    end = f"{resolved_date}T23:59:59"

    rows = fetch_daily_habit_rows(target, start=start, end=end)
    return build_daily_habits_summary(
        date=resolved_date,
        database_path=target,
        rows=rows,
    )
