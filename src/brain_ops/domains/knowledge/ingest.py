"""Knowledge ingest — process raw sources into structured wiki content."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse
from urllib.request import Request, urlopen


@dataclass(slots=True, frozen=True)
class IngestPlan:
    source_title: str
    source_type: str
    summary: str
    tldr: str
    key_ideas: list[str]
    entities_mentioned: list[str]
    suggested_entity_type: str | None
    content_for_note: str
    personal_relevance: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "source_title": self.source_title,
            "source_type": self.source_type,
            "summary": self.summary,
            "tldr": self.tldr,
            "key_ideas": list(self.key_ideas),
            "entities_mentioned": list(self.entities_mentioned),
            "suggested_entity_type": self.suggested_entity_type,
            "personal_relevance": self.personal_relevance,
        }


SOURCE_TYPE_HINTS = {
    "wikipedia.org": "encyclopedia",
    "youtube.com": "video_transcript",
    "youtu.be": "video_transcript",
    "arxiv.org": "research_paper",
    "medium.com": "article",
    "substack.com": "article",
    "github.com": "documentation",
}


def classify_source_type(url: str | None, text: str) -> str:
    if url:
        domain = urlparse(url).netloc.lower()
        for hint_domain, hint_type in SOURCE_TYPE_HINTS.items():
            if hint_domain in domain:
                return hint_type
    lowered = text[:500].lower()
    if "abstract" in lowered and "introduction" in lowered:
        return "research_paper"
    if any(kw in lowered for kw in ["chapter", "capítulo", "libro", "book"]):
        return "book_chapter"
    return "article"


def fetch_url_content(url: str) -> tuple[str, str | None]:
    req = Request(url, headers={"User-Agent": "brain-ops/1.0"})
    with urlopen(req, timeout=30) as response:
        html = response.read().decode("utf-8", errors="replace")
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else None
        body = soup.get_text(separator="\n", strip=True)
        return body, title
    except ImportError:
        return html, None


INGEST_EXTRACT_PROMPT = """You are a personal knowledge librarian building a wiki for your user. Analyze this source and extract structured information.

Important: This wiki is PERSONAL. When you mention entities, think about what they mean in context of someone learning and building knowledge. The summary should be useful for future reference.

Source type: {source_type}
Source text:
---
{text}
---

Respond in JSON with these exact fields:
- "title": a clear, descriptive title for this source (string)
- "source_type": one of "article", "book_chapter", "video_transcript", "research_paper", "encyclopedia", "documentation", "notes" (string)
- "summary": a 3-5 sentence comprehensive summary (string)
- "tldr": one sentence that captures the core insight (string)
- "key_ideas": the 5-7 most important ideas, facts, or takeaways (array of strings)
- "entities_mentioned": names of notable people, places, events, concepts, technologies mentioned — be thorough (array of strings)
- "suggested_entity_type": if this source is primarily about ONE entity, what type? One of "person", "event", "place", "concept", "book", "war", "era", "organization", "topic", or null
- "personal_relevance": one sentence on why this might be valuable to remember (string)

Respond ONLY with valid JSON, no extra text."""


def build_ingest_prompt(text: str, *, source_type: str = "article") -> str:
    truncated = text[:12000] if len(text) > 12000 else text
    return INGEST_EXTRACT_PROMPT.format(text=truncated, source_type=source_type)


def parse_ingest_extraction(extraction: dict[str, object]) -> IngestPlan:
    title = str(extraction.get("title", "Untitled Source"))
    source_type = str(extraction.get("source_type", "article"))
    summary = str(extraction.get("summary", ""))
    tldr = str(extraction.get("tldr", ""))
    key_ideas = [str(item) for item in extraction.get("key_ideas", []) if item]
    entities_mentioned = [str(item) for item in extraction.get("entities_mentioned", []) if item]
    suggested = extraction.get("suggested_entity_type")
    suggested_type = str(suggested) if isinstance(suggested, str) and suggested.strip() else None
    personal_relevance = extraction.get("personal_relevance")
    personal_rel = str(personal_relevance) if isinstance(personal_relevance, str) and personal_relevance.strip() else None

    sections = []
    if tldr:
        sections.append(f"> **TLDR:** {tldr}")
    sections.append(f"## Summary\n\n{summary}")
    if key_ideas:
        sections.append("## Key Ideas\n\n" + "\n".join(f"- {idea}" for idea in key_ideas))
    if entities_mentioned:
        sections.append("## Entities Mentioned\n\n" + "\n".join(f"- [[{name}]]" for name in entities_mentioned))
    if personal_rel:
        sections.append(f"## Why This Matters\n\n{personal_rel}")
    sections.append("## Related notes")
    content = "\n\n".join(sections)

    return IngestPlan(
        source_title=title,
        source_type=source_type,
        summary=summary,
        tldr=tldr,
        key_ideas=key_ideas,
        entities_mentioned=entities_mentioned,
        suggested_entity_type=suggested_type,
        content_for_note=content,
        personal_relevance=personal_rel,
    )


def build_deterministic_ingest_plan(text: str, *, title: str | None = None, url: str | None = None) -> IngestPlan:
    lines = text.strip().splitlines()
    inferred_title = title or (lines[0].strip("# ").strip() if lines else "Untitled Source")
    preview = " ".join(lines[:3])[:200] if lines else ""
    source_type = classify_source_type(url, text)

    content_parts = []
    if preview:
        content_parts.append(f"> **TLDR:** {preview}")
    content_parts.append(f"## Source Content\n\n{text.strip()}")
    content_parts.append("## Related notes")
    content = "\n\n".join(content_parts)

    return IngestPlan(
        source_title=inferred_title,
        source_type=source_type,
        summary=preview,
        tldr=preview,
        key_ideas=[],
        entities_mentioned=[],
        suggested_entity_type=None,
        content_for_note=content,
        personal_relevance=None,
    )


__all__ = [
    "INGEST_EXTRACT_PROMPT",
    "IngestPlan",
    "build_deterministic_ingest_plan",
    "build_ingest_prompt",
    "classify_source_type",
    "fetch_url_content",
    "parse_ingest_extraction",
]
