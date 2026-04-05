from __future__ import annotations

from pathlib import Path

from brain_ops.domains.knowledge.linking import build_note_terms, existing_wikilinks, suggest_link_candidate
from brain_ops.models import LinkSuggestionResult
from brain_ops.storage.obsidian import (
    build_report_operation,
    list_vault_markdown_notes,
    load_note_document,
    relative_note_path,
)
from brain_ops.vault import Vault

EXCLUDED_TOP_LEVEL = {"06 - Daily", "07 - Archive", "Clippings", "Tags", "Templates"}


def suggest_links(vault: Vault, note_path: Path, limit: int = 8) -> LinkSuggestionResult:
    safe_path, target_rel, frontmatter, body = load_note_document(vault, note_path)

    target_terms = build_note_terms(safe_path.stem, frontmatter, body)
    existing_links = existing_wikilinks(body)

    suggestions: list[LinkSuggestion] = []
    for candidate in list_vault_markdown_notes(
        vault,
        excluded_parts={".obsidian", "07 - Archive", "Clippings", "Tags", "Templates", "Reports"},
    ):
        if candidate == safe_path:
            continue
        candidate_rel = relative_note_path(vault, candidate)
        if candidate_rel.parts and candidate_rel.parts[0] in EXCLUDED_TOP_LEVEL:
            continue
        _, _, candidate_frontmatter, candidate_body = load_note_document(vault, candidate)
        suggestion = suggest_link_candidate(
            path=candidate_rel,
            candidate_name=candidate.stem,
            candidate_frontmatter=candidate_frontmatter,
            candidate_body=candidate_body,
            target_terms=target_terms,
            existing_links=existing_links,
            target_body=body,
        )
        if suggestion is not None:
            suggestions.append(suggestion)

    suggestions.sort(key=lambda item: (-item.score, str(item.path)))
    return LinkSuggestionResult(
        target=target_rel,
        suggestions=suggestions[:limit],
        operation=build_report_operation(safe_path, f"Generated {min(len(suggestions), limit)} link suggestion(s)."),
        reason="Suggested links using lexical overlap and note metadata.",
    )
