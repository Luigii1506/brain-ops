from __future__ import annotations

"""Deprecated compatibility facade for reporting renderers.

Internal code now consumes the specialized reporting modules directly.
This surface is retained for stable imports and staged external migration.
"""

from brain_ops.reporting_knowledge import (
    render_applied_links,
    render_daily_summary,
    render_enriched_note,
    render_inbox_report,
    render_link_suggestions,
    render_normalize_frontmatter,
    render_promoted_note,
    render_vault_audit,
    render_weekly_review,
)
from brain_ops.reporting_personal import (
    render_active_diet,
    render_body_metrics_log,
    render_body_metrics_status,
    render_budget_status,
    render_budget_target,
    render_daily_habits,
    render_daily_log,
    render_daily_macros,
    render_daily_status,
    render_diet_activation,
    render_diet_meal_update,
    render_diet_plan,
    render_diet_status,
    render_expense_log,
    render_habit_checkin,
    render_habit_target,
    render_habit_target_status,
    render_macro_status,
    render_macro_targets,
    render_meal_log,
    render_spending_summary,
    render_supplement_log,
    render_workout_log,
    render_workout_status,
)
from brain_ops.reporting_conversation import render_handle_input, render_route_decision

__all__ = [
    "render_active_diet",
    "render_applied_links",
    "render_body_metrics_log",
    "render_body_metrics_status",
    "render_budget_status",
    "render_budget_target",
    "render_daily_habits",
    "render_daily_log",
    "render_daily_macros",
    "render_daily_status",
    "render_daily_summary",
    "render_diet_activation",
    "render_diet_meal_update",
    "render_diet_plan",
    "render_diet_status",
    "render_enriched_note",
    "render_expense_log",
    "render_handle_input",
    "render_habit_checkin",
    "render_habit_target",
    "render_habit_target_status",
    "render_inbox_report",
    "render_link_suggestions",
    "render_macro_status",
    "render_macro_targets",
    "render_meal_log",
    "render_normalize_frontmatter",
    "render_promoted_note",
    "render_route_decision",
    "render_spending_summary",
    "render_supplement_log",
    "render_vault_audit",
    "render_weekly_review",
    "render_workout_log",
    "render_workout_status",
]
