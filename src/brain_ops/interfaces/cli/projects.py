"""CLI orchestration helpers for project registry commands."""

from __future__ import annotations

import os
from pathlib import Path

from rich.console import Console
from rich.table import Table

from brain_ops.application.projects import (
    ProjectAuditResult,
    ProjectSessionResult,
    execute_audit_project_workflow,
    execute_generate_all_claude_md_workflow,
    execute_generate_claude_md_workflow,
    execute_list_projects_workflow,
    execute_project_context_workflow,
    execute_project_log_workflow,
    execute_register_project_workflow,
    execute_session_workflow,
    execute_update_project_context_workflow,
    _resolve_vault_project_dir,
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
    vault_project_dir = _resolve_vault_project_dir(config_path, project_name.strip())
    result = execute_project_log_workflow(
        project_name=project_name,
        text=text,
        load_registry_path=lambda: load_project_registry_path(),
        load_database_path=lambda: load_database_path(config_path),
        vault_project_dir=vault_project_dir,
    )
    if as_json:
        console.print_json(data=result.to_dict())
        return
    stored = "SQLite + registry updated" if result.registry_updated else "SQLite"
    if vault_project_dir is not None:
        stored += " + vault"
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

    # Vault project docs
    if result.vault_status or result.vault_decisions or result.vault_bugs:
        console.print("[bold]From Project Docs:[/bold]")
        if result.vault_status:
            console.print(f"  [bold]Status:[/bold] {result.vault_status}")
        if result.vault_decisions:
            console.print("  [bold]Recent Decisions:[/bold]")
            for d in result.vault_decisions:
                console.print(f"    [blue]\\u2022[/blue] {d}")
        if result.vault_bugs:
            console.print("  [bold]Known Bugs:[/bold]")
            for b in result.vault_bugs:
                console.print(f"    [red]\\u2022[/red] {b}")
        console.print()

    # Key files
    console.print("[bold]Key Files:[/bold]")
    console.print(f"  {project.path}/CLAUDE.md")
    console.print(f"  {project.path}/src/")
    console.print(f"  {project.path}/tests/")
    if result.vault_path:
        console.print(f"  {result.vault_path}/")
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


MAX_CONTEXT_PACK_CHARS = 3000


def _build_context_pack(result: ProjectSessionResult) -> str:
    """Build a dense, focused context pack for agents. Prioritizes state > actions > history."""
    project = result.project
    sections: list[str] = []

    # TIER 1 — Identity (always included, very compact)
    header = f"Project: {project.name}"
    if project.description:
        header += f" — {project.description}"
    if project.stack:
        header += f"\nStack: {', '.join(project.stack)}"
    sections.append(header)

    # TIER 2 — Active state (highest priority)
    if project.context.phase:
        sections.append(f"Phase: {project.context.phase}")

    if result.vault_status:
        sections.append(f"Status: {result.vault_status[:500]}")

    if project.context.pending:
        top_pending = project.context.pending[:5]
        sections.append("Next actions:\n" + "\n".join(f"  - {p}" for p in top_pending))

    # TIER 3 — Active bugs/blockers
    bugs_from_logs = [log for log in (result.recent_logs or []) if log.get("entry_type") in ("bug", "blocker")]
    vault_bugs = list(result.vault_bugs or [])
    all_bugs = vault_bugs[:3] + [b["entry_text"] for b in bugs_from_logs[:3]]
    if all_bugs:
        seen = set()
        unique_bugs = [b for b in all_bugs if b not in seen and not seen.add(b)]  # type: ignore[func-returns-value]
        sections.append("Bugs/blockers:\n" + "\n".join(f"  - {b}" for b in unique_bugs[:5]))

    # TIER 4 — Commands (compact)
    if project.commands:
        cmd_lines = [f"  {label}: {cmd}" for label, cmd in project.commands.items()]
        sections.append("Commands:\n" + "\n".join(cmd_lines))

    # TIER 5 — Recent decisions (last 3 only)
    decisions = list(result.vault_decisions or []) or list(project.context.decisions or [])
    if decisions:
        sections.append("Recent decisions:\n" + "\n".join(f"  - {d}" for d in decisions[-3:]))

    # TIER 6 — Recent activity (last 5 logs, compact)
    budget_remaining = MAX_CONTEXT_PACK_CHARS - sum(len(s) for s in sections)
    if result.recent_logs and budget_remaining > 200:
        log_lines = []
        for log in result.recent_logs[:5]:
            date_part = log["logged_at"][:10] if log.get("logged_at") else "?"
            line = f"  [{date_part}] {log['entry_type']}: {log['entry_text'][:80]}"
            log_lines.append(line)
        sections.append("Recent activity:\n" + "\n".join(log_lines))

    # TIER 7 — Recent commits (last 3, only if budget allows)
    budget_remaining = MAX_CONTEXT_PACK_CHARS - sum(len(s) for s in sections)
    if result.recent_commits and budget_remaining > 150:
        sections.append("Recent commits:\n" + "\n".join(f"  {c}" for c in result.recent_commits[:3]))

    # Notes (only if budget allows)
    budget_remaining = MAX_CONTEXT_PACK_CHARS - sum(len(s) for s in sections)
    if project.context.notes and budget_remaining > 100:
        note_text = project.context.notes[:budget_remaining - 20]
        sections.append(f"Notes: {note_text}")

    pack = "\n\n".join(sections)

    # Hard limit
    if len(pack) > MAX_CONTEXT_PACK_CHARS:
        pack = pack[:MAX_CONTEXT_PACK_CHARS - 3] + "..."

    return pack


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
        config_path=config_path,
    )
    if as_json:
        console.print_json(data=result.to_dict())
        return
    if context_only:
        console.print(_build_context_pack(result))
        return
    _render_session(console, result)


def present_audit_project_command(
    console: Console,
    *,
    project_name: str,
    config_path,
    as_json: bool,
) -> None:
    result = execute_audit_project_workflow(
        project_name=project_name,
        load_registry_path=lambda: load_project_registry_path(),
        load_database_path=lambda: load_database_path(config_path),
        config_path=config_path,
    )
    if as_json:
        console.print_json(data=result.to_dict())
        return

    from rich.panel import Panel

    if result.score >= 80:
        style = "green"
    elif result.score >= 50:
        style = "yellow"
    else:
        style = "red"

    console.print()
    console.rule(f"Audit: {result.project_name}", style="bold cyan")
    console.print()
    console.print(f"[bold]Score:[/bold] [{style}]{result.score}/100[/{style}]")
    console.print()

    if result.issues:
        console.print("[bold]Issues:[/bold]")
        for issue in result.issues:
            console.print(f"  [red]\\u2022[/red] {issue}")
    else:
        console.print("[green]No issues found.[/green]")
    console.print()


__all__ = [
    "build_project_context_table",
    "build_project_list_table",
    "load_project_registry_path",
    "present_audit_project_command",
    "present_generate_all_claude_md_command",
    "present_generate_claude_md_command",
    "present_list_projects_command",
    "present_project_context_command",
    "present_project_log_command",
    "present_register_project_command",
    "present_session_command",
    "present_update_project_context_command",
]
