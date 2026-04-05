from __future__ import annotations

from brain_ops.intents import (
    ActiveDietIntent,
    BudgetStatusIntent,
    HabitStatusIntent,
    IntentModel,
    MacroStatusIntent,
    SetActiveDietIntent,
    SetBudgetTargetIntent,
    SetHabitTargetIntent,
    SetMacroTargetsIntent,
)


def format_personal_intent_message(intent: IntentModel, payload: object) -> str | None:
    match intent:
        case SetMacroTargetsIntent():
            parts = []
            if intent.calories is not None:
                parts.append(f"calorías={intent.calories:.0f}")
            if intent.protein_g is not None:
                parts.append(f"proteína={intent.protein_g:.0f}g")
            if intent.carbs_g is not None:
                parts.append(f"carbs={intent.carbs_g:.0f}g")
            if intent.fat_g is not None:
                parts.append(f"grasas={intent.fat_g:.0f}g")
            return f"Actualicé tus metas de macros: {', '.join(parts)}."
        case SetBudgetTargetIntent():
            return f"Guardé un presupuesto {intent.period} de {intent.amount:.2f} {intent.currency} para {intent.category or 'general'}."
        case SetHabitTargetIntent():
            return f"Guardé el objetivo del hábito {intent.habit_name} en {intent.target_count} por periodo {intent.period}."
        case SetActiveDietIntent():
            return f"Activé la dieta {intent.name}."
        case MacroStatusIntent():
            return format_macro_status_message(payload, intent.metric)
        case BudgetStatusIntent():
            return format_budget_status_message(payload, intent.category)
        case HabitStatusIntent():
            return format_habit_status_message(payload)
        case ActiveDietIntent():
            return f"Tu dieta activa es {payload.name}." if payload else "No tienes una dieta activa."
    return None


def format_macro_status_message(summary, metric: str | None) -> str:
    if metric == "protein_g":
        return f"Hoy te faltan {summary.protein_g_remaining:.0f}g de proteína." if summary.protein_g_remaining is not None else "No hay meta de proteína configurada."
    if metric == "carbs_g":
        return f"Hoy te faltan {summary.carbs_g_remaining:.0f}g de carbs." if summary.carbs_g_remaining is not None else "No hay meta de carbs configurada."
    if metric == "fat_g":
        return f"Hoy te faltan {summary.fat_g_remaining:.0f}g de grasa." if summary.fat_g_remaining is not None else "No hay meta de grasa configurada."
    if metric == "calories":
        return f"Hoy te faltan {summary.calories_remaining:.0f} calorías." if summary.calories_remaining is not None else "No hay meta de calorías configurada."
    return (
        f"Hoy vas en proteína {summary.protein_g_actual:.0f}/{summary.protein_g_target or 0:.0f}g, "
        f"carbs {summary.carbs_g_actual:.0f}/{summary.carbs_g_target or 0:.0f}g y grasa {summary.fat_g_actual:.0f}/{summary.fat_g_target or 0:.0f}g."
    )


def format_budget_status_message(summary, category_hint: str | None) -> str:
    if category_hint:
        for item in summary.items:
            if item.category == category_hint:
                return f"Te quedan {item.remaining_amount:.2f} {item.currency} de presupuesto {summary.period} en {item.category}."
    if summary.items:
        item = summary.items[0]
        return f"Te quedan {item.remaining_amount:.2f} {item.currency} de presupuesto {summary.period} en {item.category or 'general'}."
    return "No hay presupuesto configurado para ese periodo."


def format_habit_status_message(summary) -> str:
    if not summary.items:
        return "No hay objetivos de hábitos configurados para ese periodo."
    pending = [item for item in summary.items if item.remaining_count > 0]
    if not pending:
        return "Ya cumpliste todos tus hábitos del periodo."
    first = pending[0]
    return f"Te falta {first.remaining_count} para cumplir el hábito {first.habit_name} en este periodo."
