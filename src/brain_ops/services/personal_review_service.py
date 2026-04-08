"""Service layer for daily and weekly personal reviews."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

from brain_ops.domains.personal.reviews import (
    DailyReview,
    WeeklyReview,
    build_daily_review,
    build_weekly_review,
)
from brain_ops.services.daily_status_service import daily_status


def daily_review(database_path: Path, date_text: str | None = None) -> DailyReview:
    """Build a daily review with scoring and analysis."""
    summary = daily_status(database_path, date_text=date_text)
    return build_daily_review(summary)


def weekly_review(database_path: Path, date_text: str | None = None) -> WeeklyReview:
    """Build a weekly review aggregating 7 days of data ending on the given date."""
    if date_text:
        end_date = date.fromisoformat(date_text)
    else:
        end_date = date.today()

    start_date = end_date - timedelta(days=6)

    reviews: list[DailyReview] = []
    current = start_date
    while current <= end_date:
        day_text = current.isoformat()
        try:
            summary = daily_status(database_path, date_text=day_text)
            review = build_daily_review(summary)
            reviews.append(review)
        except Exception:
            # Day may have no data at all; skip it
            pass
        current += timedelta(days=1)

    return build_weekly_review(reviews)
