from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from brain_ops.frontmatter import dump_frontmatter, split_frontmatter
from brain_ops.models import DailySummaryResult
from brain_ops.vault import Vault, now_iso

SUMMARY_START = "<!-- brain-ops:daily-summary:start -->"
SUMMARY_END = "<!-- brain-ops:daily-summary:end -->"


def write_daily_summary(vault: Vault, date_text: str | None = None) -> DailySummaryResult:
    resolved_date = _resolve_date(date_text)
    note_title = _daily_title(resolved_date)
    note_path = vault.note_path(vault.config.folders.daily, note_title)

    meals, meal_totals = _load_meals(vault.config.database_path, resolved_date)
    supplements = _load_supplements(vault.config.database_path, resolved_date)
    workouts = _load_workouts(vault.config.database_path, resolved_date)
    expenses, expense_totals = _load_expenses(vault.config.database_path, resolved_date)
    habits = _load_habits(vault.config.database_path, resolved_date)
    body_metrics = _load_body_metrics(vault.config.database_path, resolved_date)
    daily_logs = _load_daily_logs(vault.config.database_path, resolved_date)

    summary_block, sections = _render_summary_block(
        resolved_date,
        meals,
        meal_totals,
        supplements,
        workouts,
        expenses,
        expense_totals,
        habits,
        body_metrics,
        daily_logs,
    )

    if note_path.exists():
        text = note_path.read_text(encoding="utf-8", errors="ignore")
        frontmatter, body = split_frontmatter(text)
    else:
        frontmatter, body = {}, ""

    frontmatter.setdefault("type", "daily")
    frontmatter.setdefault("created", now_iso())
    frontmatter["updated"] = now_iso()
    frontmatter.setdefault("tags", [])

    updated_body = _upsert_summary_block(body, summary_block)
    operation = vault.write_text(note_path, dump_frontmatter(frontmatter, updated_body), overwrite=True)
    return DailySummaryResult(
        date=resolved_date,
        path=note_path,
        operations=[operation],
        sections_written=sections,
        reason="Wrote the structured daily summary block into the daily note.",
    )


def _resolve_date(date_text: str | None) -> str:
    from datetime import datetime

    if not date_text:
        return datetime.now().date().isoformat()
    return datetime.fromisoformat(date_text).date().isoformat()


def _daily_title(date_text: str) -> str:
    year, month, day = date_text.split("-")
    return f"{day}-{month}-{year}"


def _load_meals(database_path: Path, date_text: str) -> tuple[list[dict[str, object]], dict[str, float]]:
    start = f"{date_text}T00:00:00"
    end = f"{date_text}T23:59:59"
    meals: list[dict[str, object]] = []
    totals = {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0}
    with sqlite3.connect(database_path.expanduser()) as connection:
        meal_rows = connection.execute(
            """
            SELECT id, logged_at, COALESCE(meal_type, 'unspecified'), note
            FROM meals
            WHERE logged_at BETWEEN ? AND ?
            ORDER BY logged_at
            """,
            (start, end),
        ).fetchall()
        for meal_id, logged_at, meal_type, note in meal_rows:
            items = connection.execute(
                """
                SELECT food_name, grams, quantity, calories, protein_g, carbs_g, fat_g
                FROM meal_items
                WHERE meal_id = ?
                ORDER BY id
                """,
                (meal_id,),
            ).fetchall()
            rendered_items = []
            for food_name, grams, quantity, calories, protein_g, carbs_g, fat_g in items:
                totals["calories"] += float(calories or 0)
                totals["protein_g"] += float(protein_g or 0)
                totals["carbs_g"] += float(carbs_g or 0)
                totals["fat_g"] += float(fat_g or 0)
                rendered_items.append(
                    {
                        "food_name": food_name,
                        "grams": grams,
                        "quantity": quantity,
                        "calories": calories,
                        "protein_g": protein_g,
                        "carbs_g": carbs_g,
                        "fat_g": fat_g,
                    }
                )
            meals.append(
                {
                    "logged_at": logged_at,
                    "meal_type": meal_type,
                    "note": note,
                    "items": rendered_items,
                }
            )
    return meals, totals


def _load_supplements(database_path: Path, date_text: str) -> list[dict[str, object]]:
    start = f"{date_text}T00:00:00"
    end = f"{date_text}T23:59:59"
    with sqlite3.connect(database_path.expanduser()) as connection:
        rows = connection.execute(
            """
            SELECT logged_at, supplement_name, amount, unit, note
            FROM supplements
            WHERE logged_at BETWEEN ? AND ?
            ORDER BY logged_at
            """,
            (start, end),
        ).fetchall()
    return [
        {"logged_at": logged_at, "supplement_name": name, "amount": amount, "unit": unit, "note": note}
        for logged_at, name, amount, unit, note in rows
    ]


