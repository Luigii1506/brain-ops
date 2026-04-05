from __future__ import annotations

from datetime import datetime

from brain_ops.domains.knowledge import (
    accumulate_audit_note,
    analyze_audit_note,
)
from brain_ops.frontmatter import split_frontmatter
from brain_ops.models import (
    AuditFinding,
    VaultAuditSummary,
)
from brain_ops.reporting_knowledge import render_vault_audit
from brain_ops.storage.obsidian import (
    build_in_memory_report_operation,
    list_vault_markdown_notes,
    read_note_text,
    timestamped_report_name,
    write_report_text,
)
from brain_ops.vault import Vault


def audit_vault(vault: Vault, write_report: bool = False) -> VaultAuditSummary:
    summary = VaultAuditSummary(generated_at=datetime.now())
    all_notes = list_vault_markdown_notes(vault, excluded_parts={".git", ".obsidian"})

    for path in sorted(all_notes):
        safe_path, rel, text = read_note_text(vault, path)
        try:
            frontmatter, body = split_frontmatter(text)
        except Exception as exc:
            frontmatter = {}
            body = text.strip()
            summary.invalid_frontmatter.append(AuditFinding(path=rel, reason=str(exc)))

        analysis = analyze_audit_note(
            text,
            frontmatter,
            rel,
            maps_folder=vault.config.folders.maps,
            systems_folder=vault.config.folders.systems,
            sources_folder=vault.config.folders.sources,
        )
        accumulate_audit_note(
            summary,
            relative_path=rel,
            frontmatter=frontmatter,
            analysis=analysis,
            in_root=path.parent == vault.root,
        )

    if write_report:
        report_name = timestamped_report_name("vault-audit", summary.generated_at)
        summary.operations.append(write_report_text(vault, report_name, render_vault_audit(summary)))
    else:
        summary.operations.append(build_in_memory_report_operation(vault, "Vault audit generated in memory only."))
    return summary
