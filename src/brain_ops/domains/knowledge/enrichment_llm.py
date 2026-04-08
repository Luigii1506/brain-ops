"""LLM-powered enrichment for existing knowledge entities."""

from __future__ import annotations

import re
from dataclasses import dataclass


ENTITY_ENRICH_PROMPT = """You are updating an existing knowledge note using new evidence.

Your job is not to rewrite the page, but to improve it while preserving structure.

Entity subtype: {subtype}

Current note content:
---
{current_content}
---

New information to integrate:
---
{new_info}
---

{writing_guide}
{role_hints}

CRITICAL RULES — READ CAREFULLY:
1. Identity MUST NOT be empty. Write 1-3 sentences about who/what this entity is.
2. Fill sections in this priority order:
   - Identity (MUST fill)
   - Key Facts (MUST fill with at least 5 facts)
   - Timeline (fill if dated events exist)
   - Relationships (fill with [[Entity Name]] — relationship type format)
   - Impact (why this matters)
   - Strategic Insights (non-obvious patterns, lessons, behaviors)
   - Contradictions & Uncertainties (disputed facts, uncertain dates)
3. NO section may be left empty if the source contains relevant information.
4. Use wikilinks [[Entity Name]] for every entity mentioned.
5. Prefer specific facts over generic claims. Dates, names, places > vague descriptions.
6. Relationships must use this format: [[Entity]] — relationship type
7. Do not duplicate existing content. Check what already exists before adding.
8. Write in the same language as the existing note. If the entity name is in Spanish, write in Spanish.
9. Keep ## Related notes as the last section.
10. Add narrative depth for key events — causes, development, consequences, not just dates.

Return ONLY the updated note body, starting from the TLDR blockquote."""


ENTITY_GENERATE_PROMPT = """You are generating a high-quality wiki page for a personal knowledge system.

Entity: {name}
Type: {entity_type}

SECTIONS TO USE (in this order):
{sections_list}

{writing_guide}
{role_hints}

CRITICAL RULES:
1. Start with: > **TLDR:** one-sentence summary
2. ## Identity MUST contain 1-3 sentences about who/what this is. NEVER leave it empty.
3. Fill ALL sections listed above. No section may be left empty.
4. For each section, write substantive content — not a single sentence. Aim for 3-8 lines minimum.
5. Use wikilinks [[Entity Name]] for every entity mentioned.
6. Prefer specific facts: "356 a.C." over "siglo IV a.C.", "40,000 soldiers" over "a large army".
7. Include narrative depth for key events — causes, development, consequences.
8. Do not invent details you're not confident about.
9. Write in Spanish if the entity name is in Spanish, otherwise English.
10. Keep ## Related notes as the last section, leave it empty for the user.

Return ONLY the note body, starting from the TLDR blockquote."""


SECTION_REPAIR_PROMPT = """The following section of a knowledge note was left empty or is too thin.
Fill it with useful content based on what you know about the entity.

Entity: {name}
Section: {section_name}
Context from the note:
---
{note_context}
---

Rules:
- Write 2-5 lines of high-quality, specific content for this section.
- Use wikilinks [[Entity Name]] for entities mentioned.
- Be factual and concise.
- Write in the same language as the context.

Return ONLY the content for this section (no heading, no other sections)."""


@dataclass(slots=True, frozen=True)
class EnrichmentResult:
    entity_name: str
    updated_body: str
    had_existing_content: bool
    sections_repaired: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "entity_name": self.entity_name,
            "had_existing_content": self.had_existing_content,
            "body_length": len(self.updated_body),
            "sections_repaired": list(self.sections_repaired),
        }


# Sections that must never be empty
REQUIRED_SECTIONS = ("Identity", "Key Facts")

# Sections we check but don't force-repair
RECOMMENDED_SECTIONS = ("Timeline", "Relationships", "Impact")


def validate_note_sections(body: str) -> list[str]:
    """Return list of required sections that are empty or missing."""
    empty_sections: list[str] = []
    for section in REQUIRED_SECTIONS:
        marker = f"## {section}"
        idx = body.find(marker)
        if idx == -1:
            empty_sections.append(section)
            continue
        # Check if section has content (look for text between this heading and next)
        after_heading = body[idx + len(marker):]
        next_heading = after_heading.find("\n## ")
        section_content = after_heading[:next_heading] if next_heading > 0 else after_heading
        stripped = section_content.strip()
        if not stripped or len(stripped) < 10:
            empty_sections.append(section)
    return empty_sections


