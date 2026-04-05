"""CLI orchestration helpers for conversation commands."""

from __future__ import annotations

from rich.console import Console

from brain_ops.application import (
    execute_handle_input_workflow,
    execute_route_input_workflow,
)
from brain_ops.interfaces.cli.presenters import print_handle_input_result, print_json_or_rendered
from brain_ops.interfaces.cli.runtime import load_event_sink, load_runtime_config
from brain_ops.reporting_conversation import render_handle_input, render_route_decision


def run_route_input_command(
    *,
    config_path,
    text: str,
    use_llm: bool | None,
):
    return execute_route_input_workflow(
        config_path=config_path,
        text=text,
        use_llm=use_llm,
        load_config=load_runtime_config,
    )


def run_handle_input_command(
    *,
    config_path,
    text: str,
    dry_run: bool,
    use_llm: bool | None,
    session_id: str | None,
):
    return execute_handle_input_workflow(
        config_path=config_path,
        text=text,
        dry_run=dry_run,
        use_llm=use_llm,
        session_id=session_id,
        load_config=load_runtime_config,
        event_sink=load_event_sink(),
    )


def present_route_input_command(
    console: Console,
    *,
    config_path,
    text: str,
    as_json: bool,
    use_llm: bool | None,
) -> None:
    result = run_route_input_command(config_path=config_path, text=text, use_llm=use_llm)
    print_json_or_rendered(console, as_json=as_json, value=result, rendered=render_route_decision(result))


def present_handle_input_command(
    console: Console,
    *,
    config_path,
    text: str,
    dry_run: bool,
    as_json: bool,
    use_llm: bool | None,
    session_id: str | None,
) -> None:
    result = run_handle_input_command(
        config_path=config_path,
        text=text,
        dry_run=dry_run,
        use_llm=use_llm,
        session_id=session_id,
    )
    print_handle_input_result(
        console,
        as_json=as_json,
        result=result,
        operations=result.operations,
        rendered=render_handle_input(result),
    )


__all__ = [
    "present_handle_input_command",
    "present_route_input_command",
    "run_handle_input_command",
    "run_route_input_command",
]
