"""Knowledge audit — comprehensive health check across entities, relations, sources, and quality."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(slots=True)
class KnowledgeAuditResult:
    # Counts
    total_entities: int = 0
    total_sources: int = 0
    total_relations: int = 0

    # Quality issues
    empty_identity: list[str] = field(default_factory=list)
    empty_key_facts: list[str] = field(default_factory=list)
    empty_timeline: list[str] = field(default_factory=list)
    empty_relationships: list[str] = field(default_factory=list)
    no_source_coverage: list[str] = field(default_factory=list)

    # Model issues
    missing_object_kind: list[str] = field(default_factory=list)
    missing_subtype: list[str] = field(default_factory=list)
    old_model_sections: list[str] = field(default_factory=list)
    missing_related_frontmatter: list[str] = field(default_factory=list)

    # Graph issues
    orphan_entities: list[str] = field(default_factory=list)
    duplicate_relations: list[str] = field(default_factory=list)

    # Candidates worth materializing
    unmaterialized_candidates: list[str] = field(default_factory=list)

    # Suggestions
    entities_needing_enrichment: list[str] = field(default_factory=list)
    weak_entities: list[str] = field(default_factory=list)

    # Campaña 0 — coverage metrics (informational, not "issues")
    missing_domain: list[str] = field(default_factory=list)
    non_canonical_domain: list[str] = field(default_factory=list)
    missing_epistemic_mode_gated: list[str] = field(default_factory=list)
    schema_errors_count: int = 0
    schema_warnings_count: int = 0

    def to_dict(self) -> dict[str, object]:
        return {
            "total_entities": self.total_entities,
            "total_sources": self.total_sources,
            "total_relations": self.total_relations,
            "empty_identity": list(self.empty_identity),
            "empty_key_facts": list(self.empty_key_facts),
            "empty_timeline": list(self.empty_timeline),
            "empty_relationships": list(self.empty_relationships),
            "no_source_coverage": list(self.no_source_coverage),
            "missing_object_kind": list(self.missing_object_kind),
            "missing_subtype": list(self.missing_subtype),
            "old_model_sections": list(self.old_model_sections),
            "missing_related_frontmatter": list(self.missing_related_frontmatter),
            "orphan_entities": list(self.orphan_entities),
            "duplicate_relations": list(self.duplicate_relations),
            "unmaterialized_candidates": list(self.unmaterialized_candidates),
            "entities_needing_enrichment": list(self.entities_needing_enrichment),
            "weak_entities": list(self.weak_entities),
            "missing_domain": list(self.missing_domain),
            "non_canonical_domain": list(self.non_canonical_domain),
            "missing_epistemic_mode_gated": list(self.missing_epistemic_mode_gated),
            "schema_errors_count": self.schema_errors_count,
            "schema_warnings_count": self.schema_warnings_count,
        }

    @property
    def total_issues(self) -> int:
        return (
            len(self.empty_identity) + len(self.empty_key_facts) +
            len(self.empty_timeline) + len(self.empty_relationships) +
            len(self.no_source_coverage) + len(self.missing_object_kind) +
            len(self.missing_subtype) + len(self.old_model_sections) +
            len(self.missing_related_frontmatter) + len(self.orphan_entities) +
            len(self.duplicate_relations)
        )

    @property
    def total_suggestions(self) -> int:
        return (
            len(self.unmaterialized_candidates) +
            len(self.entities_needing_enrichment) +
            len(self.weak_entities)
        )


OLD_SECTIONS = {"Context", "What happened", "Consequences", "Biography", "Key contributions",
                "Related events", "Definition", "Why it matters", "Examples",
                "Overview", "Key concepts", "Key figures", "Legacy",
                "Background", "Key battles", "Outcome", "Major works",
                "Style and influence", "Summary", "Key ideas", "Quotes"}

NEW_REQUIRED_SECTIONS = {"Identity", "Key Facts"}

# Equivalent section names across languages (English / Spanish)
_SECTION_ALIASES: dict[str, list[str]] = {
    "Identity": ["Identity", "Identidad", "Definition", "Definición"],
    "Key Facts": ["Key Facts", "Datos clave"],
    "Timeline": ["Timeline", "Cronología", "Línea temporal"],
    "Relationships": ["Relationships", "Relaciones"],
}


def _section_is_empty(body: str, section_name: str) -> bool:
    aliases = _SECTION_ALIASES.get(section_name, [section_name])
    for alias in aliases:
        marker = f"## {alias}"
        idx = body.find(marker)
        if idx == -1:
            continue
        after = body[idx + len(marker):]
        next_heading = after.find("\n## ")
        content = after[:next_heading] if next_heading > 0 else after
        if len(content.strip()) >= 10:
            return False
    # No alias found, or all found aliases had <10 chars
    return True


def _extract_sections(body: str) -> set[str]:
    return set(re.findall(r"^## (.+)$", body, re.MULTILINE))


def audit_knowledge(
    notes: list[tuple[str, dict[str, object], str]],
    source_notes: list[tuple[str, dict[str, object]]],
    registry_entities: dict[str, object] | None = None,
) -> KnowledgeAuditResult:
    result = KnowledgeAuditResult()

    entity_names: set[str] = set()
    all_related: set[str] = set()
    source_enriched: set[str] = set()

    # Audit entity notes
    for _path, fm, body in notes:
        if fm.get("entity") is not True:
            continue

        name = fm.get("name")
        if not isinstance(name, str):
            continue
        name = name.strip()
        entity_names.add(name)
        result.total_entities += 1

        # Quality checks
        if _section_is_empty(body, "Identity"):
            result.empty_identity.append(name)
        if _section_is_empty(body, "Key Facts"):
            result.empty_key_facts.append(name)
        if _section_is_empty(body, "Timeline"):
            result.empty_timeline.append(name)
        if _section_is_empty(body, "Relationships"):
            result.empty_relationships.append(name)

        # Model checks
        if not fm.get("object_kind"):
            result.missing_object_kind.append(name)
        if not fm.get("subtype"):
            result.missing_subtype.append(name)

        # Campaña 0 — coverage checks (domain, epistemic_mode, schema)
        from .epistemology import EPISTEMIC_GATED_DOMAINS, is_valid_epistemic_mode
        from .naming_rules import canonical_domain, is_canonical_domain
        from .schema_validator import validate_note

        raw_domain = fm.get("domain")
        if not raw_domain:
            result.missing_domain.append(name)
        elif isinstance(raw_domain, str) and not is_canonical_domain(raw_domain):
            canonical = canonical_domain(raw_domain)
            suffix = f" → should be '{canonical}'" if canonical else ""
            result.non_canonical_domain.append(f"{name}: '{raw_domain}'{suffix}")

        if isinstance(raw_domain, str) and raw_domain in EPISTEMIC_GATED_DOMAINS:
            if not is_valid_epistemic_mode(fm.get("epistemic_mode") if isinstance(fm.get("epistemic_mode"), str) else None):
                result.missing_epistemic_mode_gated.append(name)

        schema_violations = validate_note(
            note_path=_path if isinstance(_path, str) else str(_path),
            note_name=name,
            frontmatter=fm,
            new_note=False,
            gated_domains=EPISTEMIC_GATED_DOMAINS,
        )
        for v in schema_violations:
            if v.severity == "error":
                result.schema_errors_count += 1
            elif v.severity == "warning":
                result.schema_warnings_count += 1

        # Old model detection
        sections = _extract_sections(body)
        old_found = sections & OLD_SECTIONS
        if old_found:
            result.old_model_sections.append(f"{name}: {', '.join(old_found)}")

        # Related frontmatter check
        related = fm.get("related")
        if not related or (isinstance(related, list) and len(related) == 0):
            result.missing_related_frontmatter.append(name)
        elif isinstance(related, list):
            for r in related:
                if isinstance(r, str):
                    all_related.add(r.strip())

        # Count relations
        if isinstance(related, list):
            result.total_relations += len(related)

        # Weak entity detection (empty template)
        body_lines = [l for l in body.splitlines() if l.strip() and not l.startswith("## ") and not l.startswith("---") and not l.startswith(">")]
        if len(body_lines) < 5:
            result.weak_entities.append(name)

    # Audit source notes
    for _path, fm in source_notes:
        if fm.get("type") == "source":
            result.total_sources += 1
            enriched = fm.get("enriched_entities", [])
            if isinstance(enriched, list):
                for e in enriched:
                    if isinstance(e, str):
                        source_enriched.add(e.strip())

    # Source coverage: entities without any source backing
    for name in entity_names:
        if name not in source_enriched:
            result.no_source_coverage.append(name)

    # Orphan entities: no relations at all
    entities_with_relations = set()
    for _path, fm, _body in notes:
        if fm.get("entity") is not True:
            continue
        related = fm.get("related")
        if isinstance(related, list) and len(related) > 0:
            entities_with_relations.add(fm.get("name", "").strip())
    for name in entity_names:
        if name not in entities_with_relations:
            result.orphan_entities.append(name)

    # Unmaterialized candidates from registry
    if registry_entities:
        for reg_name, reg_data in registry_entities.items():
            if isinstance(reg_data, dict):
                status = reg_data.get("status", "mention")
                if status in ("candidate", "canonical") and reg_name not in entity_names:
                    result.unmaterialized_candidates.append(reg_name)

    # Entities needing enrichment (have note but weak content)
    result.entities_needing_enrichment = list(set(result.empty_identity) | set(result.weak_entities))

    return result


__all__ = [
    "KnowledgeAuditResult",
    "audit_knowledge",
]
