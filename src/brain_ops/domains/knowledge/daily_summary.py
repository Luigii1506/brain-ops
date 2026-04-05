from __future__ import annotations

import json


SUMMARY_START = "<!-- brain-ops:daily-summary:start -->"
SUMMARY_END = "<!-- brain-ops:daily-summary:end -->"


def daily_summary_note_title(date_text: str) -> str:
    year, month, day = date_text.split("-")
    return f"{day}-{month}-{year}"


def build_daily_summary_supplements(
    rows: list[tuple[str, str, float | None, str | None, str | None]],
) -> list[dict[str, object]]:
    return [
        {"logged_at": logged_at, "supplement_name": name, "amount": amount, "unit": unit, "note": note}
        for logged_at, name, amount, unit, note in rows
    ]


def build_daily_summary_habits(
    rows: list[tuple[str, str, str, str | None]],
) -> list[dict[str, object]]:
    return [
        {"checked_at": checked_at, "habit_name": habit_name, "status": status, "note": note}
        for checked_at, habit_name, status, note in rows
    ]


def build_daily_summary_daily_logs(
    rows: list[tuple[str, str, str]],
) -> list[dict[str, object]]:
    logs = []
    for logged_at, domain, payload_json in rows:
        payload = json.loads(payload_json)
        logs.append({"logged_at": logged_at, "domain": domain, "text": payload.get("text", "")})
    return logs


def build_daily_summary_body_metrics(
    rows: list[tuple[str, float | None, float | None, float | None, str | None]],
) -> list[dict[str, object]]:
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


def build_daily_summary_expenses(
    rows: list[tuple[str, float, str, str, str | None, str | None]],
) -> tuple[list[dict[str, object]], dict[str, float]]:
    totals: dict[str, float] = {}
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


def build_daily_summary_meals(
    meal_rows: list[tuple[int, str, str, str | None]],
    item_rows_by_meal: dict[int, list[tuple[str, float | None, float | None, float | None, float | None, float | None, float | None]]],
) -> tuple[list[dict[str, object]], dict[str, float]]:
    meals: list[dict[str, object]] = []
    totals = {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0}
    for meal_id, logged_at, meal_type, note in meal_rows:
        rendered_items = []
        for food_name, grams, quantity, calories, protein_g, carbs_g, fat_g in item_rows_by_meal[int(meal_id)]:
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


def build_daily_summary_workouts(
    workout_rows: list[tuple[int, str, str | None, int | None, str | None]],
    set_rows_by_workout: dict[int, list[tuple[str, int, int | None, float | None, str | None]]],
) -> list[dict[str, object]]:
    workouts: list[dict[str, object]] = []
    for workout_id, logged_at, routine_name, duration_minutes, note in workout_rows:
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
                    for exercise_name, sets_count, reps, weight_kg, set_note in set_rows_by_workout[int(workout_id)]
                ],
            }
        )
    return workouts


def render_summary_block(
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
    diet_progress,
) -> tuple[str, list[str]]:
    sections = ["Meals", "Supplements", "Workouts", "Expenses", "Habits", "Body Metrics", "Daily Logs"]
    if diet_progress.active_diet_name:
        sections.insert(1, "Diet Progress")
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

    if diet_progress.active_diet_name:
        lines.extend(["", "### Diet Progress", ""])
        lines.append(
            f"- active_diet: {diet_progress.active_diet_name} | calories={diet_progress.calories_actual:.0f}/{diet_progress.calories_target:.0f} | protein={diet_progress.protein_g_actual:.0f}/{diet_progress.protein_g_target:.0f}g | carbs={diet_progress.carbs_g_actual:.0f}/{diet_progress.carbs_g_target:.0f}g | fat={diet_progress.fat_g_actual:.0f}/{diet_progress.fat_g_target:.0f}g"
        )
        for meal in diet_progress.meals:
            lines.append(
                f"- {meal.label} ({meal.meal_type}) | logged={str(meal.logged).lower()} | items={meal.actual_count}/{meal.target_count}"
            )

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


def upsert_summary_block(body: str, summary_block: str) -> str:
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


def materialize_daily_summary_document(
    frontmatter: dict[str, object],
    body: str,
    summary_block: str,
    *,
    now: str,
) -> tuple[dict[str, object], str]:
    updated_frontmatter = dict(frontmatter)
    updated_frontmatter.setdefault("type", "daily")
    updated_frontmatter.setdefault("created", now)
    updated_frontmatter["updated"] = now
    updated_frontmatter.setdefault("tags", [])
    return updated_frontmatter, upsert_summary_block(body, summary_block)


def build_daily_summary_note_content(
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
    diet_progress,
    *,
    frontmatter: dict[str, object],
    body: str,
    now: str,
) -> tuple[dict[str, object], str, list[str]]:
    summary_block, sections = render_summary_block(
        date_text,
        meals,
        meal_totals,
        supplements,
        workouts,
        expenses,
        expense_totals,
        habits,
        body_metrics,
        daily_logs,
        diet_progress,
    )
    updated_frontmatter, updated_body = materialize_daily_summary_document(
        frontmatter,
        body,
        summary_block,
        now=now,
    )
    return updated_frontmatter, updated_body, sections
