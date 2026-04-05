from __future__ import annotations

from brain_ops.models import ResearchSource

RESEARCH_START = "<!-- brain-ops:research:start -->"
RESEARCH_END = "<!-- brain-ops:research:end -->"


def render_research_block(query: str, sources: list[ResearchSource]) -> str:
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


def merge_research_block(body: str, research_block: str) -> str:
    stripped = body.strip()
    if RESEARCH_START in stripped and RESEARCH_END in stripped:
        start = stripped.index(RESEARCH_START)
        end = stripped.index(RESEARCH_END) + len(RESEARCH_END)
        return (stripped[:start].rstrip() + "\n\n" + research_block).strip()
    if not stripped:
        return research_block
    return stripped + "\n\n" + research_block


def materialize_research_document(
    frontmatter: dict[str, object],
    body: str,
    research_block: str,
    *,
    now: str,
) -> tuple[dict[str, object], str]:
    updated_frontmatter = dict(frontmatter)
    if updated_frontmatter.get("created") in (None, ""):
        updated_frontmatter["created"] = now
    updated_frontmatter["updated"] = now
    updated_frontmatter.setdefault("tags", [])
    return updated_frontmatter, merge_research_block(body, research_block)


def research_query_candidates(query: str, title: str) -> list[str]:
    candidates = [query.strip(), title.strip()]
    lowered = query.lower()
    if "idempot" in lowered:
        candidates.append("idempotence")
    if "retry" in lowered:
        candidates.append("retry")
    if "distributed" in lowered:
        candidates.append("distributed computing")
    return candidates


def research_search_results(payload: object) -> list[tuple[str, str]]:
    titles = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
    urls = payload[3] if isinstance(payload, list) and len(payload) > 3 else []

    results: list[tuple[str, str]] = []
    for title, url in zip(titles, urls, strict=False):
        if not isinstance(title, str) or not isinstance(url, str):
            continue
        normalized_title = title.strip()
        normalized_url = url.strip()
        if not normalized_title or not normalized_url:
            continue
        results.append((normalized_title, normalized_url))
    return results


def research_summary_text(payload: object) -> str:
    extract = payload.get("extract") if isinstance(payload, dict) else None
    if not isinstance(extract, str):
        return ""
    return extract.strip()
