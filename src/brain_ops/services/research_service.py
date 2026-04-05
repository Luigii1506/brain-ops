from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

from brain_ops.domains.knowledge.research import (
    materialize_research_document,
    render_research_block,
    research_query_candidates,
    research_search_results,
    research_summary_text,
)
from brain_ops.models import ResearchNoteResult, ResearchSource
from brain_ops.storage.obsidian import load_note_document, write_note_document
from brain_ops.vault import Vault, now_iso

USER_AGENT = "brain-ops/0.2"


def research_note(vault: Vault, note_path: Path, query: str | None = None, max_sources: int = 3) -> ResearchNoteResult:
    safe_path, _, frontmatter, body = load_note_document(vault, note_path)
    resolved_query = (query or safe_path.stem).strip()
    sources, resolved_query = _search_wikipedia_with_fallback(resolved_query, safe_path.stem, max_sources=max_sources)
    research_block = render_research_block(resolved_query, sources)
    frontmatter, updated_body = materialize_research_document(
        frontmatter,
        body,
        research_block,
        now=now_iso(),
    )

    operation = write_note_document(vault, safe_path, frontmatter=frontmatter, body=updated_body, overwrite=True)
    return ResearchNoteResult(
        path=safe_path,
        query=resolved_query,
        sources=sources,
        operation=operation,
        reason=f"Added grounded research block from {len(sources)} Wikipedia source(s).",
    )


def _search_wikipedia(query: str, max_sources: int) -> list[ResearchSource]:
    search_url = (
        "https://en.wikipedia.org/w/api.php?action=opensearch"
        f"&search={quote(query)}&limit={max_sources}&namespace=0&format=json"
    )
    payload = _fetch_json(search_url)

    sources: list[ResearchSource] = []
    for title, url in research_search_results(payload):
        summary = _fetch_wikipedia_summary(title)
        if summary:
            sources.append(ResearchSource(title=title, url=url, summary=summary))
    return sources


def _search_wikipedia_with_fallback(query: str, title: str, max_sources: int) -> tuple[list[ResearchSource], str]:
    seen: set[str] = set()
    for candidate in research_query_candidates(query, title):
        normalized = candidate.strip()
        if not normalized or normalized.lower() in seen:
            continue
        seen.add(normalized.lower())
        sources = _search_wikipedia(normalized, max_sources=max_sources)
        if sources:
            return sources, normalized
    return [], query


def _fetch_wikipedia_summary(title: str) -> str:
    summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(title.replace(' ', '_'))}"
    payload = _fetch_json(summary_url)
    return research_summary_text(payload)


def _fetch_json(url: str) -> object:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8", "ignore"))