def repair_section(body: str, section_name: str, repair_content: str) -> str:
    """Insert repair content into an empty section."""
    marker = f"## {section_name}"
    idx = body.find(marker)
    if idx == -1:
        # Section doesn't exist — add before Related notes
        related_idx = body.find("## Related notes")
        if related_idx > 0:
            return body[:related_idx] + f"## {section_name}\n{repair_content.strip()}\n\n" + body[related_idx:]
        return body + f"\n\n## {section_name}\n{repair_content.strip()}\n"

    # Section exists but is empty — insert content after heading
    after_heading_start = idx + len(marker)
    next_heading = body.find("\n## ", after_heading_start)
    if next_heading > 0:
        return body[:after_heading_start] + f"\n{repair_content.strip()}\n\n" + body[next_heading:]
    return body[:after_heading_start] + f"\n{repair_content.strip()}\n"


def build_enrich_prompt(
    current_content: str,
    new_info: str,
    *,
    subtype: str = "",
    writing_guide: str = "",
    role_hints: str = "",
) -> str:
    return ENTITY_ENRICH_PROMPT.format(
        current_content=current_content[:8000],
        new_info=new_info[:8000],
        subtype=subtype or "general",
        writing_guide=f"WRITING PRIORITIES FOR THIS TYPE:\n{writing_guide}" if writing_guide else "",
        role_hints=f"ROLE-SPECIFIC GUIDANCE:\n{role_hints}" if role_hints else "",
    )


def build_generate_prompt(
    name: str,
    entity_type: str,
    sections: tuple[str, ...],
    *,
    writing_guide: str = "",
    role_hints: str = "",
) -> str:
    sections_list = "\n".join(f"- ## {s}" for s in sections)
    return ENTITY_GENERATE_PROMPT.format(
        name=name,
        entity_type=entity_type,
        sections_list=sections_list,
        writing_guide=f"WRITING PRIORITIES FOR THIS TYPE:\n{writing_guide}" if writing_guide else "",
        role_hints=f"ROLE-SPECIFIC GUIDANCE:\n{role_hints}" if role_hints else "",
    )


def build_section_repair_prompt(name: str, section_name: str, note_context: str) -> str:
    return SECTION_REPAIR_PROMPT.format(
        name=name,
        section_name=section_name,
        note_context=note_context[:2000],
    )


# ============================================================================
# POST-ENRICHMENT DEDUPLICATION
# ============================================================================

def _normalize_sentence(s: str) -> str:
    """Normalize a sentence for dedup comparison."""
    # Remove wikilink brackets, lowercase, strip
    s = re.sub(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", r"\1", s)
    return re.sub(r"\s+", " ", s.lower().strip())


def deduplicate_note_content(body: str) -> str:
    """Remove duplicate sentences/bullet items across sections of a note."""
    # Split into sections
    parts = re.split(r"(^## .+$)", body, flags=re.MULTILINE)

    # Reconstruct as (heading, content) pairs
    sections: list[tuple[str, str]] = []
    i = 0
    while i < len(parts):
        if parts[i].startswith("## "):
            heading = parts[i]
            content = parts[i + 1] if i + 1 < len(parts) else ""
            sections.append((heading, content))
            i += 2
        else:
            # Pre-heading content (TLDR, etc.)
            sections.append(("", parts[i]))
            i += 1

    seen: set[str] = set()
    result_parts: list[str] = []

    for heading, content in sections:
        if heading:
            result_parts.append(heading)

        # Split content into lines/items
        lines = content.split("\n")
        deduped_lines: list[str] = []

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("## ") or stripped.startswith("### "):
                deduped_lines.append(line)
                continue

            # For bullet items and regular sentences
            fingerprint = _normalize_sentence(stripped)
            if len(fingerprint) < 20:
                # Too short to meaningfully dedup
                deduped_lines.append(line)
                continue

            if fingerprint in seen:
                continue  # Skip duplicate
            seen.add(fingerprint)
            deduped_lines.append(line)

        result_parts.append("\n".join(deduped_lines))

    return "".join(result_parts)


__all__ = [
    "ENTITY_ENRICH_PROMPT",
    "ENTITY_GENERATE_PROMPT",
    "EnrichmentResult",
    "RECOMMENDED_SECTIONS",
    "REQUIRED_SECTIONS",
    "SECTION_REPAIR_PROMPT",
    "build_enrich_prompt",
    "build_generate_prompt",
    "build_section_repair_prompt",
    "deduplicate_note_content",
    "repair_section",
    "validate_note_sections",
]
