from __future__ import annotations

"""Deprecated compatibility wrapper for conversation formatting.

Retained for stable imports while callers migrate to
`brain_ops.interfaces.conversation.formatting`.
"""

from brain_ops.interfaces.conversation.formatting import format_intent_message as format_conversation_intent_message
from brain_ops.intents import IntentModel


def format_intent_message(intent: IntentModel, payload: object, input_text: str) -> str:
    return format_conversation_intent_message(intent, payload, input_text)


__all__ = ["format_intent_message", "IntentModel"]
