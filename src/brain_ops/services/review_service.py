from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from brain_ops.frontmatter import split_frontmatter
from brain_ops.models import OperationRecord, OperationStatus, WeeklyReviewSummary
from brain_ops.reporting import render_weekly_review, timestamped_report_name
from brain_ops.vault import Vault


def generate_weekly_review(vault: Vault, stale_days: int = 21, write_report: bool = False) -> WeeklyReviewSummary:
    summary = WeeklyReviewSummary(generated_at=datetime.now())
    all_notes = [
        path
        for path in vault.root.rglob("*.md")
        if path.is_file() and ".git" not in path.parts
    ]

    for path in all_notes:
        relative = vault.relative_path(path)
        text = path.read_text(encoding="utf-8")
        frontmatter, body = split_frontmatter(text)

        if relative.parts and relative.parts[0] == vault.config.folders.inbox:
            summary.inbox_notes.append(relative)

        if not frontmatter:
            summary.notes_missing_frontmatter.append(relative)

        if _is_stale_project(path, relative, stale_days):
            summary.stale_project_notes.append(relative)

        if _is_possible_orphan(relative, body):
            summary.possible_orphans.append(relative)

    summary.recent_changes = [
        vault.relative_path(path)
        for path in sorted(all_notes, key=lambda item: item.stat().st_mtime, reverse=True)[:10]
    ]

    if write_report:
        report_name = timestamped_report_name("weekly-review", summary.generated_at)
        report_path = vault.report_path(report_name)
        operation = vault.write_text(report_path, render_weekly_review(summary), overwrite=False)
        summary.operations.append(operation)
    else:
        summary.operations.append(
            OperationRecord(
                action="report",
                path=vault.root,
                detail="Weekly review generated in memory only.",
                status=OperationStatus.REPORT,
            )
        )
    return summary


def _is_stale_project(path: Path, relative: Path, stale_days: int) -> bool:
    cutoff = datetime.now() - timedelta(days=stale_days)
    return (
        relative.parts
        and relative.parts[0] == "04 - Projects"
        and datetime.fromtimestamp(path.stat().st_mtime) < cutoff
    )


def _is_possible_orphan(relative: Path, body: str) -> bool:
    ignored_roots = {"00 - Inbox", "03 - Maps", "05 - Systems", "06 - Daily", "07 - Archive"}
    if not relative.parts or relative.parts[0] in ignored_roots:
        return False
    stripped_body = body.strip()
    if not stripped_body:
        return True
    return "[[" not in stripped_body and "](" not in stripped_body
