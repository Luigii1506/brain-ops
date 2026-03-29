from __future__ import annotations

from datetime import datetime
from pathlib import Path

from brain_ops.frontmatter import split_frontmatter
from brain_ops.models import (
    AuditFinding,
    FolderAuditStats,
    OperationRecord,
    OperationStatus,
    VaultAuditSummary,
)
from brain_ops.reporting import render_vault_audit, timestamped_report_name
from brain_ops.vault import Vault

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


def audit_vault(vault: Vault, write_report: bool = False) -> VaultAuditSummary:
    summary = VaultAuditSummary(generated_at=datetime.now())
    all_notes = [
        path
        for path in vault.root.rglob("*.md")
        if path.is_file() and ".git" not in path.parts and ".obsidian" not in path.parts
    ]

    for path in sorted(all_notes):
        rel = vault.relative_path(path)
        text = path.read_text(encoding="utf-8", errors="ignore")
        try:
            frontmatter, body = split_frontmatter(text)
        except Exception as exc:
            frontmatter = {}
            body = text.strip()
            summary.invalid_frontmatter.append(AuditFinding(path=rel, reason=str(exc)))
        top_level = rel.parts[0] if rel.parts else ""
        stats = summary.folder_stats.setdefault(top_level, FolderAuditStats())
        stats.total += 1
        summary.total_notes += 1

        stripped_text = text.strip()
        if frontmatter:
            stats.with_frontmatter += 1
            summary.with_frontmatter += 1
        else:
            summary.notes_missing_frontmatter.append(rel)

        if path.parent == vault.root:
            summary.notes_in_root.append(rel)

        if not stripped_text:
            stats.empty += 1
            summary.empty_notes.append(rel)
        elif len(stripped_text) < 120:
            stats.very_short += 1
            summary.very_short_notes.append(rel)

        note_type = _inferred_note_type(frontmatter, rel)
        if note_type and note_type not in KNOWN_NOTE_TYPES:
            summary.notes_with_unknown_type.append(
                AuditFinding(path=rel, reason=f"Unknown note type `{note_type}`.")
            )

        if _looks_like_moc(rel, frontmatter) and top_level != vault.config.folders.maps:
            summary.moc_outside_maps.append(rel)

        if top_level == vault.config.folders.maps:
            link_count = text.count("[[")
            if link_count < 3:
                summary.maps_with_few_links.append(
                    AuditFinding(path=rel, reason=f"Only {link_count} wikilinks found.")
                )

        if note_type in SYSTEM_LIKE_TYPES and top_level != vault.config.folders.systems:
            summary.system_notes_outside_systems.append(rel)

        if note_type == "source" and top_level != vault.config.folders.sources:
            summary.source_notes_outside_sources.append(rel)

    if write_report:
        report_name = timestamped_report_name("vault-audit", summary.generated_at)
        report_path = vault.report_path(report_name)
        summary.operations.append(vault.write_text(report_path, render_vault_audit(summary), overwrite=False))
    else:
        summary.operations.append(
            OperationRecord(
                action="report",
                path=vault.root,
                detail="Vault audit generated in memory only.",
                status=OperationStatus.REPORT,
            )
        )
    return summary


def _looks_like_moc(relative_path: Path, frontmatter: dict[str, object]) -> bool:
    note_type = frontmatter.get("type")
    if isinstance(note_type, str) and note_type.strip() in {"moc", "map"}:
        return True
    return relative_path.name.lower().startswith("moc-")


def _inferred_note_type(frontmatter: dict[str, object], relative_path: Path) -> str | None:
    note_type = frontmatter.get("type")
    if isinstance(note_type, str) and note_type.strip():
        return note_type.strip()
    if frontmatter.get("source_type"):
        return "source"
    if relative_path.name.lower().startswith("moc-"):
        return "moc"
    return None
