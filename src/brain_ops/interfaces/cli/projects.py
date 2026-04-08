"""CLI orchestration helpers for project registry commands."""

from __future__ import annotations

import os
from pathlib import Path

from rich.console import Console
from rich.table import Table

from brain_ops.application.projects import (
    ProjectSessionResult,
    execute_generate_all_claude_md_workflow,
    execute_generate_claude_md_workflow,
    execute_list_projects_workflow,
    execute_project_context_workflow,
    execute_project_log_workflow,
    execute_register_project_workflow,
    execute_session_workflow,
    execute_update_project_context_workflow,
)
from brain_ops.domains.projects import Project
from brain_ops.interfaces.cli.runtime import load_database_path


def load_project_registry_path(explicit_path: Path | None = None) -> Path:
    if explicit_path is not None:
        return explicit_path
    env_path = os.getenv("BRAIN_OPS_PROJECT_REGISTRY")
    if env_path:
        return Path(env_path)
    return Path.home() / ".brain-ops" / "projects.json"


def build_project_list_table(projects: list[Project]) -> Table:
    table = Table(title="Registered Projects")
    table.add_column("Name")
    table.add_column("Path")
    table.add_column("Stack")
    table.add_column("Phase")
    for project in projects:
        table.add_row(
            project.name,
            project.path,
            ", ".join(project.stack) if project.stack else "-",
            project.context.phase or "-",
        )
    return table


def build_project_context_table(project: Project) -> Table:
    table = Table(title=f"Project: {project.name}")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Path", project.path)
    table.add_row("Stack", ", ".join(project.stack) if project.stack else "-")
    table.add_row("Description", project.description or "-")
    if project.commands:
        for label, command in project.commands.items():
            table.add_row(f"Command: {label}", command)
    table.add_row("Phase", project.context.phase or "-")
    table.add_row(
        "Pending",
        "\n".join(f"• {item}" for item in project.context.pending) if project.context.pending else "-",
    )
    table.add_row(
        "Decisions",
        "\n".join(f"• {item}" for item in project.context.decisions) if project.context.decisions else "-",
    )
    table.add_row("Notes", project.context.notes or "-")
    return table


def present_register_project_command(
    console: Console,
    *,
    name: str,
    path: str,
    stack: list[str] | None,
    description: str | None,
    commands: dict[str, str] | None,
    as_json: bool,
) -> None:
    result = execute_register_project_workflow(
        name=name,
        path=path,
        stack=stack,
        description=description,
        commands=commands,
        load_registry_path=lambda: load_project_registry_path(),
    )
    if as_json:
        console.print_json(data=result.to_dict())
        return
    action = "Registered" if result.is_new else "Updated"
    console.print(f"{action} project '{result.project.name}' at {result.project.path}")


def present_list_projects_command(
    console: Console,
    *,
    as_json: bool,
) -> None:
    projects = execute_list_projects_workflow(
        load_registry_path=lambda: load_project_registry_path(),
    )
    if as_json:
        console.print_json(data=[p.to_dict() for p in projects])
        return
    if not projects:
        console.print("No projects registered.")
        return
    console.print(build_project_list_table(projects))


def present_project_context_command(
    console: Console,
    *,
    name: str,
    as_json: bool,
) -> None:
    project = execute_project_context_workflow(
        name=name,
        load_registry_path=lambda: load_project_registry_path(),
    )
    if as_json:
        console.print_json(data=project.to_dict())
        return
    console.print(build_project_context_table(project))


def present_update_project_context_command(
    console: Console,
    *,
    name: str,
    phase: str | None,
    pending: list[str] | None,
    decisions: list[str] | None,
    notes: str | None,
    as_json: bool,
) -> None:
    project = execute_update_project_context_workflow(
        name=name,
        phase=phase,
        pending=pending,
        decisions=decisions,
        notes=notes,
        load_registry_path=lambda: load_project_registry_path(),
    )
    if as_json:
        console.print_json(data=project.to_dict())
        return
    console.print(f"Updated context for '{project.name}'")
    console.print(build_project_context_table(project))


def present_generate_claude_md_command(
    console: Console,
    *,
    name: str,
    output_path: Path | None,
    as_json: bool,
) -> None:
    result = execute_generate_claude_md_workflow(
        name=name,
        output_path=output_path,
        load_registry_path=lambda: load_project_registry_path(),
    )
    if as_json:
        console.print_json(data=result.to_dict())
        return
    console.print(f"Generated CLAUDE.md for '{result.project_name}' at {result.output_path}")


def present_generate_all_claude_md_command(
    console: Console,
    *,
    as_json: bool,
) -> None:
    results = execute_generate_all_claude_md_workflow(
        load_registry_path=lambda: load_project_registry_path(),
    )
    if as_json:
        console.print_json(data=[r.to_dict() for r in results])
        return
    for result in results:
        console.print(f"Generated CLAUDE.md for '{result.project_name}' at {result.output_path}")
    console.print(f"\nTotal: {len(results)} project(s).")


def present_project_log_command(
    console: Console,
    *,
    project_name: str,
    text: str,
    config_path,
    as_json: bool,
) -> None:
    result = execute_project_log_workflow(
        project_name=project_name,
        text=text,
        load_registry_path=lambda: load_project_registry_path(),
        load_database_path=lambda: load_database_path(config_path),
    )
    if as_json:
        console.print_json(data=result.to_dict())
        return
    stored = "SQLite + registry updated" if result.registry_updated else "SQLite"
    console.print(f"[green]\\u2713[/green] Logged: {result.entry_type}")
    console.print(f"  Project: {result.project_name}")
    console.print(f"  Entry: \"{result.entry_text}\"")
    console.print(f"  Stored: {stored}")


