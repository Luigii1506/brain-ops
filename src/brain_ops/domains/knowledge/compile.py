"""Knowledge compile — extract entity data from frontmatter into structured records."""

from __future__ import annotations

from dataclasses import dataclass

from .entities import ENTITY_TYPES, extract_entity_relations, is_entity_note


@dataclass(slots=True, frozen=True)
class CompiledEntity:
    name: str
    entity_type: str
    relative_path: str
    metadata: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "entity_type": self.entity_type,
            "relative_path": self.relative_path,
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True, frozen=True)
class CompiledRelation:
    source_entity: str
    target_entity: str
    source_type: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "source_entity": self.source_entity,
            "target_entity": self.target_entity,
            "source_type": self.source_type,
        }


@dataclass(slots=True, frozen=True)
class CompileResult:
    entities: list[CompiledEntity]
    relations: list[CompiledRelation]

    def to_dict(self) -> dict[str, object]:
        return {
            "total_entities": len(self.entities),
            "total_relations": len(self.relations),
            "entities": [e.to_dict() for e in self.entities],
            "relations": [r.to_dict() for r in self.relations],
        }


# Fields to exclude from the metadata blob (they're stored as columns)
_EXCLUDED_METADATA_KEYS = {"type", "name", "entity", "tags", "related"}


def compile_entity_from_frontmatter(
    frontmatter: dict[str, object],
    relative_path: str,
) -> CompiledEntity | None:
    if not is_entity_note(frontmatter):
        return None
    entity_type = frontmatter.get("type")
    if not isinstance(entity_type, str) or entity_type not in ENTITY_TYPES:
        return None
    name = frontmatter.get("name")
    if not isinstance(name, str) or not name.strip():
        return None
    metadata = {
        k: v for k, v in frontmatter.items()
        if k not in _EXCLUDED_METADATA_KEYS and v is not None
    }
    return CompiledEntity(
        name=name.strip(),
        entity_type=entity_type,
        relative_path=relative_path,
        metadata=metadata,
    )


def compile_relations_from_frontmatter(
    frontmatter: dict[str, object],
) -> list[CompiledRelation]:
    if not is_entity_note(frontmatter):
        return []
    name = frontmatter.get("name")
    if not isinstance(name, str) or not name.strip():
        return []
    entity_type = frontmatter.get("type")
    source_type = str(entity_type) if isinstance(entity_type, str) else None
    related = extract_entity_relations(frontmatter)
    return [
        CompiledRelation(
            source_entity=name.strip(),
            target_entity=target,
            source_type=source_type,
        )
        for target in related
    ]


def compile_vault_entities(
    notes: list[tuple[str, dict[str, object]]],
) -> CompileResult:
    entities: list[CompiledEntity] = []
    relations: list[CompiledRelation] = []
    for rel_path, frontmatter in notes:
        entity = compile_entity_from_frontmatter(frontmatter, rel_path)
        if entity is not None:
            entities.append(entity)
        relations.extend(compile_relations_from_frontmatter(frontmatter))
    return CompileResult(entities=entities, relations=relations)


__all__ = [
    "CompileResult",
    "CompiledEntity",
    "CompiledRelation",
    "compile_entity_from_frontmatter",
    "compile_relations_from_frontmatter",
    "compile_vault_entities",
]
