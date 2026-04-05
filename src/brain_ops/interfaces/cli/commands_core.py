"""Typer command registration for core/bootstrap and conversation commands."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from brain_ops.errors import BrainOpsError

from .conversation import present_handle_input_command, present_route_input_command
from .automation import present_event_log_alert_delivery_command
from .monitoring import (
    present_event_log_alert_check_command,
    present_event_log_alert_message_command,
    present_event_log_alert_presets_command,
    present_event_log_alerts_command,
    present_event_log_failures_command,
    present_event_log_hotspots_command,
    present_event_log_report_command,
    present_event_log_summary_command,
    present_event_log_tail_command,
)
from .notes import present_daily_summary_command
from .openclaw import present_openclaw_manifest
from .system import present_info_command, present_init_command, present_init_db_command


def register_core_commands(app: typer.Typer, console: Console, handle_error, *, version: str, print_operations) -> None:
    @app.command()
    def info(config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML.")) -> None:
        """Show resolved project and vault configuration."""
        try:
            present_info_command(console, version=version, config_path=config_path)
        except BrainOpsError as error:
            handle_error(error)

    @app.command("openclaw-manifest")
    def openclaw_manifest_command(
        as_json: bool = typer.Option(True, "--json/--no-json", help="Print the manifest as JSON."),
        output: Path | None = typer.Option(None, "--output", help="Optional file path to write the manifest JSON."),
    ) -> None:
        """Print the preferred OpenClaw integration manifest for brain-ops."""
        present_openclaw_manifest(console, as_json=as_json, output=output)

    @app.command()
    def init(
        vault_path: Path = typer.Option(..., "--vault-path", help="Path to the Obsidian vault."),
        config_output: Path = typer.Option(..., "--config-output", help="Where to write the YAML config."),
        force: bool = typer.Option(False, "--force", help="Overwrite existing config."),
        dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing files."),
    ) -> None:
        """Write a local config file and create the expected vault folders."""
        try:
            present_init_command(
                console,
                vault_path=vault_path,
                config_output=config_output,
                force=force,
                dry_run=dry_run,
                print_operations=print_operations,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("init-db")
    def init_db_command(
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing files."),
    ) -> None:
        """Initialize the local sqlite database for structured life-ops data."""
        try:
            present_init_db_command(
                console,
                config_path=config_path,
                dry_run=dry_run,
                print_operations=print_operations,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("daily-summary")
    def daily_summary_command(
        date: str | None = typer.Option(None, "--date", help="Date in YYYY-MM-DD format. Defaults to today."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing to the vault."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Write the structured daily summary block from SQLite into the daily note in Obsidian."""
        try:
            present_daily_summary_command(
                console,
                config_path=config_path,
                date=date,
                dry_run=dry_run,
                as_json=as_json,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("route-input")
    def route_input_command(
        text: str,
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        use_llm: bool | None = typer.Option(None, "--use-llm/--no-use-llm", help="Override config and allow Ollama-assisted routing."),
    ) -> None:
        """Classify a natural-language input into the most likely command/domain."""
        try:
            present_route_input_command(
                console,
                config_path=config_path,
                text=text,
                as_json=as_json,
                use_llm=use_llm,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("handle-input")
    def handle_input_command(
        text: str,
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        dry_run: bool = typer.Option(False, "--dry-run", help="Preview without side effects."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
        use_llm: bool | None = typer.Option(None, "--use-llm/--no-use-llm", help="Override config and allow Ollama-assisted routing."),
        session_id: str | None = typer.Option(None, "--session-id", help="Optional stable conversation/session id for follow-ups."),
    ) -> None:
        """Route a natural-language input and execute the safest matching action when possible."""
        try:
            present_handle_input_command(
                console,
                config_path=config_path,
                text=text,
                dry_run=dry_run,
                as_json=as_json,
                use_llm=use_llm,
                session_id=session_id,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("event-log-summary")
    def event_log_summary_command(
        path: Path | None = typer.Option(None, "--path", help="Path to the JSONL event log. Defaults to BRAIN_OPS_EVENT_LOG."),
        top: int = typer.Option(5, "--top", min=1, help="How many top names/sources to show."),
        source: str | None = typer.Option(None, "--source", help="Filter events by exact source, for example application.notes."),
        workflow: str | None = typer.Option(None, "--workflow", help="Filter events by exact workflow, for example capture."),
        status: str | None = typer.Option(None, "--status", help="Filter events by exact status, for example created."),
        since: str | None = typer.Option(None, "--since", help="Filter events on or after YYYY-MM-DD or ISO datetime."),
        until: str | None = typer.Option(None, "--until", help="Filter events on or before YYYY-MM-DD or ISO datetime."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Summarize the structured event log emitted by CLI workflows."""
        try:
            present_event_log_summary_command(
                console,
                event_log_path=path,
                top=top,
                source=source,
                workflow=workflow,
                status=status,
                since=since,
                until=until,
                as_json=as_json,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("event-log-tail")
    def event_log_tail_command(
        path: Path | None = typer.Option(None, "--path", help="Path to the JSONL event log. Defaults to BRAIN_OPS_EVENT_LOG."),
        limit: int = typer.Option(10, "--limit", min=1, help="How many recent events to show."),
        source: str | None = typer.Option(None, "--source", help="Filter events by exact source, for example application.notes."),
        workflow: str | None = typer.Option(None, "--workflow", help="Filter events by exact workflow, for example capture."),
        status: str | None = typer.Option(None, "--status", help="Filter events by exact status, for example created."),
        since: str | None = typer.Option(None, "--since", help="Filter events on or after YYYY-MM-DD or ISO datetime."),
        until: str | None = typer.Option(None, "--until", help="Filter events on or before YYYY-MM-DD or ISO datetime."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Show the most recent structured events emitted by CLI workflows."""
        try:
            present_event_log_tail_command(
                console,
                event_log_path=path,
                limit=limit,
                source=source,
                workflow=workflow,
                status=status,
                since=since,
                until=until,
                as_json=as_json,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("event-log-report")
    def event_log_report_command(
        path: Path | None = typer.Option(None, "--path", help="Path to the JSONL event log. Defaults to BRAIN_OPS_EVENT_LOG."),
        top: int = typer.Option(5, "--top", min=1, help="How many top names/sources/workflows/days to show."),
        limit: int = typer.Option(10, "--limit", min=1, help="How many recent events to include."),
        source: str | None = typer.Option(None, "--source", help="Filter events by exact source, for example application.notes."),
        workflow: str | None = typer.Option(None, "--workflow", help="Filter events by exact workflow, for example capture."),
        status: str | None = typer.Option(None, "--status", help="Filter events by exact status, for example created."),
        since: str | None = typer.Option(None, "--since", help="Filter events on or after YYYY-MM-DD or ISO datetime."),
        until: str | None = typer.Option(None, "--until", help="Filter events on or before YYYY-MM-DD or ISO datetime."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Print a compact observability report with summary plus recent events."""
        try:
            present_event_log_report_command(
                console,
                event_log_path=path,
                top=top,
                limit=limit,
                source=source,
                workflow=workflow,
                status=status,
                since=since,
                until=until,
                as_json=as_json,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("event-log-hotspots")
    def event_log_hotspots_command(
        path: Path | None = typer.Option(None, "--path", help="Path to the JSONL event log. Defaults to BRAIN_OPS_EVENT_LOG."),
        top: int = typer.Option(5, "--top", min=1, help="How many top sources/workflows/outcomes/paths to show."),
        source: str | None = typer.Option(None, "--source", help="Filter events by exact source, for example application.notes."),
        workflow: str | None = typer.Option(None, "--workflow", help="Filter events by exact workflow, for example capture."),
        status: str | None = typer.Option(None, "--status", help="Filter events by exact status, for example created."),
        since: str | None = typer.Option(None, "--since", help="Filter events on or after YYYY-MM-DD or ISO datetime."),
        until: str | None = typer.Option(None, "--until", help="Filter events on or before YYYY-MM-DD or ISO datetime."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Show the hottest sources, workflows, outcomes, and paths in the filtered event window."""
        try:
            present_event_log_hotspots_command(
                console,
                event_log_path=path,
                top=top,
                source=source,
                workflow=workflow,
                status=status,
                since=since,
                until=until,
                as_json=as_json,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("event-log-failures")
    def event_log_failures_command(
        path: Path | None = typer.Option(None, "--path", help="Path to the JSONL event log. Defaults to BRAIN_OPS_EVENT_LOG."),
        top: int = typer.Option(5, "--top", min=1, help="How many top sources/workflows/outcomes/paths to show."),
        limit: int = typer.Option(10, "--limit", min=1, help="How many recent attention events to include."),
        source: str | None = typer.Option(None, "--source", help="Filter events by exact source, for example application.notes."),
        workflow: str | None = typer.Option(None, "--workflow", help="Filter events by exact workflow, for example capture."),
        since: str | None = typer.Option(None, "--since", help="Filter events on or after YYYY-MM-DD or ISO datetime."),
        until: str | None = typer.Option(None, "--until", help="Filter events on or before YYYY-MM-DD or ISO datetime."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Show attention-worthy events like skipped/failed operations in the filtered event window."""
        try:
            present_event_log_failures_command(
                console,
                event_log_path=path,
                top=top,
                limit=limit,
                source=source,
                workflow=workflow,
                since=since,
                until=until,
                as_json=as_json,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("event-log-alerts")
    def event_log_alerts_command(
        path: Path | None = typer.Option(None, "--path", help="Path to the JSONL event log. Defaults to BRAIN_OPS_EVENT_LOG."),
        top: int = typer.Option(5, "--top", min=1, help="How many top sources/workflows/outcomes/paths to show."),
        limit: int = typer.Option(10, "--limit", min=1, help="How many recent attention events to include."),
        source: str | None = typer.Option(None, "--source", help="Filter events by exact source, for example application.notes."),
        workflow: str | None = typer.Option(None, "--workflow", help="Filter events by exact workflow, for example capture."),
        since: str | None = typer.Option(None, "--since", help="Filter events on or after YYYY-MM-DD or ISO datetime."),
        until: str | None = typer.Option(None, "--until", help="Filter events on or before YYYY-MM-DD or ISO datetime."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Show a composed alert view over attention-worthy events in the filtered window."""
        try:
            present_event_log_alerts_command(
                console,
                event_log_path=path,
                top=top,
                limit=limit,
                source=source,
                workflow=workflow,
                since=since,
                until=until,
                as_json=as_json,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("event-log-alert-check")
    def event_log_alert_check_command(
        path: Path | None = typer.Option(None, "--path", help="Path to the JSONL event log. Defaults to BRAIN_OPS_EVENT_LOG."),
        top: int = typer.Option(5, "--top", min=1, help="How many top sources/workflows/outcomes/paths to show."),
        limit: int = typer.Option(10, "--limit", min=1, help="How many recent attention events to include."),
        source: str | None = typer.Option(None, "--source", help="Filter events by exact source, for example application.notes."),
        workflow: str | None = typer.Option(None, "--workflow", help="Filter events by exact workflow, for example capture."),
        since: str | None = typer.Option(None, "--since", help="Filter events on or after YYYY-MM-DD or ISO datetime."),
        until: str | None = typer.Option(None, "--until", help="Filter events on or before YYYY-MM-DD or ISO datetime."),
        preset: str | None = typer.Option(None, "--preset", help="Named alert policy preset: lenient, default, strict."),
        max_total_events: int | None = typer.Option(None, "--max-total-events", min=0, help="Trigger when total attention events exceed this threshold."),
        max_latest_day_events: int | None = typer.Option(None, "--max-latest-day-events", min=0, help="Trigger when the latest active day exceeds this threshold."),
        fail_on_alerts: bool = typer.Option(False, "--fail-on-alerts", help="Exit with code 2 when any threshold is triggered."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Evaluate simple alert thresholds over the filtered attention-event window."""
        try:
            present_event_log_alert_check_command(
                console,
                event_log_path=path,
                top=top,
                limit=limit,
                source=source,
                workflow=workflow,
                since=since,
                until=until,
                preset=preset,
                max_total_events=max_total_events,
                max_latest_day_events=max_latest_day_events,
                fail_on_alerts=fail_on_alerts,
                as_json=as_json,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("event-log-alert-presets")
    def event_log_alert_presets_command(
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """List the named alert policy presets available for event-log-alert-check."""
        try:
            present_event_log_alert_presets_command(
                console,
                as_json=as_json,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("event-log-alert-message")
    def event_log_alert_message_command(
        path: Path | None = typer.Option(None, "--path", help="Path to the JSONL event log. Defaults to BRAIN_OPS_EVENT_LOG."),
        top: int = typer.Option(5, "--top", min=1, help="How many top sources/workflows/outcomes/paths to inspect."),
        limit: int = typer.Option(10, "--limit", min=1, help="How many recent attention events to include."),
        source: str | None = typer.Option(None, "--source", help="Filter events by exact source, for example application.notes."),
        workflow: str | None = typer.Option(None, "--workflow", help="Filter events by exact workflow, for example capture."),
        since: str | None = typer.Option(None, "--since", help="Filter events on or after YYYY-MM-DD or ISO datetime."),
        until: str | None = typer.Option(None, "--until", help="Filter events on or before YYYY-MM-DD or ISO datetime."),
        preset: str | None = typer.Option(None, "--preset", help="Named alert policy preset: lenient, default, strict."),
        max_total_events: int | None = typer.Option(None, "--max-total-events", min=0, help="Override max total attention events."),
        max_latest_day_events: int | None = typer.Option(None, "--max-latest-day-events", min=0, help="Override max events for the latest active day."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Render an actionable alert message from the filtered attention-event window."""
        try:
            present_event_log_alert_message_command(
                console,
                event_log_path=path,
                top=top,
                limit=limit,
                source=source,
                workflow=workflow,
                since=since,
                until=until,
                preset=preset,
                max_total_events=max_total_events,
                max_latest_day_events=max_latest_day_events,
                as_json=as_json,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("event-log-alert-deliver")
    def event_log_alert_deliver_command(
        output: Path | None = typer.Option(None, "--output", help="Where to write the alert delivery artifact. Defaults to a policy-derived path."),
        output_format: str = typer.Option("json", "--format", help="Delivery format: json or text."),
        delivery_mode: str = typer.Option("both", "--delivery-mode", help="Delivery mode: both, archive, or latest."),
        target: str = typer.Option("file", "--target", help="Delivery target. Supported: file, stdout."),
        path: Path | None = typer.Option(None, "--path", help="Path to the JSONL event log. Defaults to BRAIN_OPS_EVENT_LOG."),
        top: int = typer.Option(5, "--top", min=1, help="How many top sources/workflows/outcomes/paths to inspect."),
        limit: int = typer.Option(10, "--limit", min=1, help="How many recent attention events to include."),
        source: str | None = typer.Option(None, "--source", help="Filter events by exact source, for example application.notes."),
        workflow: str | None = typer.Option(None, "--workflow", help="Filter events by exact workflow, for example capture."),
        since: str | None = typer.Option(None, "--since", help="Filter events on or after YYYY-MM-DD or ISO datetime."),
        until: str | None = typer.Option(None, "--until", help="Filter events on or before YYYY-MM-DD or ISO datetime."),
        preset: str | None = typer.Option(None, "--preset", help="Named alert policy preset: lenient, default, strict."),
        max_total_events: int | None = typer.Option(None, "--max-total-events", min=0, help="Override max total attention events."),
        max_latest_day_events: int | None = typer.Option(None, "--max-latest-day-events", min=0, help="Override max events for the latest active day."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Write an actionable alert artifact to a file for simple automation handoff."""
        try:
            present_event_log_alert_delivery_command(
                console,
                event_log_path=path,
                top=top,
                limit=limit,
                source=source,
                workflow=workflow,
                since=since,
                until=until,
                preset=preset,
                max_total_events=max_total_events,
                max_latest_day_events=max_latest_day_events,
                output_path=output,
                output_format=output_format,
                delivery_mode=delivery_mode,
                target=target,
                as_json=as_json,
            )
        except BrainOpsError as error:
            handle_error(error)


__all__ = ["register_core_commands"]
