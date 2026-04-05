from __future__ import annotations

from brain_ops.intents import (
    HabitCheckinIntent,
    IntentModel,
    LogBodyMetricsIntent,
    LogExpenseIntent,
    LogMealIntent,
    LogSupplementIntent,
    LogWorkoutIntent,
)


def format_logging_intent_message(intent: IntentModel, payload: object) -> str | None:
    match intent:
        case LogExpenseIntent():
            return f"Registré un gasto de {intent.amount:.2f} {intent.currency}."
        case LogMealIntent():
            item_count = getattr(payload, "items", [])
            return f"Registré una comida con {len(item_count)} item(s)."
        case LogSupplementIntent():
            return f"Registré el suplemento {intent.supplement_name}."
        case HabitCheckinIntent():
            return f"Registré el hábito {intent.habit_name} como {intent.status}."
        case LogBodyMetricsIntent():
            return "Registré tus métricas corporales."
        case LogWorkoutIntent():
            exercises = getattr(payload, "exercises", [])
            return f"Registré un workout con {len(exercises)} ejercicio(s)."
    return None
