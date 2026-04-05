"""CLI orchestration helpers for automation-oriented commands."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from brain_ops.application import execute_event_log_alert_delivery_workflow, render_alert_message_text

from .runtime import load_alert_output_dir, load_event_log_path


def present_event_log_alert_delivery_command(
    console: Console,
    *,
    event_log_path: Path | None,
    top: int,
    limit: int,
    source: str | None,
    workflow: str | None,
    since: str | None,
    until: str | None,
    preset: str | None,
    max_total_events: int | None,
    max_latest_day_events: int | None,
    output_path: Path | None,
    output_format: str,
    delivery_mode: str,
    target: str,
    as_json: bool,
) -> None:
    delivery = execute_event_log_alert_delivery_workflow(
        event_log_path=event_log_path,
        top=top,
        limit=limit,
        source=source,
        workflow=workflow,
        since=since,
        until=until,
        preset=preset,
        max_total_events=max_total_events,
        max_latest_day_events=max_latest_day_events,
        output_path=output_path,
        output_format=output_format,
        delivery_mode=delivery_mode,
        target=target,
        resolve_output_dir=load_alert_output_dir,
        load_event_log_path=load_event_log_path,
    )
    if as_json:
        console.print_json(data=delivery.to_dict())
        return
    if delivery.target == "stdout":
        if delivery.output_format == "json":
            console.print_json(data=delivery.message.to_dict())
            return
        console.print(render_alert_message_text(delivery.message), end="")
        return
    console.print(f"Wrote alert delivery to {delivery.output_path} ({delivery.output_format})")
    if delivery.latest_path is not None and delivery.latest_path != delivery.output_path:
        console.print(f"Updated latest alert delivery at {delivery.latest_path}")


__all__ = ["present_event_log_alert_delivery_command"]
