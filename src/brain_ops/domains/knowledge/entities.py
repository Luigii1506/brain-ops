"""Entity type definitions and frontmatter/body builders for knowledge entities."""

from __future__ import annotations

from dataclasses import dataclass


ENTITY_TYPES: dict[str, str] = {
    "person": "Historical or notable person",
    "event": "Historical event, battle, treaty, discovery",
    "place": "Country, city, region, geographical location",
    "concept": "Idea, theory, philosophy, scientific principle",
    "book": "Book, publication, written work",
    "author": "Writer, thinker, creator of written works",
    "war": "Armed conflict, war, military campaign",
    "era": "Historical period or age",
    "organization": "Institution, company, empire, political body",
    "topic": "Broad subject area or field of study",
}


@dataclass(slots=True, frozen=True)
class EntitySchema:
    entity_type: str
    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...]
    sections: tuple[str, ...]


# Standard sections for all entity types — consistent structure for indexing and retrieval
_STANDARD_SECTIONS = ("Identity", "Key Facts", "Timeline", "Impact", "Relationships", "Strategic Insights", "Contradictions & Uncertainties", "Related notes")

ENTITY_SCHEMAS: dict[str, EntitySchema] = {
    "person": EntitySchema(
        entity_type="person",
        required_fields=("name",),
        optional_fields=("born", "died", "nationality", "era", "occupation", "related", "tags"),
        sections=_STANDARD_SECTIONS,
    ),
    "event": EntitySchema(
        entity_type="event",
        required_fields=("name",),
        optional_fields=("date", "end_date", "location", "participants", "related", "tags"),
        sections=_STANDARD_SECTIONS,
    ),
    "place": EntitySchema(
        entity_type="place",
        required_fields=("name",),
        optional_fields=("capital", "continent", "region", "population", "language", "related", "tags"),
        sections=_STANDARD_SECTIONS,
    ),
    "concept": EntitySchema(
        entity_type="concept",
        required_fields=("name",),
        optional_fields=("field", "originated", "originated_by", "related", "tags"),
        sections=_STANDARD_SECTIONS,
    ),
    "book": EntitySchema(
        entity_type="book",
        required_fields=("name",),
        optional_fields=("author", "year", "genre", "language", "pages", "related", "tags"),
        sections=_STANDARD_SECTIONS,
    ),
    "author": EntitySchema(
        entity_type="author",
        required_fields=("name",),
        optional_fields=("born", "died", "nationality", "genre", "notable_works", "related", "tags"),
        sections=_STANDARD_SECTIONS,
    ),
    "war": EntitySchema(
        entity_type="war",
        required_fields=("name",),
        optional_fields=("start_date", "end_date", "location", "belligerents", "outcome", "related", "tags"),
        sections=_STANDARD_SECTIONS,
    ),
    "era": EntitySchema(
        entity_type="era",
        required_fields=("name",),
        optional_fields=("start_date", "end_date", "region", "related", "tags"),
        sections=_STANDARD_SECTIONS,
    ),
    "organization": EntitySchema(
        entity_type="organization",
        required_fields=("name",),
        optional_fields=("founded", "dissolved", "location", "type", "related", "tags"),
        sections=_STANDARD_SECTIONS,
    ),
    "topic": EntitySchema(
        entity_type="topic",
        required_fields=("name",),
        optional_fields=("field", "related", "tags"),
        sections=_STANDARD_SECTIONS,
    ),
}


@dataclass(slots=True, frozen=True)
class EntityPlan:
    title: str
    entity_type: str
    frontmatter: dict[str, object]
    body: str


def validate_entity_type(entity_type: str) -> str:
    from .object_model import SUBTYPES, LEGACY_TYPE_MAP

    normalized = entity_type.strip().lower()
    # Accept legacy types
    if normalized in ENTITY_TYPES:
        return normalized
    # Accept any known subtype
    for _kind, subtypes in SUBTYPES.items():
        if normalized in subtypes:
            return normalized
    # Accept legacy mappable types
    if normalized in LEGACY_TYPE_MAP:
        return normalized
    allowed = ", ".join(sorted(ENTITY_TYPES))
    raise ValueError(f"Unknown entity type '{entity_type}'. Expected one of: {allowed}.")


def build_entity_frontmatter(
    entity_type: str,
    name: str,
    *,
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    from .object_model import resolve_object_kind

    object_kind, subtype = resolve_object_kind(entity_type)
    frontmatter: dict[str, object] = {
        "type": entity_type,
        "object_kind": object_kind,
        "subtype": subtype,
        "name": name,
        "entity": True,
        "status": "canonical",
    }
    schema = ENTITY_SCHEMAS.get(entity_type)
    if schema is not None:
        for field in schema.optional_fields:
            if field not in frontmatter:
                frontmatter[field] = None
    if extra:
        frontmatter.update(extra)
    return frontmatter


SECTION_HINTS: dict[str, str] = {
    "Identity": "<!-- 1-3 sentences: who/what this is, when they lived/existed, why they matter -->",
    "Key Facts": "<!-- At least 5 specific facts with dates, names, places -->",
    "Timeline": "<!-- Chronological events with specific dates: **date** — event -->",
    "Impact": "<!-- Concrete legacy: what changed because of this entity -->",
    "Relationships": "<!-- [[Entity]] — relationship type format -->",
    "Strategic Insights": "<!-- Non-obvious patterns, lessons, strategic behaviors -->",
    "Contradictions & Uncertainties": "<!-- Disputed facts, uncertain dates, conflicting sources -->",
    "Related notes": "",
}


def build_entity_body(entity_type: str, name: str) -> str:
    from .object_model import sections_for_subtype

    sections = sections_for_subtype(entity_type)
    lines: list[str] = []
    for section in sections:
        lines.append(f"## {section}")
        hint = SECTION_HINTS.get(section, "")
        if hint:
            lines.append(hint)
        lines.append("")
    return "\n".join(lines)


def plan_entity_note(
    name: str,
    *,
    entity_type: str,
    extra_frontmatter: dict[str, object] | None = None,
) -> EntityPlan:
    validated_type = validate_entity_type(entity_type)
    return EntityPlan(
        title=name.strip(),
        entity_type=validated_type,
        frontmatter=build_entity_frontmatter(validated_type, name.strip(), extra=extra_frontmatter),
        body=build_entity_body(validated_type, name.strip()),
    )


def extract_entity_relations(frontmatter: dict[str, object]) -> list[str]:
    related = frontmatter.get("related")
    if isinstance(related, list):
        return [str(item).strip() for item in related if str(item).strip()]
    if isinstance(related, str) and related.strip():
        return [related.strip()]
    return []


def is_entity_note(frontmatter: dict[str, object]) -> bool:
    return frontmatter.get("entity") is True


__all__ = [
    "ENTITY_SCHEMAS",
    "ENTITY_TYPES",
    "EntityPlan",
    "EntitySchema",
    "build_entity_body",
    "build_entity_frontmatter",
    "extract_entity_relations",
    "is_entity_note",
    "plan_entity_note",
    "validate_entity_type",
]
