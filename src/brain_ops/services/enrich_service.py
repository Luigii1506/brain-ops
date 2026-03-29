from __future__ import annotations

from pathlib import Path

from brain_ops.models import EnrichNoteResult
from brain_ops.services.apply_links_service import apply_link_suggestions
from brain_ops.services.improve_service import improve_note
from brain_ops.services.research_service import research_note
from brain_ops.vault import Vault


def enrich_note(
    vault: Vault,
    note_path: Path,
    *,
    improve: bool = True,
    research: bool = True,
    apply_links: bool = True,
    query: str | None = None,
    max_sources: int = 3,
    link_limit: int = 3,
) -> EnrichNoteResult:
    path = note_path.expanduser()
    if not path.is_absolute():
        path = vault.root / path
    safe_path = vault._safe_path(path)

    operations = []
    steps: list[str] = []

    if improve:
        improve_result = improve_note(vault, safe_path)
        operations.append(improve_result.operation)
        steps.append(f"improve-note: {improve_result.reason}")

    if research:
        research_result = research_note(vault, safe_path, query=query, max_sources=max_sources)
        operations.append(research_result.operation)
        steps.append(f"research-note: attached {len(research_result.sources)} source(s)")

    if apply_links:
        link_result = apply_link_suggestions(vault, safe_path, limit=link_limit)
        operations.append(link_result.operation)
        steps.append(f"apply-link-suggestions: inserted {len(link_result.applied_links)} link(s)")

    return EnrichNoteResult(
        path=safe_path,
        operations=operations,
        steps=steps,
        reason="Ran the configured note enrichment pipeline.",
    )
