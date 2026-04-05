from __future__ import annotations

from brain_ops.intents import CaptureNoteIntent, IntentModel
from brain_ops.models import RouteDecisionResult


def build_knowledge_intent_from_decision(
    text: str,
    decision: RouteDecisionResult,
) -> IntentModel | None:
    if decision.command.startswith("capture --type "):
        note_type = decision.command.split()[-1]
        return CaptureNoteIntent(
            force_type=note_type,
            text=text,
            confidence=decision.confidence,
            routing_source=decision.routing_source,
        )
    return None
