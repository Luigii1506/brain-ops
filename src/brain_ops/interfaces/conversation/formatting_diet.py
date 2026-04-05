from __future__ import annotations

from brain_ops.intents import (
    CreateDietPlanIntent,
    DailyStatusIntent,
    DietStatusIntent,
    IntentModel,
    UpdateDietMealIntent,
)


def format_diet_intent_message(intent: IntentModel, payload: object, input_text: str) -> str | None:
    match intent:
        case CreateDietPlanIntent():
            return f"Creé y activé la dieta {intent.name} con {len(intent.meals)} comidas."
        case UpdateDietMealIntent():
            return f"Actualicé {intent.meal_type} en tu dieta activa."
        case DietStatusIntent():
            return format_diet_status_message(payload, input_text, intent.meal_focus)
        case DailyStatusIntent():
            return format_daily_status_message(payload, input_text)
    return None


def format_diet_status_message(summary, input_text: str, meal_focus: str | None) -> str:
    if not summary.active_diet_name:
        return "No tienes una dieta activa."
    lowered = input_text.lower()
    if meal_focus:
        normalized_focus = normalize_meal_focus(meal_focus)
        if normalized_focus == "all_meals" or "comidas" in lowered:
            missing_meals = [meal.label for meal in summary.meals if not meal.logged]
            if missing_meals:
                return f"Según tu dieta {summary.active_diet_name}, todavía te faltan estas comidas: {', '.join(missing_meals)}."
            if "cumpl" in lowered:
                return f"Sí, ya cumpliste todas las comidas de tu dieta {summary.active_diet_name}."
        else:
            focused_meal = next((meal for meal in summary.meals if meal.meal_type == normalized_focus), None)
            if focused_meal is not None:
                if "cumpl" in lowered:
                    if focused_meal.logged and focused_meal.actual_count >= focused_meal.target_count:
                        return f"Sí, ya cumpliste {focused_meal.label} en tu dieta {summary.active_diet_name}."
                    if focused_meal.logged:
                        return f"Todavía no cumples {focused_meal.label}; llevas {focused_meal.actual_count}/{focused_meal.target_count} items esperados."
                    return f"Todavía no cumples {focused_meal.label}; aún no la registras hoy."
                if not focused_meal.logged:
                    return f"En tu dieta {summary.active_diet_name} todavía no registras {focused_meal.label}."
                return f"Ya registraste {focused_meal.label}; llevas {focused_meal.actual_count}/{focused_meal.target_count} items esperados."
    return (
        f"En tu dieta {summary.active_diet_name} te faltan {summary.protein_g_remaining:.0f}g de proteína, "
        f"{summary.carbs_g_remaining:.0f}g de carbs y {summary.fat_g_remaining:.0f}g de grasa hoy."
    )


def format_daily_status_message(summary, input_text: str) -> str:
    lowered = input_text.lower()
    if "resume" in lowered or "resumen" in lowered:
        return " ".join(
            [
                f"Macros: proteína {summary.protein_g_actual:.0f}/{summary.protein_g_target or 0:.0f}g, carbs {summary.carbs_g_actual:.0f}/{summary.carbs_g_target or 0:.0f}g, grasa {summary.fat_g_actual:.0f}/{summary.fat_g_target or 0:.0f}g.",
                f"Dieta pendiente: {', '.join(summary.missing_diet_meals) if summary.missing_diet_meals else 'completa'}.",
                f"Hábitos pendientes: {', '.join(summary.habit_pending) if summary.habit_pending else 'ninguno'}.",
                f"Workout: {summary.workouts_logged} sesión(es).",
                f"Gastos: {summary.expenses_total:.2f} {summary.expense_currency}.",
            ]
        )
    if "falta" in lowered:
        parts = []
        if summary.protein_g_remaining is not None:
            parts.append(f"{summary.protein_g_remaining:.0f}g proteína")
        if summary.carbs_g_remaining is not None:
            parts.append(f"{summary.carbs_g_remaining:.0f}g carbs")
        if summary.fat_g_remaining is not None:
            parts.append(f"{summary.fat_g_remaining:.0f}g grasa")
        meals = f"Comidas pendientes: {', '.join(summary.missing_diet_meals)}." if summary.missing_diet_meals else "No te faltan comidas de la dieta."
        habits = f"Hábitos pendientes: {', '.join(summary.habit_pending)}." if summary.habit_pending else "No te faltan hábitos."
        return f"Hoy te faltan {', '.join(parts)}. {meals} {habits}"
    return (
        f"Hoy vas con proteína {summary.protein_g_actual:.0f}/{summary.protein_g_target or 0:.0f}g, "
        f"carbs {summary.carbs_g_actual:.0f}/{summary.carbs_g_target or 0:.0f}g, "
        f"grasa {summary.fat_g_actual:.0f}/{summary.fat_g_target or 0:.0f}g, "
        f"{summary.workouts_logged} workout(s), {summary.expenses_total:.2f} {summary.expense_currency} gastados "
        f"y {len(summary.habit_pending)} hábito(s) pendiente(s)."
    )


def normalize_meal_focus(value: str) -> str:
    mapping = {
        "desayuno": "breakfast",
        "breakfast": "breakfast",
        "comida": "lunch",
        "lunch": "lunch",
        "cena": "dinner",
        "dinner": "dinner",
        "all_meals": "all_meals",
    }
    return mapping.get(value.lower(), value.lower())
