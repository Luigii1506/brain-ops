from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from brain_ops.frontmatter import split_frontmatter
from brain_ops.models import LinkSuggestion, LinkSuggestionResult, OperationRecord, OperationStatus
from brain_ops.vault import Vault

TOKEN_PATTERN = re.compile(r"[A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9_-]{2,}")
WIKILINK_PATTERN = re.compile(r"\[\[([^\]|#]+)")
URL_PATTERN = re.compile(r"https?://\S+")
RESEARCH_BLOCK_PATTERN = re.compile(
    r"<!-- brain-ops:research:start -->.*?<!-- brain-ops:research:end -->",
    re.DOTALL,
)
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

EXCLUDED_TOP_LEVEL = {"06 - Daily", "07 - Archive", "Clippings", "Tags", "Templates"}


def suggest_links(vault: Vault, note_path: Path, limit: int = 8) -> LinkSuggestionResult:
    path = note_path.expanduser()
    if not path.is_absolute():
        path = vault.root / path
    safe_path = vault._safe_path(path)
    target_rel = vault.relative_path(safe_path)
    text = safe_path.read_text(encoding="utf-8", errors="ignore")
    frontmatter, body = split_frontmatter(text)

    target_terms = _note_terms(safe_path.stem, frontmatter, body)
    existing_links = _existing_wikilinks(body)

    suggestions: list[LinkSuggestion] = []
    for candidate in sorted(vault.root.rglob("*.md")):
        if not candidate.is_file() or candidate == safe_path:
            continue
        if ".obsidian" in candidate.parts:
            continue
        candidate_rel = vault.relative_path(candidate)
        if candidate_rel.parts and candidate_rel.parts[0] in EXCLUDED_TOP_LEVEL:
            continue
        if "Reports" in candidate_rel.parts:
            continue
        candidate_text = candidate.read_text(encoding="utf-8", errors="ignore")
        candidate_frontmatter, candidate_body = split_frontmatter(candidate_text)
        candidate_name = candidate.stem
        if candidate_name in existing_links:
            continue

        candidate_terms = _note_terms(candidate_name, candidate_frontmatter, candidate_body)
        score, reason = _score_terms(target_terms, candidate_terms, candidate_name, body)
        if score <= 0:
            continue
        suggestions.append(LinkSuggestion(path=candidate_rel, score=round(score, 3), reason=reason))

    suggestions.sort(key=lambda item: (-item.score, str(item.path)))
    return LinkSuggestionResult(
        target=target_rel,
        suggestions=suggestions[:limit],
        operation=OperationRecord(
            action="report",
            path=safe_path,
            detail=f"Generated {min(len(suggestions), limit)} link suggestion(s).",
            status=OperationStatus.REPORT,
        ),
        reason="Suggested links using lexical overlap and note metadata.",
    )


def _note_terms(title: str, frontmatter: dict[str, object], body: str) -> Counter[str]:
    alias_terms: list[str] = []
    aliases = frontmatter.get("aliases")
    if isinstance(aliases, list):
        for alias in aliases:
            if isinstance(alias, str):
                alias_terms.extend(_tokenize(alias))
    tokens = _tokenize(title)
    tokens.extend(alias_terms)
    clean_body = RESEARCH_BLOCK_PATTERN.sub(" ", body)
    clean_body = URL_PATTERN.sub(" ", clean_body)
    tokens.extend(_tokenize(clean_body)[:80])
    return Counter(tokens)


def _tokenize(text: str) -> list[str]:
    return [
        token.lower()
        for token in TOKEN_PATTERN.findall(text)
        if token.lower() not in STOPWORDS
    ]


def _existing_wikilinks(body: str) -> set[str]:
    return {match.strip() for match in WIKILINK_PATTERN.findall(body)}


def _score_terms(
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
