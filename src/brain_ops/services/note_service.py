from __future__ import annotations

from brain_ops.config import VaultConfig
from brain_ops.models import CreateNoteRequest, OperationRecord
from brain_ops.storage.obsidian import (
    build_note_document,
    resolve_note_path,
    write_note_document,
)
from brain_ops.vault import Vault, now_iso


def create_note(vault: Vault, request: CreateNoteRequest) -> OperationRecord:
    frontmatter, body = build_note_document(
        vault.config.template_dir,
        request=request,
        now=now_iso(),
    )
    path = resolve_note_path(vault, request.note_type, request.title, request.folder)
    return write_note_document(vault, path, frontmatter=frontmatter, body=body, overwrite=request.overwrite)
