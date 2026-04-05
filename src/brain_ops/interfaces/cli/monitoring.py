"""CLI orchestration helpers for monitoring commands."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from brain_ops.application import (
    execute_event_log_alert_check_workflow,
    execute_event_log_alert_message_workflow,
    execute_event_log_alert_presets_workflow,
    execute_event_log_alerts_workflow,
    execute_event_log_failures_workflow,
    execute_event_log_hotspots_workflow,
    execute_event_log_report_workflow,
    execute_event_log_summary_workflow,
    execute_event_log_tail_workflow,
)
from brain_ops.core.events import DomainEvent, EventLogDayActivity, EventLogSummary, event_to_dict

from .automation import present_event_log_alert_delivery_command
from .runtime import load_alert_output_dir, load_event_log_path


def build_event_log_summary_table(summary: EventLogSummary) -> Table:
    table = Table(title="Event Log Summary")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Path", str(summary.path))
    table.add_row("Total events", str(summary.total_events))
    table.add_row("First event", summary.first_occurred_at.isoformat() if summary.first_occurred_at else "-")
    table.add_row("Last event", summary.last_occurred_at.isoformat() if summary.last_occurred_at else "-")
    table.add_row(
        "Top names",
        ", ".join(f"{name} ({count})" for name, count in summary.names) if summary.names else "-",
    )
    table.add_row(
        "Top sources",
        ", ".join(f"{source} ({count})" for source, count in summary.sources) if summary.sources else "-",
    )
    table.add_row(
        "Top workflows",
        ", ".join(f"{workflow} ({count})" for workflow, count in summary.workflows) if summary.workflows else "-",
    )
    table.add_row(
        "Top outcomes",
        ", ".join(f"{outcome} ({count})" for outcome, count in summary.outcomes) if summary.outcomes else "-",
    )
    table.add_row(
        "Top actions",
        ", ".join(f"{action} ({count})" for action, count in summary.actions) if summary.actions else "-",
    )
    table.add_row(
        "Top statuses",
        ", ".join(f"{status} ({count})" for status, count in summary.statuses) if summary.statuses else "-",
    )
    table.add_row(
        "Top paths",
        ", ".join(f"{path} ({count})" for path, count in summary.paths) if summary.paths else "-",
    )
    table.add_row(
        "Top days",
        ", ".join(f"{day} ({count})" for day, count in summary.days) if summary.days else "-",
    )
    return table


def present_event_log_summary_command(
    console: Console,
    *,
    event_log_path: Path | None,
    top: int,
    source: str | None,
    workflow: str | None,
    status: str | None,
    since: str | None,
    until: str | None,
    as_json: bool,
) -> None:
    summary = execute_event_log_summary_workflow(
        event_log_path=event_log_path,
        top=top,
        source=source,
        workflow=workflow,
        status=status,
        since=since,
        until=until,
        load_event_log_path=load_event_log_path,
    )
    if as_json:
        console.print_json(data=summary.to_dict())
        return
    console.print(build_event_log_summary_table(summary))


def build_event_log_tail_table(events: list[DomainEvent]) -> Table:
    table = Table(title="Recent Events")
    table.add_column("Occurred At")
    table.add_column("Name")
    table.add_column("Source")
    table.add_column("Path")
    for event in events:
        payload_path = event.payload.get("path", "-")
        table.add_row(event.occurred_at.isoformat(), event.name, event.source, str(payload_path))
    return table


def build_event_log_highlights_table(highlights: dict[str, object]) -> Table:
    table = Table(title="Highlights")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Latest day", str(highlights.get("latest_day") or "-"))
    table.add_row("Latest day total", str(highlights.get("latest_day_total_events") or 0))
    table.add_row("Latest day top source", str(highlights.get("latest_day_top_source") or "-"))
    table.add_row("Latest day top workflow", str(highlights.get("latest_day_top_workflow") or "-"))
    table.add_row("Latest day top outcome", str(highlights.get("latest_day_top_outcome") or "-"))
    table.add_row("Top path", str(highlights.get("top_path") or "-"))
    return table


def build_event_log_hotspots_table(hotspots: dict[str, object]) -> Table:
    table = Table(title="Hotspots")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row(
        "Top sources",
        ", ".join(f"{item['source']} ({item['count']})" for item in hotspots["sources"]) if hotspots["sources"] else "-",
    )
    table.add_row(
        "Top workflows",
        ", ".join(f"{item['workflow']} ({item['count']})" for item in hotspots["workflows"]) if hotspots["workflows"] else "-",
    )
    table.add_row(
        "Top outcomes",
        ", ".join(f"{item['outcome']} ({item['count']})" for item in hotspots["outcomes"]) if hotspots["outcomes"] else "-",
    )
    table.add_row(
        "Top paths",
        ", ".join(f"{item['path']} ({item['count']})" for item in hotspots["paths"]) if hotspots["paths"] else "-",
    )
    return table


def build_event_log_failures_table(summary: EventLogSummary) -> Table:
    table = Table(title="Failures")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Total attention events", str(summary.total_events))
    table.add_row(
        "Top sources",
        ", ".join(f"{source} ({count})" for source, count in summary.sources) if summary.sources else "-",
    )
    table.add_row(
        "Top workflows",
        ", ".join(f"{workflow} ({count})" for workflow, count in summary.workflows) if summary.workflows else "-",
    )
    table.add_row(
        "Top outcomes",
        ", ".join(f"{outcome} ({count})" for outcome, count in summary.outcomes) if summary.outcomes else "-",
    )
    table.add_row(
        "Top statuses",
        ", ".join(f"{item_status} ({count})" for item_status, count in summary.statuses) if summary.statuses else "-",
    )
    table.add_row(
        "Top paths",
        ", ".join(f"{path} ({count})" for path, count in summary.paths) if summary.paths else "-",
    )
    return table


def build_event_log_alert_check_table(ok: bool, triggered_rules: list[str]) -> Table:
    table = Table(title="Alert Check")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Status", "ok" if ok else "alert")
    table.add_row("Triggered rules", ", ".join(triggered_rules) if triggered_rules else "-")
    return table


def build_event_log_alert_presets_table(presets: dict[str, object]) -> Table:
    table = Table(title="Alert Policy Presets")
    table.add_column("Preset")
    table.add_column("Max Total Events")
    table.add_column("Max Latest Day Events")
    for name, policy in presets.items():
        table.add_row(
            name,
            str(policy.max_total_events) if getattr(policy, "max_total_events", None) is not None else "-",
            str(policy.max_latest_day_events) if getattr(policy, "max_latest_day_events", None) is not None else "-",
        )
    return table


def build_event_log_alert_message_table(message: dict[str, object]) -> Table:
    table = Table(title="Alert Message")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Level", str(message.get("level") or "-"))
    table.add_row("Title", str(message.get("title") or "-"))
    table.add_row("Summary", str(message.get("summary") or "-"))
    table.add_row(
        "Triggered rules",
        ", ".join(message.get("triggered_rules", [])) if message.get("triggered_rules") else "-",
    )
    return table


def build_event_log_daily_activity_table(activity: list[EventLogDayActivity]) -> Table:
    table = Table(title="Daily Activity")
    table.add_column("Day")
    table.add_column("Total")
    table.add_column("Top Sources")
    table.add_column("Top Workflows")
    table.add_column("Top Outcomes")
    for item in activity:
        table.add_row(
            item.day,
            str(item.total_events),
            ", ".join(f"{source} ({count})" for source, count in item.sources) if item.sources else "-",
            ", ".join(f"{workflow} ({count})" for workflow, count in item.workflows) if item.workflows else "-",
            ", ".join(f"{outcome} ({count})" for outcome, count in item.outcomes) if item.outcomes else "-",
        )
    return table


def present_event_log_tail_command(
    console: Console,
    *,
    event_log_path: Path | None,
    limit: int,
    source: str | None,
    workflow: str | None,
    status: str | None,
    since: str | None,
    until: str | None,
    as_json: bool,
) -> None:
    events = execute_event_log_tail_workflow(
        event_log_path=event_log_path,
        limit=limit,
        source=source,
        workflow=workflow,
        status=status,
        since=since,
        until=until,
        load_event_log_path=load_event_log_path,
    )
    if as_json:
        console.print_json(data=[event_to_dict(event) for event in events])
        return
    console.print(build_event_log_tail_table(events))


def present_event_log_report_command(
    console: Console,
    *,
    event_log_path: Path | None,
    top: int,
    limit: int,
    source: str | None,
    workflow: str | None,
    status: str | None,
    since: str | None,
    until: str | None,
    as_json: bool,
) -> None:
    report = execute_event_log_report_workflow(
        event_log_path=event_log_path,
        top=top,
        limit=limit,
        source=source,
        workflow=workflow,
        status=status,
        since=since,
        until=until,
        load_event_log_path=load_event_log_path,
    )
    if as_json:
        console.print_json(data=report.to_dict())
        return
    console.print(build_event_log_summary_table(report.summary))
    console.print(build_event_log_highlights_table(report.highlights))
    console.print(build_event_log_daily_activity_table(report.daily_activity))
    console.print(build_event_log_tail_table(report.recent_events))


def present_event_log_hotspots_command(
    console: Console,
    *,
    event_log_path: Path | None,
    top: int,
    source: str | None,
    workflow: str | None,
    status: str | None,
    since: str | None,
    until: str | None,
    as_json: bool,
) -> None:
    hotspots = execute_event_log_hotspots_workflow(
        event_log_path=event_log_path,
        top=top,
        source=source,
        workflow=workflow,
        status=status,
        since=since,
        until=until,
        load_event_log_path=load_event_log_path,
    )
    if as_json:
        console.print_json(data=hotspots.to_dict())
        return
    console.print(build_event_log_highlights_table(hotspots.highlights))
    console.print(build_event_log_hotspots_table(hotspots.to_dict()))


def present_event_log_failures_command(
    console: Console,
    *,
    event_log_path: Path | None,
    top: int,
    limit: int,
    source: str | None,
    workflow: str | None,
    since: str | None,
    until: str | None,
    as_json: bool,
) -> None:
    failures = execute_event_log_failures_workflow(
        event_log_path=event_log_path,
        top=top,
        limit=limit,
        source=source,
        workflow=workflow,
        since=since,
        until=until,
        load_event_log_path=load_event_log_path,
    )
    if as_json:
        console.print_json(data=failures.to_dict())
        return
    console.print(build_event_log_failures_table(failures.summary))
    console.print(build_event_log_tail_table(failures.recent_events))


def present_event_log_alerts_command(
    console: Console,
    *,
    event_log_path: Path | None,
    top: int,
    limit: int,
    source: str | None,
    workflow: str | None,
    since: str | None,
    until: str | None,
    as_json: bool,
) -> None:
    alerts = execute_event_log_alerts_workflow(
        event_log_path=event_log_path,
        top=top,
        limit=limit,
        source=source,
        workflow=workflow,
        since=since,
        until=until,
        load_event_log_path=load_event_log_path,
    )
    if as_json:
        console.print_json(data=alerts.to_dict())
        return
    console.print(build_event_log_failures_table(alerts.summary))
    console.print(build_event_log_highlights_table(alerts.highlights))
    console.print(build_event_log_daily_activity_table(alerts.daily_activity))
    console.print(build_event_log_tail_table(alerts.recent_events))


def present_event_log_alert_check_command(
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
    fail_on_alerts: bool,
    as_json: bool,
) -> None:
    result = execute_event_log_alert_check_workflow(
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
        load_event_log_path=load_event_log_path,
    )
    if as_json:
        console.print_json(data=result.to_dict())
    else:
        console.print(build_event_log_alert_check_table(result.ok, result.triggered_rules))
        console.print(build_event_log_failures_table(result.alerts.summary))
        console.print(build_event_log_highlights_table(result.alerts.highlights))
        console.print(build_event_log_daily_activity_table(result.alerts.daily_activity))
        console.print(build_event_log_tail_table(result.alerts.recent_events))
    if fail_on_alerts and not result.ok:
        raise typer.Exit(code=2)


def present_event_log_alert_presets_command(
    console: Console,
    *,
    as_json: bool,
) -> None:
    presets = execute_event_log_alert_presets_workflow()
    if as_json:
        console.print_json(
            data={
                name: policy.to_dict()
                for name, policy in presets.items()
            }
        )
        return
    console.print(build_event_log_alert_presets_table(presets))


def present_event_log_alert_message_command(
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
    as_json: bool,
) -> None:
    message = execute_event_log_alert_message_workflow(
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
        load_event_log_path=load_event_log_path,
    )
    if as_json:
        console.print_json(data=message.to_dict())
        return
    console.print(build_event_log_alert_message_table(message.to_dict()))


__all__ = [
    "present_event_log_alert_delivery_command",
    "present_event_log_alert_message_command",
    "build_event_log_alert_message_table",
    "present_event_log_alert_presets_command",
    "build_event_log_alert_presets_table",
    "present_event_log_alert_check_command",
    "build_event_log_alert_check_table",
    "present_event_log_alerts_command",
    "present_event_log_failures_command",
    "build_event_log_failures_table",
    "present_event_log_hotspots_command",
    "build_event_log_hotspots_table",
    "present_event_log_report_command",
    "build_event_log_highlights_table",
    "build_event_log_daily_activity_table",
    "build_event_log_summary_table",
    "build_event_log_tail_table",
    "present_event_log_summary_command",
    "present_event_log_tail_command",
]
