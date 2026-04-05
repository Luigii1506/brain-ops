from __future__ import annotations

from brain_ops.intents import IntentModel


def display_input_for_intent(intent: IntentModel) -> str:
    if hasattr(intent, "text"):
        return str(getattr(intent, "text"))
    if hasattr(intent, "meal_text"):
        return str(getattr(intent, "meal_text"))
    if hasattr(intent, "workout_text"):
        return str(getattr(intent, "workout_text"))
    if hasattr(intent, "items_text"):
        return str(getattr(intent, "items_text"))
    return intent.command
