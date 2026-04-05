"""CLAUDE.md generator from project registry context."""

from __future__ import annotations

from .registry import Project


def render_claude_md(project: Project) -> str:
    lines = [
        f"# {project.name}",
        "",
    ]

    if project.description:
        lines.append(project.description)
        lines.append("")

    if project.stack:
        lines.append(f"**Stack:** {', '.join(project.stack)}")
        lines.append("")

    if project.commands:
        lines.append("## Commands")
        lines.append("")
        for label, command in project.commands.items():
            lines.append(f"- **{label}**: `{command}`")
        lines.append("")

    ctx = project.context
    if ctx.phase:
        lines.append(f"## Current Phase")
        lines.append("")
        lines.append(ctx.phase)
        lines.append("")

    if ctx.pending:
        lines.append("## Pending")
        lines.append("")
        for item in ctx.pending:
            lines.append(f"- {item}")
        lines.append("")

    if ctx.decisions:
        lines.append("## Recent Decisions")
        lines.append("")
        for item in ctx.decisions:
            lines.append(f"- {item}")
        lines.append("")

    if ctx.notes:
        lines.append("## Notes")
        lines.append("")
        lines.append(ctx.notes)
        lines.append("")

    return "\n".join(lines)


__all__ = ["render_claude_md"]
