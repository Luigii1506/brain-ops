from __future__ import annotations

from pathlib import Path

from brain_ops.domains.knowledge import normalize_inbox_note, plan_inbox_disposition
from brain_ops.models import InboxItemResult, InboxProcessSummary
from brain_ops.storage.obsidian import (
    apply_note_frontmatter_defaults_with_change,
    list_vault_markdown_notes,
    load_note_document,
    read_note_text,
    resolve_inbox_destination_path,
    write_note_document_if_changed,
)
from brain_ops.vault import Vault, now_iso

AMBIGUOUS_PROJECT_TYPES = {"decision", "debugging_note", "changelog", "architecture"}


def process_inbox(vault: Vault, improve_structure: bool = True) -> InboxProcessSummary:
    summary = InboxProcessSummary()
    inbox_notes = list_vault_markdown_notes(vault, base_folder=vault.config.folders.inbox)
    for note_path in inbox_notes:
        summary.scanned += 1
        item_result = _process_single_note(vault, note_path, summary, improve_structure=improve_structure)
        summary.items.append(item_result)
    return summary


def _process_single_note(
    vault: Vault,
    note_path: Path,
    summary: InboxProcessSummary,
    improve_structure: bool,
) -> InboxItemResult:
    safe_path, _, frontmatter, body = load_note_document(vault, note_path)
    _, _, content = read_note_text(vault, safe_path)
    normalized = False

    frontmatter, metadata_changed = apply_note_frontmatter_defaults_with_change(frontmatter, now=now_iso())
    if metadata_changed:
        normalized = True

    note_type, frontmatter, body, inbox_normalized = normalize_inbox_note(
        frontmatter,
        body,
        improve_structure=improve_structure,
    )
    if inbox_normalized:
        normalized = True

    operation = write_note_document_if_changed(
        vault,
        safe_path,
        frontmatter=frontmatter,
        body=body,
        original_content=content,
        overwrite=True,
    )
    if operation is not None:
        summary.operations.append(operation)
        summary.normalized += 1
        normalized = True

    destination = resolve_inbox_destination_path(
        vault,
        note_path,
        frontmatter,
        ambiguous_project_types=AMBIGUOUS_PROJECT_TYPES,
    )
    disposition = plan_inbox_disposition(
        source_path=note_path,
        destination_path=destination,
        note_type=note_type,
        normalized=normalized,
    )
    if disposition.left_in_inbox:
        summary.left_in_inbox += 1
        return disposition.result

    operation = vault.move(note_path, destination)
    summary.operations.append(operation)
    summary.moved += 1
    return disposition.result
