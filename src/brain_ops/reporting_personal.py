from __future__ import annotations

from brain_ops.models import (
    BodyMetricsLogResult,
    BodyMetricsSummary,
    BudgetStatusSummary,
    BudgetTargetResult,
    DailyHabitsSummary,
    DailyLogResult,
    DailyMacrosSummary,
    DailyStatusSummary,
    DietActivationResult,
    DietMealUpdateResult,
    DietPlanResult,
    DietPlanSummary,
    DietStatusSummary,
    ExpenseLogResult,
    HabitTargetResult,
    HabitTargetStatusSummary,
    HabitCheckinResult,
    MacroStatusSummary,
    MacroTargetsResult,
    MealLogResult,
    SpendingSummary,
    SupplementLogResult,
    WorkoutLogResult,
    WorkoutStatusSummary,
)


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


def render_macro_targets(result: MacroTargetsResult) -> str:
    lines = [
        "# Macro Targets",
        "",
        f"- calories: {result.calories if result.calories is not None else '-'}",
        f"- protein_g: {result.protein_g if result.protein_g is not None else '-'}",
        f"- carbs_g: {result.carbs_g if result.carbs_g is not None else '-'}",
        f"- fat_g: {result.fat_g if result.fat_g is not None else '-'}",
        f"- reason: {result.reason}",
        "",
    ]
    return "\n".join(lines)


def render_macro_status(summary: MacroStatusSummary) -> str:
    lines = [
        f"# Macro Status - {summary.date}",
        "",
        f"- target_source: {summary.target_source or '-'}",
        f"- active_diet_name: {summary.active_diet_name or '-'}",
        f"- calories: actual={summary.calories_actual:.2f} target={summary.calories_target if summary.calories_target is not None else '-'} remaining={summary.calories_remaining if summary.calories_remaining is not None else '-'}",
        f"- protein_g: actual={summary.protein_g_actual:.2f} target={summary.protein_g_target if summary.protein_g_target is not None else '-'} remaining={summary.protein_g_remaining if summary.protein_g_remaining is not None else '-'}",
        f"- carbs_g: actual={summary.carbs_g_actual:.2f} target={summary.carbs_g_target if summary.carbs_g_target is not None else '-'} remaining={summary.carbs_g_remaining if summary.carbs_g_remaining is not None else '-'}",
        f"- fat_g: actual={summary.fat_g_actual:.2f} target={summary.fat_g_target if summary.fat_g_target is not None else '-'} remaining={summary.fat_g_remaining if summary.fat_g_remaining is not None else '-'}",
        f"- database_path: `{summary.database_path}`",
        "",
    ]
    return "\n".join(lines)


def render_diet_plan(result: DietPlanResult) -> str:
    lines = [
        f"# Diet Plan - {result.name}",
        "",
        f"- status: {result.status}",
        f"- meals: {len(result.meals)}",
        f"- reason: {result.reason}",
        "",
        "## Meals",
        "",
    ]
    if result.meals:
        for meal in result.meals:
            lines.append(
                f"- {meal.label} ({meal.meal_type}): items={len(meal.items)} | cal={meal.calories_target:.2f} | p={meal.protein_g_target:.2f} | c={meal.carbs_g_target:.2f} | f={meal.fat_g_target:.2f}"
            )
    else:
        lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def render_diet_activation(result: DietActivationResult) -> str:
    lines = [
        "# Diet Activation",
        "",
        f"- name: {result.name}",
        f"- status: {result.status}",
        f"- reason: {result.reason}",
        "",
    ]
    return "\n".join(lines)


