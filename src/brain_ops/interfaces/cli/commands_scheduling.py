"""Typer command registration for scheduling commands."""

from __future__ import annotations

import typer
from rich.console import Console

from brain_ops.errors import BrainOpsError

from .scheduling import (
    present_init_jobs_command,
    present_list_jobs_command,
    present_show_crontab_command,
)


def register_scheduling_commands(app: typer.Typer, console: Console, handle_error) -> None:
    @app.command("list-jobs")
    def list_jobs_command(
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """List all scheduled jobs."""
        try:
            present_list_jobs_command(console, as_json=as_json)
        except BrainOpsError as error:
            handle_error(error)

    @app.command("init-jobs")
    def init_jobs_command(
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Initialize the default scheduled jobs (check-all-sources, audit-vault, compile-knowledge, entity-index)."""
        try:
            present_init_jobs_command(console, as_json=as_json)
        except BrainOpsError as error:
            handle_error(error)

    @app.command("show-crontab")
    def show_crontab_command() -> None:
        """Print crontab entries for all enabled scheduled jobs."""
        try:
            present_show_crontab_command(console)
        except BrainOpsError as error:
            handle_error(error)


__all__ = ["register_scheduling_commands"]
