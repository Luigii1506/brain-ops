from __future__ import annotations

from pathlib import Path

from brain_ops.frontmatter import split_frontmatter
from brain_ops.vault import Vault


def resolve_note_document_path(vault: Vault, note_path: Path) -> tuple[Path, Path]:
    path = note_path.expanduser()
    if not path.is_absolute():
        path = vault.root / path
    safe_path = vault._safe_path(path)
    relative = vault.relative_path(safe_path)
    return safe_path, relative


def relative_note_path(vault: Vault, note_path: Path) -> Path:
    _, relative = resolve_note_document_path(vault, note_path)
    return relative


def read_note_text(vault: Vault, note_path: Path) -> tuple[Path, Path, str]:
    safe_path, relative = resolve_note_document_path(vault, note_path)
    text = safe_path.read_text(encoding="utf-8", errors="ignore")
    return safe_path, relative, text


def load_note_document(vault: Vault, note_path: Path) -> tuple[Path, Path, dict[str, object], str]:
    safe_path, relative, text = read_note_text(vault, note_path)
    frontmatter, body = split_frontmatter(text)
    return safe_path, relative, frontmatter, body


def load_optional_note_document(vault: Vault, note_path: Path) -> tuple[Path, Path, dict[str, object], str]:
    safe_path, relative = resolve_note_document_path(vault, note_path)
    if not safe_path.exists():
        return safe_path, relative, {}, ""
    _, _, frontmatter, body = load_note_document(vault, safe_path)
    return safe_path, relative, frontmatter, body
