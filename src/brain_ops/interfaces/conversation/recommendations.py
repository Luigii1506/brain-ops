from __future__ import annotations


def format_active_diet_follow_up_message(payload) -> str:
    if payload is None:
        return "No tienes una dieta activa."
    if not payload.meals:
        return f"Tu dieta activa es {payload.name}, pero todavía no tiene comidas definidas."
    meal_summaries = []
    for meal in payload.meals:
        items = ", ".join(item.food_name for item in meal.items[:3]) if meal.items else "sin items"
        suffix = "..." if len(meal.items) > 3 else ""
        meal_summaries.append(f"{meal.label}: {items}{suffix}")
    return f"Resumen de {payload.name}: " + " | ".join(meal_summaries) + "."


def format_macro_targets_follow_up_message(summary) -> str:
    if summary.target_source is None:
        return "No tienes objetivos de macros configurados."
    return (
        f"Tus objetivos actuales son {summary.calories_target or 0:.0f} kcal, "
        f"{summary.protein_g_target or 0:.0f}g de proteína, "
        f"{summary.carbs_g_target or 0:.0f}g de carbohidratos y "
        f"{summary.fat_g_target or 0:.0f}g de grasa."
    )


def format_daily_recommendations_message(summary, *, diet_name: str | None = None) -> str:
    parts: list[str] = []
    if diet_name:
        parts.append(f"Para seguir {diet_name}")
    else:
        parts.append("Para seguir tu plan de hoy")
    if summary.missing_diet_meals:
        parts.append(f"prioriza estas comidas pendientes: {', '.join(summary.missing_diet_meals)}")
    if summary.habit_pending:
        parts.append(f"y completa estos hábitos: {', '.join(summary.habit_pending)}")
    if summary.protein_g_remaining is not None and summary.protein_g_remaining > 0:
        parts.append(f"además te faltan {summary.protein_g_remaining:.0f}g de proteína")
    sentence = ", ".join(parts).rstrip(".")
    return sentence + "."
