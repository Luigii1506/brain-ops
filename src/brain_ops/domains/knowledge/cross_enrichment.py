"""Cross-enrichment — detect and apply knowledge from one entity to related entities."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass(slots=True, frozen=True)
class CrossEnrichmentCandidate:
    source_entity: str
    target_entity: str
    content_type: str  # "fact", "insight", "relationship", "timeline"
    text: str
    target_section: str
    confidence: float
    review_level: str  # "auto", "review", "manual"

    def to_dict(self) -> dict[str, object]:
        return {
            "source_entity": self.source_entity,
            "target_entity": self.target_entity,
            "content_type": self.content_type,
            "text": self.text,
            "target_section": self.target_section,
            "confidence": self.confidence,
            "review_level": self.review_level,
        }


# Rules for what content type goes to what section
CONTENT_TYPE_SECTION_MAP: dict[str, str] = {
    "fact": "Key Facts",
    "insight": "Strategic Insights",
    "relationship": "Relationships",
    "timeline": "Timeline",
    "contradiction": "Contradictions & Uncertainties",
}

# Confidence thresholds for auto-apply
AUTO_APPLY_THRESHOLD = 0.75
REVIEW_THRESHOLD = 0.5


def _extract_wikilinks(text: str) -> set[str]:
    return set(re.findall(r"\[\[([^\]]+)(?:\|[^\]]+)?\]\]", text))


def _classify_content_type(text: str) -> tuple[str, str]:
    """Classify a piece of text as fact, insight, relationship, timeline, or contradiction."""
    lowered = text.lower()

    # Timeline: has a date pattern
    if re.search(r"\d{3,4}\s*a\.?\s*[cC]\.?|\d{4}", text):
        if any(kw in lowered for kw in ["batalla", "battle", "murió", "died", "nació", "born", "fundó", "founded"]):
            return "timeline", "Timeline"

    # Relationship: mentions a clear connection
    if " — " in text or "→" in text:
        return "relationship", "Relationships"

    # Contradiction: uncertainty language
    if any(kw in lowered for kw in ["debatido", "disputed", "incierto", "uncertain", "contradict", "cuestion"]):
        return "contradiction", "Contradictions & Uncertainties"

    # Insight: analytical/strategic language
    if any(kw in lowered for kw in ["estrateg", "strateg", "demuestra", "shows", "sugiere", "suggests", "implica", "implies", "patrón", "pattern", "lección", "lesson"]):
        return "insight", "Strategic Insights"

    # Default: fact
    return "fact", "Key Facts"


def _relevance_score(text: str, target_entity: str) -> float:
    """Score how relevant a piece of text is to the target entity."""
    score = 0.0
    lowered = text.lower()
    target_lower = target_entity.lower()

    # Direct mention of target entity
    if target_lower in lowered:
        score += 0.5

    # Wikilink to target
    if f"[[{target_entity}]]" in text:
        score += 0.3

    # Action verbs about the target
    if any(f"{target_lower} {verb}" in lowered for verb in ["fue", "era", "hizo", "decidió", "ordenó", "rechazó", "lloró", "ejecutó", "trató", "conquistó"]):
        score += 0.2

    # Length penalty for very short items
    if len(text) < 20:
        score -= 0.2

    return min(max(score, 0.0), 1.0)


def _is_redundant(text: str, existing_content: str) -> bool:
    """Check if the text is already present or very similar to existing content."""
    text_lower = text.lower().strip()
    if len(text_lower) < 10:
        return True

    # Check for exact substring
    if text_lower in existing_content.lower():
        return True

    # Check for high word overlap
    text_words = set(text_lower.split())
    existing_words = set(existing_content.lower().split())
    if len(text_words) > 3:
        overlap = len(text_words & existing_words) / len(text_words)
        if overlap > 0.8:
            return True

    return False


def detect_cross_enrichment_candidates(
    source_entity: str,
    source_body: str,
    target_entity: str,
    target_body: str,
) -> list[CrossEnrichmentCandidate]:
    """Detect potential cross-enrichment candidates from source to target entity."""
    candidates: list[CrossEnrichmentCandidate] = []

    # Extract all content lines that mention the target entity
    for line in source_body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("## ") or stripped.startswith(">"):
            continue
        if stripped.startswith("---"):
            continue

        # Check if this line is relevant to the target entity
        relevance = _relevance_score(stripped, target_entity)
        if relevance < 0.3:
            continue

        # Check if it's redundant with existing content
        if _is_redundant(stripped, target_body):
            continue

        # Classify the content
        content_type, target_section = _classify_content_type(stripped)

        # Determine review level based on confidence
        confidence = relevance
        if content_type == "fact" and confidence >= AUTO_APPLY_THRESHOLD:
            review_level = "auto"
        elif content_type == "relationship" and confidence >= AUTO_APPLY_THRESHOLD:
            review_level = "auto"
        elif confidence >= REVIEW_THRESHOLD:
            review_level = "review"
        else:
            review_level = "manual"

        # Clean the text for the target context
        clean_text = stripped.lstrip("- ")

        candidates.append(CrossEnrichmentCandidate(
            source_entity=source_entity,
            target_entity=target_entity,
            content_type=content_type,
            text=clean_text,
            target_section=target_section,
            confidence=confidence,
            review_level=review_level,
        ))

    return candidates


def apply_cross_enrichment(
    target_body: str,
    candidates: list[CrossEnrichmentCandidate],
    *,
    auto_only: bool = True,
) -> tuple[str, list[CrossEnrichmentCandidate]]:
    """Apply cross-enrichment candidates to a target entity body. Returns updated body and applied candidates."""
    applied: list[CrossEnrichmentCandidate] = []

    for candidate in candidates:
        if auto_only and candidate.review_level != "auto":
            continue

        section_marker = f"## {candidate.target_section}"
        idx = target_body.find(section_marker)
        if idx == -1:
            continue

        # Find the end of this section
        after = target_body[idx + len(section_marker):]
        next_section = after.find("\n## ")
        if next_section > 0:
            section_end = idx + len(section_marker) + next_section
        else:
            section_end = len(target_body)

        # Add the new content as a bullet point at the end of the section
        insert_point = section_end
        new_line = f"\n- {candidate.text} *(cross-enriched from [[{candidate.source_entity}]])*"
        target_body = target_body[:insert_point] + new_line + target_body[insert_point:]
        applied.append(candidate)

    return target_body, applied


def save_cross_enrichment_log(
    log_dir: Path,
    source_entity: str,
    candidates: list[CrossEnrichmentCandidate],
    applied: list[CrossEnrichmentCandidate],
) -> Path:
    """Save cross-enrichment results for auditing."""
    log_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    slug = "".join(c if c.isalnum() or c in "-_ " else "" for c in source_entity)[:40].strip().replace(" ", "-").lower()
    filename = f"{now.strftime('%Y%m%d-%H%M%S')}-{slug}.json"
    path = log_dir / filename
    path.write_text(
        json.dumps({
            "source_entity": source_entity,
            "timestamp": now.isoformat(),
            "total_candidates": len(candidates),
            "total_applied": len(applied),
            "candidates": [c.to_dict() for c in candidates],
            "applied": [a.to_dict() for a in applied],
        }, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


__all__ = [
    "AUTO_APPLY_THRESHOLD",
    "CrossEnrichmentCandidate",
    "REVIEW_THRESHOLD",
    "apply_cross_enrichment",
    "detect_cross_enrichment_candidates",
    "save_cross_enrichment_log",
]
