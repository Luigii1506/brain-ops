from __future__ import annotations

from pathlib import Path

from brain_ops.domains.projects.doc_layout import (
    SCAFFOLD_DIRS_V1,
    SCAFFOLD_SPEC_V1,
)
from brain_ops.domains.knowledge.projects import plan_project_scaffold
from brain_ops.models import CreateNoteRequest, OperationRecord
from brain_ops.services.note_service import create_note
from brain_ops.vault import Vault, sanitize_note_title


def create_project_scaffold(vault: Vault, project_name: str) -> list[OperationRecord]:
    safe_project_name = sanitize_note_title(project_name)
    project_folder = f"{vault.config.folders.projects}/{safe_project_name}"

    # Create the layer subdirectories first.
    vault_root = Path(vault.config.vault_path)
    for subdir in SCAFFOLD_DIRS_V1:
        (vault_root / project_folder / subdir).mkdir(parents=True, exist_ok=True)

    # Plan and create scaffold notes in their respective layers.
    note_plans = plan_project_scaffold(safe_project_name, SCAFFOLD_SPEC_V1)
    operations: list[OperationRecord] = []
    for note_plan in note_plans:
        folder = (
            f"{project_folder}/{note_plan.folder_suffix}"
            if note_plan.folder_suffix
            else project_folder
        )
        request = CreateNoteRequest(
            title=note_plan.title,
            note_type=note_plan.note_type,
            folder=folder,
            extra_frontmatter=note_plan.extra_frontmatter,
        )
        operations.append(create_note(vault, request))
    return operations
