"""SQLite storage adapters."""

from brain_ops.storage.sqlite.body_metrics import (
    ensure_body_metrics_schema,
    ensure_body_metrics_columns,
    fetch_body_metrics_status_rows,
    insert_body_metrics_log,
)
from brain_ops.storage.sqlite.daily_status import (
    fetch_daily_status_local_context,
    fetch_daily_status_log_count,
    fetch_daily_status_supplement_names,
)
from brain_ops.storage.sqlite.daily_logs import insert_daily_log
from brain_ops.storage.sqlite.daily_summary import (
    fetch_daily_summary_context_rows,
    fetch_daily_summary_body_metric_rows,
    fetch_daily_summary_daily_log_rows,
    fetch_daily_summary_expense_rows,
    fetch_daily_summary_habit_rows,
    fetch_daily_summary_meal_rows,
    fetch_daily_summary_supplement_rows,
    fetch_daily_summary_workout_rows,
)
from brain_ops.storage.sqlite.diets import (
    activate_diet_plan,
    create_diet_plan_records,
    fetch_active_diet_plan_rows,
    fetch_actual_meal_progress_rows,
    fetch_diet_plan_names,
    update_active_diet_meal_items,
)
from brain_ops.storage.sqlite.expenses import (
    fetch_expense_category_totals,
    fetch_expense_summary_header,
    insert_expense,
)
from brain_ops.storage.sqlite.fitness import fetch_workout_status_rows, insert_workout_log
from brain_ops.storage.sqlite.follow_ups import delete_follow_up, fetch_follow_up_payload, upsert_follow_up
from brain_ops.storage.sqlite.goals import (
    fetch_budget_status_rows,
    fetch_habit_target_status_rows,
    fetch_macro_status_rows,
)
from brain_ops.storage.sqlite.goals import replace_budget_target, upsert_habit_target, upsert_macro_targets
from brain_ops.storage.sqlite.life_ops import (
    fetch_daily_habit_rows,
    insert_habit_checkin,
    insert_supplement_log,
)
from brain_ops.storage.sqlite.nutrition import fetch_daily_macro_rows, insert_meal_log
from brain_ops.storage.sqlite.capture_log import (
    fetch_recent_capture_logs,
    insert_capture_log,
)
from brain_ops.storage.sqlite.project_logs import (
    fetch_project_logs,
    fetch_recent_project_logs,
    insert_project_log,
)

__all__ = [
    "fetch_active_diet_plan_rows",
    "fetch_actual_meal_progress_rows",
    "fetch_diet_plan_names",
    "activate_diet_plan",
    "create_diet_plan_records",
    "fetch_body_metrics_status_rows",
    "fetch_budget_status_rows",
    "fetch_daily_status_local_context",
    "fetch_daily_status_log_count",
    "fetch_daily_status_supplement_names",
    "fetch_daily_summary_context_rows",
    "fetch_daily_summary_body_metric_rows",
    "fetch_daily_summary_daily_log_rows",
    "fetch_daily_summary_expense_rows",
    "fetch_daily_summary_habit_rows",
    "fetch_daily_summary_meal_rows",
    "fetch_daily_summary_supplement_rows",
    "fetch_daily_summary_workout_rows",
    "fetch_daily_habit_rows",
    "fetch_daily_macro_rows",
    "fetch_expense_category_totals",
    "fetch_expense_summary_header",
    "fetch_recent_capture_logs",
    "fetch_project_logs",
    "fetch_recent_project_logs",
    "fetch_follow_up_payload",
    "fetch_habit_target_status_rows",
    "fetch_macro_status_rows",
    "fetch_workout_status_rows",
    "ensure_body_metrics_schema",
    "ensure_body_metrics_columns",
    "delete_follow_up",
    "insert_habit_checkin",
    "insert_body_metrics_log",
    "insert_capture_log",
    "insert_daily_log",
    "insert_expense",
    "insert_meal_log",
    "insert_project_log",
    "insert_supplement_log",
    "insert_workout_log",
    "replace_budget_target",
    "update_active_diet_meal_items",
    "upsert_follow_up",
    "upsert_habit_target",
    "upsert_macro_targets",
]