def _load_workouts(database_path: Path, date_text: str) -> list[dict[str, object]]:
    start = f"{date_text}T00:00:00"
    end = f"{date_text}T23:59:59"
    workouts: list[dict[str, object]] = []
    with sqlite3.connect(database_path.expanduser()) as connection:
        workout_rows = connection.execute(
            """
            SELECT id, logged_at, COALESCE(routine_name, 'unspecified'), duration_minutes, note
            FROM workouts
            WHERE logged_at BETWEEN ? AND ?
            ORDER BY logged_at
            """,
            (start, end),
        ).fetchall()
        for workout_id, logged_at, routine_name, duration_minutes, note in workout_rows:
            sets = connection.execute(
                """
                SELECT exercise_name, COUNT(*), MAX(reps), MAX(weight_kg), MAX(note)
                FROM workout_sets
                WHERE workout_id = ?
                GROUP BY exercise_name
                ORDER BY exercise_name
                """,
                (workout_id,),
            ).fetchall()
            workouts.append(
                {
                    "logged_at": logged_at,
                    "routine_name": routine_name,
                    "duration_minutes": duration_minutes,
                    "note": note,
                    "sets": [
                        {
                            "exercise_name": exercise_name,
                            "sets": sets_count,
                            "reps": reps,
                            "weight_kg": weight_kg,
                            "note": set_note,
                        }
                        for exercise_name, sets_count, reps, weight_kg, set_note in sets
                    ],
                }
            )
    return workouts


def _load_expenses(database_path: Path, date_text: str) -> tuple[list[dict[str, object]], dict[str, float]]:
    start = f"{date_text}T00:00:00"
    end = f"{date_text}T23:59:59"
    totals: dict[str, float] = {}
    with sqlite3.connect(database_path.expanduser()) as connection:
        rows = connection.execute(
            """
            SELECT logged_at, amount, currency, COALESCE(category, 'uncategorized'), merchant, note
            FROM expenses
            WHERE logged_at BETWEEN ? AND ?
            ORDER BY logged_at
            """,
            (start, end),
        ).fetchall()
    expenses = []
    for logged_at, amount, currency, category, merchant, note in rows:
        totals[category] = totals.get(category, 0.0) + float(amount or 0)
        expenses.append(
            {
                "logged_at": logged_at,
                "amount": amount,
                "currency": currency,
                "category": category,
                "merchant": merchant,
                "note": note,
            }
        )
    return expenses, totals


def _load_habits(database_path: Path, date_text: str) -> list[dict[str, object]]:
    start = f"{date_text}T00:00:00"
    end = f"{date_text}T23:59:59"
    with sqlite3.connect(database_path.expanduser()) as connection:
        rows = connection.execute(
            """
            SELECT checked_at, habit_name, status, note
            FROM habits
            WHERE checked_at BETWEEN ? AND ?
            ORDER BY checked_at
            """,
            (start, end),
        ).fetchall()
    return [{"checked_at": checked_at, "habit_name": habit_name, "status": status, "note": note} for checked_at, habit_name, status, note in rows]


def _load_daily_logs(database_path: Path, date_text: str) -> list[dict[str, object]]:
    start = f"{date_text}T00:00:00"
    end = f"{date_text}T23:59:59"
    with sqlite3.connect(database_path.expanduser()) as connection:
        rows = connection.execute(
            """
            SELECT logged_at, domain, payload_json
            FROM daily_logs
            WHERE logged_at BETWEEN ? AND ?
            ORDER BY logged_at
            """,
            (start, end),
        ).fetchall()
    logs = []
    for logged_at, domain, payload_json in rows:
        payload = json.loads(payload_json)
        logs.append({"logged_at": logged_at, "domain": domain, "text": payload.get("text", "")})
    return logs


def _load_body_metrics(database_path: Path, date_text: str) -> list[dict[str, object]]:
    start = f"{date_text}T00:00:00"
    end = f"{date_text}T23:59:59"
    with sqlite3.connect(database_path.expanduser()) as connection:
        rows = connection.execute(
            """
            SELECT logged_at, weight_kg, body_fat_pct, waist_cm, note
            FROM body_metrics
            WHERE logged_at BETWEEN ? AND ?
            ORDER BY logged_at
            """,
            (start, end),
        ).fetchall()
    return [
        {
            "logged_at": logged_at,
            "weight_kg": weight_kg,
            "body_fat_pct": body_fat_pct,
            "waist_cm": waist_cm,
            "note": note,
        }
        for logged_at, weight_kg, body_fat_pct, waist_cm, note in rows
    ]