def render_diet_meal_update(result: DietMealUpdateResult) -> str:
    lines = [
        "# Diet Meal Update",
        "",
        f"- diet_name: {result.diet_name}",
        f"- meal_type: {result.meal_type}",
        f"- mode: {result.mode}",
        f"- items: {len(result.items)}",
        f"- reason: {result.reason}",
        "",
        "## Items",
        "",
    ]
    if result.items:
        for item in result.items:
            lines.append(
                f"- {item.food_name} | grams={item.grams or '-'} | qty={item.quantity or '-'} | cal={item.calories or '-'}"
            )
    else:
        lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def render_active_diet(summary: DietPlanSummary | None) -> str:
    if summary is None:
        return "# Active Diet\n\n- None\n"
    lines = [
        f"# Active Diet - {summary.name}",
        "",
        f"- status: {summary.status}",
        f"- calories_target: {summary.calories_target:.2f}",
        f"- protein_g_target: {summary.protein_g_target:.2f}",
        f"- carbs_g_target: {summary.carbs_g_target:.2f}",
        f"- fat_g_target: {summary.fat_g_target:.2f}",
        f"- meals: {len(summary.meals)}",
        f"- database_path: `{summary.database_path}`",
        "",
        "## Meals",
        "",
    ]
    for meal in summary.meals:
        lines.append(
            f"- {meal.label} ({meal.meal_type}): {', '.join(item.food_name for item in meal.items) or '-'}"
        )
    if not summary.meals:
        lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def render_diet_status(summary: DietStatusSummary) -> str:
    lines = [
        f"# Diet Status - {summary.date}",
        "",
        f"- active_diet_name: {summary.active_diet_name or '-'}",
        f"- calories: actual={summary.calories_actual:.2f} target={summary.calories_target:.2f} remaining={summary.calories_remaining if summary.calories_remaining is not None else '-'}",
        f"- protein_g: actual={summary.protein_g_actual:.2f} target={summary.protein_g_target:.2f} remaining={summary.protein_g_remaining if summary.protein_g_remaining is not None else '-'}",
        f"- carbs_g: actual={summary.carbs_g_actual:.2f} target={summary.carbs_g_target:.2f} remaining={summary.carbs_g_remaining if summary.carbs_g_remaining is not None else '-'}",
        f"- fat_g: actual={summary.fat_g_actual:.2f} target={summary.fat_g_target:.2f} remaining={summary.fat_g_remaining if summary.fat_g_remaining is not None else '-'}",
        f"- meals: {len(summary.meals)}",
        f"- database_path: `{summary.database_path}`",
        "",
        "## Meal Progress",
        "",
    ]
    if summary.meals:
        for meal in summary.meals:
            lines.append(
                f"- {meal.label} ({meal.meal_type}): logged={str(meal.logged).lower()} | actual_items={meal.actual_count}/{meal.target_count} | target_items={', '.join(meal.target_items) or '-'} | actual_items_list={', '.join(meal.actual_items) or '-'}"
            )
    else:
        lines.append("- None")
    lines.append("")
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


def render_habit_target(result: HabitTargetResult) -> str:
    lines = [
        "# Habit Target",
        "",
        f"- habit_name: {result.habit_name}",
        f"- period: {result.period}",
        f"- target_count: {result.target_count}",
        f"- reason: {result.reason}",
        "",
    ]
    return "\n".join(lines)


def render_habit_target_status(summary: HabitTargetStatusSummary) -> str:
    lines = [
        f"# Habit Target Status - {summary.date}",
        "",
        f"- period: {summary.period}",
        f"- items: {len(summary.items)}",
        f"- database_path: `{summary.database_path}`",
        "",
        "## Habits",
        "",
    ]
    if summary.items:
        for item in summary.items:
            lines.append(
                f"- {item.habit_name}: done={item.completed_count} target={item.target_count} remaining={item.remaining_count}"
            )
    else:
        lines.append("- None")
    lines.append("")
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
        f"- fat_mass_kg: {result.fat_mass_kg if result.fat_mass_kg is not None else '-'}",
        f"- muscle_mass_kg: {result.muscle_mass_kg if result.muscle_mass_kg is not None else '-'}",
        f"- visceral_fat: {result.visceral_fat if result.visceral_fat is not None else '-'}",
        f"- bmr_calories: {result.bmr_calories if result.bmr_calories is not None else '-'}",
        f"- arm_cm: {result.arm_cm if result.arm_cm is not None else '-'}",
        f"- waist_cm: {result.waist_cm if result.waist_cm is not None else '-'}",
        f"- thigh_cm: {result.thigh_cm if result.thigh_cm is not None else '-'}",
        f"- calf_cm: {result.calf_cm if result.calf_cm is not None else '-'}",
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
        f"- latest_fat_mass_kg: {summary.latest_fat_mass_kg if summary.latest_fat_mass_kg is not None else '-'}",
        f"- latest_muscle_mass_kg: {summary.latest_muscle_mass_kg if summary.latest_muscle_mass_kg is not None else '-'}",
        f"- latest_visceral_fat: {summary.latest_visceral_fat if summary.latest_visceral_fat is not None else '-'}",
        f"- latest_bmr_calories: {summary.latest_bmr_calories if summary.latest_bmr_calories is not None else '-'}",
        f"- latest_arm_cm: {summary.latest_arm_cm if summary.latest_arm_cm is not None else '-'}",
        f"- latest_waist_cm: {summary.latest_waist_cm if summary.latest_waist_cm is not None else '-'}",
        f"- latest_thigh_cm: {summary.latest_thigh_cm if summary.latest_thigh_cm is not None else '-'}",
        f"- latest_calf_cm: {summary.latest_calf_cm if summary.latest_calf_cm is not None else '-'}",
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


