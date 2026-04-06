"""Smart chunking — extract content by headings and prioritize by subtype."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class ContentChunk:
    heading: str
    text: str
    char_count: int


def chunk_by_headings(text: str) -> list[ContentChunk]:
    """Split text into chunks by markdown headings or HTML-like section breaks."""
    lines = text.splitlines()
    chunks: list[ContentChunk] = []
    current_heading = "Introduction"
    current_lines: list[str] = []

    for line in lines:
        heading_match = re.match(r"^#{1,3}\s+(.+)", line)
        if heading_match:
            if current_lines:
                body = "\n".join(current_lines).strip()
                if body:
                    chunks.append(ContentChunk(heading=current_heading, text=body, char_count=len(body)))
            current_heading = heading_match.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        body = "\n".join(current_lines).strip()
        if body:
            chunks.append(ContentChunk(heading=current_heading, text=body, char_count=len(body)))

    # If no headings found, split into paragraphs
    if len(chunks) <= 1 and len(text) > 2000:
        return _chunk_by_paragraphs(text)

    return chunks


def _chunk_by_paragraphs(text: str) -> list[ContentChunk]:
    """Fallback: split by double newlines for unstructured text."""
    paragraphs = re.split(r"\n\n+", text.strip())
    chunks: list[ContentChunk] = []
    for i, para in enumerate(paragraphs):
        para = para.strip()
        if para and len(para) > 50:
            chunks.append(ContentChunk(
                heading=f"Section {i + 1}",
                text=para,
                char_count=len(para),
            ))
    return chunks


# Priority keywords by subtype — chunks with these keywords rank higher
SUBTYPE_PRIORITY_KEYWORDS: dict[str, list[str]] = {
    "person": ["nacimiento", "birth", "muerte", "death", "reinado", "reign",
               "legado", "legacy", "campañas", "campaigns", "juventud", "youth",
               "ascenso", "rise", "biografía", "biography", "carrera", "career",
               "infancia", "childhood", "educación", "education"],
    "war": ["causas", "causes", "batallas", "battles", "resultado", "outcome",
            "consecuencias", "consequences", "participantes", "participants",
            "antecedentes", "background"],
    "place": ["geografía", "geography", "historia", "history", "gobierno",
              "government", "cultura", "culture", "población", "population",
              "economía", "economy"],
    "book": ["resumen", "summary", "temas", "themes", "autor", "author",
             "argumento", "plot", "personajes", "characters", "influencia", "influence"],
    "emotion": ["definición", "definition", "psicología", "psychology",
                "filosofía", "philosophy", "manifestaciones", "expressions"],
    "discipline": ["definición", "definition", "historia", "history",
                   "ramas", "branches", "métodos", "methods", "aplicaciones", "applications"],
    "celestial_body": ["órbita", "orbit", "composición", "composition",
                       "atmósfera", "atmosphere", "exploración", "exploration",
                       "características", "characteristics"],
    "deity": ["mitología", "mythology", "culto", "worship", "atributos", "attributes",
              "simbolismo", "symbolism"],
}


def rank_chunks_for_subtype(
    chunks: list[ContentChunk],
    subtype: str,
    *,
    max_chars: int = 8000,
) -> list[ContentChunk]:
    """Rank and select the best chunks for a given subtype within char budget."""
    keywords = SUBTYPE_PRIORITY_KEYWORDS.get(subtype, [])

    def score(chunk: ContentChunk) -> int:
        heading_lower = chunk.heading.lower()
        text_lower = chunk.text[:200].lower()
        s = 0
        for kw in keywords:
            if kw in heading_lower:
                s += 10
            if kw in text_lower:
                s += 3
        # Introduction always gets a boost
        if chunk.heading.lower() in ("introduction", "introducción", "section 1"):
            s += 15
        # Longer chunks slightly preferred (more content)
        if chunk.char_count > 500:
            s += 2
        return s

    scored = sorted(chunks, key=score, reverse=True)

    selected: list[ContentChunk] = []
    total_chars = 0
    for chunk in scored:
        if total_chars + chunk.char_count > max_chars:
            # Take partial if it's the first one
            if not selected:
                truncated = chunk.text[:max_chars]
                selected.append(ContentChunk(heading=chunk.heading, text=truncated, char_count=len(truncated)))
            break
        selected.append(chunk)
        total_chars += chunk.char_count

    return selected


def build_prioritized_context(text: str, subtype: str, *, max_chars: int = 8000) -> str:
    """Build the best possible context from text for a given subtype."""
    chunks = chunk_by_headings(text)
    ranked = rank_chunks_for_subtype(chunks, subtype, max_chars=max_chars)
    parts: list[str] = []
    for chunk in ranked:
        parts.append(f"[{chunk.heading}]\n{chunk.text}")
    return "\n\n".join(parts)


__all__ = [
    "ContentChunk",
    "SUBTYPE_PRIORITY_KEYWORDS",
    "build_prioritized_context",
    "chunk_by_headings",
    "rank_chunks_for_subtype",
]
