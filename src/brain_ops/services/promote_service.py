from __future__ import annotations

import re
from pathlib import Path

from brain_ops.frontmatter import dump_frontmatter, split_frontmatter
from brain_ops.models import CreateNoteRequest, ImproveNoteResult, PromoteNoteResult
from brain_ops.services.improve_service import improve_note
from brain_ops.services.note_service import create_note
from brain_ops.vault import Vault, now_iso

SECTION_PATTERN = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


def promote_note(vault: Vault, note_path: Path, target_type: str | None = None) -> PromoteNoteResult:
    path = note_path.expanduser()
    if not path.is_absolute():
        path = vault.root / path
    safe_path = vault._safe_path(path)
    relative = vault.relative_path(safe_path)
    text = safe_path.read_text(encoding="utf-8", errors="ignore")
    frontmatter, body = split_frontmatter(text)

    source_type = str(frontmatter.get("type") or _infer_type_from_path(relative))
    resolved_target = target_type or _default_target_type(source_type, frontmatter)

    if source_type == "source" and resolved_target == "knowledge":
        return _promote_source_to_knowledge(vault, safe_path, relative, frontmatter, body)
    if source_type == "knowledge" and str(frontmatter.get("status", "")).lower() == "stub" and resolved_target == "knowledge":
        return _promote_stub_to_draft(vault, safe_path, relative)

    raise ValueError(f"Unsupported promotion path: {source_type} -> {resolved_target}")


def _default_target_type(source_type: str, frontmatter: dict[str, object]) -> str:
    if source_type == "source":
        return "knowledge"
    if source_type == "knowledge" and str(frontmatter.get("status", "")).lower() == "stub":
        return "knowledge"
    return source_type


def _promote_source_to_knowledge(
    vault: Vault,
    safe_path: Path,
    relative: Path,
    frontmatter: dict[str, object],
    body: str,
) -> PromoteNoteResult:
    source_title = safe_path.stem
    promoted_title = _normalize_promoted_title(source_title)
    sections = _extract_sections(body)
    summary = sections.get("Summary", "").strip()
    key_ideas = sections.get("Key ideas", "").strip()
    source_block = sections.get("Source", body).strip()

    promoted_body_parts = [
        f"# {promoted_title}",
        "",
        "## Core idea",
        "",
        summary or f"Derived from [[{source_title}]].",
        "",
        "## Key ideas",
        "",
        key_ideas or "- Extract the durable idea from the source.",
        "",
        "## Why it matters",
        "",
        "",
        "## Sources",
        "",
        f"- [[{source_title}]]",
    ]
    if source_block and source_block != body.strip():
        promoted_body_parts.extend(["", "## Source context", "", source_block])
    promoted_body_parts.extend(["", "## Links"])

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
            body_override="\n".join(promoted_body_parts),
            overwrite=False,
        ),
    )

    updated_source_frontmatter = dict(frontmatter)
    updated_source_frontmatter["updated"] = now_iso()
    updated_source_frontmatter["promoted_to"] = promoted_title
    updated_source_frontmatter.setdefault("tags", [])
    source_body = _ensure_related_note_link(body, promoted_title)
    source_update = vault.write_text(
        safe_path,
        dump_frontmatter(updated_source_frontmatter, source_body),
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
    text = safe_path.read_text(encoding="utf-8", errors="ignore")
    frontmatter, body = split_frontmatter(text)
    frontmatter["status"] = "draft"
    frontmatter["updated"] = now_iso()
    frontmatter.setdefault("type", "knowledge")
    frontmatter.setdefault("tags", [])

    update_operation = vault.write_text(safe_path, dump_frontmatter(frontmatter, body), overwrite=True)
    improve_result: ImproveNoteResult = improve_note(vault, relative)
    return PromoteNoteResult(
        source_path=safe_path,
        promoted_path=safe_path,
        promoted_type="knowledge",
        operations=[update_operation, improve_result.operation],
        reason="Promoted a knowledge stub to draft and expanded its structure.",
    )


def _normalize_promoted_title(title: str) -> str:
    cleaned = re.sub(r"^SN-", "", title, flags=re.IGNORECASE).strip()
    return cleaned or title


def _infer_type_from_path(relative: Path) -> str:
    top = relative.parts[0] if relative.parts else ""
    if top == "01 - Sources":
        return "source"
    if top == "02 - Knowledge":
        return "knowledge"
    return "knowledge"


def _extract_sections(body: str) -> dict[str, str]:
    matches = list(SECTION_PATTERN.finditer(body))
    if not matches:
        return {}

    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        sections[match.group(1).strip()] = body[start:end].strip()
    return sections


def _ensure_related_note_link(body: str, promoted_title: str) -> str:
    target_link = f"[[{promoted_title}]]"
    if target_link in body:
        return body.strip()

    if re.search(r"^## Related notes\s*$", body, flags=re.MULTILINE):
        lines = body.splitlines()
        for index, line in enumerate(lines):
            if line.strip() == "## Related notes":
                insert_at = index + 1
                while insert_at < len(lines) and lines[insert_at].strip() == "":
                    insert_at += 1
                lines[insert_at:insert_at] = ["", f"- {target_link}"]
                return "\n".join(lines).strip()

    suffix = "\n\n## Related notes\n\n- " + target_link
    return body.strip() + suffix
