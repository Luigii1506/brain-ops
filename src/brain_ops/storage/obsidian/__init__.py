"""Obsidian storage adapters."""

from brain_ops.storage.obsidian.note_creation import build_note_document
from brain_ops.storage.obsidian.note_inference import infer_note_title_from_relative_path, infer_note_type_from_relative_path
from brain_ops.storage.obsidian.note_listing import list_vault_markdown_notes, recent_relative_note_paths
from brain_ops.storage.obsidian.note_loading import (
    load_note_document,
    load_optional_note_document,
    read_note_text,
    relative_note_path,
    resolve_note_document_path,
)
from brain_ops.storage.obsidian.note_metadata import (
    apply_note_frontmatter_defaults,
    apply_note_frontmatter_defaults_with_change,
)
from brain_ops.storage.obsidian.note_paths import (
    build_note_path,
    resolve_folder,
    resolve_inbox_destination_path,
    resolve_note_path,
)
from brain_ops.storage.obsidian.report_writing import (
    build_in_memory_report_operation,
    build_report_operation,
    timestamped_report_name,
    write_report_text,
)
from brain_ops.storage.obsidian.note_templates import resolve_note_template_path, template_for_note_type
from brain_ops.storage.obsidian.note_writing import (
    render_note_document,
    write_note_document,
    write_note_document_if_changed,
)

__all__ = [
    "apply_note_frontmatter_defaults",
    "apply_note_frontmatter_defaults_with_change",
    "build_note_path",
    "build_in_memory_report_operation",
    "build_note_document",
    "build_report_operation",
    "infer_note_title_from_relative_path",
    "infer_note_type_from_relative_path",
    "list_vault_markdown_notes",
    "load_note_document",
    "load_optional_note_document",
    "recent_relative_note_paths",
    "read_note_text",
    "relative_note_path",
    "resolve_folder",
    "resolve_inbox_destination_path",
    "resolve_note_path",
    "resolve_note_document_path",
    "resolve_note_template_path",
    "render_note_document",
    "timestamped_report_name",
    "template_for_note_type",
    "write_report_text",
    "write_note_document",
    "write_note_document_if_changed",
]
