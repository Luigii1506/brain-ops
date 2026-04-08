"""Smart chunking — extract content by headings and prioritize by subtype."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class ContentChunk:
    heading: str
    text: str
    char_count: int
    position: int = 0
    priority: str = "medium"


MAX_CHUNK_SIZE = 2500


# ============================================================================
# HEADING DETECTION
# ============================================================================

_WIKI_NOISE = {
    "editar", "predecesor", "sucesor", "otros títulos", "información personal",
    "nombre completo", "nacimiento", "fallecimiento", "religión", "familia",
    "dinastía", "padre", "madre", "consorte", "hijos", "información profesional",
    "lealtad", "unidad", "conflictos", "isbn", "véase", "véanse", "notas",
    "referencias", "bibliografía", "enlaces externos", "este artículo",
    "categorías", "editar datos en wikidata",
}


def _clean_heading(line: str) -> str:
    return re.sub(r"\s*\[editar\]\s*", "", line).strip()


def _is_heading(line: str) -> bool:
    """Detect section headings in markdown or Wikipedia plain text."""
    stripped = line.strip()

    if len(stripped) < 5 or len(stripped) > 120:
        return False

    # Skip noise
    if stripped.lower() in _WIKI_NOISE:
        return False

    # Skip references, ISBNs, metadata
    if re.match(r"^(ISBN|ISSN|\d{4}|↑|​|\[|Wikipedia:|Texto |PDF)", stripped):
        return False

    # Markdown heading
    if re.match(r"^#{1,3}\s+", stripped):
        return True

    # Wikipedia heading: capitalized, no period, few commas, may have [editar]
    if (stripped[0].isupper() and
        not stripped.endswith(".") and
        not stripped.endswith(",") and
        stripped.count(",") <= 2 and
        len(stripped.split()) <= 8 and
        not re.match(r"^\d", stripped) and
        not re.match(r"^[\[\(]", stripped)):
        # Has [editar] suffix — strong signal
        if "[editar]" in stripped:
            return True
    return False


# ============================================================================
# MAIN CHUNKING
# ============================================================================

def chunk_by_headings(text: str) -> list[ContentChunk]:
    """Smart chunk: detect headings → group content → split large chunks → sentence fallback."""
    lines = text.splitlines()

    # Pass 1: detect headings and group content
    raw_chunks: list[tuple[str, list[str]]] = []
    current_heading = "Introduction"
    current_lines: list[str] = []

    i = 0
    while i < len(lines):
        stripped = lines[i].strip()

        # Markdown heading
        md_match = re.match(r"^#{1,3}\s+(.+)", stripped)
        if md_match:
            if current_lines:
                raw_chunks.append((current_heading, list(current_lines)))
            current_heading = md_match.group(1).strip()
            current_lines = []
            i += 1
            continue

        # Wikipedia heading pattern: "Heading\n[\neditar\n]"
        if (i + 2 < len(lines) and
            lines[i + 1].strip() == "[" and
            lines[i + 2].strip().lower() == "editar" and
            len(stripped) >= 3 and len(stripped) <= 120 and
            stripped[0].isupper() and
            stripped.lower() not in _WIKI_NOISE):
            if current_lines and len(current_lines) > 2:
                raw_chunks.append((current_heading, list(current_lines)))
            current_heading = _clean_heading(stripped)
            current_lines = []
            # Skip the "[", "editar", "]" lines
            i += 4 if (i + 3 < len(lines) and lines[i + 3].strip() == "]") else i + 3
            continue

        # Skip standalone noise
        if stripped.lower() in {"editar", "[", "]"}:
            i += 1
            continue

        current_lines.append(lines[i])
        i += 1

    if current_lines:
        raw_chunks.append((current_heading, list(current_lines)))

    # Pass 2: build chunks and split large ones
    chunks: list[ContentChunk] = []
    position = 0

    for heading, lines_list in raw_chunks:
        content = "\n".join(lines_list).strip()
        if not content or len(content) < 50:
            continue

        if len(content) <= MAX_CHUNK_SIZE:
            position += 1
            chunks.append(ContentChunk(
                heading=heading,
                text=content,
                char_count=len(content),
                position=position,
            ))
        else:
            # Split large chunks by sentences
            sub_chunks = _split_by_sentences(content, heading, max_size=MAX_CHUNK_SIZE)
            for sc in sub_chunks:
                position += 1
                chunks.append(ContentChunk(
                    heading=sc[0],
                    text=sc[1],
                    char_count=len(sc[1]),
                    position=position,
                ))

    # If we got nothing useful, last resort: fixed-size blocks
    if len(chunks) <= 1 and len(text) > 3000:
        return _chunk_by_fixed_size(text, chunk_size=MAX_CHUNK_SIZE)

    return chunks


def _split_by_sentences(text: str, heading: str, max_size: int = 2500) -> list[tuple[str, str]]:
    """Split text by sentence boundaries, keeping chunks under max_size."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    result: list[tuple[str, str]] = []
    buffer: list[str] = []
    part = 0

    for sentence in sentences:
        buffer.append(sentence)
        if len(" ".join(buffer)) > max_size:
            part += 1
            label = f"{heading} (part {part})" if part > 1 else heading
            result.append((label, " ".join(buffer)))
            buffer = []

    if buffer:
        part += 1
        label = f"{heading} (part {part})" if part > 1 else heading
        result.append((label, " ".join(buffer)))

    return result


