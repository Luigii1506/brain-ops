from __future__ import annotations

from pathlib import Path

from brain_ops.config import VaultConfig
from brain_ops.vault import Vault


def build_note_path(vault: Vault, folder: str, title: str):
    return vault.note_path(folder, title)


def resolve_folder(config: VaultConfig, note_type: str, explicit_folder: str | None) -> str:
    if explicit_folder:
        return explicit_folder
    if note_type == "command":
        return f"{config.folders.systems}/Commands"
    if note_type == "security_note":
        return f"{config.folders.systems}/Security"
    return config.folder_for_note_type(note_type) or config.folders.inbox


def resolve_note_path(vault: Vault, note_type: str, title: str, explicit_folder: str | None = None):
    folder = resolve_folder(vault.config, note_type, explicit_folder)
    return build_note_path(vault, folder, title)


def resolve_inbox_destination_path(
    vault: Vault,
    note_path: Path,
    frontmatter: dict[str, object],
    *,
    ambiguous_project_types: set[str],
) -> Path | None:
    note_type = frontmatter.get("type")
    if not isinstance(note_type, str):
        return None

    if note_type in ambiguous_project_types:
        project_name = frontmatter.get("project")
        if not isinstance(project_name, str) or not project_name.strip():
            return None
        folder = f"{vault.config.folders.projects}/{project_name.strip()}"
        return build_note_path(vault, folder, note_path.stem)

    folder = resolve_folder(vault.config, note_type, None)
    return build_note_path(vault, folder, note_path.stem)
