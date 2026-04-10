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
        sections = SUBTYPE_SECTIONS[subtype]
    else:
        sections = ("Identity", "Key Facts", "Timeline", "Impact", "Relationships", "Strategic Insights", "Related notes")

    # Inject "Preguntas de recuperación" before "Related notes" if not already present
    if "Preguntas de recuperación" not in sections and "Related notes" in sections:
        idx = sections.index("Related notes")
        sections = sections[:idx] + ("Preguntas de recuperación",) + sections[idx:]
    return sections


def resolve_object_kind(legacy_type: str) -> tuple[str, str]:
    if legacy_type in LEGACY_TYPE_MAP:
        return LEGACY_TYPE_MAP[legacy_type]
    for kind, subtypes in SUBTYPES.items():
        if legacy_type in subtypes:
            return (kind, legacy_type)
    return ("entity", legacy_type)


# ============================================================================
# SUBTYPE WRITING GUIDES — instructions for LLM about what to prioritize
# ============================================================================

SUBTYPE_WRITING_GUIDES: dict[str, str] = {
    "person": (
        "In Timeline, organize by life phases (early life, rise, peak, decline/death) with specific dates. "
        "In Key Facts, include at least 8 specific facts with dates, names, and places. "
        "In Relationships, use [[Entity]] — role format and include ALL entities mentioned. "
        "Death section should be narrative with circumstances, theories if debated, and consequences. "
        "In Impact, include concrete legacy: what changed because of this person, with numbers/scale. "
        "In Contradictions, note disputed facts, uncertain dates, conflicting sources."
    ),
    "battle": (
        "In Context, explain the strategic situation leading to the battle. "
        "In Participants, list both sides with commanders, army sizes, and composition. "
        "In Timeline, give phase-by-phase tactical development. "
        "Include terrain, weather, and logistical factors. "
        "In Outcome, go beyond who won — explain casualties, prisoners, territorial changes. "
        "In Significance, explain how this battle changed the course of the war or history."
    ),
    "war": (
        "In Causes, distinguish proximate causes from structural ones. "
        "In Timeline, cover key battles and turning points with dates. "
        "In Major Battles, give tactical summaries for each. "
        "In Consequences, cover political, territorial, economic, and cultural effects."
    ),
    "empire": (
        "In Timeline, cover founding, expansion phases, zenith, and decline with specific dates. "
        "In Territory, describe maximum extent with geography. "
        "In Key Rulers, name the most important rulers with their contributions. "
        "In Achievements, cover administration, infrastructure, culture, and innovation. "
        "In Decline, analyze structural causes, not just final events."
    ),
    "civilization": (
        "Cover government structure, economic system, religion, art, science, and military. "
        "In Timeline, mark major periods and turning points. "
        "In Achievements, include specific innovations with dates and context. "
        "In Decline, analyze multiple causal factors."
    ),
    "book": (
        "In Summary, give the argument structure, not just the topic. "
        "In Core Ideas, explain the key philosophical/intellectual contributions. "
        "In Themes, connect to broader intellectual traditions. "
        "In Influence, name specific works, thinkers, or movements influenced by this book."
    ),
    "deity": (
        "In Mythology, narrate specific myths with sources (Ovid, Homer, etc.). "
        "In Symbolism, list attributes, animals, plants, and iconographic elements. "
        "In Worship, describe cult practices, temples, festivals, and priesthood. "
        "Include syncretism: identification with deities from other cultures."
    ),
    "emotion": (
        "In Definition, provide not just a dictionary definition but how it relates to adjacent concepts. "
        "Include multiple interpretive frameworks: philosophical, psychological, biological, cultural. "
        "In Psychological Perspectives, name specific theories and researchers. "
        "In Philosophical Perspectives, trace from ancient (Greek types) through modern thinkers."
    ),
    "discipline": (
        "In Definition, trace etymology and evolution from ancient to modern formulation. "
        "Organize subfields as a structured taxonomy (classical vs modern branches). "
        "Include a timeline of key paradigm shifts with specific dates. "
        "Name key figures per era with their specific contributions."
    ),
    "celestial_body": (
        "In Physical Characteristics, include exact measurements (radius, mass, density, temperature). "
        "In Orbit, include period, eccentricity, inclination. "
        "In Exploration, name specific missions with dates and discoveries. "
        "In Atmosphere & Composition, describe layers and chemical makeup."
    ),
    "city": (
        "In History, cover founding, major periods, and modern era. "
        "In Landmarks, name the most important with construction dates. "
        "Include demographics, cultural significance, and economic role."
    ),
    "country": (
        "Cover geography, political system, economy, culture, and demographics. "
        "In History, focus on formation, major conflicts, and modern development."
    ),
    "institution": (
        "In Founded, include date, founders, and original purpose. "
        "In Mission, explain what it does and why it matters. "
        "In Impact, include concrete accomplishments with dates."
    ),
}

