from __future__ import annotations

from pathlib import Path

from brain_ops.storage.db import connect_sqlite


def upsert_macro_targets(
    database_path: Path,
    *,
    calories: float | None,
    protein_g: float | None,
    carbs_g: float | None,
    fat_g: float | None,
    updated_at: str,
) -> None:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        connection.execute(
            """
            INSERT INTO macro_targets (id, calories, protein_g, carbs_g, fat_g, updated_at)
            VALUES (1, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                calories = excluded.calories,
                protein_g = excluded.protein_g,
                carbs_g = excluded.carbs_g,
                fat_g = excluded.fat_g,
                updated_at = excluded.updated_at
            """,
            (calories, protein_g, carbs_g, fat_g, updated_at),
        )


def replace_budget_target(
    database_path: Path,
    *,
    normalized_period: str,
    category: str | None,
    amount: float,
    normalized_currency: str,
    updated_at: str,
) -> None:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        connection.execute(
            """
            DELETE FROM budget_targets
            WHERE period = ? AND COALESCE(category, '') = COALESCE(?, '') AND currency = ?
            """,
            (normalized_period, category, normalized_currency),
        )
        connection.execute(
            """
            INSERT INTO budget_targets (period, category, amount, currency, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (normalized_period, category, amount, normalized_currency, updated_at),
        )


def upsert_habit_target(
    database_path: Path,
    *,
    habit_name: str,
    normalized_period: str,
    target_count: int,
    updated_at: str,
) -> None:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        connection.execute(
            """
            INSERT INTO habit_targets (habit_name, period, target_count, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(habit_name, period) DO UPDATE SET
                target_count = excluded.target_count,
                updated_at = excluded.updated_at
            """,
            (habit_name, normalized_period, target_count, updated_at),
        )


def fetch_macro_status_rows(
    database_path: Path,
    *,
    start: str,
    end: str,
) -> tuple[
    tuple[float | None, float | None, float | None, float | None] | None,
    tuple[float | None, float | None, float | None, float | None] | None,
]:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        target_row = connection.execute(
            "SELECT calories, protein_g, carbs_g, fat_g FROM macro_targets WHERE id = 1"
        ).fetchone()
        actual_row = connection.execute(
            """
            SELECT
                COALESCE(SUM(meal_items.calories), 0),
                COALESCE(SUM(meal_items.protein_g), 0),
                COALESCE(SUM(meal_items.carbs_g), 0),
                COALESCE(SUM(meal_items.fat_g), 0)
            FROM meals
            LEFT JOIN meal_items ON meal_items.meal_id = meals.id
            WHERE meals.logged_at BETWEEN ? AND ?
            """,
            (start, end),
        ).fetchone()
    return target_row, actual_row


def fetch_habit_target_status_rows(
    database_path: Path,
    *,
    normalized_period: str,
    start: str,
    end: str,
) -> tuple[list[tuple[str, int]], dict[str, int]]:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        target_rows = connection.execute(
            """
            SELECT habit_name, target_count
            FROM habit_targets
            WHERE period = ?
            ORDER BY habit_name
            """,
            (normalized_period,),
        ).fetchall()
        completed_counts_by_habit: dict[str, int] = {}
        for habit_name, _ in target_rows:
            completed_row = connection.execute(
                """
                SELECT COUNT(*)
                FROM habits
                WHERE checked_at BETWEEN ? AND ? AND habit_name = ? AND status = 'done'
                """,
                (start, end, habit_name),
            ).fetchone()
            completed_counts_by_habit[str(habit_name)] = int(completed_row[0] or 0)
    return target_rows, completed_counts_by_habit


def fetch_budget_status_rows(
    database_path: Path,
    *,
    normalized_period: str,
    start: str,
    end: str,
) -> tuple[list[tuple[str | None, float, str]], dict[tuple[str | None, str], float]]:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        target_rows = connection.execute(
            """
            SELECT category, amount, currency
            FROM budget_targets
            WHERE period = ?
            AND id IN (
                SELECT MAX(id)
                FROM budget_targets
                WHERE period = ?
                GROUP BY COALESCE(category, ''), currency
            )
            ORDER BY COALESCE(category, ''), currency
            """,
            (normalized_period, normalized_period),
        ).fetchall()
        actual_amounts_by_target: dict[tuple[str | None, str], float] = {}
        for category, _, currency in target_rows:
            if category:
                actual_row = connection.execute(
                    """
                    SELECT COALESCE(SUM(amount), 0)
                    FROM expenses
                    WHERE logged_at BETWEEN ? AND ? AND COALESCE(category, '') = ? AND currency = ?
                    """,
                    (start, end, category, currency),
                ).fetchone()
            else:
                actual_row = connection.execute(
                    """
                    SELECT COALESCE(SUM(amount), 0)
                    FROM expenses
                    WHERE logged_at BETWEEN ? AND ? AND currency = ?
                    """,
                    (start, end, currency),
                ).fetchone()
            actual_amounts_by_target[(category, currency)] = float(actual_row[0] or 0)
    return target_rows, actual_amounts_by_target
