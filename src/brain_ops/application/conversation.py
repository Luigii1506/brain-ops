"""Application workflows for conversation-oriented capabilities."""

from __future__ import annotations

from pathlib import Path

from brain_ops.core.events import EventSink
from brain_ops.interfaces.conversation import handle_input, parse_intent, route_input
from brain_ops.interfaces.conversation.routing import intent_to_route_decision
from brain_ops.intents import ParseFailure

from .events import publish_result_events


def execute_route_input_workflow(
    *,
    config_path: Path | None,
    text: str,
    use_llm: bool | None,
    load_config,
):
    heuristic_result = route_input(text)
    config = load_config(config_path)
    parsed = parse_intent(config, text, use_llm=use_llm)
    if isinstance(parsed, ParseFailure):
        heuristic_result.routing_source = parsed.routing_source
        heuristic_result.reason = parsed.reason
        return heuristic_result
    return intent_to_route_decision(parsed, text)


def execute_handle_input_workflow(
    *,
    config_path: Path | None,
    text: str,
    dry_run: bool,
    use_llm: bool | None,
    session_id: str | None,
    load_config,
    event_sink: EventSink | None = None,
):
    config = load_config(config_path)
    result = handle_input(config, text, dry_run=dry_run, use_llm=use_llm, session_id=session_id)
    return publish_result_events(
        "handle-input",
        source="application.conversation",
        result=result,
        event_sink=event_sink,
    )


__all__ = [
    "execute_handle_input_workflow",
    "execute_route_input_workflow",
]
