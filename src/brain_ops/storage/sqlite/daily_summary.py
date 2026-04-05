from __future__ import annotations

from pathlib import Path

from brain_ops.storage.db import connect_sqlite


def fetch_daily_summary_context_rows(
    database_path: Path,
    *,
    start: str,
    end: str,
) -> dict[str, object]:
    meal_rows, item_rows_by_meal = fetch_daily_summary_meal_rows(database_path, start=start, end=end)
    workout_rows, set_rows_by_workout = fetch_daily_summary_workout_rows(database_path, start=start, end=end)
    return {
        "meal_rows": meal_rows,
        "item_rows_by_meal": item_rows_by_meal,
        "supplement_rows": fetch_daily_summary_supplement_rows(database_path, start=start, end=end),
        "workout_rows": workout_rows,
        "set_rows_by_workout": set_rows_by_workout,
        "expense_rows": fetch_daily_summary_expense_rows(database_path, start=start, end=end),
        "habit_rows": fetch_daily_summary_habit_rows(database_path, start=start, end=end),
        "daily_log_rows": fetch_daily_summary_daily_log_rows(database_path, start=start, end=end),
        "body_metric_rows": fetch_daily_summary_body_metric_rows(database_path, start=start, end=end),
    }


def fetch_daily_summary_meal_rows(
    database_path: Path,
    *,
    start: str,
    end: str,
) -> tuple[
    list[tuple[int, str, str, str | None]],
    dict[int, list[tuple[str, float | None, float | None, float | None, float | None, float | None, float | None]]],
]:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        meal_rows = connection.execute(
            """
            SELECT id, logged_at, COALESCE(meal_type, 'unspecified'), note
            FROM meals
            WHERE logged_at BETWEEN ? AND ?
            ORDER BY logged_at
            """,
            (start, end),
        ).fetchall()
        item_rows_by_meal: dict[int, list[tuple[str, float | None, float | None, float | None, float | None, float | None, float | None]]] = {}
        for meal_id, _, _, _ in meal_rows:
            item_rows_by_meal[int(meal_id)] = connection.execute(
                """
                SELECT food_name, grams, quantity, calories, protein_g, carbs_g, fat_g
                FROM meal_items
                WHERE meal_id = ?
                ORDER BY id
                """,
                (meal_id,),
            ).fetchall()
    return meal_rows, item_rows_by_meal


def fetch_daily_summary_workout_rows(
    database_path: Path,
    *,
    start: str,
    end: str,
) -> tuple[
    list[tuple[int, str, str, int | None, str | None]],
    dict[int, list[tuple[str, int, int | None, float | None, str | None]]],
]:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        workout_rows = connection.execute(
            """
            SELECT id, logged_at, COALESCE(routine_name, 'unspecified'), duration_minutes, note
            FROM workouts
            WHERE logged_at BETWEEN ? AND ?
            ORDER BY logged_at
            """,
            (start, end),
        ).fetchall()
        set_rows_by_workout: dict[int, list[tuple[str, int, int | None, float | None, str | None]]] = {}
        for workout_id, _, _, _, _ in workout_rows:
            set_rows_by_workout[int(workout_id)] = connection.execute(
                """
                SELECT exercise_name, COUNT(*), MAX(reps), MAX(weight_kg), MAX(note)
                FROM workout_sets
                WHERE workout_id = ?
                GROUP BY exercise_name
                ORDER BY exercise_name
                """,
                (workout_id,),
            ).fetchall()
    return workout_rows, set_rows_by_workout


def fetch_daily_summary_supplement_rows(
    database_path: Path,
    *,
    start: str,
    end: str,
) -> list[tuple[str, str, float | None, str | None, str | None]]:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        return connection.execute(
            """
            SELECT logged_at, supplement_name, amount, unit, note
            FROM supplements
            WHERE logged_at BETWEEN ? AND ?
            ORDER BY logged_at
            """,
            (start, end),
        ).fetchall()


def fetch_daily_summary_habit_rows(
    database_path: Path,
    *,
    start: str,
    end: str,
) -> list[tuple[str, str, str, str | None]]:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        return connection.execute(
            """
            SELECT checked_at, habit_name, status, note
            FROM habits
            WHERE checked_at BETWEEN ? AND ?
            ORDER BY checked_at
            """,
            (start, end),
        ).fetchall()


def fetch_daily_summary_daily_log_rows(
    database_path: Path,
    *,
    start: str,
    end: str,
) -> list[tuple[str, str, str]]:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        return connection.execute(
            """
            SELECT logged_at, domain, payload_json
            FROM daily_logs
            WHERE logged_at BETWEEN ? AND ?
            ORDER BY logged_at
            """,
            (start, end),
        ).fetchall()


def fetch_daily_summary_body_metric_rows(
    database_path: Path,
    *,
    start: str,
    end: str,
) -> list[tuple[str, float | None, float | None, float | None, str | None]]:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        return connection.execute(
            """
            SELECT logged_at, weight_kg, body_fat_pct, waist_cm, note
            FROM body_metrics
            WHERE logged_at BETWEEN ? AND ?
            ORDER BY logged_at
            """,
            (start, end),
        ).fetchall()


def fetch_daily_summary_expense_rows(
    database_path: Path,
    *,
    start: str,
    end: str,
) -> list[tuple[str, float | None, str, str, str | None, str | None]]:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        return connection.execute(
            """
            SELECT logged_at, amount, currency, COALESCE(category, 'uncategorized'), merchant, note
            FROM expenses
            WHERE logged_at BETWEEN ? AND ?
            ORDER BY logged_at
            """,
            (start, end),
        ).fetchall()
