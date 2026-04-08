"""Domain logic for daily and weekly personal reviews."""

from __future__ import annotations

from dataclasses import dataclass, field

from brain_ops.models import DailyStatusSummary


@dataclass
class DailyReview:
    """Enriched daily status with scoring, highlights, gaps, and suggestions."""

    date: str
    summary: DailyStatusSummary

    # Macro percentages
    calories_pct: float = 0.0
    protein_pct: float = 0.0
    carbs_pct: float = 0.0
    fat_pct: float = 0.0

    # Computed
    score: float = 0.0
    highlights: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "score": self.score,
            "calories_pct": self.calories_pct,
            "protein_pct": self.protein_pct,
            "carbs_pct": self.carbs_pct,
            "fat_pct": self.fat_pct,
            "highlights": self.highlights,
            "gaps": self.gaps,
            "suggestions": self.suggestions,
            "summary": self.summary.model_dump(mode="json"),
        }


@dataclass
class WeeklyReview:
    """Aggregated weekly personal review with trends."""

    start_date: str
    end_date: str
    days_with_data: int = 0

    # Macro averages
    avg_calories: float = 0.0
    avg_protein: float = 0.0
    avg_carbs: float = 0.0
    avg_fat: float = 0.0
    calories_target: float | None = None
    protein_target: float | None = None
    carbs_target: float | None = None
    fat_target: float | None = None
    avg_calories_pct: float = 0.0
    avg_protein_pct: float = 0.0

    # Workouts
    workout_days: int = 0
    total_sets: int = 0

    # Spending
    total_spending: float = 0.0
    spending_currency: str = "MXN"
    spending_by_category: dict[str, float] = field(default_factory=dict)

    # Habits
    habit_completion: dict[str, tuple[int, int]] = field(default_factory=dict)  # habit -> (done, total_days)
    habit_completion_pct: float = 0.0

    # Body
    weight_start: float | None = None
    weight_end: float | None = None
    weight_change: float | None = None
    bf_start: float | None = None
    bf_end: float | None = None

    # Trends and scoring
    trends: list[str] = field(default_factory=list)
    score: float = 0.0

    # Per-day reviews for JSON output
    daily_reviews: list[DailyReview] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "start_date": self.start_date,
            "end_date": self.end_date,
            "days_with_data": self.days_with_data,
            "score": self.score,
            "avg_calories": self.avg_calories,
            "avg_protein": self.avg_protein,
            "avg_carbs": self.avg_carbs,
            "avg_fat": self.avg_fat,
            "calories_target": self.calories_target,
            "protein_target": self.protein_target,
            "avg_calories_pct": self.avg_calories_pct,
            "avg_protein_pct": self.avg_protein_pct,
            "workout_days": self.workout_days,
            "total_sets": self.total_sets,
            "total_spending": self.total_spending,
            "spending_currency": self.spending_currency,
            "spending_by_category": self.spending_by_category,
            "habit_completion": {k: {"done": v[0], "of": v[1]} for k, v in self.habit_completion.items()},
            "habit_completion_pct": self.habit_completion_pct,
            "weight_start": self.weight_start,
            "weight_end": self.weight_end,
            "weight_change": self.weight_change,
            "trends": self.trends,
        }


def _pct(actual: float, target: float | None) -> float:
    if target is None or target <= 0:
        return 0.0
    return round((actual / target) * 100, 1)


