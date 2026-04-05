from __future__ import annotations

from brain_ops.constants import PROJECT_SCAFFOLD_FILES
from brain_ops.domains.knowledge.projects import plan_project_scaffold
from brain_ops.models import CreateNoteRequest, OperationRecord
from brain_ops.services.note_service import create_note
from brain_ops.vault import Vault, sanitize_note_title


def create_project_scaffold(vault: Vault, project_name: str) -> list[OperationRecord]:
    safe_project_name = sanitize_note_title(project_name)
    project_folder = f"{vault.config.folders.projects}/{safe_project_name}"
    note_plans = plan_project_scaffold(safe_project_name, PROJECT_SCAFFOLD_FILES)
    operations: list[OperationRecord] = []
    for note_plan in note_plans:
        request = CreateNoteRequest(
            title=note_plan.title,
            note_type=note_plan.note_type,
            folder=project_folder,
            extra_frontmatter=note_plan.extra_frontmatter,
        )
        operations.append(create_note(vault, request))
    return operations
