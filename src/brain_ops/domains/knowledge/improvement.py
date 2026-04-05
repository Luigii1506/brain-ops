from __future__ import annotations


def improve_body(note_type: str, title: str, body: str, frontmatter: dict[str, object]) -> tuple[str, str]:
    stripped = body.strip()
    if note_type == "knowledge":
        return improve_knowledge(title, stripped, frontmatter)
    if note_type == "map":
        return improve_map(title, stripped)
    if note_type == "source":
        return improve_source(title, stripped)
    if note_type in {"system", "command", "security_note"}:
        return improve_system(title, stripped)
    if note_type == "project":
        return improve_project(title, stripped)
    return body, "No structural improvement rule matched."


def improve_knowledge(title: str, body: str, frontmatter: dict[str, object]) -> tuple[str, str]:
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


def improve_map(title: str, body: str) -> tuple[str, str]:
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


def improve_source(title: str, body: str) -> tuple[str, str]:
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


def improve_system(title: str, body: str) -> tuple[str, str]:
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


def improve_project(title: str, body: str) -> tuple[str, str]:
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


def materialize_improved_document(
    frontmatter: dict[str, object],
    updated_body: str,
    *,
    note_type: str,
    now: str,
) -> tuple[dict[str, object], str]:
    updated_frontmatter = dict(frontmatter)
    updated_frontmatter.setdefault("type", note_type)
    if updated_frontmatter.get("created") in (None, ""):
        updated_frontmatter["created"] = now
    updated_frontmatter["updated"] = now
    updated_frontmatter.setdefault("tags", [])
    return updated_frontmatter, updated_body
