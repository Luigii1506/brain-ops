from __future__ import annotations

from brain_ops.config import VaultConfig
from brain_ops.interfaces.conversation.dispatch import dispatch_parsed_input
from brain_ops.interfaces.conversation.intake import resolve_conversation_input
from brain_ops.models import HandleInputResult


def handle_input(
    config: VaultConfig,
    input_text: str,
    *,
    dry_run: bool = False,
    use_llm: bool | None = None,
    session_id: str | None = None,
) -> HandleInputResult:
    parsed = resolve_conversation_input(
        config,
        input_text,
        use_llm=use_llm,
        session_id=session_id,
    )
    if isinstance(parsed, HandleInputResult):
        return parsed
    return dispatch_parsed_input(
        config,
        input_text,
        parsed,
        dry_run=dry_run,
        session_id=session_id,
    )