def _render_summary_block(
    date_text: str,
    meals: list[dict[str, object]],
    meal_totals: dict[str, float],
    supplements: list[dict[str, object]],
    workouts: list[dict[str, object]],
    expenses: list[dict[str, object]],
    expense_totals: dict[str, float],
    habits: list[dict[str, object]],
    body_metrics: list[dict[str, object]],
    daily_logs: list[dict[str, object]],
) -> tuple[str, list[str]]:
    sections = ["Meals", "Supplements", "Workouts", "Expenses", "Habits", "Body Metrics", "Daily Logs"]
    lines = [
        SUMMARY_START,
        f"## brain-ops Daily Summary - {date_text}",
        "",
        "### Meals",
        "",
    ]
    if meals:
        lines.append(
            f"- totals: calories={meal_totals['calories']:.0f}, protein={meal_totals['protein_g']:.0f}g, carbs={meal_totals['carbs_g']:.0f}g, fat={meal_totals['fat_g']:.0f}g"
        )
        for meal in meals:
            lines.append(f"- {meal['logged_at']} | {meal['meal_type']}")
            for item in meal["items"]:
                lines.append(
                    f"  - {item['food_name']} | grams={item['grams'] or '-'} | qty={item['quantity'] or '-'} | cal={item['calories'] or '-'}"
                )
    else:
        lines.append("- None")

    lines.extend(["", "### Supplements", ""])
    if supplements:
        for supplement in supplements:
            amount = supplement["amount"] if supplement["amount"] is not None else "-"
            unit = supplement["unit"] or "-"
            lines.append(f"- {supplement['logged_at']} | {supplement['supplement_name']} | {amount} {unit}")
    else:
        lines.append("- None")

    lines.extend(["", "### Workouts", ""])
    if workouts:
        for workout in workouts:
            duration = f"{workout['duration_minutes']} min" if workout["duration_minutes"] else "-"
            lines.append(f"- {workout['logged_at']} | {workout['routine_name']} | {duration}")
            for set_info in workout["sets"]:
                weight = set_info["weight_kg"] if set_info["weight_kg"] is not None else set_info["note"] or "-"
                lines.append(
                    f"  - {set_info['exercise_name']} | {set_info['sets']}x{set_info['reps'] or '-'} | {weight}"
                )
    else:
        lines.append("- None")

    lines.extend(["", "### Expenses", ""])
    if expenses:
        total_amount = sum(float(expense["amount"] or 0) for expense in expenses)
        lines.append(f"- total: {total_amount:.2f} MXN")
        for category, total in sorted(expense_totals.items(), key=lambda item: item[1], reverse=True):
            lines.append(f"  - {category}: {total:.2f} MXN")
        for expense in expenses:
            lines.append(
                f"- {expense['logged_at']} | {expense['amount']:.2f} {expense['currency']} | {expense['category']} | {expense['merchant'] or '-'}"
            )
    else:
        lines.append("- None")

    lines.extend(["", "### Habits", ""])
    if habits:
        for habit in habits:
            lines.append(f"- {habit['checked_at']} | {habit['habit_name']} | {habit['status']}")
    else:
        lines.append("- None")

    lines.extend(["", "### Body Metrics", ""])
    if body_metrics:
        for metric in body_metrics:
            lines.append(
                f"- {metric['logged_at']} | weight={metric['weight_kg'] if metric['weight_kg'] is not None else '-'} kg | "
                f"body_fat={metric['body_fat_pct'] if metric['body_fat_pct'] is not None else '-'} % | "
                f"waist={metric['waist_cm'] if metric['waist_cm'] is not None else '-'} cm"
            )
    else:
        lines.append("- None")

    lines.extend(["", "### Daily Logs", ""])
    if daily_logs:
        for log in daily_logs:
            lines.append(f"- {log['logged_at']} | {log['domain']} | {log['text']}")
    else:
        lines.append("- None")

    lines.extend(["", SUMMARY_END])
    return "\n".join(lines).strip(), sections


def _upsert_summary_block(body: str, summary_block: str) -> str:
    stripped = body.strip()
    if SUMMARY_START in stripped and SUMMARY_END in stripped:
        start_index = stripped.index(SUMMARY_START)
        end_index = stripped.index(SUMMARY_END) + len(SUMMARY_END)
        updated = stripped[:start_index].rstrip()
        suffix = stripped[end_index:].lstrip()
        parts = [part for part in [updated, summary_block, suffix] if part]
        return "\n\n".join(parts)
    if not stripped:
        return summary_block
    return stripped + "\n\n" + summary_block
