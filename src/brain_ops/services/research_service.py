from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

from brain_ops.frontmatter import dump_frontmatter, split_frontmatter
from brain_ops.models import ResearchNoteResult, ResearchSource
from brain_ops.vault import Vault, now_iso

USER_AGENT = "brain-ops/0.2"
RESEARCH_START = "<!-- brain-ops:research:start -->"
RESEARCH_END = "<!-- brain-ops:research:end -->"


def research_note(vault: Vault, note_path: Path, query: str | None = None, max_sources: int = 3) -> ResearchNoteResult:
    path = note_path.expanduser()
    if not path.is_absolute():
        path = vault.root / path
    safe_path = vault._safe_path(path)
    relative = vault.relative_path(safe_path)

    text = safe_path.read_text(encoding="utf-8", errors="ignore")
    frontmatter, body = split_frontmatter(text)
    resolved_query = (query or safe_path.stem).strip()
    sources, resolved_query = _search_wikipedia_with_fallback(resolved_query, safe_path.stem, max_sources=max_sources)
    research_block = _render_research_block(resolved_query, sources)
    updated_body = _merge_research_block(body, research_block)

    if frontmatter.get("created") in (None, ""):
        frontmatter["created"] = now_iso()
    frontmatter["updated"] = now_iso()
    frontmatter.setdefault("tags", [])

    operation = vault.write_text(safe_path, dump_frontmatter(frontmatter, updated_body), overwrite=True)
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
    titles = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
    urls = payload[3] if isinstance(payload, list) and len(payload) > 3 else []

    sources: list[ResearchSource] = []
    for title, url in zip(titles, urls, strict=False):
        if not title or not url:
            continue
        summary = _fetch_wikipedia_summary(title)
        if summary:
            sources.append(ResearchSource(title=title, url=url, summary=summary))
    return sources


def _search_wikipedia_with_fallback(query: str, title: str, max_sources: int) -> tuple[list[ResearchSource], str]:
    candidates = [query.strip(), title.strip()]
    lowered = query.lower()
    if "idempot" in lowered:
        candidates.append("idempotence")
    if "retry" in lowered:
        candidates.append("retry")
    if "distributed" in lowered:
        candidates.append("distributed computing")

    seen: set[str] = set()
    for candidate in candidates:
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
    extract = payload.get("extract") if isinstance(payload, dict) else None
    if not isinstance(extract, str):
        return ""
    return extract.strip()


def _fetch_json(url: str) -> object:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8", "ignore"))


def _render_research_block(query: str, sources: list[ResearchSource]) -> str:
    lines = [
        RESEARCH_START,
        "## Research",
        "",
        f"Query: `{query}`",
        "",
        "### Sources",
        "",
    ]
    if sources:
        for source in sources:
            lines.append(f"- [{source.title}]({source.url})")
    else:
        lines.append("- No external sources found.")

    lines.extend(["", "### External findings", ""])
    if sources:
        for source in sources:
            lines.append(f"#### {source.title}")
            lines.append("")
            lines.append(source.summary)
            lines.append("")
    else:
        lines.append("No grounded findings were retrieved.")
        lines.append("")
    lines.append(RESEARCH_END)
    return "\n".join(lines).strip()


def _merge_research_block(body: str, research_block: str) -> str:
    stripped = body.strip()
    if RESEARCH_START in stripped and RESEARCH_END in stripped:
        start = stripped.index(RESEARCH_START)
        end = stripped.index(RESEARCH_END) + len(RESEARCH_END)
        return (stripped[:start].rstrip() + "\n\n" + research_block).strip()
    if not stripped:
        return research_block
    return stripped + "\n\n" + research_block
