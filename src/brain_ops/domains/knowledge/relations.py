"""Entity relationship extraction and graph building."""

from __future__ import annotations

from dataclasses import dataclass

from .entities import extract_entity_relations, is_entity_note


@dataclass(slots=True, frozen=True)
class EntityRelation:
    source: str
    target: str
    source_type: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "target": self.target,
            "source_type": self.source_type,
        }


def extract_relations_from_note(
    frontmatter: dict[str, object],
) -> list[EntityRelation]:
    if not is_entity_note(frontmatter):
        return []
    name = frontmatter.get("name")
    if not isinstance(name, str) or not name.strip():
        return []
    source_name = name.strip()
    entity_type = frontmatter.get("type")
    source_type = str(entity_type).strip() if isinstance(entity_type, str) else None
    related = extract_entity_relations(frontmatter)
    return [
        EntityRelation(source=source_name, target=target, source_type=source_type)
        for target in related
    ]


def build_relation_adjacency(
    relations: list[EntityRelation],
) -> dict[str, list[str]]:
    adjacency: dict[str, list[str]] = {}
    for rel in relations:
        adjacency.setdefault(rel.source, []).append(rel.target)
        adjacency.setdefault(rel.target, []).append(rel.source)
    for targets in adjacency.values():
        targets.sort()
    return adjacency


def find_entity_connections(
    entity_name: str,
    relations: list[EntityRelation],
) -> list[str]:
    connected: set[str] = set()
    for rel in relations:
        if rel.source == entity_name:
            connected.add(rel.target)
        elif rel.target == entity_name:
            connected.add(rel.source)
    return sorted(connected)


def render_entity_relations_markdown(
    entity_name: str,
    connections: list[str],
) -> str:
    lines = [
        f"# Relations: {entity_name}",
        "",
    ]
    if not connections:
        lines.append("No connections found.")
        lines.append("")
        return "\n".join(lines)

    lines.append(f"Connected entities: {len(connections)}")
    lines.append("")
    for name in connections:
        lines.append(f"- [[{name}]]")
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "EntityRelation",
    "build_relation_adjacency",
    "extract_relations_from_note",
    "find_entity_connections",
    "render_entity_relations_markdown",
]
