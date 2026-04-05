"""CLI orchestration helpers for project registry commands."""

from __future__ import annotations

import os
from pathlib import Path

from rich.console import Console
from rich.table import Table

from brain_ops.application.projects import (
    execute_generate_all_claude_md_workflow,
    execute_generate_claude_md_workflow,
    execute_list_projects_workflow,
    execute_project_context_workflow,
    execute_register_project_workflow,
    execute_update_project_context_workflow,
)
from brain_ops.domains.projects import Project


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


__all__ = [
    "build_project_context_table",
    "build_project_list_table",
    "load_project_registry_path",
    "present_generate_all_claude_md_command",
    "present_generate_claude_md_command",
    "present_list_projects_command",
    "present_project_context_command",
    "present_register_project_command",
    "present_update_project_context_command",
]
