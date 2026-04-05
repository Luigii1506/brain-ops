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


def search_notes(
    notes: list[tuple[str, dict[str, object], str]],
    query: str,
    *,
    entity_only: bool = False,
    max_results: int = 20,
) -> list[SearchResult]:
    query_lower = query.lower()
    results: list[SearchResult] = []
    for rel_path, frontmatter, body in notes:
        if entity_only and not is_entity_note(frontmatter):
            continue

        name = frontmatter.get("name")
        title = str(name).strip() if isinstance(name, str) and name.strip() else rel_path
        entity_type = frontmatter.get("type") if is_entity_note(frontmatter) else None

        match_context = _find_match_context(title, body, frontmatter, query_lower)
        if match_context is not None:
            results.append(SearchResult(
                title=title,
                entity_type=entity_type if isinstance(entity_type, str) else None,
                relative_path=rel_path,
                match_context=match_context,
            ))
            if len(results) >= max_results:
                break
    return results


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


__all__ = [
    "SearchResult",
    "search_notes",
]
