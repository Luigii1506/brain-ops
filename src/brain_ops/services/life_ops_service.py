from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from brain_ops.errors import ConfigError
from brain_ops.models import (
    DailyHabitsSummary,
    HabitCheckinResult,
    OperationRecord,
    OperationStatus,
    SupplementLogResult,
)

ALLOWED_HABIT_STATUSES = {"done", "skipped", "partial"}


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
    if not supplement_name.strip():
        raise ConfigError("Supplement name cannot be empty.")

    logged_at = logged_at or datetime.now()
    target = database_path.expanduser()
    if not dry_run:
        target.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(target) as connection:
            connection.execute(
                """
                INSERT INTO supplements (logged_at, supplement_name, amount, unit, note, source)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (logged_at.isoformat(timespec="seconds"), supplement_name.strip(), amount, unit, note, "chat"),
            )
            connection.commit()

    operation = OperationRecord(
        action="insert",
        path=target,
        detail=f"logged supplement `{supplement_name.strip()}`",
        status=OperationStatus.CREATED,
    )
    return SupplementLogResult(
        logged_at=logged_at,
        supplement_name=supplement_name.strip(),
        amount=amount,
        unit=unit,
        operations=[operation],
        reason="Logged supplement intake into SQLite.",
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
    normalized_status = status.strip().lower()
    if normalized_status not in ALLOWED_HABIT_STATUSES:
        raise ConfigError(f"Habit status must be one of: {', '.join(sorted(ALLOWED_HABIT_STATUSES))}.")
    if not habit_name.strip():
        raise ConfigError("Habit name cannot be empty.")

    checked_at = checked_at or datetime.now()
    target = database_path.expanduser()
    if not dry_run:
        target.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(target) as connection:
            connection.execute(
                """
                INSERT INTO habits (checked_at, habit_name, status, note, source)
                VALUES (?, ?, ?, ?, ?)
                """,
                (checked_at.isoformat(timespec="seconds"), habit_name.strip(), normalized_status, note, "chat"),
            )
            connection.commit()

    operation = OperationRecord(
        action="insert",
        path=target,
        detail=f"logged habit `{habit_name.strip()}` as `{normalized_status}`",
        status=OperationStatus.CREATED,
    )
    return HabitCheckinResult(
        checked_at=checked_at,
        habit_name=habit_name.strip(),
        status=normalized_status,
        operations=[operation],
        reason="Logged habit check-in into SQLite.",
    )


def daily_habits(database_path: Path, date_text: str | None = None) -> DailyHabitsSummary:
    target = database_path.expanduser()
    if not target.exists():
        raise ConfigError(f"Database file not found: {target}")

    resolved_date = _resolve_date(date_text)
    start = f"{resolved_date}T00:00:00"
    end = f"{resolved_date}T23:59:59"

    with sqlite3.connect(target) as connection:
        rows = connection.execute(
            """
            SELECT habit_name, status, COUNT(*)
            FROM habits
            WHERE checked_at BETWEEN ? AND ?
            GROUP BY habit_name, status
            ORDER BY habit_name, status
            """,
            (start, end),
        ).fetchall()

    by_status: dict[str, int] = {}
    habits: list[str] = []
    total = 0
    for habit_name, status, count in rows:
        total += int(count)
        by_status[status] = by_status.get(status, 0) + int(count)
        if habit_name not in habits:
            habits.append(habit_name)

    return DailyHabitsSummary(
        date=resolved_date,
        total_checkins=total,
        by_status=by_status,
        habits=habits,
        database_path=target,
    )


def _resolve_date(date_text: str | None) -> str:
    if not date_text:
        return datetime.now().date().isoformat()
    try:
        return datetime.fromisoformat(date_text).date().isoformat()
    except ValueError as exc:
        raise ConfigError("Date must be in YYYY-MM-DD format.") from exc