def build_daily_review(summary: DailyStatusSummary) -> DailyReview:
    """Compute score, highlights, gaps, and suggestions from a daily status."""
    review = DailyReview(date=summary.date, summary=summary)

    # Percentages
    review.calories_pct = _pct(summary.calories_actual, summary.calories_target)
    review.protein_pct = _pct(summary.protein_g_actual, summary.protein_g_target)
    review.carbs_pct = _pct(summary.carbs_g_actual, summary.carbs_g_target)
    review.fat_pct = _pct(summary.fat_g_actual, summary.fat_g_target)

    # --- Score computation (0-10) ---
    score = 5.0  # baseline

    # Macro adherence (up to +2)
    if summary.calories_target and summary.calories_target > 0:
        cal_ratio = summary.calories_actual / summary.calories_target
        if 0.85 <= cal_ratio <= 1.05:
            score += 1.0
        elif 0.70 <= cal_ratio < 0.85:
            score += 0.5
    if summary.protein_g_target and summary.protein_g_target > 0:
        prot_ratio = summary.protein_g_actual / summary.protein_g_target
        if prot_ratio >= 0.90:
            score += 1.0
        elif prot_ratio >= 0.75:
            score += 0.5

    # Workout (+1.5)
    if summary.workouts_logged > 0:
        score += 1.5

    # Habits (+1.5)
    total_habits = len(summary.habit_pending) + len(summary.habits_completed)
    if total_habits > 0:
        habit_ratio = len(summary.habits_completed) / total_habits
        score += habit_ratio * 1.5

    # Supplements (+0.5)
    if summary.supplements_logged > 0:
        score += 0.5

    # Body metrics logged (+0.5)
    if summary.body_weight_kg is not None:
        score += 0.5

    review.score = round(min(score, 10.0), 1)

    # --- Highlights ---
    if summary.workouts_logged > 0:
        parts = []
        if summary.total_workout_sets > 0:
            parts.append(f"{summary.total_workout_sets} sets")
        review.highlights.append(f"Workout completed ({', '.join(parts)})" if parts else "Workout completed")

    if review.protein_pct >= 90:
        review.highlights.append(f"Protein on target ({review.protein_pct}%)")

    if review.calories_pct >= 85 and review.calories_pct <= 105:
        review.highlights.append(f"Calories on target ({review.calories_pct}%)")

    if summary.fat_g_target and summary.fat_g_actual < summary.fat_g_target:
        review.highlights.append("Under fat target")

    if len(summary.habits_completed) == total_habits and total_habits > 0:
        review.highlights.append(f"All {total_habits} habits completed")
    elif len(summary.habits_completed) > 0:
        review.highlights.append(f"{len(summary.habits_completed)}/{total_habits} habits completed")

    if summary.supplements_logged > 0:
        review.highlights.append(f"Supplements logged ({', '.join(summary.supplement_names)})")

    # --- Gaps ---
    if summary.calories_remaining and summary.calories_remaining > 200:
        review.gaps.append(f"{summary.calories_remaining:.0f} cal remaining")

    if summary.protein_g_remaining and summary.protein_g_remaining > 20:
        review.gaps.append(f"{summary.protein_g_remaining:.0f}g protein remaining")

    if summary.workouts_logged == 0:
        review.gaps.append("No workout logged")

    if summary.habit_pending:
        review.gaps.append(f"Missing habits: {', '.join(summary.habit_pending)}")

    if summary.supplements_logged == 0:
        review.gaps.append("No supplements logged")

    if summary.missing_diet_meals:
        review.gaps.append(f"Missing diet meals: {', '.join(summary.missing_diet_meals)}")

    # --- Suggestions ---
    if summary.calories_remaining and summary.calories_remaining > 300:
        review.suggestions.append(f"Consider a snack to close {summary.calories_remaining:.0f} cal gap")

    if summary.protein_g_remaining and summary.protein_g_remaining > 30:
        review.suggestions.append(f"Add protein-rich food ({summary.protein_g_remaining:.0f}g remaining)")

    if summary.habit_pending:
        review.suggestions.append(f"Complete pending habits: {', '.join(summary.habit_pending)}")

    if summary.supplements_logged == 0:
        review.suggestions.append("Log supplements for the day")

    return review


