from __future__ import annotations

from pathlib import Path

from brain_ops.vault import Vault


def list_vault_markdown_notes(
    vault: Vault,
    *,
    base_folder: str | None = None,
    excluded_parts: set[str] | None = None,
) -> list[Path]:
    excluded = excluded_parts or set()
    root = vault.path_for_folder(base_folder) if base_folder else vault.root
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.rglob("*.md")
        if path.is_file() and not any(part in excluded for part in path.parts)
    )


def recent_relative_note_paths(vault: Vault, paths: list[Path], limit: int = 10) -> list[Path]:
    return [
        path.relative_to(vault.root)
        for path in sorted(paths, key=lambda item: item.stat().st_mtime, reverse=True)[:limit]
    ]
