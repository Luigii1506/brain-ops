"""Coverage check — detect what's in the raw source but missing from the note."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .chunking import ContentChunk, chunk_by_headings


@dataclass(slots=True, frozen=True)
class CoverageGap:
    heading: str
    char_count: int
    sample: str
    priority: str  # "high", "medium", "low"

    def to_dict(self) -> dict[str, object]:
        return {
            "heading": self.heading,
            "char_count": self.char_count,
            "sample": self.sample,
            "priority": self.priority,
        }


@dataclass(slots=True, frozen=True)
class CoverageReport:
    entity_name: str
    raw_headings: int
    covered_headings: int
    gaps: list[CoverageGap]
    coverage_pct: float
    needs_second_pass: bool
    mode: str  # "deep" or "light"

    def to_dict(self) -> dict[str, object]:
        return {
            "entity_name": self.entity_name,
            "raw_headings": self.raw_headings,
            "covered_headings": self.covered_headings,
            "coverage_pct": round(self.coverage_pct, 1),
            "needs_second_pass": self.needs_second_pass,
            "mode": self.mode,
            "gaps": [g.to_dict() for g in self.gaps],
            "high_gaps": len([g for g in self.gaps if g.priority == "high"]),
            "medium_gaps": len([g for g in self.gaps if g.priority == "medium"]),
        }


# ============================================================================
# PRIORITY CLASSIFICATION
# ============================================================================

HIGH_PRIORITY_KEYWORDS: dict[str, list[str]] = {
    "person": ["nacimiento", "birth", "infancia", "childhood", "muerte", "death",
               "reinado", "reign", "campañas", "campaigns", "conquista", "conquest",
               "legado", "legacy", "educación", "education", "ascenso", "rise",
               "exilio", "exile", "asesinato", "assassination", "batalla", "battle",
               "egipto", "egypt", "india", "persia", "últimos años", "conspiración",
               "sitio", "siege", "ocupación", "fundación"],
    "empire": ["fundación", "founding", "caída", "fall", "expansión", "expansion",
               "gobierno", "government", "territorio", "territory", "declive", "decline",
               "conquista", "conquest", "economía", "economy", "administración"],
    "battle": ["antecedentes", "background", "desarrollo", "development",
               "consecuencias", "consequences", "fuerzas", "forces", "estrategia",
               "persecución", "ocupación"],
    "civilization": ["gobierno", "government", "cultura", "culture", "religión", "religion",
                     "economía", "economy", "arte", "art", "ciencia", "science", "filosofía",
                     "guerras", "wars"],
    "book": ["resumen", "summary", "temas", "themes", "personajes", "characters",
             "autor", "author", "influencia", "influence", "ideas"],
}

LOW_PRIORITY_KEYWORDS = [
    "véase", "referencias", "bibliografía", "enlaces", "notas", "fuentes",
    "see also", "references", "bibliography", "links", "notes", "sources",
    "bustos", "monumentos", "monedas", "pinturas", "música",
    "categorías", "wikipedia", "isbn", "texto griego", "texto francés",
    "bibliografía adicional", "obras modernas", "fuentes clásicas",
]

DEEP_MODE_SUBTYPES = {
    "person", "empire", "civilization", "battle", "war", "country", "book",
    "discipline", "school_of_thought", "deity", "revolution", "historical_event",
}

MIN_SIGNIFICANT_CHARS = 200


def should_use_deep_mode(entity_subtype: str, raw_length: int) -> bool:
    """Determine if this entity needs deep coverage check."""
    if entity_subtype in DEEP_MODE_SUBTYPES:
        return True
    if raw_length > 20000:
        return True
    return False


def classify_section_priority(heading: str, char_count: int, entity_subtype: str) -> str:
    """Classify a section as high, medium, or low priority."""
    heading_lower = heading.lower()

    # Low priority: references, bibliography, metadata
    for kw in LOW_PRIORITY_KEYWORDS:
        if kw in heading_lower:
            return "low"

    # High priority: matches subtype keywords
    priority_keywords = HIGH_PRIORITY_KEYWORDS.get(entity_subtype, [])
    for kw in priority_keywords:
        if kw in heading_lower:
            return "high"

    # Large sections are at least medium
    if char_count >= 800:
        return "medium"

    # Small sections with no keyword match
    if char_count < 300:
        return "low"

    return "medium"


# ============================================================================
# COVERAGE CHECK
# ============================================================================

def check_coverage(
    entity_name: str,
    entity_subtype: str,
    raw_text: str,
    note_body: str,
) -> CoverageReport:
    """Check what headings from the raw source are missing from the note."""
    raw_chunks = chunk_by_headings(raw_text)
    note_lower = note_body.lower()
    mode = "deep" if should_use_deep_mode(entity_subtype, len(raw_text)) else "light"

    gaps: list[CoverageGap] = []
    covered = 0
    total_significant = 0

    for chunk in raw_chunks:
        if chunk.char_count < MIN_SIGNIFICANT_CHARS:
            continue

        priority = classify_section_priority(chunk.heading, chunk.char_count, entity_subtype)

        # Skip low priority in both modes
        if priority == "low":
            continue

        # In light mode, skip medium too
        if mode == "light" and priority == "medium":
            continue

        total_significant += 1

        # Check if this section's content is represented in the note
        key_phrases = _extract_key_phrases(chunk.text)
        matches = sum(1 for phrase in key_phrases if phrase in note_lower)
        coverage_ratio = matches / max(len(key_phrases), 1)

        if coverage_ratio >= 0.3:
            covered += 1
            continue

        gaps.append(CoverageGap(
            heading=chunk.heading,
            char_count=chunk.char_count,
            sample=chunk.text[:150].strip(),
            priority=priority,
        ))

    coverage_pct = (covered / total_significant * 100) if total_significant > 0 else 100.0
    high_gaps = [g for g in gaps if g.priority == "high"]
    needs_second_pass = len(high_gaps) >= 2 or (mode == "deep" and coverage_pct < 40)

    # Sort: high first, then by char_count
    gaps.sort(key=lambda g: (0 if g.priority == "high" else 1, -g.char_count))

    return CoverageReport(
        entity_name=entity_name,
        raw_headings=total_significant,
        covered_headings=covered,
        gaps=gaps,
        coverage_pct=coverage_pct,
        needs_second_pass=needs_second_pass,
        mode=mode,
    )


def _extract_key_phrases(text: str, max_phrases: int = 10) -> list[str]:
    """Extract key phrases from text for coverage matching."""
    sentences = re.split(r"[.!?]\s+", text[:2000])
    phrases: list[str] = []
    for sentence in sentences:
        words = sentence.lower().split()
        if len(words) >= 4:
            phrase = " ".join(words[1:4])
            if len(phrase) >= 10:
                phrases.append(phrase)
        if len(phrases) >= max_phrases:
            break
    return phrases


__all__ = [
    "CoverageGap",
    "CoverageReport",
    "DEEP_MODE_SUBTYPES",
    "check_coverage",
    "classify_section_priority",
    "should_use_deep_mode",
]
