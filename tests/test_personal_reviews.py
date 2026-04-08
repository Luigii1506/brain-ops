"""Tests for daily and weekly personal review domain logic and rendering."""

from __future__ import annotations

from pathlib import Path

import pytest

from brain_ops.domains.personal.reviews import (
    DailyReview,
    WeeklyReview,
    build_daily_review,
    build_weekly_review,
)
from brain_ops.models import DailyStatusSummary
from brain_ops.reporting_personal import render_daily_review, render_weekly_review_personal


def _make_summary(
    *,
    date: str = "2026-04-08",
    calories_actual: float = 1850,
    calories_target: float | None = 2500,
    protein_g_actual: float = 120,
    protein_g_target: float | None = 200,
    carbs_g_actual: float = 180,
    carbs_g_target: float | None = 250,
    fat_g_actual: float = 65,
    fat_g_target: float | None = 85,
    workouts_logged: int = 1,
    total_workout_sets: int = 16,
    expenses_total: float = 450,
    expense_currency: str = "MXN",
    supplements_logged: int = 2,
    supplement_names: list[str] | None = None,
    habit_pending: list[str] | None = None,  # None => default, [] => empty
    habits_completed: list[str] | None = None,  # None => default, [] => empty
    body_weight_kg: float | None = 78.5,
    body_fat_pct: float | None = 14.0,
    waist_cm: float | None = None,
    missing_diet_meals: list[str] | None = None,
) -> DailyStatusSummary:
    return DailyStatusSummary(
        date=date,
        calories_actual=calories_actual,
        calories_target=calories_target,
        calories_remaining=(calories_target - calories_actual) if calories_target else None,
        protein_g_actual=protein_g_actual,
        protein_g_target=protein_g_target,
        protein_g_remaining=(protein_g_target - protein_g_actual) if protein_g_target else None,
        carbs_g_actual=carbs_g_actual,
        carbs_g_target=carbs_g_target,
        carbs_g_remaining=(carbs_g_target - carbs_g_actual) if carbs_g_target else None,
        fat_g_actual=fat_g_actual,
        fat_g_target=fat_g_target,
        fat_g_remaining=(fat_g_target - fat_g_actual) if fat_g_target else None,
        workouts_logged=workouts_logged,
        total_workout_sets=total_workout_sets,
        expenses_total=expenses_total,
        expense_currency=expense_currency,
        supplements_logged=supplements_logged,
        supplement_names=supplement_names if supplement_names is not None else ["creatina", "vitamina D"],
        habit_pending=habit_pending if habit_pending is not None else ["meditar", "leer"],
        habits_completed=habits_completed if habits_completed is not None else ["dormir 8h", "agua", "caminar"],
        body_weight_kg=body_weight_kg,
        body_fat_pct=body_fat_pct,
        waist_cm=waist_cm,
        missing_diet_meals=missing_diet_meals if missing_diet_meals is not None else [],
        database_path=Path("/tmp/test.db"),
    )


class TestBuildDailyReview:
    def test_basic_review_has_score(self):
        summary = _make_summary()
        review = build_daily_review(summary)
        assert isinstance(review, DailyReview)
        assert review.date == "2026-04-08"
        assert review.score > 0
        assert review.score <= 10

    def test_percentages_computed(self):
        summary = _make_summary()
        review = build_daily_review(summary)
        assert review.calories_pct == 74.0
        assert review.protein_pct == 60.0

    def test_workout_adds_highlight(self):
        summary = _make_summary(workouts_logged=1, total_workout_sets=16)
        review = build_daily_review(summary)
        assert any("Workout completed" in h for h in review.highlights)

    def test_no_workout_adds_gap(self):
        summary = _make_summary(workouts_logged=0, total_workout_sets=0)
        review = build_daily_review(summary)
        assert any("No workout" in g for g in review.gaps)

    def test_missing_habits_in_gaps(self):
        summary = _make_summary(habit_pending=["meditar", "leer"])
        review = build_daily_review(summary)
        assert any("meditar" in g for g in review.gaps)

    def test_all_habits_completed_highlight(self):
        summary = _make_summary(habit_pending=[], habits_completed=["a", "b", "c"])
        review = build_daily_review(summary)
        assert any("All 3 habits" in h for h in review.highlights)

    def test_no_supplements_adds_gap(self):
        summary = _make_summary(supplements_logged=0, supplement_names=[])
        review = build_daily_review(summary)
        assert any("No supplements" in g for g in review.gaps)

    def test_calorie_gap_suggestion(self):
        summary = _make_summary(calories_actual=1800, calories_target=2500)
        review = build_daily_review(summary)
        assert any("snack" in s for s in review.suggestions)

    def test_score_capped_at_10(self):
        # Perfect day: on target macros, workout, all habits, supplements, body logged
        summary = _make_summary(
            calories_actual=2400,
            calories_target=2500,
            protein_g_actual=190,
            protein_g_target=200,
            workouts_logged=1,
            habit_pending=[],
            habits_completed=["a", "b", "c", "d", "e"],
            supplements_logged=3,
            body_weight_kg=78.0,
        )
        review = build_daily_review(summary)
        assert review.score <= 10.0

    def test_to_dict(self):
        summary = _make_summary()
        review = build_daily_review(summary)
        d = review.to_dict()
        assert "score" in d
        assert "highlights" in d
        assert "gaps" in d
        assert "summary" in d

    def test_no_targets_still_works(self):
        summary = _make_summary(
            calories_target=None,
            protein_g_target=None,
            carbs_g_target=None,
            fat_g_target=None,
        )
        review = build_daily_review(summary)
        assert review.calories_pct == 0.0
        assert review.score >= 0


