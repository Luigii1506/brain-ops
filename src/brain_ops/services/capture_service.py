from __future__ import annotations

from brain_ops.domains.knowledge.capture import plan_capture_note
from brain_ops.models import CaptureResult, CreateNoteRequest
from brain_ops.services.note_service import create_note
from brain_ops.vault import Vault


def capture_text(
    vault: Vault,
    text: str,
    title: str | None = None,
    force_type: str | None = None,
    tags: list[str] | None = None,
) -> CaptureResult:
    plan = plan_capture_note(text, title=title, force_type=force_type)

    operation = create_note(
        vault,
        CreateNoteRequest(
            title=plan.title,
            note_type=plan.note_type,
            tags=tags or [],
            extra_frontmatter=plan.extra_frontmatter,
            body_override=plan.body,
        ),
    )
    return CaptureResult(
        title=plan.title,
        note_type=plan.note_type,
        path=operation.path,
        operation=operation,
        reason=plan.reason,
    )
