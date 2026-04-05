from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from brain_ops.domains.knowledge.capture import (
    build_capture_body,
    build_capture_frontmatter,
    infer_capture_type,
)
from brain_ops.models import InboxItemResult


@dataclass(slots=True)
class InboxDisposition:
    result: InboxItemResult
    should_move: bool
    left_in_inbox: bool


def normalize_inbox_note(
    frontmatter: dict[str, object],
    body: str,
    *,
    improve_structure: bool,
) -> tuple[str | None, dict[str, object], str, bool]:
    normalized = False
    note_type = infer_inbox_note_type(frontmatter)
    raw_text = body.strip()

    if (not note_type or note_type == "inbox") and raw_text:
        note_type, _ = infer_capture_type(raw_text)
        normalized = True

    if note_type:
        frontmatter["type"] = note_type
        for key, value in build_capture_frontmatter(raw_text, note_type).items():
            if key not in frontmatter or frontmatter[key] in (None, ""):
                frontmatter[key] = value
                normalized = True
    else:
        if "type" not in frontmatter:
            frontmatter["type"] = "inbox"
            normalized = True
        if "status" not in frontmatter:
            frontmatter["status"] = "triage"
            normalized = True
        note_type = None

    if improve_structure and note_type and raw_text and not looks_structured(body):
        body = build_capture_body(raw_text, note_type)
        normalized = True

    return note_type, frontmatter, body, normalized


def infer_inbox_note_type(frontmatter: dict[str, object]) -> str | None:
    note_type = frontmatter.get("type")
    if isinstance(note_type, str) and note_type.strip():
        return note_type.strip()
    source_type = frontmatter.get("source_type")
    if isinstance(source_type, str) and source_type.strip():
        return "source"
    return None


def looks_structured(body: str) -> bool:
    stripped = body.strip()
    return stripped.startswith("# ") or "\n## " in stripped or stripped.startswith("## ")


def plan_inbox_disposition(
    *,
    source_path: Path,
    destination_path: Path | None,
    note_type: str | None,
    normalized: bool,
) -> InboxDisposition:
    if destination_path is None:
        return InboxDisposition(
            result=InboxItemResult(
                source_path=source_path,
                note_type=note_type,
                normalized=normalized,
                moved=False,
                reason="No unambiguous destination folder.",
            ),
            should_move=False,
            left_in_inbox=True,
        )

    if destination_path == source_path:
        return InboxDisposition(
            result=InboxItemResult(
                source_path=source_path,
                destination_path=destination_path,
                note_type=note_type,
                normalized=normalized,
                moved=False,
                reason="Already in destination folder.",
            ),
            should_move=False,
            left_in_inbox=True,
        )

    return InboxDisposition(
        result=InboxItemResult(
            source_path=source_path,
            destination_path=destination_path,
            note_type=note_type,
            normalized=normalized,
            moved=True,
            reason="Moved using note type mapping.",
        ),
        should_move=True,
        left_in_inbox=False,
    )
