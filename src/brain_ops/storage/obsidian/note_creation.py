from __future__ import annotations

from pathlib import Path

from brain_ops.frontmatter import split_frontmatter
from brain_ops.models import CreateNoteRequest
from brain_ops.storage.obsidian.note_metadata import apply_note_frontmatter_defaults
from brain_ops.storage.obsidian.note_templates import resolve_note_template_path
from brain_ops.templates import render_template


def build_note_document(
    template_dir: Path,
    *,
    request: CreateNoteRequest,
    now: str,
) -> tuple[dict[str, object], str]:
    template_path = resolve_note_template_path(
        template_dir,
        note_type=request.note_type,
        explicit_template_name=request.template_name,
    )
    rendered = render_template(
        template_path,
        {
            "title": request.title,
            "created": now,
            "updated": now,
        },
    )
    frontmatter, body = split_frontmatter(rendered)
    frontmatter = apply_note_frontmatter_defaults(
        frontmatter,
        now=now,
        note_type=request.note_type,
        tags=request.tags if request.tags else None,
    )
    frontmatter["type"] = request.note_type
    for key, value in request.extra_frontmatter.items():
        frontmatter[key] = value
    if request.body_override is not None:
        body = request.body_override.strip()
    return frontmatter, body
