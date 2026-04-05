from __future__ import annotations

from pathlib import Path

from brain_ops.domains.knowledge.linking import materialize_linked_document
from brain_ops.models import ApplyLinksResult
from brain_ops.services.link_service import suggest_links
from brain_ops.storage.obsidian import load_note_document, write_note_document
from brain_ops.vault import Vault, now_iso


def apply_link_suggestions(vault: Vault, note_path: Path, limit: int = 3) -> ApplyLinksResult:
    safe_path, relative, frontmatter, body = load_note_document(vault, note_path)

    suggestion_result = suggest_links(vault, safe_path, limit=limit)
    applied = [suggestion.path.stem for suggestion in suggestion_result.suggestions]
    frontmatter, updated_body = materialize_linked_document(
        frontmatter,
        body,
        applied,
        now=now_iso(),
    )

    operation = write_note_document(vault, safe_path, frontmatter=frontmatter, body=updated_body, overwrite=True)
    return ApplyLinksResult(
        target=relative,
        applied_links=applied,
        operation=operation,
        reason=f"Applied {len(applied)} suggested link(s).",
    )
