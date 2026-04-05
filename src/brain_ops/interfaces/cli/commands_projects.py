"""Typer command registration for project registry and context commands."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from brain_ops.errors import BrainOpsError

from .projects import (
    present_generate_all_claude_md_command,
    present_generate_claude_md_command,
    present_list_projects_command,
    present_project_context_command,
    present_register_project_command,
    present_update_project_context_command,
)


def register_project_commands(app: typer.Typer, console: Console, handle_error) -> None:
    @app.command("register-project")
    def register_project_command(
        name: str,
        path: str = typer.Option(..., "--path", help="Absolute path to the project directory."),
        stack: list[str] = typer.Option(None, "--stack", help="Repeatable tech stack entry (e.g. python, react)."),
        description: str | None = typer.Option(None, "--description", help="Short project description."),
        run_cmd: str | None = typer.Option(None, "--run", help="Command to run the project."),
        test_cmd: str | None = typer.Option(None, "--test", help="Command to run tests."),
        build_cmd: str | None = typer.Option(None, "--build", help="Command to build the project."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Register a project in the brain-ops project registry."""
        try:
            commands: dict[str, str] = {}
            if run_cmd:
                commands["run"] = run_cmd
            if test_cmd:
                commands["test"] = test_cmd
            if build_cmd:
                commands["build"] = build_cmd
            present_register_project_command(
                console,
                name=name,
                path=path,
                stack=stack or [],
                description=description,
                commands=commands or None,
                as_json=as_json,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("list-projects")
    def list_projects_command(
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """List all registered projects."""
        try:
            present_list_projects_command(console, as_json=as_json)
        except BrainOpsError as error:
            handle_error(error)

    @app.command("project-context")
    def project_context_command(
        name: str,
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Show full context for a registered project."""
        try:
            present_project_context_command(console, name=name, as_json=as_json)
        except BrainOpsError as error:
            handle_error(error)

    @app.command("update-project-context")
    def update_project_context_command(
        name: str,
        phase: str | None = typer.Option(None, "--phase", help="Current project phase."),
        pending: list[str] = typer.Option(None, "--pending", help="Repeatable pending item."),
        decisions: list[str] = typer.Option(None, "--decision", help="Repeatable recent decision."),
        notes: str | None = typer.Option(None, "--notes", help="Free-form context notes."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Update the context for a registered project."""
        try:
            present_update_project_context_command(
                console,
                name=name,
                phase=phase,
                pending=pending or None,
                decisions=decisions or None,
                notes=notes,
                as_json=as_json,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("generate-claude-md")
    def generate_claude_md_command(
        name: str,
        output: Path | None = typer.Option(None, "--output", help="Output path. Defaults to {project_path}/CLAUDE.md."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Generate a CLAUDE.md file from the project's registered context."""
        try:
            present_generate_claude_md_command(
                console,
                name=name,
                output_path=output,
                as_json=as_json,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("generate-all-claude-md")
    def generate_all_claude_md_command(
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Generate CLAUDE.md files for all registered projects."""
        try:
            present_generate_all_claude_md_command(console, as_json=as_json)
        except BrainOpsError as error:
            handle_error(error)


__all__ = ["register_project_commands"]
