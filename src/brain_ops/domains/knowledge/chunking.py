"""Smart chunking — extract content by headings and prioritize by subtype."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class ContentChunk:
    heading: str
    text: str
    char_count: int


_WIKI_NOISE_WORDS = {
    "editar", "predecesor", "sucesor", "otros títulos", "información personal",
    "nombre completo", "nacimiento", "fallecimiento", "religión", "familia",
    "dinastía", "padre", "madre", "consorte", "hijos", "información profesional",
    "lealtad", "unidad", "conflictos", "isbn", "véase", "véanse", "artículo principal",
    "notas", "referencias", "bibliografía", "enlaces externos", "este artículo",
    "pdf", "texto griego", "texto francés", "texto inglés",
}


def _is_wiki_section_header(line: str, next_line: str | None) -> bool:
    """Detect Wikipedia-style section headers in plain text."""
    stripped = line.strip()
    if not stripped or len(stripped) > 60 or len(stripped) < 5:
        return False
    # Skip noise
    if stripped.lower() in _WIKI_NOISE_WORDS:
        return False
    # Skip lines that look like references, ISBNs, dates, or metadata
    if re.match(r"^(ISBN|ISSN|\d{4}|↑|​|\[|Wikipedia:|Texto )", stripped):
        return False
    # Wikipedia: section name followed by "editar" on next line
    if next_line and next_line.strip().lower() == "editar":
        return True
    return False


def chunk_by_headings(text: str) -> list[ContentChunk]:
    """Split text into chunks by markdown headings, Wikipedia sections, or paragraphs."""
    lines = text.splitlines()
    chunks: list[ContentChunk] = []
    current_heading = "Introduction"
    current_lines: list[str] = []
    found_headings = 0

    for i, line in enumerate(lines):
        next_line = lines[i + 1] if i + 1 < len(lines) else None

        # Markdown heading
        heading_match = re.match(r"^#{1,3}\s+(.+)", line)
        if heading_match:
            if current_lines:
                body = "\n".join(current_lines).strip()
                if body:
                    chunks.append(ContentChunk(heading=current_heading, text=body, char_count=len(body)))
            current_heading = heading_match.group(1).strip()
            current_lines = []
            found_headings += 1
            continue

        # Wikipedia-style section header
        if found_headings == 0 and _is_wiki_section_header(line, next_line):
            # Only use wiki detection if no markdown headings found
            if len(current_lines) > 5:  # Require some content before treating as new section
                body = "\n".join(current_lines).strip()
                if body and len(body) > 100:
                    chunks.append(ContentChunk(heading=current_heading, text=body, char_count=len(body)))
                current_heading = line.strip()
                current_lines = []
                continue

        # Skip "editar" lines (Wikipedia artifact)
        if line.strip().lower() == "editar":
            continue

        current_lines.append(line)

    if current_lines:
        body = "\n".join(current_lines).strip()
        if body:
            chunks.append(ContentChunk(heading=current_heading, text=body, char_count=len(body)))

    # If still just 1 big chunk, try splitting by paragraphs or fixed size
    if len(chunks) <= 1 and len(text) > 2000:
        para_chunks = _chunk_by_paragraphs(text)
        if len(para_chunks) > 1:
            return para_chunks
        # Last resort: split by fixed character count
        return _chunk_by_size(text, chunk_size=3000)

    return chunks


def _chunk_by_paragraphs(text: str) -> list[ContentChunk]:
    """Fallback: split by double newlines into meaningful blocks."""
    paragraphs = re.split(r"\n\n+", text.strip())
    chunks: list[ContentChunk] = []
    current_block: list[str] = []
    current_chars = 0
    block_num = 0

    for para in paragraphs:
        para = para.strip()
        if not para or len(para) < 30:
            continue

        current_block.append(para)
        current_chars += len(para)

        # Group paragraphs into ~2000 char blocks
        if current_chars >= 2000:
            block_num += 1
            block_text = "\n\n".join(current_block)
            # Use first significant words as heading
            first_words = " ".join(block_text.split()[:8])
            heading = first_words[:60] if len(first_words) > 10 else f"Block {block_num}"
            chunks.append(ContentChunk(heading=heading, text=block_text, char_count=len(block_text)))
            current_block = []
            current_chars = 0

    if current_block:
        block_num += 1
        block_text = "\n\n".join(current_block)
        first_words = " ".join(block_text.split()[:8])
        heading = first_words[:60] if len(first_words) > 10 else f"Block {block_num}"
        chunks.append(ContentChunk(heading=heading, text=block_text, char_count=len(block_text)))

    return chunks


def _chunk_by_size(text: str, chunk_size: int = 3000) -> list[ContentChunk]:
    """Last resort: split text into fixed-size chunks, breaking at line boundaries."""
    lines = text.splitlines()
    chunks: list[ContentChunk] = []
    current_lines: list[str] = []
    current_chars = 0
    block_num = 0

    for line in lines:
        current_lines.append(line)
        current_chars += len(line)

        if current_chars >= chunk_size:
            block_num += 1
            block_text = "\n".join(current_lines)
            first_words = " ".join(block_text.split()[:8])
            heading = first_words[:60] if len(first_words) > 10 else f"Block {block_num}"
            chunks.append(ContentChunk(heading=heading, text=block_text, char_count=len(block_text)))
            current_lines = []
            current_chars = 0

    if current_lines:
        block_num += 1
        block_text = "\n".join(current_lines)
        first_words = " ".join(block_text.split()[:8])
        heading = first_words[:60] if len(first_words) > 10 else f"Block {block_num}"
        chunks.append(ContentChunk(heading=heading, text=block_text, char_count=len(block_text)))
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
