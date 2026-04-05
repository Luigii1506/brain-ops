from __future__ import annotations

from pathlib import Path

from brain_ops.core.validation import resolve_iso_date
from brain_ops.domains.knowledge.daily_summary import (
    build_daily_summary_expenses,
    build_daily_summary_body_metrics,
    build_daily_summary_daily_logs,
    build_daily_summary_meals,
    build_daily_summary_note_content,
    build_daily_summary_habits,
    build_daily_summary_supplements,
    build_daily_summary_workouts,
    daily_summary_note_title,
)
from brain_ops.models import DailySummaryResult
from brain_ops.services.diet_service import diet_status
from brain_ops.storage.obsidian import build_note_path, load_optional_note_document, write_note_document
from brain_ops.storage.sqlite import (
    fetch_daily_summary_context_rows,
)
from brain_ops.vault import Vault, now_iso


def write_daily_summary(vault: Vault, date_text: str | None = None) -> DailySummaryResult:
    resolved_date = resolve_iso_date(date_text)
    note_title = daily_summary_note_title(resolved_date)
    note_path = build_note_path(vault, vault.config.folders.daily, note_title)

    meals, meal_totals, supplements, workouts, expenses, expense_totals, habits, body_metrics, daily_logs = (
        _load_daily_summary_context(vault.config.database_path, resolved_date)
    )
    diet_progress = diet_status(vault.config.database_path, resolved_date)

    _, _, frontmatter, body = load_optional_note_document(vault, note_path)

    frontmatter, updated_body, sections = build_daily_summary_note_content(
        resolved_date,
        meals,
        meal_totals,
        supplements,
        workouts,
        expenses,
        expense_totals,
        habits,
        body_metrics,
        daily_logs,
        diet_progress,
        frontmatter=frontmatter,
        body=body,
        now=now_iso(),
    )
    operation = write_note_document(
        vault,
        note_path,
        frontmatter=frontmatter,
        body=updated_body,
        overwrite=True,
    )
    return DailySummaryResult(
        date=resolved_date,
        path=note_path,
        operations=[operation],
        sections_written=sections,
        reason="Wrote the structured daily summary block into the daily note.",
    )


def _load_daily_summary_context(
    database_path: Path,
    date_text: str,
) -> tuple[
    list[dict[str, object]],
    dict[str, float],
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
    dict[str, float],
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
]:
    start = f"{date_text}T00:00:00"
    end = f"{date_text}T23:59:59"
    rows = fetch_daily_summary_context_rows(database_path, start=start, end=end)
    meals, meal_totals = build_daily_summary_meals(rows["meal_rows"], rows["item_rows_by_meal"])
    expenses, expense_totals = build_daily_summary_expenses(rows["expense_rows"])
    return (
        meals,
        meal_totals,
        build_daily_summary_supplements(rows["supplement_rows"]),
        build_daily_summary_workouts(rows["workout_rows"], rows["set_rows_by_workout"]),
        expenses,
        expense_totals,
        build_daily_summary_habits(rows["habit_rows"]),
        build_daily_summary_body_metrics(rows["body_metric_rows"]),
        build_daily_summary_daily_logs(rows["daily_log_rows"]),
    )
