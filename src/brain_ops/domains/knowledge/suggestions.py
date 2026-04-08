"""Suggestion engine — recommend next entities to create, enrich, or split."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


SuggestionAction = Literal["create", "enrich", "split", "review"]


@dataclass(slots=True)
class SuggestionCandidate:
    canonical_name: str
    action: SuggestionAction = "create"
    object_kind: str | None = None
    subtype: str | None = None

    # Signals
    query_count: int = 0
    gap_count: int = 0
    source_mentions: int = 0
    graph_degree: float = 0.0
    graph_bridge_score: float = 0.0
    moc_mentions: int = 0
    source_coverage: int = 0

    # Current quality
    has_note: bool = False
    has_identity: bool = True
    has_old_model: bool = False
    is_orphan: bool = False
    is_ambiguous: bool = False

    # Priority
    domain_priority: float = 0.0

    # Output
    score: float = 0.0
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.canonical_name,
            "action": self.action,
            "score": round(self.score, 2),
            "object_kind": self.object_kind,
            "subtype": self.subtype,
            "reasons": list(self.reasons),
            "query_count": self.query_count,
            "gap_count": self.gap_count,
            "source_mentions": self.source_mentions,
            "graph_degree": self.graph_degree,
        }


def _norm(value: float, max_val: float = 10.0) -> float:
    return min(value / max_val, 1.0) if max_val > 0 else 0.0


def score_create(c: SuggestionCandidate) -> float:
    return (
        _norm(c.gap_count, 5) * 0.30
        + _norm(c.query_count, 5) * 0.20
        + _norm(c.source_mentions, 5) * 0.15
        + _norm(c.graph_degree, 10) * 0.15
        + _norm(c.graph_bridge_score, 1) * 0.10
        + _norm(c.moc_mentions, 3) * 0.05
        + c.domain_priority * 0.05
    )


def score_enrich(c: SuggestionCandidate) -> float:
    weakness = (
        (0.35 if not c.has_identity else 0.0)
        + (0.25 if c.source_coverage == 0 else 0.0)
        + (0.20 if c.has_old_model else 0.0)
        + (0.10 if c.is_orphan else 0.0)
        + (0.10 if c.is_ambiguous else 0.0)
    )
    return (
        weakness * 0.35
        + _norm(c.query_count, 5) * 0.20
        + _norm(c.graph_degree, 10) * 0.15
        + _norm(c.source_mentions, 5) * 0.10
        + _norm(c.moc_mentions, 3) * 0.10
        + c.domain_priority * 0.10
    )


def score_split(c: SuggestionCandidate) -> float:
    return (
        (0.50 if c.is_ambiguous else 0.0)
        + _norm(c.query_count, 5) * 0.15
        + _norm(c.source_mentions, 5) * 0.15
        + _norm(c.graph_degree, 10) * 0.10
        + c.domain_priority * 0.10
    )


def infer_action(c: SuggestionCandidate) -> SuggestionAction:
    if c.is_ambiguous:
        return "split"
    if c.has_note:
        return "enrich"
    return "create"


def build_reasons(c: SuggestionCandidate) -> list[str]:
    reasons: list[str] = []
    if c.gap_count >= 2:
        reasons.append(f"aparece como gap en {c.gap_count} queries")
    elif c.gap_count >= 1:
        reasons.append("detectada como gap en query")
    if c.query_count >= 2:
        reasons.append(f"aparece en {c.query_count} consultas")
    if c.source_mentions >= 2:
        reasons.append(f"mencionada en {c.source_mentions} fuentes")
    if c.graph_bridge_score >= 0.3:
        reasons.append("conecta clusters importantes del grafo")
    if c.graph_degree >= 5:
        reasons.append(f"alta centralidad ({int(c.graph_degree)} conexiones)")
    if c.moc_mentions >= 1:
        reasons.append("aparece en MOCs o rutas existentes")
    if c.has_note and not c.has_identity:
        reasons.append("la nota existe pero tiene Identity vacío")
    if c.has_old_model:
        reasons.append("usa el modelo viejo de secciones")
    if c.source_coverage == 0 and c.has_note:
        reasons.append("no tiene source coverage")
    if c.is_orphan and c.has_note:
        reasons.append("entidad huérfana (sin relaciones)")
    if c.is_ambiguous:
        reasons.append("entidad ambigua — necesita desambiguación")
    if not reasons:
        reasons.append("mencionada en el knowledge base")
    return reasons


def suggest_next_entities(
    registry_entities: dict[str, dict[str, object]],
    existing_entity_names: set[str],
    *,
    gap_registry: dict[str, dict[str, object]] | None = None,
    audit_data: dict[str, object] | None = None,
    max_suggestions: int = 15,
) -> list[SuggestionCandidate]:
    """Build, score, and rank entity suggestions combining all signals."""
    candidates: dict[str, SuggestionCandidate] = {}

    # 1. From registry
    for name, data in registry_entities.items():
        c = candidates.setdefault(name, SuggestionCandidate(canonical_name=name))
        c.source_mentions = int(data.get("source_count", 0))
        c.query_count = int(data.get("query_count", 0))
        c.graph_degree = float(data.get("relation_count", 0))
        c.object_kind = data.get("object_kind") if isinstance(data.get("object_kind"), str) else None
        c.subtype = data.get("subtype") if isinstance(data.get("subtype"), str) else None
        c.has_note = name in existing_entity_names

        # Bridge score: how many distinct subtypes among neighbors
        freq_rels = data.get("frequent_relations", [])
        if isinstance(freq_rels, list):
            subtypes_connected = set()
            for rel_name in freq_rels:
                rel_data = registry_entities.get(rel_name, {})
                st = rel_data.get("subtype", "")
                if st:
                    subtypes_connected.add(st)
            c.graph_bridge_score = min(len(subtypes_connected) / 5.0, 1.0)

    # 2. From gap registry
    if gap_registry:
        for name, gap_data in gap_registry.items():
            c = candidates.setdefault(name, SuggestionCandidate(canonical_name=name))
            c.gap_count = int(gap_data.get("times_seen_in_queries", 0))
            if not c.has_note:
                c.has_note = name in existing_entity_names

    # 3. From audit data
    if audit_data:
        for name in audit_data.get("empty_identity", []):
            c = candidates.setdefault(name, SuggestionCandidate(canonical_name=name))
            c.has_identity = False
            c.has_note = True

        for name in audit_data.get("no_source_coverage", []):
            if name in candidates:
                candidates[name].source_coverage = 0

        for entry in audit_data.get("old_model_sections", []):
            entity_name = entry.split(":")[0].strip() if ":" in entry else entry
            if entity_name in candidates:
                candidates[entity_name].has_old_model = True

        for name in audit_data.get("orphan_entities", []):
            if name in candidates:
                candidates[name].is_orphan = True

    # 4. Score and rank
    for c in candidates.values():
        c.action = infer_action(c)
        if c.action == "create":
            c.score = score_create(c) * 10
        elif c.action == "enrich":
            c.score = score_enrich(c) * 10
        elif c.action == "split":
            c.score = score_split(c) * 10
        c.reasons = build_reasons(c)

    valid = [c for c in candidates.values() if c.score >= 0.5]
    valid.sort(key=lambda x: x.score, reverse=True)
    return valid[:max_suggestions]


def suggest_entities_for_topic(
    registry_entities: dict[str, dict[str, object]],
    existing_entity_names: set[str],
    topic_related_names: set[str],
    *,
    max_suggestions: int = 10,
) -> list[SuggestionCandidate]:
    """Suggest entities specifically relevant to a topic."""
    all_suggestions = suggest_next_entities(registry_entities, existing_entity_names, max_suggestions=50)
    topic_suggestions = [s for s in all_suggestions if s.canonical_name in topic_related_names]
    topic_suggestions.sort(key=lambda s: s.score, reverse=True)
    return topic_suggestions[:max_suggestions]


__all__ = [
    "SuggestionAction",
    "SuggestionCandidate",
    "suggest_entities_for_topic",
    "suggest_next_entities",
]
