"""Evidence policy — confidence scoring and knowledge quality rules by source type."""

from __future__ import annotations

from dataclasses import dataclass


# ============================================================================
# CONFIDENCE SCORING BY SOURCE TYPE
# ============================================================================

SOURCE_CONFIDENCE: dict[str, float] = {
    "encyclopedia": 0.9,
    "research_paper": 0.85,
    "documentation": 0.85,
    "article": 0.6,
    "tutorial": 0.6,
    "news": 0.5,
    "notes": 0.4,
    "thread": 0.3,
}

# What each source type is good for
SOURCE_STRENGTHS: dict[str, list[str]] = {
    "encyclopedia": ["facts", "identity", "timeline", "relationships"],
    "research_paper": ["findings", "methodology", "contributions", "evidence"],
    "documentation": ["concepts", "architecture", "usage", "components"],
    "article": ["insights", "arguments", "perspectives", "examples"],
    "tutorial": ["procedures", "tools", "pitfalls", "practical_tips"],
    "news": ["events", "actors", "immediate_impact", "dates"],
    "thread": ["opinions", "claims", "weak_signals", "ideas"],
    "notes": ["reflections", "personal_observations", "questions", "ideas"],
}

# What each source type should NOT be trusted for
SOURCE_WEAKNESSES: dict[str, list[str]] = {
    "encyclopedia": ["opinions", "cutting_edge", "personal_relevance"],
    "research_paper": ["broad_context", "accessibility", "practical_use"],
    "documentation": ["history", "opinions", "broader_impact"],
    "article": ["canonical_facts", "completeness", "neutrality"],
    "tutorial": ["depth", "theory", "canonical_facts"],
    "news": ["permanence", "completeness", "deep_analysis"],
    "thread": ["accuracy", "completeness", "canonical_facts", "neutrality"],
    "notes": ["accuracy", "completeness", "objectivity"],
}


def confidence_for_source(source_type: str) -> float:
    return SOURCE_CONFIDENCE.get(source_type, 0.5)


def is_strong_for(source_type: str, knowledge_type: str) -> bool:
    return knowledge_type in SOURCE_STRENGTHS.get(source_type, [])


def is_weak_for(source_type: str, knowledge_type: str) -> bool:
    return knowledge_type in SOURCE_WEAKNESSES.get(source_type, [])


# ============================================================================
# KNOWLEDGE QUALITY LINT RULES BY SOURCE TYPE
# ============================================================================

@dataclass(slots=True, frozen=True)
class LintResult:
    passed: bool
    issues: list[str]

    def to_dict(self) -> dict[str, object]:
        return {"passed": self.passed, "issues": list(self.issues)}


def lint_extraction(source_type: str, extraction: dict[str, object]) -> LintResult:
    """Validate extraction quality based on source type expectations."""
    issues: list[str] = []

    # Universal checks
    if not extraction.get("title"):
        issues.append("Missing title")
    if not extraction.get("tldr"):
        issues.append("Missing TLDR")
    if not extraction.get("summary"):
        issues.append("Missing summary")

    entities = extraction.get("entities", [])
    relationships = extraction.get("relationships", [])
    timeline = extraction.get("timeline", [])
    facts = extraction.get("core_facts", [])
    insights = extraction.get("key_insights", [])

    # Type-specific checks
    if source_type == "encyclopedia":
        if len(entities) < 2:
            issues.append("Encyclopedia should extract at least 2 entities")
        if len(facts) < 3:
            issues.append("Encyclopedia should extract at least 3 core facts")
        if len(relationships) < 1:
            issues.append("Encyclopedia should extract at least 1 relationship")

    elif source_type == "article":
        if len(insights) < 1:
            issues.append("Article should extract at least 1 key insight")

    elif source_type == "news":
        if len(entities) < 1:
            issues.append("News should identify at least 1 entity (actor)")
        has_date = any(isinstance(t, dict) and t.get("date") for t in timeline)
        if not has_date and not extraction.get("timeline"):
            issues.append("News should capture when the event occurred")

    elif source_type == "research_paper":
        if len(facts) < 2:
            issues.append("Research paper should extract at least 2 findings/facts")
        if len(insights) < 1:
            issues.append("Research paper should extract at least 1 insight/contribution")

    elif source_type == "documentation":
        if len(entities) < 1:
            issues.append("Documentation should identify the tool/library as an entity")

    elif source_type == "thread":
        if len(insights) < 1:
            issues.append("Thread should extract at least 1 takeaway/claim")

    return LintResult(passed=len(issues) == 0, issues=issues)


# ============================================================================
# EVIDENCE TAGGING
# ============================================================================

def tag_evidence_strength(source_type: str) -> str:
    """Return evidence strength tag for a source type."""
    confidence = confidence_for_source(source_type)
    if confidence >= 0.8:
        return "strong"
    if confidence >= 0.5:
        return "moderate"
    return "weak"


def should_enrich_canonical(source_type: str) -> bool:
    """Should this source type be used to enrich canonical entity notes?"""
    return source_type in ("encyclopedia", "research_paper", "documentation")


def should_create_event(source_type: str) -> bool:
    """Should this source type potentially create event entities?"""
    return source_type in ("news", "encyclopedia")


__all__ = [
    "LintResult",
    "SOURCE_CONFIDENCE",
    "SOURCE_STRENGTHS",
    "SOURCE_WEAKNESSES",
    "confidence_for_source",
    "is_strong_for",
    "is_weak_for",
    "lint_extraction",
    "should_create_event",
    "should_enrich_canonical",
    "tag_evidence_strength",
]