def _render_session(console: Console, result: ProjectSessionResult) -> None:
    from rich.panel import Panel
    from rich.text import Text

    project = result.project

    console.print()
    console.rule(f"Session: {project.name}", style="bold cyan")
    console.print()

    if project.description:
        console.print(f"[bold]Description:[/bold] {project.description}")
    if project.stack:
        console.print(f"[bold]Stack:[/bold] {', '.join(project.stack)}")
    if project.context.phase:
        console.print(f"[bold]Phase:[/bold] {project.context.phase}")
    console.print()

    # Commands
    if project.commands:
        console.print("[bold]Commands:[/bold]")
        for label, cmd in project.commands.items():
            console.print(f"  {label}:  [cyan]{cmd}[/cyan]")
        console.print()

    # Pending
    if project.context.pending:
        console.print("[bold]Pending:[/bold]")
        for item in project.context.pending:
            console.print(f"  [yellow]\\u2022[/yellow] {item}")
        console.print()

    # Decisions
    if project.context.decisions:
        console.print("[bold]Recent Decisions:[/bold]")
        for item in project.context.decisions:
            console.print(f"  [blue]\\u2022[/blue] {item}")
        console.print()

    # Recent activity from project_logs
    if result.recent_logs:
        updates = [l for l in result.recent_logs if l["entry_type"] == "update"]
        bugs = [l for l in result.recent_logs if l["entry_type"] == "bug"]
        next_items = [l for l in result.recent_logs if l["entry_type"] == "next"]
        blockers = [l for l in result.recent_logs if l["entry_type"] == "blocker"]
        ideas = [l for l in result.recent_logs if l["entry_type"] == "idea"]
        decisions_log = [l for l in result.recent_logs if l["entry_type"] == "decision"]

        all_activity = sorted(result.recent_logs, key=lambda l: l["logged_at"], reverse=True)
        if all_activity:
            console.print("[bold]Recent Activity (last 7 days):[/bold]")
            for log in all_activity[:15]:
                date_part = log["logged_at"][:10] if log["logged_at"] else "?"
                console.print(f"  [{date_part}] {log['entry_type']}: {log['entry_text']}")
            console.print()

        if bugs:
            console.print("[bold red]Known Bugs:[/bold red]")
            for log in bugs:
                date_part = log["logged_at"][:10] if log["logged_at"] else "?"
                console.print(f"  [{date_part}] {log['entry_text']}")
            console.print()

        if blockers:
            console.print("[bold red]Blockers:[/bold red]")
            for log in blockers:
                date_part = log["logged_at"][:10] if log["logged_at"] else "?"
                console.print(f"  [{date_part}] {log['entry_text']}")
            console.print()

        if next_items:
            console.print("[bold]Next Actions:[/bold]")
            for log in next_items:
                console.print(f"  [yellow]\\u2022[/yellow] {log['entry_text']}")
            console.print()

    # Key files
    console.print("[bold]Key Files:[/bold]")
    console.print(f"  {project.path}/CLAUDE.md")
    console.print(f"  {project.path}/src/")
    console.print(f"  {project.path}/tests/")
    console.print()

    # Notes
    if project.context.notes:
        console.print(f"[bold]Notes:[/bold] {project.context.notes}")
        console.print()

    # Recent commits
    if result.recent_commits:
        console.print("[bold]Recent Commits:[/bold]")
        for commit_line in result.recent_commits[:10]:
            console.print(f"  {commit_line}")
        console.print()

    # Context pack
    console.rule("Context Pack (copy for agent)", style="dim")
    context_text = _build_context_pack(result)
    console.print(context_text)


def _build_context_pack(result: ProjectSessionResult) -> str:
    project = result.project
    lines: list[str] = []
    lines.append(f"Project: {project.name}")
    if project.description:
        lines.append(f"Description: {project.description}")
    if project.stack:
        lines.append(f"Stack: {', '.join(project.stack)}")
    if project.context.phase:
        lines.append(f"Phase: {project.context.phase}")
    if project.commands:
        lines.append("Commands:")
        for label, cmd in project.commands.items():
            lines.append(f"  {label}: {cmd}")
    if project.context.pending:
        lines.append("Pending:")
        for item in project.context.pending:
            lines.append(f"  - {item}")
    if project.context.decisions:
        lines.append("Decisions:")
        for item in project.context.decisions:
            lines.append(f"  - {item}")
    if project.context.notes:
        lines.append(f"Notes: {project.context.notes}")

    if result.recent_logs:
        lines.append("Recent logs:")
        for log in result.recent_logs[:10]:
            date_part = log["logged_at"][:10] if log["logged_at"] else "?"
            lines.append(f"  [{date_part}] {log['entry_type']}: {log['entry_text']}")

    if result.recent_commits:
        lines.append("Recent commits:")
        for commit_line in result.recent_commits[:5]:
            lines.append(f"  {commit_line}")

    return "\n".join(lines)


def present_session_command(
    console: Console,
    *,
    project_name: str,
    config_path,
    as_json: bool,
    context_only: bool,
) -> None:
    result = execute_session_workflow(
        project_name=project_name,
        load_registry_path=lambda: load_project_registry_path(),
        load_database_path=lambda: load_database_path(config_path),
    )
    if as_json:
        console.print_json(data=result.to_dict())
        return
    if context_only:
        console.print(_build_context_pack(result))
        return
    _render_session(console, result)


__all__ = [
    "build_project_context_table",
    "build_project_list_table",
    "load_project_registry_path",
    "present_generate_all_claude_md_command",
    "present_generate_claude_md_command",
    "present_list_projects_command",
    "present_project_context_command",
    "present_project_log_command",
    "present_register_project_command",
    "present_session_command",
    "present_update_project_context_command",
]
