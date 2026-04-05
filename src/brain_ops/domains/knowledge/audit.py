from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from brain_ops.models import AuditFinding, FolderAuditStats, VaultAuditSummary

KNOWN_NOTE_TYPES = {
    "inbox",
    "source",
    "knowledge",
    "permanent_note",
    "study_note",
    "idea",
    "map",
    "moc",
    "project",
    "project_note",
    "system",
    "command",
    "security_note",
    "sop",
    "runbook",
    "prompt",
    "script_doc",
    "daily",
    "architecture",
    "decision",
    "debugging_note",
    "changelog",
}

SYSTEM_LIKE_TYPES = {
    "system",
    "command",
    "security_note",
    "sop",
    "runbook",
    "prompt",
    "script_doc",
}


@dataclass(slots=True)
class AuditNoteAnalysis:
    note_type: str | None
    is_empty: bool
    is_very_short: bool
    moc_outside_maps: bool
    maps_with_few_links_reason: str | None
    system_note_outside_systems: bool
    source_note_outside_sources: bool
    unknown_type_reason: str | None


def looks_like_moc_note(relative_path: Path, frontmatter: dict[str, object]) -> bool:
    note_type = frontmatter.get("type")
    if isinstance(note_type, str) and note_type.strip() in {"moc", "map"}:
        return True
    return relative_path.name.lower().startswith("moc-")


def infer_audit_note_type(frontmatter: dict[str, object], relative_path: Path) -> str | None:
    note_type = frontmatter.get("type")
    if isinstance(note_type, str) and note_type.strip():
        return note_type.strip()
    if frontmatter.get("source_type"):
        return "source"
    if relative_path.name.lower().startswith("moc-"):
        return "moc"
    return None


def analyze_audit_note(
    text: str,
    frontmatter: dict[str, object],
    relative_path: Path,
    *,
    maps_folder: str,
    systems_folder: str,
    sources_folder: str,
) -> AuditNoteAnalysis:
    stripped_text = text.strip()
    top_level = relative_path.parts[0] if relative_path.parts else ""
    note_type = infer_audit_note_type(frontmatter, relative_path)
    link_count = text.count("[[") if top_level == maps_folder else 0

    unknown_type_reason = None
    if note_type and note_type not in KNOWN_NOTE_TYPES:
        unknown_type_reason = f"Unknown note type `{note_type}`."

    maps_with_few_links_reason = None
    if top_level == maps_folder and link_count < 3:
        maps_with_few_links_reason = f"Only {link_count} wikilinks found."

    return AuditNoteAnalysis(
        note_type=note_type,
        is_empty=not stripped_text,
        is_very_short=bool(stripped_text) and len(stripped_text) < 120,
        moc_outside_maps=looks_like_moc_note(relative_path, frontmatter) and top_level != maps_folder,
        maps_with_few_links_reason=maps_with_few_links_reason,
        system_note_outside_systems=bool(note_type in SYSTEM_LIKE_TYPES and top_level != systems_folder),
        source_note_outside_sources=bool(note_type == "source" and top_level != sources_folder),
        unknown_type_reason=unknown_type_reason,
    )


def accumulate_audit_note(
    summary: VaultAuditSummary,
    *,
    relative_path: Path,
    frontmatter: dict[str, object],
    analysis: AuditNoteAnalysis,
    in_root: bool,
) -> None:
    top_level = relative_path.parts[0] if relative_path.parts else ""
    stats = summary.folder_stats.setdefault(top_level, FolderAuditStats())
    stats.total += 1
    summary.total_notes += 1

    if frontmatter:
        stats.with_frontmatter += 1
        summary.with_frontmatter += 1
    else:
        summary.notes_missing_frontmatter.append(relative_path)

    if in_root:
        summary.notes_in_root.append(relative_path)

    if analysis.is_empty:
        stats.empty += 1
        summary.empty_notes.append(relative_path)
    elif analysis.is_very_short:
        stats.very_short += 1
        summary.very_short_notes.append(relative_path)

    if analysis.unknown_type_reason is not None:
        summary.notes_with_unknown_type.append(
            AuditFinding(path=relative_path, reason=analysis.unknown_type_reason)
        )

    if analysis.moc_outside_maps:
        summary.moc_outside_maps.append(relative_path)

    if analysis.maps_with_few_links_reason is not None:
        summary.maps_with_few_links.append(
            AuditFinding(path=relative_path, reason=analysis.maps_with_few_links_reason)
        )

    if analysis.system_note_outside_systems:
        summary.system_notes_outside_systems.append(relative_path)

    if analysis.source_note_outside_sources:
        summary.source_notes_outside_sources.append(relative_path)
