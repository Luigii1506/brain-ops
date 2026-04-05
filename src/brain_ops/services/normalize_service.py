from __future__ import annotations

from brain_ops.domains.knowledge import normalize_note_frontmatter
from brain_ops.frontmatter import split_frontmatter
from brain_ops.models import AuditFinding, NormalizeFrontmatterSummary
from brain_ops.storage.obsidian import (
    apply_note_frontmatter_defaults,
    apply_note_frontmatter_defaults_with_change,
    list_vault_markdown_notes,
    read_note_text,
    write_note_document_if_changed,
)
from brain_ops.vault import Vault, now_iso


def normalize_frontmatter(vault: Vault) -> NormalizeFrontmatterSummary:
    summary = NormalizeFrontmatterSummary()
    for path in list_vault_markdown_notes(vault, excluded_parts={".git", ".obsidian", "07 - Archive"}):

        summary.scanned += 1
        _, relative, text = read_note_text(vault, path)
        try:
            frontmatter, body = split_frontmatter(text)
        except Exception as exc:
            summary.invalid.append(AuditFinding(path=relative, reason=str(exc)))
            summary.skipped += 1
            continue

        original = text
        changed = False
        frontmatter, semantic_changed = normalize_note_frontmatter(
            frontmatter,
            relative,
            systems_folder=vault.config.folders.systems,
            maps_folder=vault.config.folders.maps,
        )
        if semantic_changed:
            changed = True

        frontmatter, metadata_changed = apply_note_frontmatter_defaults_with_change(frontmatter, now=now_iso())
        if metadata_changed:
            changed = True

        operation = (
            write_note_document_if_changed(
                vault,
                path,
                frontmatter=frontmatter,
                body=body,
                original_content=original,
                overwrite=True,
            )
            if changed
            else None
        )
        if operation is not None:
            summary.operations.append(operation)
            summary.updated += 1
        else:
            summary.skipped += 1
    return summary
