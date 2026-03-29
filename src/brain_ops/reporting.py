from __future__ import annotations

from datetime import datetime
from pathlib import Path

from brain_ops.models import (
    ApplyLinksResult,
    BodyMetricsLogResult,
    BodyMetricsSummary,
    DailyHabitsSummary,
    DailyLogResult,
    DailyMacrosSummary,
    DailySummaryResult,
    EnrichNoteResult,
    ExpenseLogResult,
    HandleInputResult,
    HabitCheckinResult,
    InboxProcessSummary,
    LinkSuggestionResult,
    MealLogResult,
    NormalizeFrontmatterSummary,
    PromoteNoteResult,
    RouteDecisionResult,
    SupplementLogResult,
    SpendingSummary,
    VaultAuditSummary,
    WeeklyReviewSummary,
    WorkoutLogResult,
    WorkoutStatusSummary,
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


def render_meal_log(result: MealLogResult) -> str:
    lines = [
        f"# Meal Logged - {result.logged_at.isoformat(timespec='seconds')}",
        "",
        f"- meal_type: {result.meal_type or 'unspecified'}",
        f"- items: {len(result.items)}",
        f"- reason: {result.reason}",
        "",
        "## Items",
        "",
    ]
    if result.items:
        for item in result.items:
            lines.append(
                f"- {item.food_name} | grams={item.grams or '-'} | qty={item.quantity or '-'} | "
                f"cal={item.calories or '-'} | p={item.protein_g or '-'} | c={item.carbs_g or '-'} | f={item.fat_g or '-'}"
            )
    else:
        lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def render_daily_macros(summary: DailyMacrosSummary) -> str:
    lines = [
        f"# Daily Macros - {summary.date}",
        "",
        f"- meals_logged: {summary.meals_logged}",
        f"- items_logged: {summary.items_logged}",
        f"- calories: {summary.calories:.2f}",
        f"- protein_g: {summary.protein_g:.2f}",
        f"- carbs_g: {summary.carbs_g:.2f}",
        f"- fat_g: {summary.fat_g:.2f}",
        f"- database_path: `{summary.database_path}`",
        "",
    ]
    return "\n".join(lines)


def render_supplement_log(result: SupplementLogResult) -> str:
    lines = [
        f"# Supplement Logged - {result.logged_at.isoformat(timespec='seconds')}",
        "",
        f"- supplement_name: {result.supplement_name}",
        f"- amount: {result.amount if result.amount is not None else '-'}",
        f"- unit: {result.unit or '-'}",
        f"- reason: {result.reason}",
        "",
    ]
    return "\n".join(lines)


def render_habit_checkin(result: HabitCheckinResult) -> str:
    lines = [
        f"# Habit Check-in - {result.checked_at.isoformat(timespec='seconds')}",
        "",
        f"- habit_name: {result.habit_name}",
        f"- status: {result.status}",
        f"- reason: {result.reason}",
        "",
    ]
    return "\n".join(lines)


def render_daily_habits(summary: DailyHabitsSummary) -> str:
    lines = [
        f"# Daily Habits - {summary.date}",
        "",
        f"- total_checkins: {summary.total_checkins}",
        f"- habits: {len(summary.habits)}",
        f"- database_path: `{summary.database_path}`",
        "",
        "## By status",
        "",
    ]
    if summary.by_status:
        for status, count in sorted(summary.by_status.items()):
            lines.append(f"- {status}: {count}")
    else:
        lines.append("- None")
    lines.extend(["", "## Habits", ""])
    if summary.habits:
        lines.extend([f"- {habit}" for habit in summary.habits])
    else:
        lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def render_body_metrics_log(result: BodyMetricsLogResult) -> str:
    lines = [
        f"# Body Metrics Logged - {result.logged_at.isoformat(timespec='seconds')}",
        "",
        f"- weight_kg: {result.weight_kg if result.weight_kg is not None else '-'}",
        f"- body_fat_pct: {result.body_fat_pct if result.body_fat_pct is not None else '-'}",
        f"- waist_cm: {result.waist_cm if result.waist_cm is not None else '-'}",
        f"- reason: {result.reason}",
        "",
    ]
    return "\n".join(lines)


def render_body_metrics_status(summary: BodyMetricsSummary) -> str:
    lines = [
        f"# Body Metrics Status - {summary.date}",
        "",
        f"- entries_logged: {summary.entries_logged}",
        f"- latest_logged_at: {summary.latest_logged_at or '-'}",
        f"- latest_weight_kg: {summary.latest_weight_kg if summary.latest_weight_kg is not None else '-'}",
        f"- latest_body_fat_pct: {summary.latest_body_fat_pct if summary.latest_body_fat_pct is not None else '-'}",
        f"- latest_waist_cm: {summary.latest_waist_cm if summary.latest_waist_cm is not None else '-'}",
        f"- database_path: `{summary.database_path}`",
        "",
    ]
    return "\n".join(lines)


def render_workout_log(result: WorkoutLogResult) -> str:
    lines = [
        f"# Workout Logged - {result.logged_at.isoformat(timespec='seconds')}",
        "",
        f"- routine_name: {result.routine_name or 'unspecified'}",
        f"- exercises: {len(result.exercises)}",
        f"- reason: {result.reason}",
        "",
        "## Exercises",
        "",
    ]
    if result.exercises:
        for exercise in result.exercises:
            lines.append(
                f"- {exercise.exercise_name} | sets={exercise.sets} | reps={exercise.reps or '-'} | "
                f"weight_kg={exercise.weight_kg if exercise.weight_kg is not None else '-'} | note={exercise.note or '-'}"
            )
    else:
        lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def render_workout_status(summary: WorkoutStatusSummary) -> str:
    lines = [
        f"# Workout Status - {summary.date}",
        "",
        f"- workouts_logged: {summary.workouts_logged}",
        f"- total_sets: {summary.total_sets}",
        f"- unique_exercises: {len(summary.unique_exercises)}",
        f"- database_path: `{summary.database_path}`",
        "",
        "## Exercises",
        "",
    ]
    if summary.unique_exercises:
        lines.extend([f"- {exercise}" for exercise in summary.unique_exercises])
    else:
        lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def render_expense_log(result: ExpenseLogResult) -> str:
    lines = [
        f"# Expense Logged - {result.logged_at.isoformat(timespec='seconds')}",
        "",
        f"- amount: {result.amount:.2f} {result.currency}",
        f"- category: {result.category or '-'}",
        f"- merchant: {result.merchant or '-'}",
        f"- reason: {result.reason}",
        "",
    ]
    return "\n".join(lines)


def render_spending_summary(summary: SpendingSummary) -> str:
    lines = [
        f"# Spending Summary - {summary.date}",
        "",
        f"- transaction_count: {summary.transaction_count}",
        f"- total_amount: {summary.total_amount:.2f} {summary.currency}",
        f"- categories: {len(summary.by_category)}",
        f"- database_path: `{summary.database_path}`",
        "",
        "## By category",
        "",
    ]
    if summary.by_category:
        for category, total in summary.by_category.items():
            lines.append(f"- {category}: {total:.2f} {summary.currency}")
    else:
        lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def render_daily_log(result: DailyLogResult) -> str:
    lines = [
        f"# Daily Log - {result.logged_at.isoformat(timespec='seconds')}",
        "",
        f"- domain: {result.domain}",
        f"- reason: {result.reason}",
        "",
    ]
    return "\n".join(lines)


def render_daily_summary(result: DailySummaryResult) -> str:
    lines = [
        f"# Daily Summary - {result.date}",
        "",
        f"- path: `{result.path}`",
        f"- sections_written: {len(result.sections_written)}",
        f"- reason: {result.reason}",
        "",
        "## Sections",
        "",
    ]
    if result.sections_written:
        lines.extend([f"- {section}" for section in result.sections_written])
    else:
        lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def render_route_decision(result: RouteDecisionResult) -> str:
    lines = [
        "# Route Decision",
        "",
        f"- domain: {result.domain}",
        f"- command: {result.command}",
        f"- confidence: {result.confidence:.2f}",
        f"- routing_source: {result.routing_source}",
        f"- reason: {result.reason}",
        "",
        "## Extracted fields",
        "",
    ]
    if result.extracted_fields:
        for key, value in result.extracted_fields.items():
            lines.append(f"- {key}: {value}")
    else:
        lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def render_handle_input(result: HandleInputResult) -> str:
    lines = [
        "# Handle Input",
        "",
        f"- executed: {str(result.executed).lower()}",
        f"- domain: {result.target_domain or result.decision.domain}",
        f"- command: {result.executed_command or result.decision.command}",
        f"- confidence: {result.decision.confidence:.2f}",
        f"- routing_source: {result.routing_source or result.decision.routing_source}",
        f"- needs_follow_up: {str(result.needs_follow_up).lower()}",
        f"- reason: {result.reason}",
        "",
    ]
    if result.extracted_fields:
        lines.extend(["## Extracted Fields", ""])
        for key, value in result.extracted_fields.items():
            lines.append(f"- {key}: {value}")
        lines.append("")
    if result.assistant_message:
        lines.extend(["## Assistant Message", "", f"- {result.assistant_message}", ""])
    if result.sub_results:
        lines.extend(["## Sub Results", ""])
        for sub_result in result.sub_results:
            lines.append(
                f"- `{sub_result.input_text}` | executed={str(sub_result.executed).lower()} | "
                f"command={sub_result.executed_command or '-'} | domain={sub_result.target_domain or '-'}"
            )
        lines.append("")
    if result.follow_up:
        lines.extend(["## Follow up", "", f"- {result.follow_up}", ""])
    return "\n".join(lines)


def timestamped_report_name(prefix: str, now: datetime | None = None) -> str:
    now = now or datetime.now()
    return f"{prefix}-{now.strftime('%Y%m%d-%H%M%S')}"
