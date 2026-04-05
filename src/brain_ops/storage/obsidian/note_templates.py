from __future__ import annotations

from pathlib import Path

from brain_ops.templates import resolve_template_path


def template_for_note_type(note_type: str) -> str:
    mapping = {
        "project": "project",
        "project_note": "project",
        "source": "source",
        "knowledge": "knowledge",
        "permanent_note": "permanent_note",
        "map": "map",
        "moc": "map",
        "system": "system",
        "command": "system",
        "security_note": "system",
        "sop": "sop",
        "runbook": "runbook",
        "architecture": "architecture",
        "decision": "decision",
        "debugging_note": "debugging_note",
        "changelog": "changelog",
    }
    return mapping.get(note_type, "knowledge")


def resolve_note_template_path(
    template_dir: Path,
    *,
    note_type: str,
    explicit_template_name: str | None,
) -> Path:
    template_name = explicit_template_name or template_for_note_type(note_type)
    return resolve_template_path(template_dir, template_name)
