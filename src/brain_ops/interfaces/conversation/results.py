from __future__ import annotations

from brain_ops.interfaces.conversation.formatting import format_intent_message
from brain_ops.interfaces.conversation.routing_input import route_input as route_input_heuristic
from brain_ops.interfaces.conversation.routing import intent_to_route_decision
from brain_ops.intents import IntentModel, ParseFailure
from brain_ops.models import HandleInputResult, HandleInputSubResult, RouteDecisionResult


def build_single_intent_result(
    input_text: str,
    intent: IntentModel,
    outcome_reason: str,
    outcome_payload: object,
    operations: list[object],
    normalized_fields: dict[str, object],
) -> HandleInputResult:
    decision = intent_to_route_decision(intent, input_text, reason=outcome_reason)
    return HandleInputResult(
        input_text=input_text,
        decision=decision,
        intent=intent.intent,
        intent_version=intent.intent_version,
        executed=True,
        operations=operations,
        executed_command=intent.command,
        target_domain=intent.domain,
        routing_source=intent.routing_source,
        confidence=intent.confidence,
        extracted_fields=decision.extracted_fields,
        normalized_fields=normalized_fields,
        needs_follow_up=False,
        assistant_message=format_intent_message(intent, outcome_payload, input_text),
        reason=outcome_reason,
    )


def build_sub_result(
    display_input: str,
    intent: IntentModel,
    outcome_reason: str,
    outcome_payload: object,
    normalized_fields: dict[str, object],
) -> HandleInputSubResult:
    return HandleInputSubResult(
        input_text=display_input,
        intent=intent.intent,
        intent_version=intent.intent_version,
        executed=True,
        executed_command=intent.command,
        target_domain=intent.domain,
        routing_source=intent.routing_source,
        confidence=intent.confidence,
        extracted_fields=intent_to_route_decision(intent, display_input).extracted_fields,
        normalized_fields=normalized_fields,
        assistant_message=format_intent_message(intent, outcome_payload, display_input),
        reason=outcome_reason,
    )


def build_multi_intent_result(
    input_text: str,
    intents: list[IntentModel],
    operations: list[object],
    sub_results: list[HandleInputSubResult],
) -> HandleInputResult:
    routing_source = "hybrid" if any(intent.routing_source == "llm" for intent in intents) else "heuristic"
    confidence = max(intent.confidence for intent in intents) if intents else 0.0
    extracted_fields = {"intent_count": len(intents)}
    summary_commands = ", ".join(intent.command for intent in intents)
    return HandleInputResult(
        input_text=input_text,
        decision=RouteDecisionResult(
            input_text=input_text,
            domain="multi",
            command="multi-action",
            confidence=confidence,
            reason="Detected multiple actionable intents in one input.",
            routing_source=routing_source,
            extracted_fields=extracted_fields,
        ),
        intent="multi_action",
        intent_version="1",
        executed=True,
        operations=operations,
        executed_command="multi-action",
        target_domain="multi",
        routing_source=routing_source,
        confidence=confidence,
        extracted_fields=extracted_fields,
        normalized_fields={"intents": [intent.intent for intent in intents]},
        needs_follow_up=False,
        assistant_message=f"Procesé varias acciones en una sola entrada: {summary_commands}.",
        sub_results=sub_results,
        reason="Executed multiple intents from one input.",
    )


def build_failure_result(input_text: str, failure: ParseFailure) -> HandleInputResult:
    decision = route_input_heuristic(input_text)
    return HandleInputResult(
        input_text=input_text,
        decision=decision,
        executed=False,
        operations=[],
        executed_command=None,
        target_domain=decision.domain,
        routing_source=failure.routing_source,
        confidence=decision.confidence,
        extracted_fields=decision.extracted_fields,
        normalized_fields={},
        needs_follow_up=True,
        follow_up=failure.follow_up or f"Suggested next command: {decision.command}",
        assistant_message="Necesito una entrada más estructurada para ejecutar una acción segura.",
        reason=failure.reason,
    )
