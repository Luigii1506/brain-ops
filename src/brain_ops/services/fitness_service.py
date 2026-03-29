from __future__ import annotations

import re
import sqlite3
from datetime import datetime
from pathlib import Path

from brain_ops.errors import ConfigError
from brain_ops.models import OperationRecord, OperationStatus, WorkoutLogResult, WorkoutSetInput, WorkoutStatusSummary

ENTRY_SPLIT_PATTERN = re.compile(r"\s*;\s*")
SERIES_PATTERN = re.compile(
    r"^(?P<exercise>.+?)\s+(?P<sets>\d+)x(?P<reps>\d+)(?:@(?P<weight>bodyweight|\d+(?:\.\d+)?)\s*(?P<unit>kg)?)?$",
    re.IGNORECASE,
)


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
    if not workout_text.strip():
        raise ConfigError("Workout text cannot be empty.")

    exercises = parse_workout_entries(workout_text)
    if not exercises:
        raise ConfigError("No workout entries could be parsed.")

    logged_at = logged_at or datetime.now()
    target = database_path.expanduser()
    if not dry_run:
        target.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(target) as connection:
            connection.execute("PRAGMA foreign_keys=ON")
            cursor = connection.execute(
                """
                INSERT INTO workouts (logged_at, routine_name, duration_minutes, note, source)
                VALUES (?, ?, ?, ?, ?)
                """,
                (logged_at.isoformat(timespec="seconds"), routine_name, duration_minutes, note or workout_text.strip(), "chat"),
            )
            workout_id = int(cursor.lastrowid)
            for exercise in exercises:
                for set_index in range(1, exercise.sets + 1):
                    connection.execute(
                        """
                        INSERT INTO workout_sets (
                            workout_id, exercise_name, set_index, reps, weight_kg, note
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            workout_id,
                            exercise.exercise_name,
                            set_index,
                            exercise.reps,
                            exercise.weight_kg,
                            exercise.note,
                        ),
                    )
            connection.commit()

    operation = OperationRecord(
        action="insert",
        path=target,
        detail=f"logged workout with {len(exercises)} exercise(s)",
        status=OperationStatus.CREATED,
    )
    return WorkoutLogResult(
        logged_at=logged_at,
        routine_name=routine_name,
        exercises=exercises,
        operations=[operation],
        reason="Logged workout session into SQLite.",
    )


def workout_status(database_path: Path, date_text: str | None = None) -> WorkoutStatusSummary:
    target = database_path.expanduser()
    if not target.exists():
        raise ConfigError(f"Database file not found: {target}")

    resolved_date = _resolve_date(date_text)
    start = f"{resolved_date}T00:00:00"
    end = f"{resolved_date}T23:59:59"

    with sqlite3.connect(target) as connection:
        workouts_logged = int(
            connection.execute(
                "SELECT COUNT(*) FROM workouts WHERE logged_at BETWEEN ? AND ?",
                (start, end),
            ).fetchone()[0]
        )
        rows = connection.execute(
            """
            SELECT workout_sets.exercise_name, COUNT(*)
            FROM workouts
            JOIN workout_sets ON workout_sets.workout_id = workouts.id
            WHERE workouts.logged_at BETWEEN ? AND ?
            GROUP BY workout_sets.exercise_name
            ORDER BY workout_sets.exercise_name
            """,
            (start, end),
        ).fetchall()

    total_sets = sum(int(count) for _, count in rows)
    unique_exercises = [name for name, _ in rows]
    return WorkoutStatusSummary(
        date=resolved_date,
        workouts_logged=workouts_logged,
        total_sets=total_sets,
        unique_exercises=unique_exercises,
        database_path=target,
    )


def parse_workout_entries(workout_text: str) -> list[WorkoutSetInput]:
    entries = [part.strip() for part in ENTRY_SPLIT_PATTERN.split(workout_text.strip()) if part.strip()]
    return [_parse_entry(entry) for entry in entries]


def _parse_entry(entry: str) -> WorkoutSetInput:
    match = SERIES_PATTERN.match(entry)
    if not match:
        raise ConfigError(
            "Workout entries must look like 'Press banca 4x8@80kg' or 'Dominadas 3x10@bodyweight'."
        )

    exercise_name = match.group("exercise").strip()
    sets = int(match.group("sets"))
    reps = int(match.group("reps"))
    weight_raw = match.group("weight")
    weight_kg = None if not weight_raw or weight_raw.lower() == "bodyweight" else float(weight_raw)
    note = "bodyweight" if weight_raw and weight_raw.lower() == "bodyweight" else None
    return WorkoutSetInput(
        exercise_name=exercise_name,
        sets=sets,
        reps=reps,
        weight_kg=weight_kg,
        note=note,
    )


def _resolve_date(date_text: str | None) -> str:
    if not date_text:
        return datetime.now().date().isoformat()
    try:
        return datetime.fromisoformat(date_text).date().isoformat()
    except ValueError as exc:
        raise ConfigError("Date must be in YYYY-MM-DD format.") from exc
