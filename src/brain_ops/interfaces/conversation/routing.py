from __future__ import annotations

from brain_ops.intents import IntentModel
from brain_ops.models import RouteDecisionResult


def intent_to_route_decision(intent: IntentModel, input_text: str, *, reason: str | None = None) -> RouteDecisionResult:
    return RouteDecisionResult(
        input_text=input_text.strip(),
        domain=intent.domain,
        command=intent.command,
        confidence=intent.confidence,
        reason=reason or f"Built `{intent.intent}` intent.",
        routing_source=intent.routing_source,
        extracted_fields=_normalized_fields(intent),
    )


def _normalized_fields(intent: IntentModel) -> dict[str, object]:
    ignored = {"intent", "intent_version", "domain", "command", "routing_source", "confidence"}
    return {key: value for key, value in intent.model_dump().items() if key not in ignored and value is not None}
