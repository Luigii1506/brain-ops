"""Registry health check — detect issues in the entity registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .registry import EntityRegistry


@dataclass(slots=True)
class RegistryLintResult:
    total_entities: int = 0
    canonical_count: int = 0
    candidate_count: int = 0
    mention_count: int = 0
    low_confidence: list[str] = field(default_factory=list)
    no_relations: list[str] = field(default_factory=list)
    high_source_not_canonical: list[str] = field(default_factory=list)
    missing_subtype: list[str] = field(default_factory=list)
    missing_object_kind: list[str] = field(default_factory=list)
    promotable_to_candidate: list[str] = field(default_factory=list)
    promotable_to_canonical: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "total_entities": self.total_entities,
            "canonical_count": self.canonical_count,
            "candidate_count": self.candidate_count,
            "mention_count": self.mention_count,
            "low_confidence": list(self.low_confidence),
            "no_relations": list(self.no_relations),
            "high_source_not_canonical": list(self.high_source_not_canonical),
            "missing_subtype": list(self.missing_subtype),
            "missing_object_kind": list(self.missing_object_kind),
            "promotable_to_candidate": list(self.promotable_to_candidate),
            "promotable_to_canonical": list(self.promotable_to_canonical),
        }

    @property
    def total_issues(self) -> int:
        return (
            len(self.low_confidence) + len(self.no_relations) +
            len(self.high_source_not_canonical) + len(self.missing_subtype) +
            len(self.missing_object_kind) + len(self.promotable_to_candidate) +
            len(self.promotable_to_canonical)
        )


def lint_registry(registry: EntityRegistry) -> RegistryLintResult:
    result = RegistryLintResult()
    result.total_entities = len(registry.entities)

    for entity in registry.entities.values():
        if entity.status == "canonical":
            result.canonical_count += 1
        elif entity.status == "candidate":
            result.candidate_count += 1
        else:
            result.mention_count += 1

        if entity.confidence == "low" and entity.source_count >= 2:
            result.low_confidence.append(entity.canonical_name)

        if entity.relation_count == 0:
            result.no_relations.append(entity.canonical_name)

        if entity.source_count >= 3 and entity.status != "canonical":
            result.high_source_not_canonical.append(entity.canonical_name)

        if not entity.subtype:
            result.missing_subtype.append(entity.canonical_name)

        if not entity.object_kind:
            result.missing_object_kind.append(entity.canonical_name)

        if entity.status == "mention" and (entity.source_count >= 2 or entity.relation_count >= 2):
            result.promotable_to_candidate.append(entity.canonical_name)

        if entity.status == "candidate" and entity.source_count >= 3 and entity.relation_count >= 2:
            result.promotable_to_canonical.append(entity.canonical_name)

    return result


__all__ = [
    "RegistryLintResult",
    "lint_registry",
]
