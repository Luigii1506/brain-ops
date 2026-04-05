"""CLI orchestration helpers for automation-oriented commands."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.table import Table

from brain_ops.application import (
    execute_alert_delivery_presets_workflow,
    execute_event_log_alert_delivery_workflow,
    render_alert_message_text,
)

from .runtime import load_alert_output_dir, load_event_log_path


def build_alert_delivery_presets_table(presets: dict[str, object]) -> Table:
    table = Table(title="Alert Delivery Presets")
    table.add_column("Preset")
    table.add_column("Format")
    table.add_column("Target")
    table.add_column("Delivery Mode")
    table.add_column("Write Latest")
    for name, preset in presets.items():
        table.add_row(
            name,
            str(getattr(preset, "output_format", "-")),
            str(getattr(preset, "target", "-")),
            str(getattr(preset, "delivery_mode", "-")),
            str(getattr(preset, "write_latest", "-")),
        )
    return table


def present_alert_delivery_presets_command(
    console: Console,
    *,
    as_json: bool,
) -> None:
    presets = execute_alert_delivery_presets_workflow()
    if as_json:
        console.print_json(
            data={
                name: preset.to_dict()
                for name, preset in presets.items()
            }
        )
        return
    console.print(build_alert_delivery_presets_table(presets))


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
    output_format: str | None,
    delivery_mode: str | None,
    target: str | None,
    delivery_preset: str | None = None,
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
        delivery_preset=delivery_preset,
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


__all__ = [
    "build_alert_delivery_presets_table",
    "present_alert_delivery_presets_command",
    "present_event_log_alert_delivery_command",
]
