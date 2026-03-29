from __future__ import annotations

from pathlib import Path

from brain_ops.frontmatter import dump_frontmatter, split_frontmatter
from brain_ops.models import ImproveNoteResult
from brain_ops.vault import Vault, now_iso


def improve_note(vault: Vault, note_path: Path) -> ImproveNoteResult:
    path = note_path.expanduser()
    if not path.is_absolute():
        path = vault.root / path
    safe_path = vault._safe_path(path)
    relative = vault.relative_path(safe_path)
    text = safe_path.read_text(encoding="utf-8", errors="ignore")
    frontmatter, body = split_frontmatter(text)

    note_type = str(frontmatter.get("type", _infer_type_from_path(relative)))
    title = _infer_title_from_path(relative)
    updated_body, reason = _improve_body(note_type, title, body, frontmatter)
    frontmatter.setdefault("type", note_type)
    if frontmatter.get("created") in (None, ""):
        frontmatter["created"] = now_iso()
    frontmatter["updated"] = now_iso()
    frontmatter.setdefault("tags", [])

    operation = vault.write_text(safe_path, dump_frontmatter(frontmatter, updated_body), overwrite=True)
    return ImproveNoteResult(
        path=safe_path,
        note_type=note_type,
        operation=operation,
        reason=reason,
    )


def _infer_type_from_path(relative: Path) -> str:
    top = relative.parts[0] if relative.parts else ""
    if top == "01 - Sources":
        return "source"
    if top == "02 - Knowledge":
        return "knowledge"
    if top == "03 - Maps":
        return "map"
    if top == "04 - Projects":
        return "project"
    if top == "05 - Systems":
        return "system"
    if top == "06 - Daily":
        return "daily"
    return "knowledge"


def _infer_title_from_path(relative: Path) -> str:
    return relative.stem


def _improve_body(note_type: str, title: str, body: str, frontmatter: dict[str, object]) -> tuple[str, str]:
    stripped = body.strip()
    if note_type == "knowledge":
        return _improve_knowledge(title, stripped, frontmatter)
    if note_type == "map":
        return _improve_map(title, stripped)
    if note_type == "source":
        return _improve_source(title, stripped)
    if note_type in {"system", "command", "security_note"}:
        return _improve_system(title, stripped)
    if note_type == "project":
        return _improve_project(title, stripped)
    return body, "No structural improvement rule matched."


def _improve_knowledge(title: str, body: str, frontmatter: dict[str, object]) -> tuple[str, str]:
    if frontmatter.get("status") == "stub" or "Stub note created from an existing graph seed." in body:
        return (
            "\n".join(
                [
                    f"# {title}",
                    "",
                    "## Current status",
                    "",
                    "This note is a knowledge stub created from an existing graph seed.",
                    "",
                    "## What this note should explain",
                    "",
                    "- Definition",
                    "- Why it matters",
                    "- Key facts or distinctions",
                    "- Related notes",
                    "",
                    "## Links",
                ]
            ),
            "Expanded knowledge stub into a clearer scaffold.",
        )

    if not body:
        return (
            "\n".join(
                [
                    f"# {title}",
                    "",
                    "## Core idea",
                    "",
                    "## Why it matters",
                    "",
                    "## Links",
                ]
            ),
            "Added default knowledge structure to an empty note.",
        )

    if body.startswith("[[") and "\n" not in body.strip():
        return (
            "\n".join(
                [
                    f"# {title}",
                    "",
                    "## Core idea",
                    "",
                    "This note currently acts as a pointer to a related concept.",
                    "",
                    "## Linked concept",
                    "",
                    body,
                    "",
                    "## Why it matters",
                    "",
                    "## Links",
                ]
            ),
            "Wrapped a single-link note into a usable knowledge structure.",
        )

    if body.startswith("# "):
        return body, "Note already has a heading structure."

    return (
        "\n".join(
            [
                f"# {title}",
                "",
                "## Existing content",
                "",
                body,
                "",
                "## Why it matters",
                "",
                "## Links",
            ]
        ),
        "Wrapped loose knowledge content into a standard structure.",
    )


def _improve_map(title: str, body: str) -> tuple[str, str]:
    link_lines = [line.strip() for line in body.splitlines() if "[[" in line]
    purpose = next((line.strip() for line in body.splitlines() if line.strip() and "[[" not in line and not line.strip().startswith("#")), "")
    if not body or body.startswith("# "):
        return body, "Map already has heading content."
    entry_points = link_lines if link_lines else ["- Add related notes here."]
    return (
        "\n".join(
            [
                f"# {title}",
                "",
                "## Purpose",
                "",
                purpose or f"This map organizes notes related to {title.replace('MOC-', '')}.",
                "",
                "## Entry points",
                "",
                *entry_points,
                "",
                "## Related notes",
            ]
        ),
        "Wrapped sparse map content into a navigable MOC structure.",
    )


def _improve_source(title: str, body: str) -> tuple[str, str]:
    if body.startswith("# "):
        return body, "Source already has heading content."
    return (
        "\n".join(
            [
                f"# {title}",
                "",
                "## Source",
                "",
                body if body else "",
                "",
                "## Summary",
                "",
                "## Key ideas",
                "",
                "## Related notes",
            ]
        ),
        "Wrapped source content into the standard source structure.",
    )


def _improve_system(title: str, body: str) -> tuple[str, str]:
    if body.startswith("# "):
        return body, "System note already has heading content."
    return (
        "\n".join(
            [
                f"# {title}",
                "",
                "## Objective",
                "",
                body if body else "",
                "",
                "## Procedure",
                "",
                "## Related notes",
            ]
        ),
        "Wrapped system content into the standard operational structure.",
    )


def _improve_project(title: str, body: str) -> tuple[str, str]:
    if body.startswith("# "):
        return body, "Project note already has heading content."
    return (
        "\n".join(
            [
                f"# {title}",
                "",
                "## Objective",
                "",
                body if body else "",
                "",
                "## Current status",
                "",
                "## Next action",
                "",
                "## Related notes",
            ]
        ),
        "Wrapped project content into the standard project structure.",
    )
