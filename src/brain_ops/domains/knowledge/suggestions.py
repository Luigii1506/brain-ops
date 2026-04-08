"""Suggestion engine — recommend next entities to create and sources to process."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class EntitySuggestion:
    name: str
    reason: str
    source_count: int
    relation_count: int
    score: float

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "reason": self.reason,
            "source_count": self.source_count,
            "relation_count": self.relation_count,
            "score": self.score,
        }


def suggest_next_entities(
    registry_entities: dict[str, dict[str, object]],
    existing_entity_names: set[str],
    *,
    max_suggestions: int = 10,
) -> list[EntitySuggestion]:
    """Suggest entities worth creating based on registry intelligence."""
    suggestions: list[EntitySuggestion] = []

    for name, data in registry_entities.items():
        if name in existing_entity_names:
            continue

        source_count = int(data.get("source_count", 0))
        relation_count = int(data.get("relation_count", 0))
        status = str(data.get("status", "mention"))
        confidence = str(data.get("confidence", "low"))

        # Score based on evidence
        score = 0.0
        reason_parts: list[str] = []

        if source_count >= 3:
            score += 3.0
            reason_parts.append(f"appears in {source_count} sources")
        elif source_count >= 2:
            score += 2.0
            reason_parts.append(f"appears in {source_count} sources")
        elif source_count >= 1:
            score += 1.0

        if relation_count >= 5:
            score += 3.0
            reason_parts.append(f"has {relation_count} connections")
        elif relation_count >= 2:
            score += 2.0
            reason_parts.append(f"has {relation_count} connections")

        if status == "candidate":
            score += 1.5
            reason_parts.append("promoted to candidate")
        elif status == "canonical":
            score += 2.0
            reason_parts.append("already canonical in registry")

        frequent_relations = data.get("frequent_relations", [])
        if isinstance(frequent_relations, list) and len(frequent_relations) >= 3:
            score += 1.0
            reason_parts.append(f"connected to {len(frequent_relations)} entities")

        if score >= 2.0:
            reason = "; ".join(reason_parts) if reason_parts else "mentioned in knowledge base"
            suggestions.append(EntitySuggestion(
                name=name,
                reason=reason,
                source_count=source_count,
                relation_count=relation_count,
                score=score,
            ))

    suggestions.sort(key=lambda s: s.score, reverse=True)
    return suggestions[:max_suggestions]


def suggest_entities_for_topic(
    registry_entities: dict[str, dict[str, object]],
    existing_entity_names: set[str],
    topic_related_names: set[str],
    *,
    max_suggestions: int = 10,
) -> list[EntitySuggestion]:
    """Suggest entities specifically relevant to a topic."""
    all_suggestions = suggest_next_entities(registry_entities, existing_entity_names, max_suggestions=50)
    topic_suggestions = [s for s in all_suggestions if s.name in topic_related_names]
    topic_suggestions.sort(key=lambda s: s.score, reverse=True)
    return topic_suggestions[:max_suggestions]


__all__ = [
    "EntitySuggestion",
    "suggest_entities_for_topic",
    "suggest_next_entities",
]
