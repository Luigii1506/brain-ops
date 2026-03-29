from __future__ import annotations

from brain_ops.constants import PROJECT_SCAFFOLD_FILES
from brain_ops.models import CreateNoteRequest, OperationRecord
from brain_ops.services.note_service import create_note
from brain_ops.vault import Vault, sanitize_note_title


def create_project_scaffold(vault: Vault, project_name: str) -> list[OperationRecord]:
    safe_project_name = sanitize_note_title(project_name)
    project_folder = f"{vault.config.folders.projects}/{safe_project_name}"
    operations: list[OperationRecord] = []
    for note_type, title_template in PROJECT_SCAFFOLD_FILES:
        note_title = title_template.format(title=safe_project_name)
        request = CreateNoteRequest(
            title=note_title,
            note_type=note_type,
            folder=project_folder,
            extra_frontmatter={"project": safe_project_name},
        )
        operations.append(create_note(vault, request))
    return operations
