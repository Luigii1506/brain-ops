from __future__ import annotations

from brain_ops.intents import CaptureNoteIntent, DailyLogIntent, IntentModel


def format_general_intent_message(intent: IntentModel) -> str | None:
    match intent:
        case CaptureNoteIntent():
            return f"Capturé una nota de tipo {intent.force_type}."
        case DailyLogIntent():
            return f"Guardé el evento diario en el dominio {intent.log_domain}."
    return None