class TestBuildWeeklyReview:
    def _make_week(self) -> list[DailyReview]:
        reviews = []
        for i in range(7):
            day = f"2026-04-0{i + 2}"
            wl = 1 if i < 4 else 0  # 4 workout days
            summary = _make_summary(
                date=day,
                workouts_logged=wl,
                calories_actual=1800 + i * 100,
                body_weight_kg=78.5 - i * 0.05 if i in (0, 6) else None,
            )
            reviews.append(build_daily_review(summary))
        return reviews

    def test_basic_weekly(self):
        reviews = self._make_week()
        weekly = build_weekly_review(reviews)
        assert isinstance(weekly, WeeklyReview)
        assert weekly.days_with_data == 7
        assert weekly.workout_days == 4
        assert weekly.score > 0

    def test_avg_macros(self):
        reviews = self._make_week()
        weekly = build_weekly_review(reviews)
        assert weekly.avg_calories > 0
        assert weekly.avg_protein > 0

    def test_habit_completion(self):
        reviews = self._make_week()
        weekly = build_weekly_review(reviews)
        assert len(weekly.habit_completion) > 0
        assert weekly.habit_completion_pct >= 0

    def test_weight_change(self):
        reviews = self._make_week()
        weekly = build_weekly_review(reviews)
        assert weekly.weight_start is not None
        assert weekly.weight_end is not None
        assert weekly.weight_change is not None

    def test_trends_populated(self):
        reviews = self._make_week()
        weekly = build_weekly_review(reviews)
        assert isinstance(weekly.trends, list)

    def test_empty_week(self):
        weekly = build_weekly_review([])
        assert weekly.start_date == ""
        assert weekly.end_date == ""
        assert weekly.days_with_data == 0

    def test_to_dict(self):
        reviews = self._make_week()
        weekly = build_weekly_review(reviews)
        d = weekly.to_dict()
        assert "score" in d
        assert "trends" in d
        assert "habit_completion" in d


class TestRenderDailyReview:
    def test_render_has_key_sections(self):
        summary = _make_summary()
        review = build_daily_review(summary)
        output = render_daily_review(review)
        assert "Daily Review" in output
        assert "Score:" in output
        assert "Macros:" in output

    def test_render_shows_gaps(self):
        summary = _make_summary(workouts_logged=0, total_workout_sets=0)
        review = build_daily_review(summary)
        output = render_daily_review(review)
        assert "Gaps:" in output
        assert "No workout" in output

    def test_render_shows_highlights(self):
        summary = _make_summary()
        review = build_daily_review(summary)
        output = render_daily_review(review)
        assert "Highlights:" in output


class TestRenderWeeklyReview:
    def test_render_has_key_sections(self):
        reviews = []
        for i in range(7):
            summary = _make_summary(date=f"2026-04-0{i + 2}")
            reviews.append(build_daily_review(summary))
        weekly = build_weekly_review(reviews)
        output = render_weekly_review_personal(weekly)
        assert "Weekly Review" in output
        assert "Score:" in output
        assert "Avg Macros:" in output
        assert "Workouts:" in output
