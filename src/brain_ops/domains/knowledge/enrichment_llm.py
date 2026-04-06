"""LLM-powered enrichment for existing knowledge entities."""

from __future__ import annotations

from dataclasses import dataclass


ENTITY_ENRICH_PROMPT = """You are updating an existing knowledge note using new evidence.

Your job is not to rewrite the page, but to improve it while preserving structure.

Current note content:
---
{current_content}
---

New information to integrate:
---
{new_info}
---

When integrating the new information:
- Preserve existing valid content — never delete what's already there
- Add new atomic facts under ## Key Facts
- Expand ## Timeline when new dated events appear
- Expand ## Relationships when new entities or connections appear
- Add contradictions explicitly under ## Contradictions & Uncertainties
- Do not duplicate existing facts
- Prefer concise, information-dense additions
- Use wikilinks [[Entity Name]] for any entities mentioned
- Keep the markdown structure stable
- Preserve the TLDR (update it only if the new info significantly changes the picture)
- Keep ## Related notes at the bottom

Required sections (create if missing):
- > **TLDR:** ...
- ## Identity
- ## Key Facts
- ## Timeline
- ## Impact
- ## Relationships
- ## Strategic Insights
- ## Contradictions & Uncertainties
- ## Related notes

Return ONLY the updated note body, starting from the TLDR blockquote."""


ENTITY_GENERATE_PROMPT = """You are generating a high-quality wiki page for a personal knowledge system.

Entity: {name}
Type: {entity_type}

Write the note in a way that is:
- concise but information-dense
- easy to scan
- useful for retrieval and future reasoning
- rich in explicit relationships
- factually grounded

Use this structure:

> **TLDR:** one-sentence summary

## Identity
Who or what this entity is. Titles, period, classification.

## Key Facts
- concise factual bullets
- names, dates, titles, locations, roles
- be specific: prefer "356 a.C." over "siglo IV a.C."

## Timeline
- date — event
- date — event

## Impact
Why this entity matters. What changed because of it.

## Relationships
- [[Entity]] — relationship type (mentor of, father of, conquered, founded, etc.)
- [[Entity]] — relationship type

## Strategic Insights
Non-obvious lessons, patterns, behaviors, or principles worth remembering.

## Related notes

Rules:
- Use wikilinks [[Entity Name]] for every entity mentioned
- Prefer specific facts over generic claims
- Do not invent details you're not confident about
- Keep sections compact and high-signal
- Write in Spanish if the entity name is in Spanish, otherwise English
- Return ONLY the note body, starting from the TLDR blockquote"""


@dataclass(slots=True, frozen=True)
class EnrichmentResult:
    entity_name: str
    updated_body: str
    had_existing_content: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "entity_name": self.entity_name,
            "had_existing_content": self.had_existing_content,
            "body_length": len(self.updated_body),
        }


def build_enrich_prompt(current_content: str, new_info: str) -> str:
    return ENTITY_ENRICH_PROMPT.format(
        current_content=current_content[:8000],
        new_info=new_info[:4000],
    )


def build_generate_prompt(name: str, entity_type: str, sections: tuple[str, ...]) -> str:
    return ENTITY_GENERATE_PROMPT.format(
        name=name,
        entity_type=entity_type,
    )


__all__ = [
    "ENTITY_ENRICH_PROMPT",
    "ENTITY_GENERATE_PROMPT",
    "EnrichmentResult",
    "build_enrich_prompt",
    "build_generate_prompt",
]
