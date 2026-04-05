from __future__ import annotations

from pathlib import Path

from brain_ops.storage.db import connect_sqlite


def insert_workout_log(
    database_path: Path,
    *,
    logged_at: str,
    routine_name: str | None,
    duration_minutes: int | None,
    note: str,
    exercises: list[object],
) -> None:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        cursor = connection.execute(
            """
            INSERT INTO workouts (logged_at, routine_name, duration_minutes, note, source)
            VALUES (?, ?, ?, ?, ?)
            """,
            (logged_at, routine_name, duration_minutes, note, "chat"),
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


def fetch_workout_status_rows(
    database_path: Path,
    *,
    start: str,
    end: str,
) -> tuple[int, list[tuple[str, int]]]:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
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
    return workouts_logged, rows
