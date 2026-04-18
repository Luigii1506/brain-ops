"""Knowledge compile — extract entity data from frontmatter into structured records.

Relation compilation (Campaña 2.0):
- Reads typed relations from `relationships:` (via `relations_typed.parse_relationships`)
- Reads legacy untyped relations from `related:` (existing behaviour)
- Dedup key for typed relations: (source, predicate, object) — multiple
  predicates between the same subject-object pair are legitimate.
- Legacy `related:` entries are OMITTED when the object already appears in
  ANY typed relation from the same source (typed wins over legacy for the
  same target).
- Legacy relations produce rows with `predicate=None`; typed relations
  populate `predicate` and `confidence`.

No schema migration is introduced — the `predicate` and `confidence`
columns already exist from Campaña 0 migration m001.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .entities import ENTITY_TYPES, extract_entity_relations, is_entity_note
from .relations_typed import TypedRelation, parse_relationships


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
    """A single edge in the compiled graph.

    `predicate` is None for legacy (untyped `related:`) entries; populated
    for typed (`relationships:`) entries. `confidence` defaults to "medium"
    for typed relations and is ignored for legacy (stored as the default
    from the SQLite schema).
    """

    source_entity: str
    target_entity: str
    source_type: str | None
    predicate: str | None = None
    confidence: str = "medium"

    @property
    def is_typed(self) -> bool:
        return self.predicate is not None

    def to_dict(self) -> dict[str, object]:
        return {
            "source_entity": self.source_entity,
            "target_entity": self.target_entity,
            "source_type": self.source_type,
            "predicate": self.predicate,
            "confidence": self.confidence,
        }


@dataclass(slots=True, frozen=True)
class CompileResult:
    entities: list[CompiledEntity]
    relations: list[CompiledRelation]

    def to_dict(self) -> dict[str, object]:
        return {
            "total_entities": len(self.entities),
            "total_relations": len(self.relations),
            "total_typed_relations": sum(1 for r in self.relations if r.is_typed),
            "total_legacy_relations": sum(1 for r in self.relations if not r.is_typed),
            "entities": [e.to_dict() for e in self.entities],
            "relations": [r.to_dict() for r in self.relations],
        }


# Fields to exclude from the metadata blob (stored as columns or as
# relation edges; not duplicated into metadata JSON).
_EXCLUDED_METADATA_KEYS = {
    "type", "name", "entity", "tags", "related", "relationships",
}


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
    """Compile typed + legacy relations from a note's frontmatter.

    Order guarantees in the returned list:
        1. Typed relations (from `relationships:`) in input order.
        2. Legacy relations (from `related:`) for targets NOT already
           present in any typed relation, in input order.

    Uniqueness rule for typed relations: (source, predicate, object).
    Legacy dedup rule: skip if target is already in any typed relation.
    """
    if not is_entity_note(frontmatter):
        return []
    name = frontmatter.get("name")
    if not isinstance(name, str) or not name.strip():
        return []
    source = name.strip()
    entity_type = frontmatter.get("type")
    source_type = str(entity_type) if isinstance(entity_type, str) else None

    out: list[CompiledRelation] = []

    # 1. Typed relations from `relationships:`
    parse_result = parse_relationships(source, frontmatter)
    typed_targets: set[str] = set()
    for tr in parse_result.typed:
        out.append(CompiledRelation(
            source_entity=tr.source,
            target_entity=tr.object,
            source_type=source_type,
            predicate=tr.predicate,
            confidence=tr.confidence,
        ))
        typed_targets.add(tr.object)

    # 2. Legacy relations from `related:` — skip targets already typed
    legacy_targets = extract_entity_relations(frontmatter)
    seen_legacy: set[str] = set()
    for target in legacy_targets:
        if target in typed_targets:
            continue
        # Also dedup within legacy itself (a name appearing twice in `related:`)
        if target in seen_legacy:
            continue
        seen_legacy.add(target)
        out.append(CompiledRelation(
            source_entity=source,
            target_entity=target,
            source_type=source_type,
            predicate=None,
            confidence="medium",
        ))

    return out


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
