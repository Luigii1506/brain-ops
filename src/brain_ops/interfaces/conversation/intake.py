from __future__ import annotations

from brain_ops.config import VaultConfig
from brain_ops.interfaces.conversation.follow_up_input import resolve_follow_up
from brain_ops.intents import IntentModel, ParseFailure
from brain_ops.interfaces.conversation.parsing_input import parse_intents
from brain_ops.models import HandleInputResult


def resolve_conversation_input(
    config: VaultConfig,
    input_text: str,
    *,
    use_llm: bool | None,
    session_id: str | None,
) -> HandleInputResult | list[IntentModel] | ParseFailure:
    if session_id:
        pending_resolution = resolve_follow_up(config, session_id, input_text)
        if pending_resolution is not None:
            return pending_resolution
    return parse_intents(config, input_text, use_llm=use_llm)