def render_budget_target(result: BudgetTargetResult) -> str:
    lines = [
        "# Budget Target",
        "",
        f"- period: {result.period}",
        f"- category: {result.category or 'all'}",
        f"- amount: {result.amount:.2f} {result.currency}",
        f"- reason: {result.reason}",
        "",
    ]
    return "\n".join(lines)


def render_budget_status(summary: BudgetStatusSummary) -> str:
    lines = [
        f"# Budget Status - {summary.date}",
        "",
        f"- period: {summary.period}",
        f"- items: {len(summary.items)}",
        f"- database_path: `{summary.database_path}`",
        "",
        "## Targets",
        "",
    ]
    if summary.items:
        for item in summary.items:
            lines.append(
                f"- {item.category or 'all'}: actual={item.actual_amount:.2f} target={item.target_amount:.2f} remaining={item.remaining_amount:.2f} {item.currency}"
            )
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


def render_daily_status(summary: DailyStatusSummary) -> str:
    lines = [
        f"# Daily Status - {summary.date}",
        "",
        f"- active_diet_name: {summary.active_diet_name or '-'}",
        f"- calories: {summary.calories_actual:.2f}/{summary.calories_target if summary.calories_target is not None else '-'}",
        f"- protein_g: {summary.protein_g_actual:.2f}/{summary.protein_g_target if summary.protein_g_target is not None else '-'}",
        f"- carbs_g: {summary.carbs_g_actual:.2f}/{summary.carbs_g_target if summary.carbs_g_target is not None else '-'}",
        f"- fat_g: {summary.fat_g_actual:.2f}/{summary.fat_g_target if summary.fat_g_target is not None else '-'}",
        f"- workouts_logged: {summary.workouts_logged}",
        f"- total_workout_sets: {summary.total_workout_sets}",
        f"- expenses_total: {summary.expenses_total:.2f} {summary.expense_currency}",
        f"- supplements_logged: {summary.supplements_logged}",
        f"- daily_logs_count: {summary.daily_logs_count}",
        f"- database_path: `{summary.database_path}`",
        "",
        "## Missing diet meals",
        "",
    ]
    if summary.missing_diet_meals:
        lines.extend([f"- {meal}" for meal in summary.missing_diet_meals])
    else:
        lines.append("- None")
    lines.extend(["", "## Pending habits", ""])
    if summary.habit_pending:
        lines.extend([f"- {habit}" for habit in summary.habit_pending])
    else:
        lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def render_daily_review(review: "DailyReview") -> str:  # noqa: F821
    s = review.summary
    lines: list[str] = []

    lines.append(f"=== Daily Review: {review.date} ===")
    lines.append("")

    # Macros line
    cal_str = f"{s.calories_actual:.0f}"
    if s.calories_target:
        cal_str += f" / {s.calories_target:.0f} cal ({review.calories_pct}%)"
    else:
        cal_str += " cal"
    protein_str = f"P: {s.protein_g_actual:.0f}"
    if s.protein_g_target:
        protein_str += f"/{s.protein_g_target:.0f}g"
    else:
        protein_str += "g"
    carbs_str = f"C: {s.carbs_g_actual:.0f}"
    if s.carbs_g_target:
        carbs_str += f"/{s.carbs_g_target:.0f}g"
    else:
        carbs_str += "g"
    fat_str = f"F: {s.fat_g_actual:.0f}"
    if s.fat_g_target:
        fat_str += f"/{s.fat_g_target:.0f}g"
    else:
        fat_str += "g"
    lines.append(f"  Macros: {cal_str} | {protein_str} | {carbs_str} | {fat_str}")

    # Workout line
    if s.workouts_logged > 0:
        lines.append(f"  Workout: {s.workouts_logged} session(s), {s.total_workout_sets} sets")
    else:
        lines.append("  Workout: none")

    # Spending line
    lines.append(f"  Spending: ${s.expenses_total:,.0f} {s.expense_currency}")

    # Habits line
    total_habits = len(s.habits_completed) + len(s.habit_pending)
    if total_habits > 0:
        pending_str = ""
        if s.habit_pending:
            pending_str = " (" + ", ".join(f"{h} -" for h in s.habit_pending) + ")"
        lines.append(f"  Habits: {len(s.habits_completed)}/{total_habits} done{pending_str}")
    else:
        lines.append("  Habits: no targets set")

    # Body line
    body_parts = []
    if s.body_weight_kg is not None:
        body_parts.append(f"{s.body_weight_kg} kg")
    if s.body_fat_pct is not None:
        body_parts.append(f"{s.body_fat_pct}% BF")
    if s.waist_cm is not None:
        body_parts.append(f"{s.waist_cm} cm waist")
    if body_parts:
        lines.append(f"  Body: {' | '.join(body_parts)}")

    # Highlights
    if review.highlights:
        lines.append("")
        lines.append("Highlights:")
        for h in review.highlights:
            lines.append(f"  - {h}")

    # Gaps
    if review.gaps:
        lines.append("")
        lines.append("Gaps:")
        for g in review.gaps:
            lines.append(f"  - {g}")

    # Suggestions
    if review.suggestions:
        lines.append("")
        lines.append("Suggestions:")
        for sug in review.suggestions:
            lines.append(f"  - {sug}")

    lines.append("")
    lines.append(f"Score: {review.score}/10")
    lines.append("")
    return "\n".join(lines)


