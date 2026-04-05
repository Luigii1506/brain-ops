from __future__ import annotations

from pathlib import Path

from brain_ops.domains.knowledge.promotion import (
    build_promoted_knowledge_body,
    default_target_type,
    extract_sections,
    materialize_source_promotion,
    materialize_stub_promotion,
    normalize_promoted_title,
)
from brain_ops.models import CreateNoteRequest, ImproveNoteResult, PromoteNoteResult
from brain_ops.services.improve_service import improve_note
from brain_ops.services.note_service import create_note
from brain_ops.storage.obsidian import (
    infer_note_type_from_relative_path,
    load_note_document,
    write_note_document,
)
from brain_ops.vault import Vault, now_iso


def promote_note(vault: Vault, note_path: Path, target_type: str | None = None) -> PromoteNoteResult:
    safe_path, relative, frontmatter, body = load_note_document(vault, note_path)

    source_type = str(frontmatter.get("type") or infer_note_type_from_relative_path(relative))
    resolved_target = target_type or default_target_type(source_type, frontmatter)

    if source_type == "source" and resolved_target == "knowledge":
        return _promote_source_to_knowledge(vault, safe_path, relative, frontmatter, body)
    if source_type == "knowledge" and str(frontmatter.get("status", "")).lower() == "stub" and resolved_target == "knowledge":
        return _promote_stub_to_draft(vault, safe_path, relative)

    raise ValueError(f"Unsupported promotion path: {source_type} -> {resolved_target}")


def _promote_source_to_knowledge(
    vault: Vault,
    safe_path: Path,
    relative: Path,
    frontmatter: dict[str, object],
    body: str,
) -> PromoteNoteResult:
    source_title = safe_path.stem
    promoted_title = normalize_promoted_title(source_title)
    sections = extract_sections(body)
    summary = sections.get("Summary", "").strip()
    key_ideas = sections.get("Key ideas", "").strip()
    source_block = sections.get("Source", body).strip()

    operation = create_note(
        vault,
        CreateNoteRequest(
            title=promoted_title,
            note_type="knowledge",
            tags=list(frontmatter.get("tags", [])) if isinstance(frontmatter.get("tags"), list) else [],
            extra_frontmatter={
                "status": "draft",
                "derived_from": str(relative),
            },
            body_override=build_promoted_knowledge_body(
                promoted_title=promoted_title,
                source_title=source_title,
                summary=summary,
                key_ideas=key_ideas,
                source_block=source_block,
                original_body=body,
            ),
            overwrite=False,
        ),
    )

    updated_source_frontmatter, source_body = materialize_source_promotion(
        frontmatter,
        body,
        promoted_title,
        now=now_iso(),
    )
    source_update = write_note_document(
        vault,
        safe_path,
        frontmatter=updated_source_frontmatter,
        body=source_body,
        overwrite=True,
    )

    return PromoteNoteResult(
        source_path=safe_path,
        promoted_path=operation.path,
        promoted_type="knowledge",
        operations=[operation, source_update],
        reason="Created a draft knowledge note from a source and linked it back to the source note.",
    )


def _promote_stub_to_draft(vault: Vault, safe_path: Path, relative: Path) -> PromoteNoteResult:
    _, _, frontmatter, body = load_note_document(vault, safe_path)
    frontmatter, body = materialize_stub_promotion(frontmatter, body, now=now_iso())

    update_operation = write_note_document(vault, safe_path, frontmatter=frontmatter, body=body, overwrite=True)
    improve_result: ImproveNoteResult = improve_note(vault, relative)
    return PromoteNoteResult(
        source_path=safe_path,
        promoted_path=safe_path,
        promoted_type="knowledge",
        operations=[update_operation, improve_result.operation],
        reason="Promoted a knowledge stub to draft and expanded its structure.",
    )
