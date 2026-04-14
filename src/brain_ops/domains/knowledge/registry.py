"""Entity registry — canonical names, aliases, confidence, and accumulated intelligence."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path


_DISAMBIG_PATTERN = re.compile(r'^(.+?)\s*\(([^)]+)\)$')


def extract_base_name(canonical_name: str) -> str:
    """Strip parenthetical disambiguator: 'Mercurio (deity)' -> 'Mercurio'."""
    m = _DISAMBIG_PATTERN.match(canonical_name.strip())
    return m.group(1).strip() if m else canonical_name.strip()


@dataclass(slots=True)
class RegisteredEntity:
    canonical_name: str
    entity_type: str
    aliases: list[str] = field(default_factory=list)
    source_count: int = 0
    query_count: int = 0
    relation_count: int = 0
    confidence: str = "medium"
    status: str = "mention"
    object_kind: str | None = None
    subtype: str | None = None
    domains: list[str] = field(default_factory=list)
    frequent_relations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "canonical_name": self.canonical_name,
            "entity_type": self.entity_type,
            "aliases": list(self.aliases),
            "source_count": self.source_count,
            "query_count": self.query_count,
            "relation_count": self.relation_count,
            "confidence": self.confidence,
            "status": self.status,
            "object_kind": self.object_kind,
            "subtype": self.subtype,
            "domains": list(self.domains),
            "frequent_relations": list(self.frequent_relations),
        }

    @staticmethod
    def from_dict(data: dict[str, object]) -> RegisteredEntity:
        return RegisteredEntity(
            canonical_name=str(data.get("canonical_name", "")),
            entity_type=str(data.get("entity_type", "concept")),
            aliases=list(data.get("aliases", [])),
            source_count=int(data.get("source_count", 0)),
            query_count=int(data.get("query_count", 0)),
            relation_count=int(data.get("relation_count", 0)),
            confidence=str(data.get("confidence", "medium")),
            status=str(data.get("status", "mention")),
            object_kind=data.get("object_kind") if isinstance(data.get("object_kind"), str) else None,
            subtype=data.get("subtype") if isinstance(data.get("subtype"), str) else None,
            domains=list(data.get("domains", [])),
            frequent_relations=list(data.get("frequent_relations", [])),
        )


@dataclass(slots=True)
class EntityRegistry:
    entities: dict[str, RegisteredEntity] = field(default_factory=dict)
    alias_index: dict[str, str] = field(default_factory=dict)
    base_name_index: dict[str, list[str]] = field(default_factory=dict)

    def resolve(self, name: str) -> str:
        normalized = name.strip()
        if normalized in self.entities:
            return normalized
        return self.alias_index.get(normalized.lower(), normalized)

    def register(self, entity: RegisteredEntity) -> None:
        self.entities[entity.canonical_name] = entity
        for alias in entity.aliases:
            self.alias_index[alias.lower()] = entity.canonical_name
        # Populate base_name_index for disambiguation lookups
        base = extract_base_name(entity.canonical_name).lower()
        if base not in self.base_name_index:
            self.base_name_index[base] = []
        if entity.canonical_name not in self.base_name_index[base]:
            self.base_name_index[base].append(entity.canonical_name)

    def find_collisions(self, name: str) -> list[RegisteredEntity]:
        """Find all registered entities sharing the same base name."""
        base = extract_base_name(name).lower()
        canonical_names = self.base_name_index.get(base, [])
        return [self.entities[cn] for cn in canonical_names if cn in self.entities]

    def resolve_with_context(
        self, name: str, *, subtype: str | None = None, domain: str | None = None,
    ) -> str | list["DisambiguationCandidate"]:
        """Resolve a name, using subtype/domain to disambiguate if multiple matches exist.

        Returns:
            str: the resolved canonical name (unambiguous)
            list[DisambiguationCandidate]: candidates when ambiguous
        """
        from .object_model import DisambiguationCandidate

        # Try exact match first
        normalized = name.strip()
        if normalized in self.entities:
            return normalized
        # Try alias
        via_alias = self.alias_index.get(normalized.lower())
        if via_alias and via_alias in self.entities:
            return via_alias

        # Check base name collisions
        collisions = self.find_collisions(name)
        if not collisions:
            return normalized  # unknown entity, pass through
        if len(collisions) == 1:
            return collisions[0].canonical_name

        # Multiple matches — try to narrow by subtype
        if subtype:
            for entity in collisions:
                if entity.subtype == subtype:
                    return entity.canonical_name
        # Try to narrow by domain
        if domain:
            for entity in collisions:
                if domain in entity.domains:
                    return entity.canonical_name

        # Still ambiguous — return candidates
        return [
            DisambiguationCandidate(
                canonical_name=e.canonical_name,
                display_name=e.canonical_name,
                subtype=e.subtype or e.entity_type,
                disambiguation_key=e.subtype or e.entity_type,
            )
            for e in collisions
        ]

    def add_alias(self, canonical_name: str, alias: str) -> None:
        entity = self.entities.get(canonical_name)
        if entity is None:
            return
        normalized_alias = alias.strip()
        if normalized_alias and normalized_alias not in entity.aliases and normalized_alias != canonical_name:
            entity.aliases.append(normalized_alias)
            self.alias_index[normalized_alias.lower()] = canonical_name

    def increment_source_count(self, name: str) -> None:
        resolved = self.resolve(name)
        entity = self.entities.get(resolved)
        if entity is not None:
            entity.source_count += 1

    def add_domain(self, name: str, domain: str) -> None:
        resolved = self.resolve(name)
        entity = self.entities.get(resolved)
        if entity is not None and domain not in entity.domains:
            entity.domains.append(domain)

    def add_frequent_relation(self, name: str, related_name: str) -> None:
        resolved = self.resolve(name)
        entity = self.entities.get(resolved)
        if entity is not None and related_name not in entity.frequent_relations:
            entity.frequent_relations.append(related_name)
            if len(entity.frequent_relations) > 20:
                entity.frequent_relations = entity.frequent_relations[-20:]

    def update_confidence(self, name: str) -> None:
        resolved = self.resolve(name)
        entity = self.entities.get(resolved)
        if entity is None:
            return
        if entity.source_count >= 5:
            entity.confidence = "high"
        elif entity.source_count >= 2:
            entity.confidence = "medium"

    def compute_importance(self, name: str) -> float:
        """Compute importance score separating evidence (sources) from interest (queries)."""
        resolved = self.resolve(name)
        entity = self.entities.get(resolved)
        if entity is None:
            return 0.0
        return (
            entity.source_count * 0.35 +
            entity.query_count * 0.20 +
            entity.relation_count * 0.20 +
            (0.10 if entity.status == "canonical" else 0.05 if entity.status == "candidate" else 0.0) +
            len(entity.frequent_relations) * 0.02
        )

    def get(self, name: str) -> RegisteredEntity | None:
        resolved = self.resolve(name)
        return self.entities.get(resolved)

    def list_all(self) -> list[RegisteredEntity]:
        return sorted(self.entities.values(), key=lambda e: e.canonical_name.lower())

    def to_dict(self) -> dict[str, object]:
        return {
            name: entity.to_dict()
            for name, entity in self.entities.items()
        }


def load_entity_registry(registry_path: Path) -> EntityRegistry:
    registry = EntityRegistry()
    if not registry_path.exists():
        return registry
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return registry
    for _name, entity_data in data.items():
        if isinstance(entity_data, dict):
            entity = RegisteredEntity.from_dict(entity_data)
            registry.register(entity)
    return registry


def save_entity_registry(registry_path: Path, registry: EntityRegistry) -> Path:
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        json.dumps(registry.to_dict(), indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return registry_path


def learn_from_ingest(
    registry: EntityRegistry,
    *,
    entities_mentioned: list[dict[str, str]],
    relationships: list[dict[str, str]],
    source_domain: str | None = None,
) -> list[str]:
    """Update the registry with intelligence from an ingest operation. Returns new entity names."""
    from .object_model import resolve_object_kind, should_promote_to_candidate, should_promote_to_canonical

    new_entities: list[str] = []

    for entity_data in entities_mentioned:
        name = str(entity_data.get("name", "")).strip()
        entity_type = str(entity_data.get("type", entity_data.get("entity_type", "concept")))
        importance = str(entity_data.get("importance", "medium"))
        if not name:
            continue

        resolved = registry.resolve(name)
        existing = registry.get(resolved)

        if existing is None:
            object_kind, subtype = resolve_object_kind(entity_type)
            entity = RegisteredEntity(
                canonical_name=name,
                entity_type=entity_type,
                source_count=1,
                confidence="low",
                status="mention",
                object_kind=object_kind,
                subtype=subtype,
            )
            if importance == "high":
                entity.status = "candidate"
            if source_domain:
                entity.domains.append(source_domain)
            registry.register(entity)
            new_entities.append(name)
        else:
            existing.source_count += 1
            if existing.object_kind is None:
                ok, st = resolve_object_kind(entity_type)
                existing.object_kind = ok
                existing.subtype = st
            registry.update_confidence(resolved)
            if source_domain and source_domain not in existing.domains:
                existing.domains.append(source_domain)

    for rel in relationships:
        subject = str(rel.get("subject", "")).strip()
        obj = str(rel.get("object", "")).strip()
        if subject and obj:
            registry.add_frequent_relation(subject, obj)
            registry.add_frequent_relation(obj, subject)
            sub_entity = registry.get(subject)
            if sub_entity:
                sub_entity.relation_count += 1
            obj_entity = registry.get(obj)
            if obj_entity:
                obj_entity.relation_count += 1

    # Apply promotion rules
    for entity in registry.entities.values():
        if entity.status == "mention":
            if should_promote_to_candidate(entity.source_count, entity.relation_count, "medium"):
                entity.status = "candidate"
        if entity.status == "candidate":
            if should_promote_to_canonical(entity.source_count, entity.relation_count, has_dedicated_note=False):
                entity.status = "canonical"

    return new_entities


__all__ = [
    "EntityRegistry",
    "RegisteredEntity",
    "extract_base_name",
    "learn_from_ingest",
    "load_entity_registry",
    "save_entity_registry",
]