def build_weekly_review(daily_reviews: list[DailyReview]) -> WeeklyReview:
    """Aggregate multiple daily reviews into a weekly review."""
    if not daily_reviews:
        return WeeklyReview(start_date="", end_date="")

    sorted_reviews = sorted(daily_reviews, key=lambda r: r.date)
    review = WeeklyReview(
        start_date=sorted_reviews[0].date,
        end_date=sorted_reviews[-1].date,
        days_with_data=len(sorted_reviews),
        daily_reviews=sorted_reviews,
    )

    n = len(sorted_reviews)

    # Macro averages
    review.avg_calories = round(sum(r.summary.calories_actual for r in sorted_reviews) / n, 1)
    review.avg_protein = round(sum(r.summary.protein_g_actual for r in sorted_reviews) / n, 1)
    review.avg_carbs = round(sum(r.summary.carbs_g_actual for r in sorted_reviews) / n, 1)
    review.avg_fat = round(sum(r.summary.fat_g_actual for r in sorted_reviews) / n, 1)

    # Targets (use the latest available)
    for r in reversed(sorted_reviews):
        if r.summary.calories_target and review.calories_target is None:
            review.calories_target = r.summary.calories_target
        if r.summary.protein_g_target and review.protein_target is None:
            review.protein_target = r.summary.protein_g_target
        if r.summary.carbs_g_target and review.carbs_target is None:
            review.carbs_target = r.summary.carbs_g_target
        if r.summary.fat_g_target and review.fat_target is None:
            review.fat_target = r.summary.fat_g_target

    review.avg_calories_pct = _pct(review.avg_calories, review.calories_target)
    review.avg_protein_pct = _pct(review.avg_protein, review.protein_target)

    # Workouts
    review.workout_days = sum(1 for r in sorted_reviews if r.summary.workouts_logged > 0)
    review.total_sets = sum(r.summary.total_workout_sets for r in sorted_reviews)

    # Spending
    review.total_spending = round(sum(r.summary.expenses_total for r in sorted_reviews), 2)
    review.spending_currency = sorted_reviews[-1].summary.expense_currency

    # Habits
    all_habits: set[str] = set()
    for r in sorted_reviews:
        all_habits.update(r.summary.habits_completed)
        all_habits.update(r.summary.habit_pending)

    for habit in sorted(all_habits):
        done = sum(1 for r in sorted_reviews if habit in r.summary.habits_completed)
        total = sum(1 for r in sorted_reviews if habit in r.summary.habits_completed or habit in r.summary.habit_pending)
        review.habit_completion[habit] = (done, total)

    total_habit_checks = sum(v[1] for v in review.habit_completion.values())
    total_habit_done = sum(v[0] for v in review.habit_completion.values())
    review.habit_completion_pct = round((total_habit_done / total_habit_checks * 100) if total_habit_checks > 0 else 0, 1)

    # Body trends
    for r in sorted_reviews:
        if r.summary.body_weight_kg is not None:
            if review.weight_start is None:
                review.weight_start = r.summary.body_weight_kg
            review.weight_end = r.summary.body_weight_kg
        if r.summary.body_fat_pct is not None:
            if review.bf_start is None:
                review.bf_start = r.summary.body_fat_pct
            review.bf_end = r.summary.body_fat_pct

    if review.weight_start is not None and review.weight_end is not None:
        review.weight_change = round(review.weight_end - review.weight_start, 2)

    # --- Trends ---
    if review.avg_protein_pct > 0 and review.avg_protein_pct < 90:
        review.trends.append(f"Protein consistently under target (avg {review.avg_protein_pct}%)")

    if review.avg_calories_pct > 0 and review.avg_calories_pct < 80:
        review.trends.append(f"Calories under target (avg {review.avg_calories_pct}%)")
    elif review.avg_calories_pct > 110:
        review.trends.append(f"Calories over target (avg {review.avg_calories_pct}%)")

    # Best and worst habits
    if review.habit_completion:
        best_habit = max(review.habit_completion.items(), key=lambda x: x[1][0] / max(x[1][1], 1))
        worst_habit = min(review.habit_completion.items(), key=lambda x: x[1][0] / max(x[1][1], 1))
        if best_habit[1][1] > 0:
            best_pct = round(best_habit[1][0] / best_habit[1][1] * 100)
            review.trends.append(f"Best habit: {best_habit[0]} ({best_pct}%)")
        if worst_habit[0] != best_habit[0] and worst_habit[1][1] > 0:
            worst_pct = round(worst_habit[1][0] / worst_habit[1][1] * 100)
            review.trends.append(f"Weakest habit: {worst_habit[0]} ({worst_pct}%)")

    if review.weight_change is not None and review.weight_change != 0:
        direction = "down" if review.weight_change < 0 else "up"
        review.trends.append(f"Weight {direction} {abs(review.weight_change):.1f} kg")

    if review.workout_days >= 5:
        review.trends.append(f"Strong training frequency ({review.workout_days}/7 days)")
    elif review.workout_days <= 2:
        review.trends.append(f"Low training frequency ({review.workout_days}/7 days)")

    # --- Score (average of daily scores) ---
    review.score = round(sum(r.score for r in sorted_reviews) / n, 1)

    return review
