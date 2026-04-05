from __future__ import annotations

from pathlib import Path

from brain_ops.domains.personal.daily_status import build_daily_status_summary
from brain_ops.models import DailyStatusSummary
from brain_ops.services.body_metrics_service import body_metrics_status
from brain_ops.services.diet_service import diet_status
from brain_ops.services.expenses_service import spending_summary
from brain_ops.services.fitness_service import workout_status
from brain_ops.services.goals_service import habit_target_status, macro_status
from brain_ops.storage.db import require_database_file
from brain_ops.storage.sqlite import fetch_daily_status_local_context


def daily_status(database_path: Path, date_text: str | None = None) -> DailyStatusSummary:
    target = require_database_file(database_path)

    macro = macro_status(target, date_text=date_text)
    diet = diet_status(target, date_text=date_text)
    workout = workout_status(target, date_text=date_text)
    spending = spending_summary(target, date_text=date_text)
    habits = habit_target_status(target, period="daily", date_text=date_text)
    body = body_metrics_status(target, date_text=date_text)
    supplement_names, daily_logs_count = _load_local_context(target, macro.date)

    return build_daily_status_summary(
        macro=macro,
        diet=diet,
        workout=workout,
        spending=spending,
        habits=habits,
        body=body,
        supplements_logged=len(supplement_names),
        supplement_names=supplement_names,
        daily_logs_count=daily_logs_count,
        database_path=target,
    )


def _load_local_context(database_path: Path, date_text: str) -> tuple[list[str], int]:
    start = f"{date_text}T00:00:00"
    end = f"{date_text}T23:59:59"
    return fetch_daily_status_local_context(database_path, start=start, end=end)
