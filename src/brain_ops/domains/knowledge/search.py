"""Knowledge search — search entities and notes by content."""

from __future__ import annotations

from dataclasses import dataclass

from .entities import ENTITY_TYPES, is_entity_note


@dataclass(slots=True, frozen=True)
class SearchResult:
    title: str
    entity_type: str | None
    relative_path: str
    match_context: str

    def to_dict(self) -> dict[str, object]:
        return {
            "title": self.title,
            "entity_type": self.entity_type,
            "relative_path": self.relative_path,
            "match_context": self.match_context,
        }


STOP_WORDS = {
    "qué", "que", "cómo", "como", "cuál", "cual", "por", "para", "entre",
    "hay", "tiene", "fue", "era", "son", "los", "las", "del", "una", "uno",
    "con", "sin", "más", "mas", "pero", "también", "tambien", "sobre",
    "desde", "hasta", "donde", "cuando", "quien", "cuyo", "todo", "cada",
    "otro", "esta", "este", "ese", "esa", "aquel", "muy", "bien", "mal",
    "the", "what", "how", "why", "who", "which", "and", "or", "is", "was",
    "are", "were", "has", "have", "had", "does", "did", "not", "from",
    "with", "for", "that", "this", "relación", "relacion", "relationship",
}


def _tokenize_query(query: str) -> list[str]:
    """Split query into meaningful search tokens, removing stop words and punctuation."""
    import re
    words = re.findall(r"[a-záéíóúñü]+", query.lower())
    tokens = [w for w in words if w not in STOP_WORDS and len(w) >= 3]
    return tokens


def search_notes(
    notes: list[tuple[str, dict[str, object], str]],
    query: str,
    *,
    entity_only: bool = False,
    max_results: int = 20,
) -> list[SearchResult]:
    query_lower = query.lower()
    tokens = _tokenize_query(query)
    results: list[tuple[SearchResult, int]] = []

    for rel_path, frontmatter, body in notes:
        if entity_only and not is_entity_note(frontmatter):
            continue

        name = frontmatter.get("name")
        title = str(name).strip() if isinstance(name, str) and name.strip() else rel_path
        entity_type = frontmatter.get("type") if is_entity_note(frontmatter) else None

        # Try exact match first
        match_context = _find_match_context(title, body, frontmatter, query_lower)
        if match_context is not None:
            results.append((SearchResult(
                title=title,
                entity_type=entity_type if isinstance(entity_type, str) else None,
                relative_path=rel_path,
                match_context=match_context,
            ), 100))
            continue

        # Try token-based matching
        if tokens:
            score, context = _score_by_tokens(title, body, frontmatter, tokens)
            if score > 0:
                results.append((SearchResult(
                    title=title,
                    entity_type=entity_type if isinstance(entity_type, str) else None,
                    relative_path=rel_path,
                    match_context=context or f"Matched {score} terms",
                ), score))

    # Sort by score descending
    results.sort(key=lambda x: x[1], reverse=True)
    return [r for r, _score in results[:max_results]]


def _find_match_context(title: str, body: str, frontmatter: dict[str, object], query_lower: str) -> str | None:
    if query_lower in title.lower():
        return f"Title: {title}"

    for key, value in frontmatter.items():
        if isinstance(value, str) and query_lower in value.lower():
            return f"{key}: {value}"
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str) and query_lower in item.lower():
                    return f"{key}: {item}"

    for line in body.splitlines():
        if query_lower in line.lower():
            stripped = line.strip()[:120]
            return stripped if stripped else None

    return None


def _score_by_tokens(title: str, body: str, frontmatter: dict[str, object], tokens: list[str]) -> tuple[int, str | None]:
    """Score a note by how many query tokens it matches."""
    full_text = f"{title} {body}".lower()
    fm_text = " ".join(
        str(v) for v in frontmatter.values()
        if isinstance(v, str)
    ).lower()
    related = frontmatter.get("related", [])
    related_text = " ".join(str(r) for r in related if isinstance(r, str)).lower()

    all_text = f"{full_text} {fm_text} {related_text}"

    matched = 0
    first_context = None
    for token in tokens:
        if token in all_text:
            matched += 1
            if first_context is None:
                # Find a line with this token for context
                if token in title.lower():
                    first_context = f"Title: {title}"
                else:
                    for line in body.splitlines():
                        if token in line.lower() and line.strip():
                            first_context = line.strip()[:120]
                            break

    return matched, first_context


__all__ = [
    "SearchResult",
    "search_notes",
]
