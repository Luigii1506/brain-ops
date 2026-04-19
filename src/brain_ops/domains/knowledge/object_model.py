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
    "disambiguation": "A disambiguation page listing entities with the same name",
}

SUBTYPES: dict[str, list[str]] = {
    "entity": [
        "person", "animal", "plant", "celestial_body", "civilization", "polity",
        "deity", "myth", "symbol", "artifact", "weapon", "technology", "programming_language",
        # Campaña 0 additions — life & language
        "organism", "species", "anatomical_structure",
        "language", "script",
    ],
    "concept": [
        "abstract_concept", "emotion", "value", "theory", "discipline",
        "school_of_thought", "scientific_concept", "philosophical_concept",
        "religious_concept", "process", "classification",
        "algorithm", "metric", "technical_concept", "architecture_pattern",
        # Campaña 0 additions — biology / chemistry / medicine
        "biological_process", "cell", "cell_type", "gene",
        "chemical_element", "compound", "molecule",
        "disease", "medical_theory",
        # Campaña 0 additions — mathematics
        "theorem", "mathematical_object", "constant", "mathematical_function",
        "proof_method", "mathematical_field",
        # Campaña 0 additions — esoteric concepts
        "symbolic_system", "divination_system", "mystical_concept",
    ],
    "work": [
        "book", "paper", "poem", "play", "artwork", "dataset", "software_project",
        "case_study",
        # Campaña 0 additions — sacred & esoteric texts
        "sacred_text", "esoteric_text",
    ],
    "event": [
        "war", "battle", "revolution", "treaty", "discovery", "historical_event",
        "phenomenon",
        # Campaña 0 additions — temporal / processual blocks
        "historical_period", "dynasty", "historical_process",
        "ritual",
    ],
    "place": [
        "country", "city", "region", "empire", "continent", "landmark",
        "geological_feature", "mythological_place",
    ],
    "organization": [
        "company", "institution", "government", "religion", "military_unit",
        "academic_school", "office_role",
        # Campaña 0 additions — esoteric institutions
        "esoteric_tradition", "occult_movement",
    ],
    "source": [
        "article", "encyclopedia", "book_chapter", "video_transcript",
        "research_paper", "documentation", "notes",
    ],
    "topic": [
        "umbrella_topic", "research_area", "study_track",
    ],
    "disambiguation": [
        "disambiguation_page",
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
    "algorithm": ("concept", "algorithm"),
    "metric": ("concept", "metric"),
    "technical_concept": ("concept", "technical_concept"),
    "pattern": ("concept", "architecture_pattern"),
    "architecture_pattern": ("concept", "architecture_pattern"),
    "case_study": ("work", "case_study"),
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
    "adopted_by": "adoptee to adoptive parent (distinct from biological child_of)",
    "adoptive_parent_of": "adoptive parent to adoptee (distinct from biological parent_of)",
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
    # Intellectual — Campaña 0 additions
    "reacted_against": "critical reaction to a prior idea or thinker",
    "developed": "elaborated or advanced an idea",
    "extended": "extended an existing framework",
    "synthesized": "combined multiple traditions into a new whole",
    "refuted": "presented a formal or argumentative rebuttal",
    "criticized": "criticized without fully refuting",
    "inspired": "served as creative or intellectual inspiration",
    "derived_from": "derived from a prior source or tradition",
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
    # Historical — Campaña 0 additions
    "belongs_to_period": "temporal placement inside a historical period",
    "contemporary_of": "lived or existed at the same time",
    "emerged_from": "historical emergence from a prior state",
    "transformed_into": "historical transformation into a subsequent state",
    "ruled_by": "governed by a specific entity",
    "centered_on": "historically centered on a place, person, or theme",
    "continuation_of": "institutional or cultural continuation",
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
    # Religious / mythological / esoteric — Campaña 0 additions
    "worshipped": "worshipped a deity or entity",
    "worshipped_by": "object of worship",
    "associated_with": "symbolic or cultural association",
    "symbolizes": "symbolic representation of",
    "used_in": "used within a practice or ritual",
    "practiced_by": "practice associated with a group or tradition",
    "interpreted_as": "subject to a specific interpretation",
    "appears_in": "appears within a text, myth, or work",
    # Work — Campaña 0 additions
    "depicts": "depicts an entity or event",
    "describes": "describes an entity or event",
    "argues_for": "argues in favor of a thesis",
    "argues_against": "argues against a thesis",
    "written_in": "language the work is written in",
    "based_on": "derivative or adaptation relationship",
    # Scientific — Campaña 0 additions
    "explains": "provides a scientific explanation for",
    "measured_by": "measured via a given metric or instrument",
    "studied_in": "subject of study within a discipline",
    "part_of_system": "component of a broader system",
    "precedes_in_process": "comes before in a process or pathway",
    "depends_on": "causal or functional dependency",
    # Generic participation — complements fought_in
    "participated_in": "general participation in an event or process",
    # Classification
    "instance_of": "type membership",
    "subclass_of": "type hierarchy",
    "related_to": "general association (fallback — use typed predicate when possible)",
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
    "adopted by": "adopted_by",
    "adopted son of": "adopted_by",
    "adopted daughter of": "adopted_by",
    "hijo adoptivo de": "adopted_by",
    "hija adoptiva de": "adopted_by",
    "adoptado por": "adopted_by",
    "adoptive father of": "adoptive_parent_of",
    "adoptive mother of": "adoptive_parent_of",
    "adoptive parent of": "adoptive_parent_of",
    "adopted": "adoptive_parent_of",
    "padre adoptivo de": "adoptive_parent_of",
    "madre adoptiva de": "adoptive_parent_of",
    "adoptó a": "adoptive_parent_of",
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
    "combatió en": "fought_in",
    # Campaña 0: genérico participativo coexiste con fought_in (militar)
    "participated in": "participated_in",
    "participó en": "participated_in",
    "tomó parte en": "participated_in",
    "was part of": "participated_in",
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
    # Campaña 0 — intellectual
    "reacted against": "reacted_against",
    "reaccionó contra": "reacted_against",
    "se opuso intelectualmente a": "reacted_against",
    "developed": "developed",
    "desarrolló": "developed",
    "elaboró": "developed",
    "extended": "extended",
    "extendió": "extended",
    "amplió": "extended",
    "synthesized": "synthesized",
    "sintetizó": "synthesized",
    "combinó": "synthesized",
    "refuted": "refuted",
    "refutó": "refuted",
    "criticized": "criticized",
    "criticó": "criticized",
    "inspired": "inspired",
    "inspiró": "inspired",
    "sirvió de inspiración a": "inspired",
    "derived from": "derived_from",
    "derivado de": "derived_from",
    "proviene de": "derived_from",
    # Campaña 0 — historical
    "belongs to period": "belongs_to_period",
    "pertenece al período": "belongs_to_period",
    "del período": "belongs_to_period",
    "contemporary of": "contemporary_of",
    "contemporáneo de": "contemporary_of",
    "contemporánea de": "contemporary_of",
    "emerged from": "emerged_from",
    "emergió de": "emerged_from",
    "surgió de": "emerged_from",
    "transformed into": "transformed_into",
    "se transformó en": "transformed_into",
    "devino en": "transformed_into",
    "ruled by": "ruled_by",
    "gobernado por": "ruled_by",
    "dirigido por": "ruled_by",
    "centered on": "centered_on",
    "centrado en": "centered_on",
    "continuation of": "continuation_of",
    "continuación de": "continuation_of",
    # Campaña 0 — religious / mythological / esoteric
    "worshipped": "worshipped",
    "adoró": "worshipped",
    "veneró": "worshipped",
    "worshipped by": "worshipped_by",
    "adorado por": "worshipped_by",
    "adorada por": "worshipped_by",
    "venerado por": "worshipped_by",
    "venerada por": "worshipped_by",
    "associated with": "associated_with",
    "asociado con": "associated_with",
    "asociada con": "associated_with",
    "symbolizes": "symbolizes",
    "simboliza": "symbolizes",
    "representa simbólicamente": "symbolizes",
    "used in": "used_in",
    "usado en": "used_in",
    "utilizado en": "used_in",
    "empleado en": "used_in",
    "practiced by": "practiced_by",
    "practicado por": "practiced_by",
    "interpreted as": "interpreted_as",
    "interpretado como": "interpreted_as",
    "interpretada como": "interpreted_as",
    "appears in": "appears_in",
    "aparece en": "appears_in",
    "figura en": "appears_in",
    # Campaña 0 — work
    "depicts": "depicts",
    "representa": "depicts",
    "retrata": "depicts",
    "describes": "describes",
    "describe": "describes",
    "argues for": "argues_for",
    "argumenta a favor de": "argues_for",
    "defiende": "argues_for",
    "argues against": "argues_against",
    "argumenta contra": "argues_against",
    "written in": "written_in",
    "escrito en": "written_in",
    "escrita en": "written_in",
    "based on": "based_on",
    "basado en": "based_on",
    "basada en": "based_on",
    # Campaña 0 — scientific
    "explains": "explains",
    "explica": "explains",
    "da cuenta de": "explains",
    "measured by": "measured_by",
    "medido por": "measured_by",
    "medida por": "measured_by",
    "studied in": "studied_in",
    "estudiado en": "studied_in",
    "estudiada en": "studied_in",
    "part of system": "part_of_system",
    "parte del sistema": "part_of_system",
    "precedes in process": "precedes_in_process",
    "precede en el proceso": "precedes_in_process",
    "depends on": "depends_on",
    "depende de": "depends_on",
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


# Spanish labels for disambiguation suffixes — human-readable in Obsidian
DISAMBIGUATION_LABELS: dict[str, str] = {
    # Entity subtypes
    "person": "persona",
    "animal": "animal",
    "plant": "planta",
    "celestial_body": "planeta",
    "civilization": "civilización",
    "deity": "dios",
    "myth": "mito",
    "symbol": "símbolo",
    "artifact": "artefacto",
    "technology": "tecnología",
    "weapon": "arma",
    "programming_language": "lenguaje",
    # Concept subtypes
    "abstract_concept": "concepto",
    "emotion": "emoción",
    "value": "valor",
    "theory": "teoría",
    "discipline": "disciplina",
    "school_of_thought": "escuela",
    "scientific_concept": "concepto científico",
    "philosophical_concept": "concepto filosófico",
    "religious_concept": "concepto religioso",
    "process": "proceso",
    "classification": "clasificación",
    "algorithm": "algoritmo",
    "metric": "métrica",
    "technical_concept": "concepto técnico",
    "architecture_pattern": "patrón",
    # Work subtypes
    "book": "libro",
    "paper": "artículo",
    "poem": "poema",
    "play": "obra",
    "artwork": "obra de arte",
    "dataset": "dataset",
    "software_project": "software",
    "case_study": "caso de estudio",
    # Event subtypes
    "war": "guerra",
    "battle": "batalla",
    "revolution": "revolución",
    "treaty": "tratado",
    "discovery": "descubrimiento",
    "historical_event": "evento",
    "phenomenon": "fenómeno",
    # Place subtypes
    "country": "país",
    "city": "ciudad",
    "region": "región",
    "empire": "imperio",
    "continent": "continente",
    "landmark": "monumento",
    "geological_feature": "formación geológica",
    "mythological_place": "lugar mítico",
    # Organization subtypes
    "company": "empresa",
    "institution": "institución",
    "government": "gobierno",
    "religion": "religión",
    "military_unit": "unidad militar",
    "academic_school": "escuela académica",
    "office_role": "cargo",
    # Entity subtypes added
    "polity": "estado",
    # Campaña 0 additions — life & language
    "organism": "organismo",
    "species": "especie",
    "anatomical_structure": "estructura anatómica",
    "language": "lengua",
    "script": "escritura",
    # Campaña 0 additions — biology / chemistry / medicine
    "biological_process": "proceso biológico",
    "cell": "célula",
    "cell_type": "tipo celular",
    "gene": "gen",
    "chemical_element": "elemento químico",
    "compound": "compuesto",
    "molecule": "molécula",
    "disease": "enfermedad",
    "medical_theory": "teoría médica",
    # Campaña 0 additions — mathematics
    "theorem": "teorema",
    "mathematical_object": "objeto matemático",
    "constant": "constante",
    "mathematical_function": "función",
    "proof_method": "método de demostración",
    "mathematical_field": "rama matemática",
    # Campaña 0 additions — esoteric
    "symbolic_system": "sistema simbólico",
    "divination_system": "sistema adivinatorio",
    "mystical_concept": "concepto místico",
    "esoteric_tradition": "tradición esotérica",
    "occult_movement": "movimiento ocultista",
    "sacred_text": "texto sagrado",
    "esoteric_text": "texto esotérico",
    # Campaña 0 additions — temporal/processual
    "historical_period": "período",
    "dynasty": "dinastía",
    "historical_process": "proceso histórico",
    "ritual": "ritual",
}


def disambiguation_label(subtype: str) -> str:
    """Return the Spanish label for a subtype, or the subtype itself as fallback."""
    return DISAMBIGUATION_LABELS.get(subtype, subtype)


def build_disambiguated_name(name: str, subtype: str) -> str:
    label = disambiguation_label(subtype)
    return f"{name} ({label})"


def needs_disambiguation(name: str, existing_types: list[str]) -> bool:
    return len(existing_types) > 1


# ============================================================================
# SECTION TEMPLATES PER SUBTYPE
# ============================================================================

_BASE_SECTIONS = ("Identity", "Key Facts", "Relationships", "Related notes")

SUBTYPE_SECTIONS: dict[str, tuple[str, ...]] = {
    # Entity subtypes
    "person": ("Identity", "Key Facts", "Timeline", "Impact", "Relationships", "Strategic Insights", "Contradictions & Uncertainties", "Frases célebres", "Related notes"),
    "animal": ("Identity", "Key Facts", "Taxonomy", "Habitat & Distribution", "Diet & Behavior", "Conservation Status", "Relationships", "Related notes"),
    "plant": ("Identity", "Key Facts", "Taxonomy", "Habitat & Distribution", "Uses", "Relationships", "Related notes"),
    "celestial_body": ("Identity", "Key Facts", "Physical Characteristics", "Orbit & Position", "Atmosphere & Composition", "Exploration", "Relationships", "Related notes"),
    "civilization": ("Identity", "Key Facts", "Timeline", "Territory", "Achievements", "Decline", "Relationships", "Related notes"),
    "polity": ("Identity", "Key Facts", "Timeline", "Territory", "Government", "Key Rulers", "Achievements", "Decline", "Relationships", "Related notes"),
    "deity": ("Identity", "Key Facts", "Mythology", "Symbolism", "Worship", "Relationships", "Related notes"),
    "myth": ("Identity", "Key Facts", "Narrative", "Characters", "Themes & Symbolism", "Cultural Impact", "Versions & Sources", "Relationships", "Related notes"),
    "symbol": ("Identity", "Key Facts", "Origin", "Meaning", "Appearances", "Cultural Impact", "Relationships", "Related notes"),
    "technology": ("Identity", "Key Facts", "How It Works", "Applications", "Impact", "Timeline", "Relationships", "Related notes"),
    "weapon": ("Identity", "Key Facts", "Design & Construction", "Tactical Use", "Historical Impact", "Decline or Replacement", "Relationships", "Related notes"),
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
    "case_study": ("Identity", "Key Facts", "Problem", "Approach", "Architecture", "Results", "Lessons Learned", "Relationships", "Related notes"),
    # Event subtypes
    "war": ("Identity", "Key Facts", "Causes", "Participants", "Timeline", "Major Battles", "Outcome", "Consequences", "Relationships", "Related notes"),
    "battle": ("Identity", "Key Facts", "Context", "Participants", "Timeline", "Outcome", "Significance", "Relationships", "Related notes"),
    "revolution": ("Identity", "Key Facts", "Causes", "Timeline", "Key Figures", "Outcome", "Legacy", "Relationships", "Related notes"),
    "discovery": ("Identity", "Key Facts", "Context", "How It Happened", "Impact", "Relationships", "Related notes"),
    "historical_event": ("Identity", "Key Facts", "Context", "Timeline", "Impact", "Relationships", "Contradictions & Uncertainties", "Related notes"),
    "phenomenon": ("Identity", "Key Facts", "What Happens", "When & Where", "Causes", "Observable Effects", "Scale & Frequency", "Significance", "Relationships", "Related notes"),
    # Concept subtypes (ML / technical)
    "algorithm": ("Definition", "Key Facts", "Intuition", "Mathematical Formulation", "Pseudocode", "Complexity", "When to Use", "Limitations", "Implementation Notes", "Relationships", "Related notes"),
    "metric": ("Definition", "Key Facts", "Formula", "Interpretation", "When to Use", "Pitfalls", "Variants", "Relationships", "Related notes"),
    "technical_concept": ("Definition", "Key Facts", "How It Works", "When to Use", "Tradeoffs", "Examples", "Relationships", "Related notes"),
    "architecture_pattern": ("Definition", "Key Facts", "Components", "Data Flow", "Tradeoffs", "When to Use", "Examples", "Relationships", "Related notes"),
    # Concept subtypes (science)
    "process": ("Definition", "Key Facts", "Stages", "Driving Forces", "Conditions", "Outcome", "Where It Occurs", "Relationships", "Related notes"),
    "classification": ("Definition", "Key Facts", "Criteria", "Categories", "Comparison Table", "Exceptions & Edge Cases", "Relationships", "Related notes"),
    # Place subtypes
    "country": ("Identity", "Key Facts", "Geography", "History", "Government", "Culture", "Relationships", "Related notes"),
    "city": ("Identity", "Key Facts", "Geography", "History", "Landmarks", "Relationships", "Related notes"),
    "empire": ("Identity", "Key Facts", "Timeline", "Territory", "Key Rulers", "Achievements", "Decline", "Relationships", "Related notes"),
    "continent": ("Identity", "Key Facts", "Geography", "Countries", "History", "Relationships", "Related notes"),
    "geological_feature": ("Identity", "Key Facts", "Formation", "Structure", "Types", "Distribution", "Geological Significance", "Relationships", "Related notes"),
    "mythological_place": ("Identity", "Key Facts", "Mythology", "Cosmological Role", "Inhabitants & Guardians", "Cultural Impact", "Relationships", "Related notes"),
    # Organization subtypes
    "company": ("Identity", "Key Facts", "Founded", "Products & Services", "Leadership", "Impact", "Relationships", "Related notes"),
    "institution": ("Identity", "Key Facts", "Founded", "Mission", "Structure", "Impact", "Relationships", "Related notes"),
    "religion": ("Identity", "Key Facts", "Origins", "Core Beliefs", "Practices", "Sacred Texts", "Denominations", "Relationships", "Related notes"),
    "office_role": ("Identity", "Key Facts", "Origins", "Powers & Duties", "Requirements", "Notable Holders", "Evolution", "Relationships", "Related notes"),
    # Disambiguation
    "disambiguation_page": ("Disambiguation", "Related notes"),
    # Campaña 0 — life & language (entity)
    "organism": ("Identity", "Key Facts", "Taxonomy", "Anatomy & Physiology", "Habitat & Distribution", "Behavior", "Evolution", "Relationships", "Related notes"),
    "species": ("Identity", "Key Facts", "Taxonomy", "Habitat & Distribution", "Behavior", "Evolution", "Conservation Status", "Relationships", "Related notes"),
    "anatomical_structure": ("Identity", "Key Facts", "Anatomy", "Function", "Location in Body", "Related Structures", "Clinical Relevance", "Relationships", "Related notes"),
    "language": ("Identity", "Key Facts", "Family & Origins", "Geographic Distribution", "Grammar & Structure", "Script", "Historical Development", "Relationships", "Related notes"),
    "script": ("Identity", "Key Facts", "Origins", "Structure", "Languages Used", "Decipherment", "Historical Impact", "Relationships", "Related notes"),
    # Campaña 0 — biology / chemistry / medicine (concept)
    "biological_process": ("Definition", "Key Facts", "Stages", "Molecules Involved", "Where It Occurs", "Regulation", "Significance", "Relationships", "Related notes"),
    "cell": ("Definition", "Key Facts", "Structure", "Organelles", "Function", "Types", "Relationships", "Related notes"),
    "cell_type": ("Definition", "Key Facts", "Structure", "Function", "Location in Organism", "Lifecycle", "Relationships", "Related notes"),
    "gene": ("Definition", "Key Facts", "Location", "Function", "Associated Phenotypes", "Mutations", "Evolution", "Relationships", "Related notes"),
    "chemical_element": ("Definition", "Key Facts", "Atomic Properties", "Isotopes", "Occurrence", "Uses", "Discovery", "Relationships", "Related notes"),
    "compound": ("Definition", "Key Facts", "Structure", "Properties", "Reactions", "Uses", "Relationships", "Related notes"),
    "molecule": ("Definition", "Key Facts", "Structure", "Properties", "Biological Role", "Synthesis", "Relationships", "Related notes"),
    "disease": ("Definition", "Key Facts", "Causes", "Symptoms", "Diagnosis", "Treatment", "Epidemiology", "Relationships", "Related notes"),
    "medical_theory": ("Definition", "Key Facts", "Origins", "Core Principles", "Evidence", "Criticisms", "Impact", "Relationships", "Related notes"),
    # Campaña 0 — mathematics (concept)
    "theorem": ("Definition", "Key Facts", "Statement", "Historical Context", "Proof Sketch", "Consequences", "Generalizations", "Relationships", "Related notes"),
    "mathematical_object": ("Definition", "Key Facts", "Formal Definition", "Properties", "Examples", "Operations", "Relationships", "Related notes"),
    "constant": ("Definition", "Key Facts", "Value", "Mathematical Significance", "Appearances", "History", "Relationships", "Related notes"),
    "mathematical_function": ("Definition", "Key Facts", "Formula", "Domain & Range", "Properties", "Applications", "Relationships", "Related notes"),
    "proof_method": ("Definition", "Key Facts", "How It Works", "Classic Examples", "When to Use", "Limitations", "Relationships", "Related notes"),
    "mathematical_field": ("Definition", "Key Facts", "Scope", "Core Objects", "Key Theorems", "Subfields", "Key Figures", "Relationships", "Related notes"),
    # Campaña 0 — esoteric (concept / organization / work)
    "symbolic_system": ("Definition", "Key Facts", "Origins", "Structure", "Core Symbols", "Interpretation", "Uses", "Relationships", "Related notes"),
    "divination_system": ("Definition", "Key Facts", "Origins", "Tools & Methods", "Structure", "Interpretation", "Cultural Context", "Relationships", "Related notes"),
    "mystical_concept": ("Definition", "Key Facts", "Origins", "Interpretations", "Traditions Using It", "Relationships", "Related notes"),
    "esoteric_tradition": ("Identity", "Key Facts", "Origins", "Historical Context", "Core Beliefs", "Key Figures", "Principal Texts", "Main Practices", "Core Symbols", "Influence", "Relationships", "Related notes"),
    "occult_movement": ("Identity", "Key Facts", "Founded", "Core Figures", "Beliefs & Practices", "Publications", "Influence", "Relationships", "Related notes"),
    "sacred_text": ("Identity", "Key Facts", "Tradition", "Authorship", "Composition & Date", "Structure", "Core Teachings", "Interpretations", "Influence", "Relationships", "Related notes"),
    "esoteric_text": ("Identity", "Key Facts", "Tradition", "Authorship", "Date", "Core Teachings", "Symbolism", "Influence", "Relationships", "Related notes"),
    # Campaña 0 — temporal / processual (event)
    "historical_period": ("Identity", "Key Facts", "Timeline", "Region", "Defining Traits", "Key Figures", "Major Events", "Transition In", "Transition Out", "Relationships", "Related notes"),
    "dynasty": ("Identity", "Key Facts", "Timeline", "Territory", "Rulers", "Achievements", "Decline", "Relationships", "Related notes"),
    "historical_process": ("Identity", "Key Facts", "Scope & Duration", "Driving Forces", "Stages", "Actors & Agents", "Outcomes", "Relationships", "Related notes"),
    "ritual": ("Identity", "Key Facts", "Tradition", "Purpose", "Participants", "Sequence", "Symbols & Tools", "Historical Context", "Relationships", "Related notes"),
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
        "In Contradictions, note disputed facts, uncertain dates, conflicting sources. "
        "In Frases célebres, each quote as blockquote with context, date, theme, source, and reliability. "
        "Use ^quote-slug block IDs for cross-referencing from thematic collections. "
        "Format: > \"Quote\" / > — Context, date / tema:: X / fuente:: Y / confiabilidad:: alta|media|baja|apócrifa"
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
    "weapon": (
        "In Design & Construction, describe materials, dimensions, weight, and manufacturing. "
        "In Tactical Use, explain formation, training requirements, and combat role. "
        "In Historical Impact, describe how this weapon changed warfare. "
        "In Decline or Replacement, explain what superseded it and why."
    ),
    "mythological_place": (
        "In Mythology, narrate the key myths associated with this place and cite sources. "
        "In Cosmological Role, explain where it sits in the mythological geography. "
        "In Inhabitants & Guardians, name beings associated with this place. "
        "In Cultural Impact, explain how this place influenced literature, art, or language."
    ),
    "process": (
        "In Stages, describe step-by-step with triggers, durations, and what changes at each step. "
        "In Driving Forces, explain what causes and sustains the process. "
        "In Conditions, specify what must be true for the process to occur. "
        "In Outcome, describe what the process produces or transforms. "
        "Include temporal scale (seconds? millions of years?) and spatial scale."
    ),
    "phenomenon": (
        "In What Happens, describe the phenomenon as if explaining to someone who has never seen it. "
        "In Causes, link to underlying processes and concepts with [[wikilinks]]. "
        "In Observable Effects, describe what you can actually see or measure. "
        "In Scale & Frequency, state how often it occurs and at what magnitude."
    ),
    "classification": (
        "In Criteria, explain what properties are used to classify. "
        "In Categories, list each type with 1-2 sentence description. "
        "In Comparison Table, use a markdown table comparing key properties across types. "
        "In Exceptions, note items that don't fit cleanly into categories."
    ),
    "geological_feature": (
        "In Formation, explain the geological process that creates this feature. "
        "In Structure, describe internal composition and layers if applicable. "
        "In Types, distinguish subtypes with examples (e.g., shield vs stratovolcano). "
        "In Distribution, describe where on Earth (or other planets) this feature is found."
    ),
    "algorithm": (
        "In Intuition, explain the core idea in plain language before any math. "
        "In Mathematical Formulation, give the formal definition with variable explanations. "
        "In Pseudocode, provide clear step-by-step pseudocode. "
        "In Complexity, state time and space complexity with Big-O notation. "
        "In When to Use, list concrete scenarios and data characteristics where this algorithm excels. "
        "In Limitations, be specific about failure modes and edge cases. "
        "In Implementation Notes, mention practical tips, common libraries, and hyperparameters."
    ),
    "metric": (
        "In Formula, give the mathematical formula with variable definitions. "
        "In Interpretation, explain what values mean — what is good, bad, or suspicious. "
        "In When to Use, specify which tasks, datasets, and evaluation contexts fit this metric. "
        "In Pitfalls, describe common misinterpretations and gaming scenarios. "
        "In Variants, list related metrics and how they differ (e.g., micro vs macro averaging)."
    ),
    "technical_concept": (
        "In How It Works, explain the mechanism or technique step by step. "
        "In When to Use, describe practical scenarios where this concept applies. "
        "In Tradeoffs, cover pros, cons, and alternatives. "
        "In Examples, give concrete instances from real systems or well-known applications."
    ),
    "architecture_pattern": (
        "In Components, list each component with its role and responsibilities. "
        "In Data Flow, describe how data moves through the system end to end. "
        "In Tradeoffs, cover latency, throughput, complexity, and cost considerations. "
        "In When to Use, specify scale requirements and problem characteristics. "
        "In Examples, reference real-world systems or papers that use this pattern."
    ),
    "case_study": (
        "In Problem, describe the real-world problem being solved with specific constraints. "
        "In Approach, explain the chosen strategy and why alternatives were rejected. "
        "In Architecture, describe the system design with components and data flow. "
        "In Results, include concrete outcomes — metrics, performance, lessons. "
        "In Lessons Learned, capture what you would do differently and reusable insights."
    ),
    # Campaña 0 guides — temporal/processual
    "historical_period": (
        "A period is a bounded stretch of time with defining traits, not a single event. "
        "In Timeline, give start/end dates with the criteria that mark the boundaries. "
        "In Defining Traits, describe what makes this period cohesive (political system, art, economy). "
        "In Key Figures, name the people who embody or shape the period. "
        "In Transition In / Transition Out, explain what came before and after, and why the change happened. "
        "Distinguish period from dynasty (political lineage) and from process (extended transformation)."
    ),
    "dynasty": (
        "A dynasty is a line of rulers from one family or house. "
        "In Timeline, give founding and end dates with key transitions. "
        "In Rulers, list each ruler with reign dates and their contribution or failure. "
        "In Achievements, cover administrative, cultural, and territorial legacies. "
        "In Decline, analyze why the dynasty lost power — structural, external, or personal causes. "
        "Distinguish from historical_period: a dynasty can span one period or several."
    ),
    "historical_process": (
        "A historical process is a structural transformation that unfolds over years or centuries. "
        "Examples: romanización, feudalización, cristianización, industrialización. "
        "In Scope & Duration, define where and when the process operates. "
        "In Driving Forces, explain what powers the process (demographic, economic, ideological, technological). "
        "In Stages, describe the phases with characteristic features of each. "
        "In Actors & Agents, name who drove it and who resisted. "
        "In Outcomes, describe what the world looks like after the process has worked through. "
        "Distinguish from historical_event (punctual) and historical_period (bounded time)."
    ),
    "ritual": (
        "A ritual is a structured practice with symbolic or sacred intent. "
        "In Tradition, name the religious, esoteric, or cultural system it belongs to. "
        "In Purpose, explain what the ritual is meant to accomplish (transformation, commemoration, appeasement). "
        "In Sequence, describe the steps in order. "
        "In Symbols & Tools, list what is used and what it represents. "
        "Distinguish ritual from ceremony: rituals carry symbolic weight beyond the occasion."
    ),
    # Campaña 0 guides — biology
    "organism": (
        "An organism entity covers a named individual or a taxonomically identified being treated as one case. "
        "In Taxonomy, give the full lineage: domain, kingdom, phylum, class, order, family, genus, species. "
        "In Evolution, place the organism in evolutionary context with approximate divergence dates. "
        "Prefer species for species-level biology; reserve organism for famous named individuals (Bucéfalo, Dolly)."
    ),
    "species": (
        "A species entity covers an entire biological species. "
        "In Taxonomy, give the full Linnaean classification. "
        "In Habitat & Distribution, describe where the species lives and historical range changes. "
        "In Evolution, name closest relatives and divergence estimates. "
        "In Conservation Status, use IUCN categories if relevant."
    ),
    "biological_process": (
        "Describe the process as a sequence, not a snapshot. "
        "In Stages, enumerate steps with inputs and outputs. "
        "In Molecules Involved, name key enzymes, substrates, and products with [[wikilinks]]. "
        "In Where It Occurs, specify organelle, tissue, organism level. "
        "In Regulation, explain what speeds it up, slows it down, or conditions it."
    ),
    "gene": (
        "In Location, give chromosome and cytogenetic band if known. "
        "In Function, describe the protein product and its role in biology. "
        "In Associated Phenotypes, describe known traits, diseases, or variations. "
        "In Evolution, name orthologs and conservation across species."
    ),
    # Campaña 0 guides — chemistry
    "chemical_element": (
        "In Atomic Properties, give atomic number, mass, electron configuration, electronegativity. "
        "In Isotopes, list stable and notable unstable isotopes. "
        "In Occurrence, describe natural abundance (crustal, biological, cosmic). "
        "In Uses, cover industrial, biological, and symbolic/historical uses. "
        "In Discovery, name discoverer and date if known."
    ),
    "compound": (
        "In Structure, describe molecular structure and bonding. "
        "In Properties, cover melting/boiling points, solubility, reactivity. "
        "In Reactions, name characteristic reactions with equations if helpful. "
        "In Uses, cover practical, biological, and industrial applications."
    ),
    "molecule": (
        "In Structure, describe the 3D shape and bonding pattern. "
        "In Biological Role, explain where and how it functions in living systems. "
        "In Synthesis, describe how it forms naturally or industrially."
    ),
    # Campaña 0 guides — medicine
    "disease": (
        "In Causes, cover genetic, infectious, environmental, and idiopathic causes as applicable. "
        "In Symptoms, list typical presentation and variations. "
        "In Diagnosis, describe clinical criteria and key tests. "
        "In Treatment, cover current standard of care and prognosis. "
        "In Epidemiology, include prevalence, geography, and demographics."
    ),
    # Campaña 0 guides — mathematics
    "theorem": (
        "In Statement, give the formal mathematical statement with variables defined. "
        "In Historical Context, name who proved it, when, and why it mattered. "
        "In Proof Sketch, outline the key ideas without full rigor. "
        "In Consequences, explain what becomes provable or computable because of it. "
        "In Generalizations, point to extensions, weakenings, or related theorems."
    ),
    "mathematical_object": (
        "In Formal Definition, give the axiomatic or constructive definition. "
        "In Properties, list the characteristic properties that identify this object. "
        "In Examples, give concrete instances and edge cases. "
        "In Operations, describe what operations are defined on the object."
    ),
    "constant": (
        "In Value, give the numerical value and precision. "
        "In Mathematical Significance, explain what makes the constant important. "
        "In Appearances, list key formulas and phenomena where it shows up. "
        "In History, name who discovered or first used the constant."
    ),
    "mathematical_field": (
        "In Scope, describe what kinds of questions this field answers. "
        "In Core Objects, name the central objects of study. "
        "In Key Theorems, link to major theorems with [[wikilinks]]. "
        "In Subfields, give a structured breakdown of the subareas. "
        "In Key Figures, name major contributors across eras."
    ),
    # Campaña 0 guides — language
    "language": (
        "In Family & Origins, give the language family and closest relatives. "
        "In Geographic Distribution, describe where it is (or was) spoken. "
        "In Grammar & Structure, cover writing system, phonology, syntax features that are distinctive. "
        "In Historical Development, outline major stages and shifts."
    ),
    "script": (
        "In Origins, describe when and where the script emerged. "
        "In Structure, describe whether it is alphabetic, syllabic, logographic, etc., and direction. "
        "In Languages Used, list languages historically written with the script. "
        "In Decipherment, if applicable, explain how the script was decoded and by whom."
    ),
    # Campaña 0 guides — esoteric
    "esoteric_tradition": (
        "An esoteric tradition is a structured body of symbolic, ritual, and philosophical practice. "
        "In Historical Context, place the tradition in time and relation to religion and science of its era. "
        "In Core Beliefs, describe cosmology and soteriology in neutral language. "
        "In Principal Texts, list foundational works with authors and dates. "
        "In Influence, cover impact on philosophy, art, science, or other traditions. "
        "ALWAYS set epistemic_mode to 'esoteric' and state certainty_level explicitly."
    ),
    "occult_movement": (
        "In Founded, give date and founders with biographical context. "
        "In Beliefs & Practices, describe the distinctive doctrine and ritual system. "
        "In Publications, list key books and their reception. "
        "In Influence, cover who inherited or reacted against the movement. "
        "ALWAYS set epistemic_mode to 'esoteric'."
    ),
    "sacred_text": (
        "In Tradition, name the religion or community that treats the text as sacred. "
        "In Authorship, cover traditional attribution vs. scholarly consensus. "
        "In Composition & Date, give layered dating if the text was assembled over time. "
        "In Structure, describe the organization (books, chapters, sutras, etc.). "
        "In Core Teachings, summarize without endorsing or rejecting. "
        "In Interpretations, cover major hermeneutic traditions."
    ),
    "esoteric_text": (
        "In Tradition, name the esoteric school or current the text belongs to. "
        "In Authorship, note if the text is pseudepigraphic (attributed to a legendary figure). "
        "In Symbolism, describe the key symbols and their standard interpretations. "
        "In Influence, cover downstream esoteric and non-esoteric reception. "
        "ALWAYS mark epistemic_mode and certainty_level."
    ),
    "symbolic_system": (
        "In Structure, describe how the system's elements relate (tree, cycle, hierarchy, grid). "
        "In Core Symbols, enumerate the principal symbols with their conventional meanings. "
        "In Interpretation, describe the hermeneutic rules for reading the system. "
        "In Uses, cover divinatory, meditative, ritual, or philosophical uses."
    ),
    "divination_system": (
        "In Tools & Methods, describe what is cast, drawn, or observed and how. "
        "In Interpretation, explain how results are read and contextualized. "
        "In Cultural Context, place the system in its originating tradition and any later adoption."
    ),
    "mystical_concept": (
        "In Interpretations, cover multiple traditions' readings (Jewish mysticism, Sufism, Christian mystics, etc., as applicable). "
        "In Traditions Using It, name the schools that develop the concept and how they differ."
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
    "DISAMBIGUATION_LABELS",
    "build_disambiguated_name",
    "detect_role",
    "disambiguation_label",
    "get_writing_guide",
    "needs_disambiguation",
    "normalize_predicate",
    "resolve_object_kind",
    "sections_for_subtype",
    "should_promote_to_candidate",
    "should_promote_to_canonical",
]