def _chunk_by_fixed_size(text: str, chunk_size: int = 2500) -> list[ContentChunk]:
    """Last resort: split by sentences into fixed-size blocks."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[ContentChunk] = []
    buffer: list[str] = []
    block_num = 0

    for sentence in sentences:
        buffer.append(sentence)
        if len(" ".join(buffer)) > chunk_size:
            block_num += 1
            block_text = " ".join(buffer)
            first_words = " ".join(block_text.split()[:8])[:60]
            chunks.append(ContentChunk(
                heading=first_words or f"Block {block_num}",
                text=block_text,
                char_count=len(block_text),
                position=block_num,
            ))
            buffer = []

    if buffer:
        block_num += 1
        block_text = " ".join(buffer)
        first_words = " ".join(block_text.split()[:8])[:60]
        chunks.append(ContentChunk(
            heading=first_words or f"Block {block_num}",
            text=block_text,
            char_count=len(block_text),
            position=block_num,
        ))

    return chunks


# ============================================================================
# SUBTYPE PRIORITY RANKING
# ============================================================================

SUBTYPE_PRIORITY_KEYWORDS: dict[str, list[str]] = {
    "person": ["nacimiento", "birth", "muerte", "death", "reinado", "reign",
               "legado", "legacy", "campañas", "campaigns", "juventud", "youth",
               "ascenso", "rise", "biografía", "biography", "carrera", "career",
               "infancia", "childhood", "educación", "education", "conquista"],
    "war": ["causas", "causes", "batallas", "battles", "resultado", "outcome",
            "consecuencias", "consequences", "participantes", "participants"],
    "place": ["geografía", "geography", "historia", "history", "gobierno",
              "government", "cultura", "culture", "población", "population"],
    "book": ["resumen", "summary", "temas", "themes", "autor", "author",
             "argumento", "plot", "personajes", "characters", "influencia"],
    "emotion": ["definición", "definition", "psicología", "psychology",
                "filosofía", "philosophy", "manifestaciones", "expressions"],
    "discipline": ["definición", "definition", "historia", "history",
                   "ramas", "branches", "métodos", "methods", "aplicaciones"],
    "celestial_body": ["órbita", "orbit", "composición", "composition",
                       "atmósfera", "atmosphere", "exploración", "exploration"],
    "deity": ["mitología", "mythology", "culto", "worship", "atributos",
              "simbolismo", "symbolism"],
    "empire": ["fundación", "founding", "caída", "fall", "expansión",
               "territorio", "gobierno", "economía"],
    "battle": ["antecedentes", "desarrollo", "consecuencias", "fuerzas",
               "estrategia", "resultado"],
    "civilization": ["gobierno", "cultura", "religión", "economía", "arte",
                     "ciencia", "filosofía"],
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
        text_lower = chunk.text[:300].lower()
        s = 0
        for kw in keywords:
            if kw in heading_lower:
                s += 10
            if kw in text_lower:
                s += 3
        if chunk.position <= 2:
            s += 8
        if chunk.char_count > 500:
            s += 2
        return s

    scored = sorted(chunks, key=score, reverse=True)

    selected: list[ContentChunk] = []
    total_chars = 0
    for chunk in scored:
        if total_chars + chunk.char_count > max_chars:
            if not selected:
                truncated_text = chunk.text[:max_chars]
                selected.append(ContentChunk(
                    heading=chunk.heading,
                    text=truncated_text,
                    char_count=len(truncated_text),
                    position=chunk.position,
                ))
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
