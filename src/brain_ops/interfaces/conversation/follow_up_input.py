from __future__ import annotations

from brain_ops.config import VaultConfig
from brain_ops.core.execution.dispatch import execute_intent
from brain_ops.interfaces.conversation.follow_up import (
    build_canceled_follow_up_result,
    build_resolved_follow_up_result,
    build_unresolved_follow_up_result,
)
from brain_ops.interfaces.conversation.recommendations import (
    format_active_diet_follow_up_message,
    format_daily_recommendations_message,
    format_macro_targets_follow_up_message,
)
from brain_ops.interfaces.conversation.follow_up_state import (
    PendingFollowUp,
    clear_follow_up,
    load_follow_up,
)
from brain_ops.intents import ActiveDietIntent, DailyStatusIntent, MacroStatusIntent
from brain_ops.models import HandleInputResult


def resolve_follow_up(config: VaultConfig, session_id: str, input_text: str) -> HandleInputResult | None:
    pending = load_follow_up(config.database_path, session_id)
    if pending is None:
        return None

    selected = _resolve_selected_option(input_text, pending)
    if selected == "__cancel__":
        clear_follow_up(config.database_path, session_id)
        return build_canceled_follow_up_result(input_text, pending.followup_type)

    if selected is None:
        return build_unresolved_follow_up_result(
            input_text,
            followup_type=pending.followup_type,
            question=pending.question,
            options=pending.options,
        )

    clear_follow_up(config.database_path, session_id)
    if pending.followup_type == "active_diet_options":
        return _resolve_active_diet_follow_up(config, input_text, selected, pending)
    return None


def _resolve_active_diet_follow_up(
    config: VaultConfig,
    input_text: str,
    selected: str,
    pending: PendingFollowUp,
) -> HandleInputResult:
    diet_name = str(pending.context.get("diet_name") or "")
    if selected == "resumen":
        intent = ActiveDietIntent(routing_source="follow_up", confidence=1.0)
        outcome = execute_intent(config, intent)
        message = format_active_diet_follow_up_message(outcome.payload)
        command = intent.command
        domain = intent.domain
        normalized_fields = {"selected_option": selected, "active_diet_name": diet_name}
    elif selected == "objetivos":
        intent = MacroStatusIntent(routing_source="follow_up", confidence=1.0)
        outcome = execute_intent(config, intent)
        message = format_macro_targets_follow_up_message(outcome.payload)
        command = intent.command
        domain = intent.domain
        normalized_fields = {"selected_option": selected, "active_diet_name": diet_name}
    else:
        intent = DailyStatusIntent(routing_source="follow_up", confidence=1.0)
        outcome = execute_intent(config, intent)
        message = format_daily_recommendations_message(outcome.payload, diet_name=diet_name)
        command = intent.command
        domain = intent.domain
        normalized_fields = {"selected_option": selected, "active_diet_name": diet_name}

    return build_resolved_follow_up_result(
        input_text,
        selected_option=selected,
        command=command,
        domain=domain,
        operations=outcome.operations,
        normalized_fields=normalized_fields,
        assistant_message=message,
    )


def _resolve_selected_option(input_text: str, pending: PendingFollowUp) -> str | None:
    lowered = input_text.strip().lower()
    if lowered in {"no", "nop", "cancelar", "olvidalo", "olvídalo"}:
        return "__cancel__"
    if lowered in {"si", "sí", "s", "ok", "dale", "va", "claro"}:
        return pending.default_option
    for option in pending.options:
        if option in lowered:
            return option
    if "macro" in lowered or "objetivo" in lowered:
        return "objetivos"
    if "recomend" in lowered:
        return "recomendaciones"
    if "resumen" in lowered or "plan" in lowered or "comidas" in lowered:
        return "resumen"
    return None
