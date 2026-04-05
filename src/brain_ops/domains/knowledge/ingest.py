"""Knowledge ingest — process raw sources into structured wiki content."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class IngestPlan:
    source_title: str
    source_type: str
    summary: str
    key_ideas: list[str]
    entities_mentioned: list[str]
    suggested_entity_type: str | None
    content_for_note: str

    def to_dict(self) -> dict[str, object]:
        return {
            "source_title": self.source_title,
            "source_type": self.source_type,
            "summary": self.summary,
            "key_ideas": list(self.key_ideas),
            "entities_mentioned": list(self.entities_mentioned),
            "suggested_entity_type": self.suggested_entity_type,
            "content_for_note": self.content_for_note,
        }


INGEST_EXTRACT_PROMPT = """You are a knowledge librarian. Analyze the following source text and extract structured information.

Source text:
---
{text}
---

Respond in JSON with these exact fields:
- "title": a clear title for this source (string)
- "source_type": one of "article", "book_chapter", "video_transcript", "research_paper", "web_page", "notes" (string)
- "summary": a 2-3 sentence summary of the content (string)
- "key_ideas": the 3-5 most important ideas or facts (array of strings)
- "entities_mentioned": names of notable people, places, events, concepts mentioned (array of strings)
- "suggested_entity_type": if this source is primarily about ONE entity, what type is it? One of "person", "event", "place", "concept", "book", "war", "era", "organization", "topic", or null (string or null)

Respond ONLY with valid JSON, no extra text."""


def build_ingest_prompt(text: str) -> str:
    truncated = text[:8000] if len(text) > 8000 else text
    return INGEST_EXTRACT_PROMPT.format(text=truncated)


def parse_ingest_extraction(extraction: dict[str, object]) -> IngestPlan:
    title = str(extraction.get("title", "Untitled Source"))
    source_type = str(extraction.get("source_type", "web_page"))
    summary = str(extraction.get("summary", ""))
    key_ideas = [str(item) for item in extraction.get("key_ideas", []) if item]
    entities_mentioned = [str(item) for item in extraction.get("entities_mentioned", []) if item]
    suggested = extraction.get("suggested_entity_type")
    suggested_type = str(suggested) if isinstance(suggested, str) and suggested.strip() else None

    sections = [f"## Summary\n\n{summary}"]
    if key_ideas:
        sections.append("## Key Ideas\n\n" + "\n".join(f"- {idea}" for idea in key_ideas))
    if entities_mentioned:
        sections.append("## Entities Mentioned\n\n" + "\n".join(f"- [[{name}]]" for name in entities_mentioned))
    sections.append("## Related notes")
    content = "\n\n".join(sections)

    return IngestPlan(
        source_title=title,
        source_type=source_type,
        summary=summary,
        key_ideas=key_ideas,
        entities_mentioned=entities_mentioned,
        suggested_entity_type=suggested_type,
        content_for_note=content,
    )


def build_deterministic_ingest_plan(text: str, *, title: str | None = None) -> IngestPlan:
    """Fallback ingest without LLM — creates a source note with raw text."""
    lines = text.strip().splitlines()
    inferred_title = title or (lines[0].strip("# ").strip() if lines else "Untitled Source")
    preview = " ".join(lines[:3])[:200] if lines else ""
    return IngestPlan(
        source_title=inferred_title,
        source_type="web_page",
        summary=preview,
        key_ideas=[],
        entities_mentioned=[],
        suggested_entity_type=None,
        content_for_note=f"## Source Content\n\n{text.strip()}\n\n## Related notes",
    )


__all__ = [
    "INGEST_EXTRACT_PROMPT",
    "IngestPlan",
    "build_deterministic_ingest_plan",
    "build_ingest_prompt",
    "parse_ingest_extraction",
]
