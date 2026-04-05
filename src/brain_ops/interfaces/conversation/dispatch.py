from __future__ import annotations

from brain_ops.config import VaultConfig
from brain_ops.intents import IntentModel, ParseFailure
from brain_ops.interfaces.conversation.execution import (
    execute_multi_intent_result,
    execute_single_intent_result,
)
from brain_ops.interfaces.conversation.results import build_failure_result
from brain_ops.models import HandleInputResult


def dispatch_parsed_input(
    config: VaultConfig,
    input_text: str,
    parsed: list[IntentModel] | ParseFailure,
    *,
    dry_run: bool,
    session_id: str | None,
) -> HandleInputResult:
    if isinstance(parsed, ParseFailure):
        return build_failure_result(input_text, parsed)
    if len(parsed) == 1:
        return execute_single_intent_result(
            config,
            input_text,
            parsed[0],
            dry_run=dry_run,
            session_id=session_id,
        )
    return execute_multi_intent_result(config, input_text, parsed, dry_run=dry_run)
