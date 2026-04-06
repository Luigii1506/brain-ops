"""Universal Knowledge Object model — the standard for all knowledge in brain-ops."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


# ============================================================================
# OBJECT KINDS AND SUBTYPES
# ============================================================================

OBJECT_KINDS: dict[str, str] = {
    "entity": "A concrete thing: person, animal, planet, technology",
    "concept": "An abstract idea: emotion, theory, discipline, value",
    "work": "A created artifact: book, paper, artwork, software",
    "event": "Something that happened: war, revolution, discovery",
    "place": "A location: country, city, continent, landmark",
    "organization": "A group: company, religion, government, school",
    "source": "An ingested reference: article, video, documentation",
    "topic": "A knowledge grouping: research area, study track",
}

SUBTYPES: dict[str, list[str]] = {
    "entity": [
        "person", "animal", "plant", "celestial_body", "civilization",
        "deity", "artifact", "technology", "programming_language",
    ],
    "concept": [
        "abstract_concept", "emotion", "value", "theory", "discipline",
        "school_of_thought", "scientific_concept", "philosophical_concept",
        "religious_concept",
    ],
    "work": [
        "book", "paper", "poem", "play", "artwork", "dataset", "software_project",
    ],
    "event": [
        "war", "battle", "revolution", "treaty", "discovery", "historical_event",
    ],
    "place": [
        "country", "city", "region", "empire", "continent", "landmark",
    ],
    "organization": [
        "company", "institution", "government", "religion", "military_unit",
        "academic_school",
    ],
    "source": [
        "article", "encyclopedia", "book_chapter", "video_transcript",
        "research_paper", "documentation", "notes",
    ],
    "topic": [
        "umbrella_topic", "research_area", "study_track",
    ],
}

# Backwards compatibility: map old entity_type → (object_kind, subtype)
LEGACY_TYPE_MAP: dict[str, tuple[str, str]] = {
    "person": ("entity", "person"),
    "author": ("entity", "person"),
    "book": ("work", "book"),
    "war": ("event", "war"),
    "era": ("event", "historical_event"),
    "concept": ("concept", "abstract_concept"),
    "topic": ("topic", "umbrella_topic"),
    "event": ("event", "historical_event"),
    "place": ("place", "country"),
    "organization": ("organization", "institution"),
    "country": ("place", "country"),
}


# ============================================================================
# ENTITY STATUS / PROMOTION
# ============================================================================

ENTITY_STATUSES = ("mention", "candidate", "canonical", "merged", "ambiguous")


def should_promote_to_candidate(source_count: int, relation_count: int, importance: str) -> bool:
    if importance == "high":
        return True
    return source_count >= 2 or relation_count >= 2


def should_promote_to_canonical(source_count: int, relation_count: int, has_dedicated_note: bool) -> bool:
    if has_dedicated_note:
        return True
    return source_count >= 3 and relation_count >= 2


# ============================================================================
# CANONICAL PREDICATES
# ============================================================================

CANONICAL_PREDICATES: dict[str, str] = {
    # Biographical
    "born_in": "birthplace",
    "died_in": "place of death",
    "parent_of": "parent-child relationship",
    "child_of": "child-parent relationship",
    "sibling_of": "sibling relationship",
    "married_to": "marriage",
    "nationality": "citizenship or origin",
    # Intellectual
    "studied_under": "student-teacher relationship",
    "mentor_of": "teacher-student relationship",
    "influenced_by": "intellectual influence received",
    "influenced": "intellectual influence given",
    "author_of": "created a work",
    "wrote": "authored a work",
    # Political/Military
    "led": "leadership role",
    "conquered": "military conquest",
    "founded": "establishment or creation",
    "ruled": "governance",
    "succeeded": "succession",
    "preceded_by": "previous in sequence",
    "fought_in": "military participation",
    "allied_with": "alliance",
    "opposed": "opposition or rivalry",
    # Organizational
    "member_of": "membership",
    "part_of": "component relationship",
    "headquartered_in": "location of headquarters",
    "affiliated_with": "loose association",
    # Spatial
    "located_in": "geographical containment",
    "capital_of": "capital city relationship",
    "borders": "geographical adjacency",
    "contains": "geographical containment (inverse)",
    # Temporal
    "occurred_in": "temporal placement",
    "caused": "causal relationship",
    "caused_by": "effect relationship",
    "preceded": "temporal ordering",
    "followed": "temporal ordering",
    # Classification
    "instance_of": "type membership",
    "subclass_of": "type hierarchy",
    "related_to": "general association",
    "about": "topical relationship",
    "example_of": "illustrative instance",
}

# Normalization map: raw LLM predicates → canonical
PREDICATE_NORMALIZATION: dict[str, str] = {
    "father of": "parent_of",
    "mother of": "parent_of",
    "son of": "child_of",
    "daughter of": "child_of",
    "padre de": "parent_of",
    "madre de": "parent_of",
    "hijo de": "child_of",
    "hija de": "child_of",
    "student of": "studied_under",
    "teacher of": "mentor_of",
    "tutor of": "mentor_of",
    "tutor": "mentor_of",
    "mentor": "mentor_of",
    "alumno de": "studied_under",
    "discípulo de": "studied_under",
    "maestro de": "mentor_of",
    "wrote": "author_of",
    "escribió": "author_of",
    "autor de": "author_of",
    "king of": "ruled",
    "queen of": "ruled",
    "emperor of": "ruled",
    "rey de": "ruled",
    "emperador de": "ruled",
    "born in": "born_in",
    "nació en": "born_in",
    "died in": "died_in",
    "murió en": "died_in",
    "founded": "founded",
    "fundó": "founded",
    "conquered": "conquered",
    "conquistó": "conquered",
    "fought in": "fought_in",
    "luchó en": "fought_in",
    "participated in": "fought_in",
    "participó en": "fought_in",
    "capital of": "capital_of",
    "capital de": "capital_of",
    "located in": "located_in",
    "ubicado en": "located_in",
    "part of": "part_of",
    "parte de": "part_of",
    "member of": "member_of",
    "miembro de": "member_of",
    "influenced by": "influenced_by",
    "influenciado por": "influenced_by",
    "influenced": "influenced",
    "influyó en": "influenced",
    "related to": "related_to",
    "relacionado con": "related_to",
    "caused": "caused",
    "causó": "caused",
    "caused by": "caused_by",
    "causado por": "caused_by",
    "preceded by": "preceded_by",
    "preceded": "preceded",
    "succeeded": "succeeded",
    "sucedió a": "succeeded",
    "principal adversario": "opposed",
    "principal objetivo de conquista": "conquered",
    "lugar de muerte": "died_in",
    "padre y predecesor": "parent_of",
}


def normalize_predicate(raw_predicate: str) -> str:
    normalized = raw_predicate.strip().lower()
    if normalized in CANONICAL_PREDICATES:
        return normalized
    mapped = PREDICATE_NORMALIZATION.get(normalized)
    if mapped:
        return mapped
    for key, canonical in PREDICATE_NORMALIZATION.items():
        if key in normalized:
            return canonical
    return "related_to"


# ============================================================================
# DISAMBIGUATION
# ============================================================================

@dataclass(slots=True, frozen=True)
class DisambiguationCandidate:
    canonical_name: str
    display_name: str
    subtype: str
    disambiguation_key: str

    def to_dict(self) -> dict[str, object]:
        return {
            "canonical_name": self.canonical_name,
            "display_name": self.display_name,
            "subtype": self.subtype,
            "disambiguation_key": self.disambiguation_key,
        }


def build_disambiguated_name(name: str, subtype: str) -> str:
    return f"{name} ({subtype})"


def needs_disambiguation(name: str, existing_types: list[str]) -> bool:
    return len(existing_types) > 1


# ============================================================================
# SECTION TEMPLATES PER SUBTYPE
# ============================================================================

_BASE_SECTIONS = ("Identity", "Key Facts", "Relationships", "Related notes")

SUBTYPE_SECTIONS: dict[str, tuple[str, ...]] = {
    # Entity subtypes
    "person": ("Identity", "Key Facts", "Timeline", "Impact", "Relationships", "Strategic Insights", "Contradictions & Uncertainties", "Related notes"),
    "animal": ("Identity", "Key Facts", "Taxonomy", "Habitat & Distribution", "Diet & Behavior", "Conservation Status", "Relationships", "Related notes"),
    "plant": ("Identity", "Key Facts", "Taxonomy", "Habitat & Distribution", "Uses", "Relationships", "Related notes"),
    "celestial_body": ("Identity", "Key Facts", "Physical Characteristics", "Orbit & Position", "Atmosphere & Composition", "Exploration", "Relationships", "Related notes"),
    "civilization": ("Identity", "Key Facts", "Timeline", "Territory", "Achievements", "Decline", "Relationships", "Related notes"),
    "deity": ("Identity", "Key Facts", "Mythology", "Symbolism", "Worship", "Relationships", "Related notes"),
    "technology": ("Identity", "Key Facts", "How It Works", "Applications", "Impact", "Timeline", "Relationships", "Related notes"),
    "programming_language": ("Identity", "Key Facts", "Design Philosophy", "Key Features", "Common Use Cases", "Ecosystem", "Relationships", "Related notes"),
    # Concept subtypes
    "abstract_concept": ("Definition", "Key Facts", "Interpretations", "Examples", "Impact", "Relationships", "Related notes"),
    "emotion": ("Definition", "Key Facts", "Psychological Perspectives", "Philosophical Perspectives", "Expressions & Examples", "Relationships", "Related notes"),
    "value": ("Definition", "Key Facts", "Philosophical Perspectives", "Cultural Variations", "Examples", "Relationships", "Related notes"),
    "theory": ("Definition", "Key Facts", "Origins", "Core Principles", "Evidence", "Criticisms", "Impact", "Relationships", "Related notes"),
    "discipline": ("Definition", "Key Facts", "Scope & Methods", "Core Questions", "Subfields", "Key Figures", "Relationships", "Related notes"),
    "school_of_thought": ("Definition", "Key Facts", "Origins", "Core Principles", "Key Figures", "Influence", "Criticisms", "Relationships", "Related notes"),
    "scientific_concept": ("Definition", "Key Facts", "Mathematical Formulation", "Evidence", "Applications", "Relationships", "Related notes"),
    "philosophical_concept": ("Definition", "Key Facts", "Historical Context", "Interpretations", "Arguments", "Criticisms", "Relationships", "Related notes"),
    # Work subtypes
    "book": ("Identity", "Key Facts", "Author", "Summary", "Core Ideas", "Themes", "Quotes", "Influence", "Relationships", "Related notes"),
    "paper": ("Identity", "Key Facts", "Authors", "Abstract", "Methodology", "Findings", "Impact", "Relationships", "Related notes"),
    "artwork": ("Identity", "Key Facts", "Artist", "Context", "Interpretation", "Influence", "Relationships", "Related notes"),
    "software_project": ("Identity", "Key Facts", "Stack", "Architecture", "Setup & Commands", "Current Status", "Relationships", "Related notes"),
    # Event subtypes
    "war": ("Identity", "Key Facts", "Causes", "Participants", "Timeline", "Major Battles", "Outcome", "Consequences", "Relationships", "Related notes"),
    "battle": ("Identity", "Key Facts", "Context", "Participants", "Timeline", "Outcome", "Significance", "Relationships", "Related notes"),
    "revolution": ("Identity", "Key Facts", "Causes", "Timeline", "Key Figures", "Outcome", "Legacy", "Relationships", "Related notes"),
    "discovery": ("Identity", "Key Facts", "Context", "How It Happened", "Impact", "Relationships", "Related notes"),
    "historical_event": ("Identity", "Key Facts", "Context", "Timeline", "Impact", "Relationships", "Contradictions & Uncertainties", "Related notes"),
    # Place subtypes
    "country": ("Identity", "Key Facts", "Geography", "History", "Government", "Culture", "Relationships", "Related notes"),
    "city": ("Identity", "Key Facts", "Geography", "History", "Landmarks", "Relationships", "Related notes"),
    "empire": ("Identity", "Key Facts", "Timeline", "Territory", "Key Rulers", "Achievements", "Decline", "Relationships", "Related notes"),
    "continent": ("Identity", "Key Facts", "Geography", "Countries", "History", "Relationships", "Related notes"),
    # Organization subtypes
    "company": ("Identity", "Key Facts", "Founded", "Products & Services", "Leadership", "Impact", "Relationships", "Related notes"),
    "institution": ("Identity", "Key Facts", "Founded", "Mission", "Structure", "Impact", "Relationships", "Related notes"),
    "religion": ("Identity", "Key Facts", "Origins", "Core Beliefs", "Practices", "Sacred Texts", "Denominations", "Relationships", "Related notes"),
}


def sections_for_subtype(subtype: str | None) -> tuple[str, ...]:
    if subtype and subtype in SUBTYPE_SECTIONS:
        return SUBTYPE_SECTIONS[subtype]
    return ("Identity", "Key Facts", "Timeline", "Impact", "Relationships", "Strategic Insights", "Related notes")


def resolve_object_kind(legacy_type: str) -> tuple[str, str]:
    if legacy_type in LEGACY_TYPE_MAP:
        return LEGACY_TYPE_MAP[legacy_type]
    for kind, subtypes in SUBTYPES.items():
        if legacy_type in subtypes:
            return (kind, legacy_type)
    return ("entity", legacy_type)


__all__ = [
    "CANONICAL_PREDICATES",
    "DisambiguationCandidate",
    "ENTITY_STATUSES",
    "LEGACY_TYPE_MAP",
    "OBJECT_KINDS",
    "PREDICATE_NORMALIZATION",
    "SUBTYPES",
    "SUBTYPE_SECTIONS",
    "build_disambiguated_name",
    "needs_disambiguation",
    "normalize_predicate",
    "resolve_object_kind",
    "sections_for_subtype",
    "should_promote_to_candidate",
    "should_promote_to_canonical",
]
