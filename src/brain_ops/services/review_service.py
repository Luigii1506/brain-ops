from __future__ import annotations

from datetime import datetime

from brain_ops.domains.knowledge import accumulate_review_note, analyze_review_note
from brain_ops.models import WeeklyReviewSummary
from brain_ops.reporting_knowledge import render_weekly_review
from brain_ops.storage.obsidian import (
    build_in_memory_report_operation,
    list_vault_markdown_notes,
    load_note_document,
    recent_relative_note_paths,
    timestamped_report_name,
    write_report_text,
)
from brain_ops.vault import Vault


def generate_weekly_review(vault: Vault, stale_days: int = 21, write_report: bool = False) -> WeeklyReviewSummary:
    summary = WeeklyReviewSummary(generated_at=datetime.now())
    all_notes = list_vault_markdown_notes(vault, excluded_parts={".git"})

    for path in all_notes:
        _, relative, frontmatter, body = load_note_document(vault, path)
        analysis = analyze_review_note(
            path,
            relative,
            frontmatter,
            body,
            inbox_folder=vault.config.folders.inbox,
            stale_days=stale_days,
        )
        accumulate_review_note(summary, relative_path=relative, analysis=analysis)

    summary.recent_changes = recent_relative_note_paths(vault, all_notes, limit=10)

    if write_report:
        report_name = timestamped_report_name("weekly-review", summary.generated_at)
        operation = write_report_text(vault, report_name, render_weekly_review(summary))
        summary.operations.append(operation)
    else:
        summary.operations.append(build_in_memory_report_operation(vault, "Weekly review generated in memory only."))
    return summary