# ============================================================================
# ROLE DETECTION — sub-subtype guidance for persons
# ============================================================================

ROLE_WRITING_HINTS: dict[str, str] = {
    "military_leader": (
        "IMPORTANT: Include a '## Campañas militares' section with phases organized chronologically. "
        "Each phase should name battles, troop numbers, and tactical innovations. "
        "Include a paragraph on logistics and scale (distances, duration, army size, empire extent). "
        "Major sieges deserve their own subsection with engineering details."
    ),
    "philosopher": (
        "IMPORTANT: Include a '## Obras' section organized by discipline (Logic, Metaphysics, Ethics, "
        "Politics, etc.). For each work, explain the key arguments and lasting influence. "
        "Include student-teacher lineages and school founding."
    ),
    "scientist": (
        "IMPORTANT: Include a '## Descubrimientos y obras' section with discoveries listed by date "
        "and methodology. Note paradigm shifts and the chain of influence. "
        "Include experimental methods and instruments used."
    ),
    "political_leader": (
        "IMPORTANT: Include a section on political ascent — alliances, elections, key legislation. "
        "Cover power dynamics, rivalries, and succession. "
        "Distinguish between domestic and foreign policy achievements."
    ),
    "author": (
        "IMPORTANT: Include a '## Obras principales' section with works listed by date, genre, "
        "and significance. Include literary movement affiliation and critical reception. "
        "Note influence on later writers and adaptations."
    ),
}

_ROLE_KEYWORDS: dict[str, list[str]] = {
    "military_leader": [
        "rey", "reina", "emperor", "emperador", "emperatriz", "conquistador",
        "general", "king", "queen", "conqueror", "commander", "comandante",
        "warrior", "guerrero", "pharaoh", "faraón", "hegemon", "hegemón",
        "dictador", "dictator", "caudillo", "mariscal", "marshal",
    ],
    "philosopher": [
        "filósofo", "philosopher", "pensador", "thinker", "sofista", "sophist",
    ],
    "scientist": [
        "científico", "scientist", "inventor", "matemático", "mathematician",
        "physicist", "físico", "astrónomo", "astronomer", "biólogo", "biologist",
        "químico", "chemist", "naturalista", "naturalist",
    ],
    "political_leader": [
        "presidente", "president", "primer ministro", "prime minister",
        "chancellor", "canciller", "senador", "senator", "cónsul", "consul",
        "político", "statesman", "legislador", "legislator",
    ],
    "author": [
        "escritor", "writer", "poeta", "poet", "novelista", "novelist",
        "dramaturgo", "playwright", "ensayista", "essayist", "cronista",
        "historiador", "historian",
    ],
}


def detect_role(subtype: str, occupation: str | None = None) -> str | None:
    """Detect a person's role from occupation metadata. Returns role key or None."""
    if subtype != "person" or not occupation:
        return None
    occ_lower = occupation.lower()
    for role, keywords in _ROLE_KEYWORDS.items():
        if any(kw in occ_lower for kw in keywords):
            return role
    return None


def get_writing_guide(subtype: str, occupation: str | None = None) -> tuple[str, str]:
    """Return (subtype_guide, role_hints) for prompt injection."""
    guide = SUBTYPE_WRITING_GUIDES.get(subtype, "")
    role = detect_role(subtype, occupation)
    hints = ROLE_WRITING_HINTS.get(role, "") if role else ""
    return guide, hints


__all__ = [
    "CANONICAL_PREDICATES",
    "DisambiguationCandidate",
    "ENTITY_STATUSES",
    "LEGACY_TYPE_MAP",
    "OBJECT_KINDS",
    "PREDICATE_NORMALIZATION",
    "ROLE_WRITING_HINTS",
    "SUBTYPES",
    "SUBTYPE_SECTIONS",
    "SUBTYPE_WRITING_GUIDES",
    "build_disambiguated_name",
    "detect_role",
    "get_writing_guide",
    "needs_disambiguation",
    "normalize_predicate",
    "resolve_object_kind",
    "sections_for_subtype",
    "should_promote_to_candidate",
    "should_promote_to_canonical",
]
