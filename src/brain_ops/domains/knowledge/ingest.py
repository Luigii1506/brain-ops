"""Knowledge ingest — process raw sources into structured intelligence."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.request import Request, urlopen


@dataclass(slots=True, frozen=True)
class EntityMention:
    name: str
    entity_type: str
    importance: str
    role_in_source: str

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "type": self.entity_type, "importance": self.importance, "role": self.role_in_source}


@dataclass(slots=True, frozen=True)
class Relationship:
    subject: str
    predicate: str
    object: str
    confidence: str

    def to_dict(self) -> dict[str, object]:
        return {"subject": self.subject, "predicate": self.predicate, "object": self.object, "confidence": self.confidence}


@dataclass(slots=True, frozen=True)
class TimelineEntry:
    date: str
    event: str

    def to_dict(self) -> dict[str, object]:
        return {"date": self.date, "event": self.event}


@dataclass(slots=True, frozen=True)
class IngestPlan:
    source_title: str
    source_type: str
    summary: str
    tldr: str
    core_facts: list[str]
    key_insights: list[str]
    timeline: list[TimelineEntry]
    entities: list[EntityMention]
    relationships: list[Relationship]
    strategic_patterns: list[str]
    contradictions: list[str]
    personal_relevance: str | None
    content_for_note: str

    def to_dict(self) -> dict[str, object]:
        return {
            "source_title": self.source_title,
            "source_type": self.source_type,
            "summary": self.summary,
            "tldr": self.tldr,
            "core_facts": list(self.core_facts),
            "key_insights": list(self.key_insights),
            "timeline": [t.to_dict() for t in self.timeline],
            "entities": [e.to_dict() for e in self.entities],
            "relationships": [r.to_dict() for r in self.relationships],
            "strategic_patterns": list(self.strategic_patterns),
            "contradictions": list(self.contradictions),
            "personal_relevance": self.personal_relevance,
        }


@dataclass(slots=True, frozen=True)
class FetchedUrlDocument:
    text: str
    title: str | None
    html: str | None
    source_profile: str


def classify_source_type(url: str | None, text: str) -> str:
    from .source_strategy import classify_source
    return classify_source(url, text)


def fetch_url_document(url: str) -> FetchedUrlDocument:
    from .source_blocks import detect_source_profile

    req = Request(url, headers={"User-Agent": "brain-ops/1.0"})
    with urlopen(req, timeout=30) as response:
        html = response.read().decode("utf-8", errors="replace")

    source_profile = detect_source_profile(url)

    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else None
        body = soup.get_text(separator="\n", strip=True)
        return FetchedUrlDocument(
            text=body,
            title=title,
            html=html,
            source_profile=source_profile,
        )
    except ImportError:
        return FetchedUrlDocument(
            text=html,
            title=None,
            html=html,
            source_profile=source_profile,
        )


def fetch_url_content(url: str) -> tuple[str, str | None]:
    document = fetch_url_document(url)
    return document.text, document.title


INGEST_EXTRACT_PROMPT = """You are not summarizing. You are building a high-quality personal knowledge system.

Your task is to extract reusable intelligence from a source, not just rewrite it.

Think like:
- a historian
- a strategist
- a knowledge graph builder
- an information architect

Source type: {source_type}
Source text:
---
{text}
---

Analyze the source and return valid JSON with the following fields:

{{
  "title": "clear descriptive title",
  "source_type": "article | book_chapter | video_transcript | research_paper | encyclopedia | documentation | notes",
  "tldr": "one sentence that captures the core insight",
  "summary": "3-5 sentence comprehensive summary",
  "core_facts": [
    "atomic, factual statements with dates, places, names where possible"
  ],
  "key_insights": [
    "important insights or conclusions worth remembering"
  ],
  "timeline": [
    {{"date": "356 a.C.", "event": "description of what happened"}}
  ],
  "entities": [
    {{"name": "canonical name", "type": "person | place | event | concept | organization | era | war | book | topic", "importance": "high | medium | low", "role_in_source": "brief role description"}}
  ],
  "relationships": [
    {{"subject": "Entity A", "predicate": "mentor of | father of | conquered | founded | died in | participated in | opposed | influenced | succeeded", "object": "Entity B", "confidence": "high | medium | low"}}
  ],
  "strategic_patterns": [
    "repeatable patterns, behaviors, strategic approaches, or principles"
  ],
  "contradictions_or_uncertainties": [
    "uncertain dates, conflicting accounts, disputed interpretations"
  ],
  "personal_relevance": "one sentence on why this might be valuable to remember"
}}

