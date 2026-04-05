"""CLI app construction."""

from __future__ import annotations

import typer
from rich.console import Console

from brain_ops.errors import BrainOpsError

from .commands import register_cli_commands
from .errors import exit_with_brain_ops_error


def create_cli_app(*, version: str, console: Console | None = None) -> typer.Typer:
    app = typer.Typer(help="brain-ops CLI")
    cli_console = console or Console()

    def handle_error(error: BrainOpsError) -> None:
        exit_with_brain_ops_error(cli_console, error)

    register_cli_commands(app, cli_console, handle_error, version=version)
    return app


__all__ = ["create_cli_app"]
