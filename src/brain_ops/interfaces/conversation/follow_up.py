from __future__ import annotations

from brain_ops.models import HandleInputResult, RouteDecisionResult


def apply_pending_follow_up(
    result: HandleInputResult,
    *,
    question: str,
    options: list[str],
) -> HandleInputResult:
    result.needs_follow_up = True
    result.follow_up = question
    result.follow_up_options = options
    result.assistant_message = question
    return result


def build_canceled_follow_up_result(input_text: str, followup_type: str) -> HandleInputResult:
    return HandleInputResult(
        input_text=input_text,
        decision=RouteDecisionResult(
            input_text=input_text,
            domain="follow_up",
            command="resolve-follow-up",
            confidence=1.0,
            reason="Canceled pending follow-up.",
            routing_source="follow_up",
            extracted_fields={"followup_type": followup_type},
        ),
        intent="follow_up",
        intent_version="1",
        executed=False,
        executed_command=None,
        target_domain="follow_up",
        routing_source="follow_up",
        confidence=1.0,
        extracted_fields={"followup_type": followup_type},
        normalized_fields={"selected_option": "cancel"},
        needs_follow_up=False,
        assistant_message="Entendido. Cancelé la aclaración pendiente.",
        reason="Canceled pending follow-up.",
    )


def build_unresolved_follow_up_result(
    input_text: str,
    *,
    followup_type: str,
    question: str,
    options: list[str],
) -> HandleInputResult:
    return HandleInputResult(
        input_text=input_text,
        decision=RouteDecisionResult(
            input_text=input_text,
            domain="follow_up",
            command="resolve-follow-up",
            confidence=0.4,
            reason="Could not resolve the pending follow-up choice.",
            routing_source="follow_up",
            extracted_fields={"followup_type": followup_type},
        ),
        intent="follow_up",
        intent_version="1",
        executed=False,
        executed_command=None,
        target_domain="follow_up",
        routing_source="follow_up",
        confidence=0.4,
        extracted_fields={"followup_type": followup_type},
        normalized_fields={},
        needs_follow_up=True,
        follow_up=question,
        follow_up_options=options,
        assistant_message=f"Necesito que elijas una opción: {', '.join(options)}.",
        reason="Pending follow-up requires a concrete option.",
    )


def build_resolved_follow_up_result(
    input_text: str,
    *,
    selected_option: str,
    command: str,
    domain: str,
    operations: list[object],
    normalized_fields: dict[str, object],
    assistant_message: str,
) -> HandleInputResult:
    return HandleInputResult(
        input_text=input_text,
        decision=RouteDecisionResult(
            input_text=input_text,
            domain=domain,
            command=command,
            confidence=1.0,
            reason="Resolved pending follow-up from prior assistant question.",
            routing_source="follow_up",
            extracted_fields={"selected_option": selected_option},
        ),
        intent="follow_up",
        intent_version="1",
        executed=True,
        operations=operations,
        executed_command=command,
        target_domain=domain,
        routing_source="follow_up",
        confidence=1.0,
        extracted_fields={"selected_option": selected_option},
        normalized_fields=normalized_fields,
        needs_follow_up=False,
        assistant_message=assistant_message,
        reason="Resolved pending follow-up from prior assistant question.",
    )
