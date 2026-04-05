from __future__ import annotations

from brain_ops.interfaces.conversation.formatting_diet import format_diet_intent_message
from brain_ops.interfaces.conversation.formatting_general import format_general_intent_message
from brain_ops.interfaces.conversation.formatting_logging import format_logging_intent_message
from brain_ops.interfaces.conversation.formatting_personal import format_personal_intent_message
from brain_ops.intents import IntentModel


def format_intent_message(intent: IntentModel, payload: object, input_text: str) -> str:
    logging_message = format_logging_intent_message(intent, payload)
    if logging_message is not None:
        return logging_message
    personal_message = format_personal_intent_message(intent, payload)
    if personal_message is not None:
        return personal_message
    diet_message = format_diet_intent_message(intent, payload, input_text)
    if diet_message is not None:
        return diet_message
    general_message = format_general_intent_message(intent)
    if general_message is not None:
        return general_message
    return "Procesé tu solicitud."
