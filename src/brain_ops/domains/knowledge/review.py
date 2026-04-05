from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from brain_ops.models import WeeklyReviewSummary


@dataclass(slots=True)
class ReviewNoteAnalysis:
    inbox_note: bool
    missing_frontmatter: bool
    stale_project: bool
    possible_orphan: bool


def is_stale_project_note(path: Path, relative: Path, stale_days: int) -> bool:
    cutoff = datetime.now() - timedelta(days=stale_days)
    return (
        relative.parts
        and relative.parts[0] == "04 - Projects"
        and datetime.fromtimestamp(path.stat().st_mtime) < cutoff
    )


def is_possible_orphan_note(relative: Path, body: str) -> bool:
    ignored_roots = {"00 - Inbox", "03 - Maps", "05 - Systems", "06 - Daily", "07 - Archive"}
    if not relative.parts or relative.parts[0] in ignored_roots:
        return False
    stripped_body = body.strip()
    if not stripped_body:
        return True
    return "[[" not in stripped_body and "](" not in stripped_body


def analyze_review_note(
    path: Path,
    relative: Path,
    frontmatter: dict[str, object],
    body: str,
    *,
    inbox_folder: str,
    stale_days: int,
) -> ReviewNoteAnalysis:
    return ReviewNoteAnalysis(
        inbox_note=bool(relative.parts and relative.parts[0] == inbox_folder),
        missing_frontmatter=not frontmatter,
        stale_project=is_stale_project_note(path, relative, stale_days),
        possible_orphan=is_possible_orphan_note(relative, body),
    )


def accumulate_review_note(
    summary: WeeklyReviewSummary,
    *,
    relative_path: Path,
    analysis: ReviewNoteAnalysis,
) -> None:
    if analysis.inbox_note:
        summary.inbox_notes.append(relative_path)

    if analysis.missing_frontmatter:
        summary.notes_missing_frontmatter.append(relative_path)

    if analysis.stale_project:
        summary.stale_project_notes.append(relative_path)

    if analysis.possible_orphan:
        summary.possible_orphans.append(relative_path)
