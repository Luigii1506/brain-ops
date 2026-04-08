"""Entity index generation for knowledge base navigation."""

from __future__ import annotations

from dataclasses import dataclass

from .entities import ENTITY_TYPES, is_entity_note


@dataclass(slots=True, frozen=True)
class EntityIndexEntry:
    title: str
    entity_type: str
    relative_path: str
    summary: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "title": self.title,
            "entity_type": self.entity_type,
            "relative_path": self.relative_path,
            "summary": self.summary,
        }


def build_entity_index_entry(
    frontmatter: dict[str, object],
    relative_path: str,
) -> EntityIndexEntry | None:
    if not is_entity_note(frontmatter):
        return None
    # Use object_kind or subtype for grouping, fallback to type
    entity_type = frontmatter.get("subtype") or frontmatter.get("type")
    if not isinstance(entity_type, str):
        return None
    name = frontmatter.get("name")
    title = str(name).strip() if name else relative_path
    return EntityIndexEntry(
        title=title,
        entity_type=entity_type,
        relative_path=relative_path,
    )


def group_index_entries_by_type(
    entries: list[EntityIndexEntry],
) -> dict[str, list[EntityIndexEntry]]:
    groups: dict[str, list[EntityIndexEntry]] = {}
    for entry in entries:
        groups.setdefault(entry.entity_type, []).append(entry)
    for group in groups.values():
        group.sort(key=lambda e: e.title.lower())
    return groups


def render_entity_index_markdown(
    entries: list[EntityIndexEntry],
) -> str:
    groups = group_index_entries_by_type(entries)
    lines: list[str] = [
        "# Knowledge Entity Index",
        "",
    ]
    if not groups:
        lines.append("No entities found.")
        lines.append("")
        return "\n".join(lines)

    lines.append(f"Total entities: {len(entries)}")
    lines.append("")

    for entity_type in sorted(groups):
        type_label = ENTITY_TYPES.get(entity_type, entity_type.replace("_", " ").title())
        group = groups[entity_type]
        lines.append(f"## {entity_type.title()} ({len(group)})")
        lines.append(f"*{type_label}*")
        lines.append("")
        for entry in group:
            link = f"[[{entry.title}]]"
            lines.append(f"- {link}")
        lines.append("")

    return "\n".join(lines)


__all__ = [
    "EntityIndexEntry",
    "build_entity_index_entry",
    "group_index_entries_by_type",
    "render_entity_index_markdown",
]
