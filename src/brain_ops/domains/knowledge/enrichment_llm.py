"""LLM-powered enrichment for existing knowledge entities."""

from __future__ import annotations

from dataclasses import dataclass


ENTITY_ENRICH_PROMPT = """You are a personal knowledge librarian. You are enriching an existing wiki page with new information.

Current note content:
---
{current_content}
---

New information to integrate:
---
{new_info}
---

Rules:
- Keep the existing structure (sections with ##)
- ADD new content under the appropriate sections — never delete existing content
- Add new wikilinks as [[Entity Name]] for any entities mentioned
- If new info contradicts existing content, note the contradiction explicitly
- Add a TLDR at the top if one doesn't exist (as a blockquote > **TLDR:** ...)
- Keep the "## Related notes" section at the bottom
- Write in the same language as the existing note

Return ONLY the updated note body (no frontmatter), starting from the TLDR or first ## section."""


ENTITY_GENERATE_PROMPT = """You are a personal knowledge librarian. Generate initial content for a wiki page about this entity.

Entity: {name}
Type: {entity_type}
Sections to fill: {sections}

Rules:
- Write comprehensive but concise content for each section
- Use wikilinks [[Entity Name]] for related entities
- Start with a TLDR blockquote: > **TLDR:** one sentence summary
- Write in Spanish if the entity name is in Spanish, otherwise English
- Focus on what's most important and useful to remember
- Be factual and specific — dates, names, places

Return ONLY the note body, starting from the TLDR blockquote."""


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
        sections=", ".join(sections),
    )


__all__ = [
    "ENTITY_ENRICH_PROMPT",
    "ENTITY_GENERATE_PROMPT",
    "EnrichmentResult",
    "build_enrich_prompt",
    "build_generate_prompt",
]
