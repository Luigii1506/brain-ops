"""Top-level CLI command registration."""

from __future__ import annotations

import typer
from rich.console import Console

from .commands_core import register_core_commands
from .commands_notes import register_note_and_knowledge_commands
from .commands_personal import register_personal_commands
from .presenters import print_operations


def register_cli_commands(
    app: typer.Typer,
    console: Console,
    handle_error,
    *,
    version: str,
) -> None:
    register_core_commands(
        app,
        console,
        handle_error,
        version=version,
        print_operations=print_operations,
    )
    register_personal_commands(app, console, handle_error)
    register_note_and_knowledge_commands(app, console, handle_error)


__all__ = ["register_cli_commands"]
