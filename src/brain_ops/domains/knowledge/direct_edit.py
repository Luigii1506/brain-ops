from __future__ import annotations

import re

from brain_ops.domains.knowledge.promotion import extract_sections

_SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")
_TIMELINE_LINE_PATTERN = re.compile(
    r"^(?:[-*]\s*)?(?:\*\*)?(?P<date>[^*—–:\-]{1,60}?)(?:\*\*)?\s*(?:[—–:\-]\s+)(?P<event>.+)$"
)


def _normalize_lines(block: str) -> list[str]:
    lines: list[str] = []
    for raw_line in block.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        line = re.sub(r"^[-*]\s+", "", line)
        line = re.sub(r"^\d+\.\s+", "", line)
        line = re.sub(r"^\[(?: |x)\]\s+", "", line, flags=re.IGNORECASE)
        line = line.strip()
        if line:
            lines.append(line)
    return lines


def _section_items(sections: dict[str, str], *names: str) -> list[str]:
    items: list[str] = []
    for name in names:
        content = sections.get(name)
        if not content:
            continue
        items.extend(_normalize_lines(content))
    return items


def _summary_from_sections(sections: dict[str, str], body: str) -> str:
    candidates = _section_items(
        sections,
        "Identity",
        "Summary",
        "Core idea",
        "Key Facts",
        "Impact",
        "Why it matters",
    )
    if candidates:
        return candidates[0][:500]

    compact_body = " ".join(line.strip() for line in body.splitlines() if line.strip())
    return compact_body[:500]


def _tldr_from_summary(summary: str) -> str:
    if not summary:
        return ""
    first_sentence = _SENTENCE_SPLIT_PATTERN.split(summary.strip(), maxsplit=1)[0]
    return first_sentence[:240]


def _timeline_from_sections(sections: dict[str, str]) -> list[dict[str, str]]:
    timeline: list[dict[str, str]] = []
    for line in _section_items(sections, "Timeline"):
        match = _TIMELINE_LINE_PATTERN.match(line)
        if match:
            timeline.append(
                {
                    "date": match.group("date").strip(),
                    "event": match.group("event").strip(),
                }
            )
        else:
            timeline.append({"date": "", "event": line})
    return timeline


def build_direct_edit_extraction(
    frontmatter: dict[str, object],
    body: str,
    *,
    name: str,
    source_url: str | None = None,
) -> dict[str, object]:
    sections = extract_sections(body)
    summary = _summary_from_sections(sections, body)
    tldr = _tldr_from_summary(summary)

    related = frontmatter.get("related", [])
    if isinstance(related, str):
        related_names = [related] if related.strip() else []
    elif isinstance(related, list):
        related_names = [str(item).strip() for item in related if str(item).strip()]
    else:
        related_names = []

    entities: list[dict[str, str]] = [
        {
            "name": name,
            "type": str(frontmatter.get("type", "concept")),
            "importance": "high",
            "role_in_source": "primary entity",
        }
    ]
    entities.extend(
        {
            "name": related_name,
            "type": "concept",
            "importance": "medium",
            "role_in_source": "related entity",
        }
        for related_name in related_names
    )

    relationships = [
        {
            "subject": name,
            "predicate": "related_to",
            "object": related_name,
            "confidence": "medium",
        }
        for related_name in related_names
    ]

    strategic_patterns = _section_items(sections, "Strategic Insights")
    contradictions = _section_items(sections, "Contradictions & Uncertainties")
    key_insights = _section_items(sections, "Impact", "Strategic Insights", "Why it matters", "Key ideas")
    core_facts = _section_items(sections, "Key Facts", "Identity")
    personal_relevance_items = _section_items(sections, "Personal relevance", "Why it matters")

    return {
        "title": name,
        "source_type": "direct_edit",
        "source_url": source_url,
        "tldr": tldr,
        "summary": summary,
        "core_facts": core_facts,
        "key_insights": key_insights,
        "timeline": _timeline_from_sections(sections),
        "entities": entities,
        "relationships": relationships,
        "strategic_patterns": strategic_patterns,
        "contradictions_or_uncertainties": contradictions,
        "personal_relevance": personal_relevance_items[0] if personal_relevance_items else None,
    }


__all__ = [
    "build_direct_edit_extraction",
]
