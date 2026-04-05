"""Typer command registration for monitoring source commands."""

from __future__ import annotations

import typer
from rich.console import Console

from brain_ops.errors import BrainOpsError

from .sources import (
    present_add_source_command,
    present_check_all_sources_command,
    present_check_source_command,
    present_list_sources_command,
    present_remove_source_command,
)


def register_source_commands(app: typer.Typer, console: Console, handle_error) -> None:
    @app.command("add-source")
    def add_source_command(
        name: str,
        url: str = typer.Option(..., "--url", help="URL to monitor."),
        source_type: str = typer.Option("web", "--type", help="Source type: web or api."),
        selector: str | None = typer.Option(None, "--selector", help="CSS selector (web) or JSON path (api) to watch."),
        check_interval: str = typer.Option("daily", "--interval", help="Check frequency: daily, hourly."),
        description: str | None = typer.Option(None, "--description", help="Short source description."),
        tags: list[str] = typer.Option(None, "--tag", help="Repeatable tag option."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Register a URL to monitor for changes."""
        try:
            present_add_source_command(
                console,
                name=name,
                url=url,
                source_type=source_type,
                selector=selector,
                check_interval=check_interval,
                description=description,
                tags=tags or [],
                as_json=as_json,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("list-sources")
    def list_sources_command(
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """List all monitored sources."""
        try:
            present_list_sources_command(console, as_json=as_json)
        except BrainOpsError as error:
            handle_error(error)

    @app.command("remove-source")
    def remove_source_command(
        name: str,
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Remove a monitored source."""
        try:
            present_remove_source_command(console, name=name, as_json=as_json)
        except BrainOpsError as error:
            handle_error(error)

    @app.command("check-source")
    def check_source_command(
        name: str,
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Fetch a monitored source and check for changes since the last snapshot."""
        try:
            present_check_source_command(console, name=name, as_json=as_json)
        except BrainOpsError as error:
            handle_error(error)

    @app.command("check-all-sources")
    def check_all_sources_command(
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Fetch all monitored sources and check for changes."""
        try:
            present_check_all_sources_command(console, as_json=as_json)
        except BrainOpsError as error:
            handle_error(error)


__all__ = ["register_source_commands"]