def render_weekly_review_personal(review: "WeeklyReview") -> str:  # noqa: F821
    lines: list[str] = []

    # Header
    lines.append(f"=== Weekly Review: {review.start_date} to {review.end_date} ===")
    lines.append("")

    # Avg macros
    cal_str = f"{review.avg_calories:.0f}"
    if review.calories_target:
        cal_str += f"/{review.calories_target:.0f} cal ({review.avg_calories_pct}%)"
    else:
        cal_str += " cal"
    prot_str = f"P: {review.avg_protein:.0f}"
    if review.protein_target:
        prot_str += f"/{review.protein_target:.0f}g"
    else:
        prot_str += "g"
    carbs_str = f"C: {review.avg_carbs:.0f}"
    if review.carbs_target:
        carbs_str += f"/{review.carbs_target:.0f}g"
    else:
        carbs_str += "g"
    lines.append(f"  Avg Macros: {cal_str} | {prot_str} | {carbs_str}")

    # Workouts
    lines.append(f"  Workouts: {review.workout_days}/7 days trained ({review.total_sets} total sets)")

    # Spending
    lines.append(f"  Total Spent: ${review.total_spending:,.0f} {review.spending_currency}")

    # Habits
    lines.append(f"  Habits: {review.habit_completion_pct}% completion rate")
    for habit, (done, total) in sorted(review.habit_completion.items()):
        lines.append(f"    {habit}: {done}/{total}")

    # Body
    if review.weight_start is not None and review.weight_end is not None:
        change_str = ""
        if review.weight_change is not None:
            sign = "+" if review.weight_change > 0 else ""
            change_str = f" ({sign}{review.weight_change:.1f})"
        lines.append(f"  Weight: {review.weight_start:.1f} -> {review.weight_end:.1f} kg{change_str}")

    # Trends
    if review.trends:
        lines.append("")
        lines.append("Trends:")
        for t in review.trends:
            lines.append(f"  - {t}")

    lines.append("")
    lines.append(f"Score: {review.score}/10")
    lines.append("")
    return "\n".join(lines)
