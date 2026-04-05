from __future__ import annotations

from pathlib import Path

from brain_ops.domains.knowledge.improvement import improve_body, materialize_improved_document
from brain_ops.models import ImproveNoteResult
from brain_ops.storage.obsidian import (
    infer_note_title_from_relative_path,
    infer_note_type_from_relative_path,
    load_note_document,
    write_note_document,
)
from brain_ops.vault import Vault, now_iso


def improve_note(vault: Vault, note_path: Path) -> ImproveNoteResult:
    safe_path, relative, frontmatter, body = load_note_document(vault, note_path)

    note_type = str(frontmatter.get("type", infer_note_type_from_relative_path(relative)))
    title = infer_note_title_from_relative_path(relative)
    updated_body, reason = improve_body(note_type, title, body, frontmatter)
    frontmatter, updated_body = materialize_improved_document(
        frontmatter,
        updated_body,
        note_type=note_type,
        now=now_iso(),
    )

    operation = write_note_document(vault, safe_path, frontmatter=frontmatter, body=updated_body, overwrite=True)
    return ImproveNoteResult(
        path=safe_path,
        note_type=note_type,
        operation=operation,
        reason=reason,
    )