Rules:
- Be specific, not generic
- Prefer concrete facts over vague phrasing
- Extract relationships explicitly with clear predicates
- Include important dates where available
- If the source is mostly about one entity, make that clear
- Keep wording concise and information-dense
- Return ONLY valid JSON, no extra text"""


def build_ingest_prompt(
    text: str,
    *,
    source_type: str = "article",
    known_entities: list[str] | None = None,
    user_context: str | None = None,
) -> str:
    from .source_strategy import get_source_type_prompt, strategy_for_source

    strategy = strategy_for_source(source_type)
    truncated = text[:strategy.max_context_chars] if len(text) > strategy.max_context_chars else text

    # Build type-specific prompt
    type_instructions = get_source_type_prompt(source_type)
    prompt = f"{type_instructions}\n\n{INGEST_EXTRACT_PROMPT.format(text=truncated, source_type=source_type)}"

    # Add strategy-specific instructions
    if strategy.extra_instructions:
        prompt = prompt.replace("Rules:", f"Additional instructions for this source type:\n{strategy.extra_instructions}\n\nRules:")

    context_parts: list[str] = []
    if known_entities:
        top = known_entities[:50]
        context_parts.append(f"\nKnown entities in the system (use these canonical names when possible, link to them):\n{', '.join(top)}")
    if user_context:
        context_parts.append(f"\n{user_context}")
    if context_parts:
        prompt = prompt.replace("Rules:", "\n".join(context_parts) + "\n\nRules:")

    return prompt


def _parse_entities(raw: list) -> list[EntityMention]:
    result = []
    for item in raw:
        if isinstance(item, dict):
            result.append(EntityMention(
                name=str(item.get("name", "")),
                entity_type=str(item.get("type", "concept")),
                importance=str(item.get("importance", "medium")),
                role_in_source=str(item.get("role_in_source", "")),
            ))
        elif isinstance(item, str):
            result.append(EntityMention(name=item, entity_type="concept", importance="medium", role_in_source=""))
    return result


def _parse_relationships(raw: list) -> list[Relationship]:
    from .object_model import normalize_predicate

    result = []
    for item in raw:
        if isinstance(item, dict):
            raw_predicate = str(item.get("predicate", ""))
            result.append(Relationship(
                subject=str(item.get("subject", "")),
                predicate=normalize_predicate(raw_predicate),
                object=str(item.get("object", "")),
                confidence=str(item.get("confidence", "medium")),
            ))
    return result


def _parse_timeline(raw: list) -> list[TimelineEntry]:
    result = []
    for item in raw:
        if isinstance(item, dict):
            result.append(TimelineEntry(
                date=str(item.get("date", "")),
                event=str(item.get("event", "")),
            ))
    return result


def _render_structured_note(plan_data: dict) -> str:
    sections: list[str] = []

    tldr = plan_data.get("tldr", "")
    if tldr:
        sections.append(f"> **TLDR:** {tldr}")

    summary = plan_data.get("summary", "")
    if summary:
        sections.append(f"## Summary\n\n{summary}")

    facts = plan_data.get("core_facts", [])
    if facts:
        sections.append("## Key Facts\n\n" + "\n".join(f"- {f}" for f in facts))

    insights = plan_data.get("key_insights", [])
    if insights:
        sections.append("## Key Insights\n\n" + "\n".join(f"- {i}" for i in insights))

    timeline = plan_data.get("timeline", [])
    if timeline:
        lines = []
        for entry in timeline:
            if isinstance(entry, dict):
                lines.append(f"- **{entry.get('date', '?')}** — {entry.get('event', '')}")
        if lines:
            sections.append("## Timeline\n\n" + "\n".join(lines))

    entities = plan_data.get("entities", [])
    if entities:
        lines = []
        for e in entities:
            if isinstance(e, dict):
                name = e.get("name", "")
                role = e.get("role_in_source", "")
                lines.append(f"- [[{name}]] — {role}" if role else f"- [[{name}]]")
            elif isinstance(e, str):
                lines.append(f"- [[{e}]]")
        if lines:
            sections.append("## Entities\n\n" + "\n".join(lines))

    relationships = plan_data.get("relationships", [])
    if relationships:
        lines = []
        for r in relationships:
            if isinstance(r, dict):
                lines.append(f"- [[{r.get('subject', '')}]] — {r.get('predicate', '')} → [[{r.get('object', '')}]]")
        if lines:
            sections.append("## Relationships\n\n" + "\n".join(lines))

    patterns = plan_data.get("strategic_patterns", [])
    if patterns:
        sections.append("## Strategic Insights\n\n" + "\n".join(f"- {p}" for p in patterns))

    contradictions = plan_data.get("contradictions_or_uncertainties", [])
    if contradictions:
        sections.append("## Contradictions & Uncertainties\n\n" + "\n".join(f"- {c}" for c in contradictions))

    relevance = plan_data.get("personal_relevance", "")
    if relevance:
        sections.append(f"## Why This Matters\n\n{relevance}")

    sections.append("## Related notes")
    return "\n\n".join(sections)


def parse_ingest_extraction(extraction: dict[str, object]) -> IngestPlan:
    entities = _parse_entities(extraction.get("entities", extraction.get("entities_mentioned", [])))
    relationships = _parse_relationships(extraction.get("relationships", []))
    timeline = _parse_timeline(extraction.get("timeline", []))
    contradictions = [str(c) for c in extraction.get("contradictions_or_uncertainties", []) if c]
    patterns = [str(p) for p in extraction.get("strategic_patterns", []) if p]
    core_facts = [str(f) for f in extraction.get("core_facts", []) if f]
    key_insights = [str(i) for i in extraction.get("key_insights", extraction.get("key_ideas", [])) if i]
    personal_relevance = extraction.get("personal_relevance")

    content = _render_structured_note(extraction)

    return IngestPlan(
        source_title=str(extraction.get("title", "Untitled Source")),
        source_type=str(extraction.get("source_type", "article")),
        summary=str(extraction.get("summary", "")),
        tldr=str(extraction.get("tldr", "")),
        core_facts=core_facts,
        key_insights=key_insights,
        timeline=timeline,
        entities=entities,
        relationships=relationships,
        strategic_patterns=patterns,
        contradictions=contradictions,
        personal_relevance=str(personal_relevance) if isinstance(personal_relevance, str) else None,
        content_for_note=content,
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
        core_facts=[],
        key_insights=[],
        timeline=[],
        entities=[],
        relationships=[],
        strategic_patterns=[],
        contradictions=[],
        personal_relevance=None,
        content_for_note=content,
    )


__all__ = [
    "EntityMention",
    "INGEST_EXTRACT_PROMPT",
    "IngestPlan",
    "Relationship",
    "TimelineEntry",
    "build_deterministic_ingest_plan",
    "build_ingest_prompt",
    "classify_source_type",
    "fetch_url_content",
    "parse_ingest_extraction",
]
