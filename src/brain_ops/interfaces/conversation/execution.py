from __future__ import annotations

from brain_ops.config import VaultConfig
from brain_ops.core.execution.dispatch import execute_intent
from brain_ops.interfaces.conversation.follow_up import apply_pending_follow_up
from brain_ops.interfaces.conversation.follow_up_state import (
    active_diet_pending_follow_up,
    save_follow_up,
)
from brain_ops.intents import IntentModel
from brain_ops.interfaces.conversation.projection import display_input_for_intent
from brain_ops.interfaces.conversation.results import (
    build_multi_intent_result,
    build_single_intent_result,
    build_sub_result,
)
from brain_ops.models import HandleInputResult


def execute_single_intent_result(
    config: VaultConfig,
    input_text: str,
    intent: IntentModel,
    *,
    dry_run: bool,
    session_id: str | None,
) -> HandleInputResult:
    outcome = execute_intent(config, intent, dry_run=dry_run)
    result = build_single_intent_result(
        input_text=input_text,
        intent=intent,
        outcome_reason=outcome.reason,
        outcome_payload=outcome.payload,
        operations=outcome.operations,
        normalized_fields=outcome.normalized_fields,
    )
    if session_id and intent.intent == "active_diet" and outcome.payload is not None:
        pending = active_diet_pending_follow_up(outcome.payload.name)
        save_follow_up(config.database_path, session_id, pending)
        return apply_pending_follow_up(result, question=pending.question, options=pending.options)
    return result


def execute_multi_intent_result(
    config: VaultConfig,
    input_text: str,
    intents: list[IntentModel],
    *,
    dry_run: bool,
) -> HandleInputResult:
    sub_results = []
    operations = []
    for intent in intents:
        outcome = execute_intent(config, intent, dry_run=dry_run)
        operations.extend(outcome.operations)
        sub_results.append(
            build_sub_result(
                display_input=display_input_for_intent(intent),
                intent=intent,
                outcome_reason=outcome.reason,
                outcome_payload=outcome.payload,
                normalized_fields=outcome.normalized_fields,
            )
        )
    return build_multi_intent_result(
        input_text=input_text,
        intents=intents,
        operations=operations,
        sub_results=sub_results,
    )
