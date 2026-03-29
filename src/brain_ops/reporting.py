from __future__ import annotations

from datetime import datetime
from pathlib import Path

from brain_ops.models import (
    ApplyLinksResult,
    EnrichNoteResult,
    InboxProcessSummary,
    LinkSuggestionResult,
    NormalizeFrontmatterSummary,
    PromoteNoteResult,
    VaultAuditSummary,
    WeeklyReviewSummary,
)


def render_inbox_report(summary: InboxProcessSummary) -> str:
    lines = [
        "# Inbox Processing Report",
        "",
        f"- scanned: {summary.scanned}",
        f"- normalized: {summary.normalized}",
        f"- moved: {summary.moved}",
        f"- left_in_inbox: {summary.left_in_inbox}",
        "",
        "## Item details",
        "",
    ]
    for item in summary.items:
        destination = item.destination_path if item.destination_path else "stayed in inbox"
        lines.append(f"- `{item.source_path.name}` -> `{destination}` | {item.reason}")
    if not summary.items:
        lines.append("- No inbox notes found.")
    lines.append("")
    return "\n".join(lines)


def render_weekly_review(summary: WeeklyReviewSummary) -> str:
    generated_at = summary.generated_at.isoformat(timespec="seconds")
    sections: list[tuple[str, list[Path]]] = [
        ("Inbox Notes", summary.inbox_notes),
        ("Notes Missing Frontmatter", summary.notes_missing_frontmatter),
        ("Stale Project Notes", summary.stale_project_notes),
        ("Possible Orphans", summary.possible_orphans),
        ("Recent Changes", summary.recent_changes),
    ]
    lines = [f"# Weekly Review - {generated_at}", ""]
    for title, items in sections:
        lines.extend([f"## {title}", ""])
        if items:
            for item in items:
                lines.append(f"- `{item}`")
        else:
            lines.append("- None")
        lines.append("")
    return "\n".join(lines)


def render_vault_audit(summary: VaultAuditSummary) -> str:
    generated_at = summary.generated_at.isoformat(timespec="seconds")
    lines = [
        f"# Vault Audit - {generated_at}",
        "",
        "## Summary",
        "",
        f"- total_notes: {summary.total_notes}",
        f"- with_frontmatter: {summary.with_frontmatter}",
        f"- missing_frontmatter: {len(summary.notes_missing_frontmatter)}",
        f"- invalid_frontmatter: {len(summary.invalid_frontmatter)}",
        f"- empty_notes: {len(summary.empty_notes)}",
        f"- very_short_notes: {len(summary.very_short_notes)}",
        f"- moc_outside_maps: {len(summary.moc_outside_maps)}",
        f"- maps_with_few_links: {len(summary.maps_with_few_links)}",
        f"- system_notes_outside_systems: {len(summary.system_notes_outside_systems)}",
        f"- source_notes_outside_sources: {len(summary.source_notes_outside_sources)}",
        f"- notes_in_root: {len(summary.notes_in_root)}",
        "",
        "## Folder Stats",
        "",
    ]

    for folder_name, stats in sorted(summary.folder_stats.items()):
        lines.append(
            f"- `{folder_name}`: total={stats.total}, frontmatter={stats.with_frontmatter}, "
            f"empty={stats.empty}, very_short={stats.very_short}"
        )

    sections: list[tuple[str, list[str]]] = [
        ("Notes In Root", [f"`{path}`" for path in summary.notes_in_root]),
        ("Notes Missing Frontmatter", [f"`{path}`" for path in summary.notes_missing_frontmatter[:50]]),
        (
            "Invalid Frontmatter",
            [f"`{finding.path}` | {finding.reason}" for finding in summary.invalid_frontmatter[:50]],
        ),
        ("Empty Notes", [f"`{path}`" for path in summary.empty_notes[:50]]),
        ("Very Short Notes", [f"`{path}`" for path in summary.very_short_notes[:50]]),
        ("MOCs Outside Maps", [f"`{path}`" for path in summary.moc_outside_maps]),
        (
            "Maps With Few Links",
            [f"`{finding.path}` | {finding.reason}" for finding in summary.maps_with_few_links],
        ),
        (
            "System Notes Outside Systems",
            [f"`{path}`" for path in summary.system_notes_outside_systems],
        ),
        (
            "Source Notes Outside Sources",
            [f"`{path}`" for path in summary.source_notes_outside_sources],
        ),
        (
            "Unknown Note Types",
            [f"`{finding.path}` | {finding.reason}" for finding in summary.notes_with_unknown_type],
        ),
    ]

    for title, items in sections:
        lines.extend(["", f"## {title}", ""])
        if items:
            lines.extend([f"- {item}" for item in items])
        else:
            lines.append("- None")

    lines.append("")
    return "\n".join(lines)


def render_normalize_frontmatter(summary: NormalizeFrontmatterSummary) -> str:
    lines = [
        "# Frontmatter Normalization Report",
        "",
        f"- scanned: {summary.scanned}",
        f"- updated: {summary.updated}",
        f"- skipped: {summary.skipped}",
        f"- invalid: {len(summary.invalid)}",
        "",
        "## Invalid frontmatter",
        "",
    ]
    if summary.invalid:
        for finding in summary.invalid:
            lines.append(f"- `{finding.path}` | {finding.reason}")
    else:
        lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def render_link_suggestions(result: LinkSuggestionResult) -> str:
    lines = [
        f"# Link Suggestions - `{result.target}`",
        "",
        f"- suggestions: {len(result.suggestions)}",
        f"- reason: {result.reason}",
        "",
        "## Candidates",
        "",
    ]
    if result.suggestions:
        for suggestion in result.suggestions:
            lines.append(
                f"- `{suggestion.path}` | score={suggestion.score} | {suggestion.reason}"
            )
    else:
        lines.append("- No link suggestions found.")
    lines.append("")
    return "\n".join(lines)


def render_applied_links(result: ApplyLinksResult) -> str:
    lines = [
        f"# Applied Links - `{result.target}`",
        "",
        f"- applied: {len(result.applied_links)}",
        f"- reason: {result.reason}",
        "",
        "## Links",
        "",
    ]
    if result.applied_links:
        lines.extend([f"- `[[{title}]]`" for title in result.applied_links])
    else:
        lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def render_promoted_note(result: PromoteNoteResult) -> str:
    lines = [
        f"# Promoted Note - `{result.source_path}`",
        "",
        f"- promoted_path: `{result.promoted_path}`",
        f"- promoted_type: `{result.promoted_type}`",
        f"- operations: {len(result.operations)}",
        f"- reason: {result.reason}",
        "",
    ]
    return "\n".join(lines)


def render_enriched_note(result: EnrichNoteResult) -> str:
    lines = [
        f"# Enriched Note - `{result.path}`",
        "",
        f"- operations: {len(result.operations)}",
        f"- reason: {result.reason}",
        "",
        "## Steps",
        "",
    ]
    if result.steps:
        lines.extend([f"- {step}" for step in result.steps])
    else:
        lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def timestamped_report_name(prefix: str, now: datetime | None = None) -> str:
    now = now or datetime.now()
    return f"{prefix}-{now.strftime('%Y%m%d-%H%M%S')}"
