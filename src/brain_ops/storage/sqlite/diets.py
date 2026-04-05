from __future__ import annotations

from pathlib import Path

from brain_ops.storage.db import connect_sqlite


def create_diet_plan_records(
    database_path: Path,
    *,
    normalized_name: str,
    notes: str | None,
    status: str,
    created_at: str,
    activate: bool,
    parsed_meals: list[object],
) -> bool:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        existing = connection.execute(
            "SELECT id FROM diet_plans WHERE name = ?",
            (normalized_name,),
        ).fetchone()
        if existing:
            return False

        if activate:
            connection.execute("UPDATE diet_plans SET status = 'inactive'")

        cursor = connection.execute(
            """
            INSERT INTO diet_plans (name, notes, status, created_at, updated_at, activated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                normalized_name,
                notes,
                status,
                created_at,
                created_at,
                created_at if activate else None,
            ),
        )
        plan_id = int(cursor.lastrowid)
        for meal in parsed_meals:
            meal_cursor = connection.execute(
                """
                INSERT INTO diet_plan_meals (plan_id, meal_type, label, sort_order, note)
                VALUES (?, ?, ?, ?, ?)
                """,
                (plan_id, meal.meal_type.lower(), meal.label, meal.sort_order, meal.note),
            )
            plan_meal_id = int(meal_cursor.lastrowid)
            for item in meal.items:
                connection.execute(
                    """
                    INSERT INTO diet_plan_items (
                        plan_meal_id, food_name, grams, quantity, calories, protein_g, carbs_g, fat_g, note
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        plan_meal_id,
                        item.food_name,
                        item.grams,
                        item.quantity,
                        item.calories,
                        item.protein_g,
                        item.carbs_g,
                        item.fat_g,
                        None,
                    ),
                )
    return True


def activate_diet_plan(
    database_path: Path,
    *,
    normalized_name: str,
    activated_at: str,
) -> bool:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        row = connection.execute(
            "SELECT id FROM diet_plans WHERE name = ?",
            (normalized_name,),
        ).fetchone()
        if not row:
            return False
        connection.execute("UPDATE diet_plans SET status = 'inactive', updated_at = ?", (activated_at,))
        connection.execute(
            """
            UPDATE diet_plans
            SET status = 'active', updated_at = ?, activated_at = ?
            WHERE name = ?
            """,
            (activated_at, activated_at, normalized_name),
        )
    return True


def update_active_diet_meal_items(
    database_path: Path,
    *,
    normalized_meal_type: str,
    normalized_mode: str,
    parsed_items: list[object],
    updated_at: str,
) -> bool:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        meal_row = connection.execute(
            """
            SELECT diet_plan_meals.id
            FROM diet_plan_meals
            JOIN diet_plans ON diet_plans.id = diet_plan_meals.plan_id
            WHERE diet_plans.status = 'active' AND diet_plan_meals.meal_type = ?
            ORDER BY diet_plan_meals.id
            LIMIT 1
            """,
            (normalized_meal_type,),
        ).fetchone()
        if not meal_row:
            return False
        meal_id = int(meal_row[0])
        if normalized_mode == "replace":
            connection.execute("DELETE FROM diet_plan_items WHERE plan_meal_id = ?", (meal_id,))
        for item in parsed_items:
            connection.execute(
                """
                INSERT INTO diet_plan_items (
                    plan_meal_id, food_name, grams, quantity, calories, protein_g, carbs_g, fat_g, note
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
                    None,
                ),
            )
        connection.execute(
            """
            UPDATE diet_plans
            SET updated_at = ?
            WHERE status = 'active'
            """,
            (updated_at,),
        )
    return True


def fetch_active_diet_plan_rows(
    database_path: Path,
) -> tuple[
    tuple[int, str, str, str | None] | None,
    list[tuple[int, str, str]],
    dict[int, list[tuple[str, float | None, float | None, float | None, float | None, float | None, float | None]]],
]:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        plan_row = connection.execute(
            """
            SELECT id, name, status, notes
            FROM diet_plans
            WHERE status = 'active'
            ORDER BY activated_at DESC, id DESC
            LIMIT 1
            """
        ).fetchone()
        if not plan_row:
            return None, [], {}

        plan_id = int(plan_row[0])
        meal_rows = connection.execute(
            """
            SELECT id, meal_type, label
            FROM diet_plan_meals
            WHERE plan_id = ?
            ORDER BY sort_order, id
            """,
            (plan_id,),
        ).fetchall()

        item_rows_by_meal: dict[int, list[tuple[str, float | None, float | None, float | None, float | None, float | None, float | None]]] = {}
        for meal_id, _, _ in meal_rows:
            item_rows_by_meal[int(meal_id)] = connection.execute(
                """
                SELECT food_name, grams, quantity, calories, protein_g, carbs_g, fat_g
                FROM diet_plan_items
                WHERE plan_meal_id = ?
                ORDER BY id
                """,
                (meal_id,),
            ).fetchall()

    return plan_row, meal_rows, item_rows_by_meal


def fetch_actual_meal_progress_rows(
    database_path: Path,
    *,
    start: str,
    end: str,
) -> list[tuple[str, str, float | None, float | None, float | None, float | None]]:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        return connection.execute(
            """
            SELECT
                COALESCE(meals.meal_type, 'unspecified'),
                meal_items.food_name,
                meal_items.calories,
                meal_items.protein_g,
                meal_items.carbs_g,
                meal_items.fat_g
            FROM meals
            JOIN meal_items ON meal_items.meal_id = meals.id
            WHERE meals.logged_at BETWEEN ? AND ?
            ORDER BY meals.logged_at, meal_items.id
            """,
            (start, end),
        ).fetchall()


def fetch_diet_plan_names(database_path: Path) -> list[str]:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        rows = connection.execute(
            "SELECT name FROM diet_plans ORDER BY LENGTH(name) DESC, name"
        ).fetchall()
    return [str(name) for (name,) in rows]
