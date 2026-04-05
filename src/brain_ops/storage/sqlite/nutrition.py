from __future__ import annotations

from pathlib import Path

from brain_ops.storage.db import connect_sqlite


def insert_meal_log(
    database_path: Path,
    *,
    logged_at: str,
    meal_type: str | None,
    note: str,
    items: list[object],
) -> None:
    target = database_path.expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    with connect_sqlite(target) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        cursor = connection.execute(
            "INSERT INTO meals (logged_at, meal_type, note, source) VALUES (?, ?, ?, ?)",
            (logged_at, meal_type, note, "chat"),
        )
        meal_id = int(cursor.lastrowid)
        for item in items:
            connection.execute(
                """
                INSERT INTO meal_items (
                    meal_id, food_name, grams, quantity, calories, protein_g, carbs_g, fat_g, note
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    meal_id,
                    item.food_name,
                    item.grams,
                    item.quantity,
                    item.calories,
                    item.protein_g,
                    item.carbs_g,
                    item.fat_g,
                    item.note,
                ),
            )


def fetch_daily_macro_rows(
    database_path: Path,
    *,
    date_start: str,
    date_end: str,
) -> tuple[int, tuple[int, float, float, float, float] | None]:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        meals_logged = int(
            connection.execute(
                "SELECT COUNT(*) FROM meals WHERE logged_at BETWEEN ? AND ?",
                (date_start, date_end),
            ).fetchone()[0]
        )
        row = connection.execute(
            """
            SELECT
                COUNT(meal_items.id),
                COALESCE(SUM(meal_items.calories), 0),
                COALESCE(SUM(meal_items.protein_g), 0),
                COALESCE(SUM(meal_items.carbs_g), 0),
                COALESCE(SUM(meal_items.fat_g), 0)
            FROM meals
            LEFT JOIN meal_items ON meal_items.meal_id = meals.id
            WHERE meals.logged_at BETWEEN ? AND ?
            """,
            (date_start, date_end),
        ).fetchone()
    return meals_logged, row
