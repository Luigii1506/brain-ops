"""Coverage check — detect what's in the raw source but missing from the note."""

from __future__ import annotations

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

    def to_dict(self) -> dict[str, object]:
        return {
            "entity_name": self.entity_name,
            "raw_headings": self.raw_headings,
            "covered_headings": self.covered_headings,
            "coverage_pct": round(self.coverage_pct, 1),
            "needs_second_pass": self.needs_second_pass,
            "gaps": [g.to_dict() for g in self.gaps],
        }


# Keywords that indicate high-priority content per subtype
HIGH_PRIORITY_KEYWORDS: dict[str, list[str]] = {
    "person": ["juventud", "youth", "nacimiento", "birth", "muerte", "death",
               "reinado", "reign", "campañas", "campaigns", "legado", "legacy",
               "educación", "education", "matrimonio", "marriage", "asesinato",
               "assassination", "exilio", "exile", "conquista", "conquest"],
    "empire": ["fundación", "founding", "caída", "fall", "expansión", "expansion",
               "gobierno", "government", "territorio", "territory", "economía", "economy"],
    "battle": ["antecedentes", "background", "desarrollo", "development",
               "consecuencias", "consequences", "fuerzas", "forces"],
    "civilization": ["gobierno", "government", "cultura", "culture", "religión", "religion",
                     "economía", "economy", "arte", "art", "ciencia", "science"],
    "book": ["resumen", "summary", "temas", "themes", "personajes", "characters",
             "autor", "author", "influencia", "influence"],
}

# Minimum chars for a heading to be considered significant
MIN_SIGNIFICANT_CHARS = 200


def check_coverage(
    entity_name: str,
    entity_subtype: str,
    raw_text: str,
    note_body: str,
) -> CoverageReport:
    """Check what headings from the raw source are missing from the note."""
    raw_chunks = chunk_by_headings(raw_text)
    note_lower = note_body.lower()

    priority_keywords = HIGH_PRIORITY_KEYWORDS.get(entity_subtype, [])

    gaps: list[CoverageGap] = []
    covered = 0

    for chunk in raw_chunks:
        if chunk.char_count < MIN_SIGNIFICANT_CHARS:
            continue

        heading_lower = chunk.heading.lower()

        # Check if this heading's content is represented in the note
        # Simple heuristic: check if key phrases from the chunk appear in the note
        key_phrases = _extract_key_phrases(chunk.text)
        matches = sum(1 for phrase in key_phrases if phrase in note_lower)
        coverage_ratio = matches / max(len(key_phrases), 1)

        if coverage_ratio >= 0.3:
            covered += 1
            continue

        # This heading is not well covered — is it important?
        is_high_priority = any(kw in heading_lower for kw in priority_keywords)
        priority = "high" if is_high_priority else "medium" if chunk.char_count > 500 else "low"

        gaps.append(CoverageGap(
            heading=chunk.heading,
            char_count=chunk.char_count,
            sample=chunk.text[:150].strip(),
            priority=priority,
        ))

    significant_chunks = [c for c in raw_chunks if c.char_count >= MIN_SIGNIFICANT_CHARS]
    total = len(significant_chunks)
    coverage_pct = (covered / total * 100) if total > 0 else 100.0

    high_gaps = [g for g in gaps if g.priority == "high"]
    needs_second_pass = len(high_gaps) >= 2 or coverage_pct < 50

    return CoverageReport(
        entity_name=entity_name,
        raw_headings=total,
        covered_headings=covered,
        gaps=gaps,
        coverage_pct=coverage_pct,
        needs_second_pass=needs_second_pass,
    )


def _extract_key_phrases(text: str, max_phrases: int = 10) -> list[str]:
    """Extract key phrases from text for coverage matching."""
    import re
    sentences = re.split(r"[.!?]\s+", text[:2000])
    phrases: list[str] = []
    for sentence in sentences:
        words = sentence.lower().split()
        if len(words) >= 4:
            # Take 3-4 word sequences as key phrases
            phrase = " ".join(words[1:4])
            if len(phrase) >= 10:
                phrases.append(phrase)
        if len(phrases) >= max_phrases:
            break
    return phrases


__all__ = [
    "CoverageGap",
    "CoverageReport",
    "check_coverage",
]
