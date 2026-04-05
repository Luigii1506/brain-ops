from __future__ import annotations

from collections import Counter
import re

from brain_ops.models import LinkSuggestion

SECTION_PATTERNS = [
    re.compile(r"^## Links\s*$", re.MULTILINE),
    re.compile(r"^## Related notes\s*$", re.MULTILINE),
    re.compile(r"^## Entry points\s*$", re.MULTILINE),
]
TOKEN_PATTERN = re.compile(r"[A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9_-]{2,}")
WIKILINK_PATTERN = re.compile(r"\[\[([^\]|#]+)")
STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "sobre", "para",
    "como", "con", "una", "uno", "las", "los", "del", "que", "por", "todo", "toda",
    "nota", "map", "moc", "de", "la", "el", "en", "un", "y", "to", "of", "or",
    "core", "idea", "links", "link", "source", "summary", "related", "notes", "note",
    "purpose", "entry", "points", "status", "current", "what", "should", "contain",
    "existing", "content", "why", "matters", "objective", "procedure", "history",
    "information", "general", "context", "research", "external", "findings", "query",
    "principal", "saber", "concept", "one", "such", "sources",
}
URL_PATTERN = re.compile(r"https?://\S+")
RESEARCH_BLOCK_PATTERN = re.compile(
    r"<!-- brain-ops:research:start -->.*?<!-- brain-ops:research:end -->",
    re.DOTALL,
)


def insert_links(body: str, link_titles: list[str]) -> str:
    if not link_titles:
        return body.strip()

    lines = body.splitlines()
    existing = set(re.findall(r"\[\[([^\]|#]+)", body))
    links_to_add = [title for title in link_titles if title not in existing]
    if not links_to_add:
        return body.strip()

    for pattern in SECTION_PATTERNS:
        for index, line in enumerate(lines):
            if pattern.match(line):
                insert_at = index + 1
                while insert_at < len(lines) and lines[insert_at].strip() == "":
                    insert_at += 1
                additions = [f"- [[{title}]]" for title in links_to_add]
                lines[insert_at:insert_at] = [""] + additions
                return "\n".join(lines).strip()

    additions = "\n".join(f"- [[{title}]]" for title in links_to_add)
    suffix = "\n\n## Links\n\n" + additions
    return body.strip() + suffix


def materialize_linked_document(
    frontmatter: dict[str, object],
    body: str,
    link_titles: list[str],
    *,
    now: str,
) -> tuple[dict[str, object], str]:
    updated_frontmatter = dict(frontmatter)
    if updated_frontmatter.get("created") in (None, ""):
        updated_frontmatter["created"] = now
    updated_frontmatter["updated"] = now
    updated_frontmatter.setdefault("tags", [])
    return updated_frontmatter, insert_links(body, link_titles)


def tokenize(text: str) -> list[str]:
    return [
        token.lower()
        for token in TOKEN_PATTERN.findall(text)
        if token.lower() not in STOPWORDS
    ]


def existing_wikilinks(body: str) -> set[str]:
    return {match.strip() for match in WIKILINK_PATTERN.findall(body)}


def build_note_terms(title: str, frontmatter: dict[str, object], body: str) -> Counter[str]:
    alias_terms: list[str] = []
    aliases = frontmatter.get("aliases")
    if isinstance(aliases, list):
        for alias in aliases:
            if isinstance(alias, str):
                alias_terms.extend(tokenize(alias))
    tokens = tokenize(title)
    tokens.extend(alias_terms)
    clean_body = RESEARCH_BLOCK_PATTERN.sub(" ", body)
    clean_body = URL_PATTERN.sub(" ", clean_body)
    tokens.extend(tokenize(clean_body)[:80])
    return Counter(tokens)


def score_terms(
    target_terms: Counter[str],
    candidate_terms: Counter[str],
    candidate_name: str,
    target_body: str,
) -> tuple[float, str]:
    shared = set(target_terms) & set(candidate_terms)
    if not shared:
        return 0.0, ""

    overlap = sum(min(target_terms[token], candidate_terms[token]) for token in shared)
    if overlap < 2:
        return 0.0, ""
    score = overlap / max(3, min(sum(target_terms.values()), sum(candidate_terms.values())))

    reason_parts: list[str] = []
    top_shared = sorted(shared, key=lambda token: (-min(target_terms[token], candidate_terms[token]), token))[:4]
    if top_shared:
        reason_parts.append("shared terms: " + ", ".join(top_shared))
    if candidate_name in target_body:
        score += 0.15
        reason_parts.append("candidate title appears in note body")

    if score < 0.08:
        return 0.0, ""
    return score, "; ".join(reason_parts)


def suggest_link_candidate(
    *,
    path,
    candidate_name: str,
    candidate_frontmatter: dict[str, object],
    candidate_body: str,
    target_terms: Counter[str],
    existing_links: set[str],
    target_body: str,
) -> LinkSuggestion | None:
    if candidate_name in existing_links:
        return None

    candidate_terms = build_note_terms(candidate_name, candidate_frontmatter, candidate_body)
    score, reason = score_terms(target_terms, candidate_terms, candidate_name, target_body)
    if score <= 0:
        return None
    return LinkSuggestion(path=path, score=round(score, 3), reason=reason)
