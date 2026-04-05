from __future__ import annotations

from pathlib import Path

from brain_ops.frontmatter import dump_frontmatter
from brain_ops.models import OperationRecord
from brain_ops.vault import Vault


def render_note_document(
    *,
    frontmatter: dict[str, object],
    body: str,
) -> str:
    return dump_frontmatter(frontmatter, body)


def write_note_document(
    vault: Vault,
    path: Path,
    *,
    frontmatter: dict[str, object],
    body: str,
    overwrite: bool = True,
) -> OperationRecord:
    return vault.write_text(path, render_note_document(frontmatter=frontmatter, body=body), overwrite=overwrite)


def write_note_document_if_changed(
    vault: Vault,
    path: Path,
    *,
    frontmatter: dict[str, object],
    body: str,
    original_content: str,
    overwrite: bool = True,
) -> OperationRecord | None:
    rendered = render_note_document(frontmatter=frontmatter, body=body)
    if rendered == original_content:
        return None
    return vault.write_text(path, rendered, overwrite=overwrite)
