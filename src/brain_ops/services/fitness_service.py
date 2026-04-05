from __future__ import annotations
from datetime import datetime
from pathlib import Path

from brain_ops.core.validation import resolve_iso_date
from brain_ops.domains.personal.tracking import build_workout_log_result, build_workout_status_summary
from brain_ops.domains.personal.fitness.workout_parsing import normalize_workout_log_input
from brain_ops.models import WorkoutLogResult
from brain_ops.storage.db import ensure_database_parent, require_database_file, resolve_database_path
from brain_ops.storage.sqlite import fetch_workout_status_rows, insert_workout_log


def log_workout(
    database_path: Path,
    workout_text: str,
    *,
    routine_name: str | None = None,
    duration_minutes: int | None = None,
    note: str | None = None,
    logged_at: datetime | None = None,
    dry_run: bool = False,
) -> WorkoutLogResult:
    normalized_text, exercises = normalize_workout_log_input(workout_text)

    logged_at = logged_at or datetime.now()
    target = resolve_database_path(database_path)
    if not dry_run:
        ensure_database_parent(target)
        insert_workout_log(
            target,
            logged_at=logged_at.isoformat(timespec="seconds"),
            routine_name=routine_name,
            duration_minutes=duration_minutes,
            note=note or normalized_text,
            exercises=exercises,
        )
    return build_workout_log_result(
        database_path=target,
        logged_at=logged_at,
        routine_name=routine_name,
        exercises=exercises,
    )


def workout_status(database_path: Path, date_text: str | None = None):
    target = require_database_file(database_path)

    resolved_date = resolve_iso_date(date_text)
    start = f"{resolved_date}T00:00:00"
    end = f"{resolved_date}T23:59:59"

    workouts_logged, rows = fetch_workout_status_rows(target, start=start, end=end)

    return build_workout_status_summary(
        date=resolved_date,
        database_path=target,
        workouts_logged=workouts_logged,
        rows=rows,
    )
