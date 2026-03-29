from __future__ import annotations

from pathlib import Path

from brain_ops.frontmatter import dump_frontmatter, split_frontmatter
from brain_ops.models import InboxItemResult, InboxProcessSummary
from brain_ops.services.capture_service import (
    build_capture_body,
    build_capture_frontmatter,
    infer_capture_type,
)
from brain_ops.services.note_service import resolve_folder
from brain_ops.vault import Vault, now_iso

AMBIGUOUS_PROJECT_TYPES = {"decision", "debugging_note", "changelog", "architecture"}


def process_inbox(vault: Vault, improve_structure: bool = True) -> InboxProcessSummary:
    summary = InboxProcessSummary()
    inbox_notes = vault.list_markdown_files(vault.config.folders.inbox)
    for note_path in inbox_notes:
        summary.scanned += 1
        item_result = _process_single_note(vault, note_path, summary, improve_structure=improve_structure)
        summary.items.append(item_result)
    return summary


def _process_single_note(
    vault: Vault,
    note_path: Path,
    summary: InboxProcessSummary,
    improve_structure: bool,
) -> InboxItemResult:
    content = note_path.read_text(encoding="utf-8")
    frontmatter, body = split_frontmatter(content)
    normalized = False
    note_type = _infer_note_type(frontmatter)
    raw_text = body.strip()

    if (not note_type or note_type == "inbox") and raw_text:
        note_type, _ = infer_capture_type(raw_text)
        normalized = True

    if "created" not in frontmatter or frontmatter.get("created") in (None, ""):
        frontmatter["created"] = now_iso()
        normalized = True
    frontmatter["updated"] = now_iso()
    frontmatter.setdefault("tags", [])

    if note_type:
        frontmatter["type"] = note_type
        for key, value in build_capture_frontmatter(raw_text, note_type).items():
            if key not in frontmatter or frontmatter[key] in (None, ""):
                frontmatter[key] = value
                normalized = True
    else:
        frontmatter.setdefault("type", "inbox")
        frontmatter.setdefault("status", "triage")
        note_type = None

    if improve_structure and note_type and raw_text and not _looks_structured(body):
        body = build_capture_body(raw_text, note_type)
        normalized = True

    normalized_content = dump_frontmatter(frontmatter, body)
    if normalized_content != content:
        operation = vault.write_text(note_path, normalized_content, overwrite=True)
        summary.operations.append(operation)
        summary.normalized += 1
        normalized = True

    destination = _destination_for_note(vault, note_path, frontmatter)
    if destination is None:
        summary.left_in_inbox += 1
        return InboxItemResult(
            source_path=note_path,
            note_type=note_type,
            normalized=normalized,
            moved=False,
            reason="No unambiguous destination folder.",
        )

    if destination == note_path:
        summary.left_in_inbox += 1
        return InboxItemResult(
            source_path=note_path,
            destination_path=destination,
            note_type=note_type,
            normalized=normalized,
            moved=False,
            reason="Already in destination folder.",
        )

    operation = vault.move(note_path, destination)
    summary.operations.append(operation)
    summary.moved += 1
    return InboxItemResult(
        source_path=note_path,
        destination_path=destination,
        note_type=note_type,
        normalized=normalized,
        moved=True,
        reason="Moved using note type mapping.",
    )


def _infer_note_type(frontmatter: dict[str, object]) -> str | None:
    note_type = frontmatter.get("type")
    if isinstance(note_type, str) and note_type.strip():
        return note_type.strip()
    source_type = frontmatter.get("source_type")
    if isinstance(source_type, str) and source_type.strip():
        return "source"
    return None


def _destination_for_note(vault: Vault, note_path: Path, frontmatter: dict[str, object]) -> Path | None:
    note_type = frontmatter.get("type")
    if not isinstance(note_type, str):
        return None

    if note_type in AMBIGUOUS_PROJECT_TYPES:
        project_name = frontmatter.get("project")
        if not isinstance(project_name, str) or not project_name.strip():
            return None
        folder = f"{vault.config.folders.projects}/{project_name.strip()}"
        return vault.note_path(folder, note_path.stem)

    folder = resolve_folder(vault.config, note_type, None)
    return vault.note_path(folder, note_path.stem)


def _looks_structured(body: str) -> bool:
    stripped = body.strip()
    return stripped.startswith("# ") or "\n## " in stripped or stripped.startswith("## ")
