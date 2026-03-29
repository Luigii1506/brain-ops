from __future__ import annotations

from brain_ops.config import VaultConfig
from brain_ops.frontmatter import dump_frontmatter, split_frontmatter
from brain_ops.models import CreateNoteRequest, OperationRecord
from brain_ops.templates import render_template, resolve_template_path
from brain_ops.vault import Vault, now_iso


def template_for_note_type(note_type: str) -> str:
    mapping = {
        "project": "project",
        "project_note": "project",
        "source": "source",
        "knowledge": "knowledge",
        "permanent_note": "permanent_note",
        "map": "map",
        "moc": "map",
        "system": "system",
        "command": "system",
        "security_note": "system",
        "sop": "sop",
        "runbook": "runbook",
        "architecture": "architecture",
        "decision": "decision",
        "debugging_note": "debugging_note",
        "changelog": "changelog",
    }
    return mapping.get(note_type, "knowledge")


def resolve_folder(config: VaultConfig, note_type: str, explicit_folder: str | None) -> str:
    if explicit_folder:
        return explicit_folder
    if note_type == "command":
        return f"{config.folders.systems}/Commands"
    if note_type == "security_note":
        return f"{config.folders.systems}/Security"
    return config.folder_for_note_type(note_type) or config.folders.inbox


def create_note(vault: Vault, request: CreateNoteRequest) -> OperationRecord:
    template_name = request.template_name or template_for_note_type(request.note_type)
    template_path = resolve_template_path(vault.config.template_dir, template_name)
    rendered = render_template(
        template_path,
        {
            "title": request.title,
            "created": now_iso(),
            "updated": now_iso(),
        },
    )
    frontmatter, body = split_frontmatter(rendered)
    frontmatter["type"] = request.note_type
    if frontmatter.get("created") in (None, ""):
        frontmatter["created"] = now_iso()
    frontmatter["updated"] = now_iso()
    if request.tags:
        frontmatter["tags"] = request.tags
    for key, value in request.extra_frontmatter.items():
        frontmatter[key] = value
    if request.body_override is not None:
        body = request.body_override.strip()
    folder = resolve_folder(vault.config, request.note_type, request.folder)
    path = vault.note_path(folder, request.title)
    content = dump_frontmatter(frontmatter, body)
    return vault.write_text(path, content, overwrite=request.overwrite)
