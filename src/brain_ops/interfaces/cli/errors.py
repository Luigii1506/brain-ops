"""Error helpers for CLI output."""

from __future__ import annotations

import typer
from rich.console import Console

from brain_ops.errors import BrainOpsError


def exit_with_brain_ops_error(console: Console, error: BrainOpsError) -> None:
    console.print(f"[red]Error:[/red] {error}")
    raise typer.Exit(code=1)


__all__ = ["exit_with_brain_ops_error"]
