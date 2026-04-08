"""CLI orchestration helpers for personal status and summary commands."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from brain_ops.application import (
    execute_active_diet_workflow,
    execute_body_metrics_status_workflow,
    execute_budget_status_workflow,
    execute_daily_habits_workflow,
    execute_daily_macros_workflow,
    execute_daily_review_workflow,
    execute_daily_status_workflow,
    execute_diet_status_workflow,
    execute_habit_status_workflow,
    execute_macro_status_workflow,
    execute_spending_summary_workflow,
    execute_weekly_review_personal_workflow,
    execute_workout_status_workflow,
)
from brain_ops.interfaces.cli.presenters import (
    print_json_or_rendered,
    print_optional_json_or_rendered,
)
from brain_ops.interfaces.cli.runtime import load_database_path
from brain_ops.reporting_personal import (
    render_active_diet,
    render_body_metrics_status,
    render_budget_status,
    render_daily_habits,
    render_daily_macros,
    render_daily_review,
    render_daily_status,
    render_diet_status,
    render_habit_target_status,
    render_macro_status,
    render_spending_summary,
    render_weekly_review_personal,
    render_workout_status,
)


def run_daily_macros_command(
    *,
    config_path: Path | None,
    date: str | None,
):
    return execute_daily_macros_workflow(config_path=config_path, date=date, load_database_path=load_database_path)


def present_daily_macros_command(
    console: Console,
    *,
    config_path: Path | None,
    date: str | None,
    as_json: bool,
) -> None:
    summary = run_daily_macros_command(config_path=config_path, date=date)
    print_json_or_rendered(console, as_json=as_json, value=summary, rendered=render_daily_macros(summary))


def run_macro_status_command(
    *,
    config_path: Path | None,
    date: str | None,
):
    return execute_macro_status_workflow(config_path=config_path, date=date, load_database_path=load_database_path)


def present_macro_status_command(
    console: Console,
    *,
    config_path: Path | None,
    date: str | None,
    as_json: bool,
) -> None:
    summary = run_macro_status_command(config_path=config_path, date=date)
    print_json_or_rendered(console, as_json=as_json, value=summary, rendered=render_macro_status(summary))


def run_active_diet_command(
    *,
    config_path: Path | None,
):
    return execute_active_diet_workflow(config_path=config_path, load_database_path=load_database_path)


def present_active_diet_command(
    console: Console,
    *,
    config_path: Path | None,
    as_json: bool,
) -> None:
    summary = run_active_diet_command(config_path=config_path)
    print_optional_json_or_rendered(console, as_json=as_json, value=summary, rendered=render_active_diet(summary))


def run_diet_status_command(
    *,
    config_path: Path | None,
    date: str | None,
):
    return execute_diet_status_workflow(config_path=config_path, date=date, load_database_path=load_database_path)


def present_diet_status_command(
    console: Console,
    *,
    config_path: Path | None,
    date: str | None,
    as_json: bool,
) -> None:
    summary = run_diet_status_command(config_path=config_path, date=date)
    print_json_or_rendered(console, as_json=as_json, value=summary, rendered=render_diet_status(summary))


def run_daily_habits_command(
    *,
    config_path: Path | None,
    date: str | None,
):
    return execute_daily_habits_workflow(config_path=config_path, date=date, load_database_path=load_database_path)


def present_daily_habits_command(
    console: Console,
    *,
    config_path: Path | None,
    date: str | None,
    as_json: bool,
) -> None:
    summary = run_daily_habits_command(config_path=config_path, date=date)
    print_json_or_rendered(console, as_json=as_json, value=summary, rendered=render_daily_habits(summary))


def run_habit_status_command(
    *,
    config_path: Path | None,
    period: str,
    date: str | None,
):
    return execute_habit_status_workflow(
        config_path=config_path,
        period=period,
        date=date,
        load_database_path=load_database_path,
    )


def present_habit_status_command(
    console: Console,
    *,
    config_path: Path | None,
    period: str,
    date: str | None,
    as_json: bool,
) -> None:
    summary = run_habit_status_command(config_path=config_path, period=period, date=date)
    print_json_or_rendered(console, as_json=as_json, value=summary, rendered=render_habit_target_status(summary))


def run_body_metrics_status_command(
    *,
    config_path: Path | None,
    date: str | None,
):
    return execute_body_metrics_status_workflow(
        config_path=config_path,
        date=date,
        load_database_path=load_database_path,
    )


def present_body_metrics_status_command(
    console: Console,
    *,
    config_path: Path | None,
    date: str | None,
    as_json: bool,
) -> None:
    summary = run_body_metrics_status_command(config_path=config_path, date=date)
    print_json_or_rendered(
        console,
        as_json=as_json,
        value=summary,
        rendered=render_body_metrics_status(summary),
    )


def run_workout_status_command(
    *,
    config_path: Path | None,
    date: str | None,
):
    return execute_workout_status_workflow(config_path=config_path, date=date, load_database_path=load_database_path)


def present_workout_status_command(
    console: Console,
    *,
    config_path: Path | None,
    date: str | None,
    as_json: bool,
) -> None:
    summary = run_workout_status_command(config_path=config_path, date=date)
    print_json_or_rendered(console, as_json=as_json, value=summary, rendered=render_workout_status(summary))


def run_spending_summary_command(
    *,
    config_path: Path | None,
    date: str | None,
    currency: str,
):
    return execute_spending_summary_workflow(
        config_path=config_path,
        date=date,
        currency=currency,
        load_database_path=load_database_path,
    )


def present_spending_summary_command(
    console: Console,
    *,
    config_path: Path | None,
    date: str | None,
    currency: str,
    as_json: bool,
) -> None:
    summary = run_spending_summary_command(config_path=config_path, date=date, currency=currency)
    print_json_or_rendered(console, as_json=as_json, value=summary, rendered=render_spending_summary(summary))


def run_budget_status_command(
    *,
    config_path: Path | None,
    period: str,
    date: str | None,
):
    return execute_budget_status_workflow(
        config_path=config_path,
        period=period,
        date=date,
        load_database_path=load_database_path,
    )


def present_budget_status_command(
    console: Console,
    *,
    config_path: Path | None,
    period: str,
    date: str | None,
    as_json: bool,
) -> None:
    summary = run_budget_status_command(config_path=config_path, period=period, date=date)
    print_json_or_rendered(console, as_json=as_json, value=summary, rendered=render_budget_status(summary))


def run_daily_status_command(
    *,
    config_path: Path | None,
    date: str | None,
):
    return execute_daily_status_workflow(config_path=config_path, date=date, load_database_path=load_database_path)


def present_daily_status_command(
    console: Console,
    *,
    config_path: Path | None,
    date: str | None,
    as_json: bool,
) -> None:
    summary = run_daily_status_command(config_path=config_path, date=date)
    print_json_or_rendered(console, as_json=as_json, value=summary, rendered=render_daily_status(summary))


def run_daily_review_command(
    *,
    config_path: Path | None,
    date: str | None,
):
    return execute_daily_review_workflow(config_path=config_path, date=date, load_database_path=load_database_path)


def present_daily_review_command(
    console: Console,
    *,
    config_path: Path | None,
    date: str | None,
    as_json: bool,
) -> None:
    import json

    review = run_daily_review_command(config_path=config_path, date=date)
    if as_json:
        console.print_json(json.dumps(review.to_dict(), indent=2, default=str))
    else:
        console.print(render_daily_review(review))


def run_weekly_review_personal_command(
    *,
    config_path: Path | None,
    date: str | None,
):
    return execute_weekly_review_personal_workflow(config_path=config_path, date=date, load_database_path=load_database_path)


def present_weekly_review_personal_command(
    console: Console,
    *,
    config_path: Path | None,
    date: str | None,
    as_json: bool,
) -> None:
    import json

    review = run_weekly_review_personal_command(config_path=config_path, date=date)
    if as_json:
        console.print_json(json.dumps(review.to_dict(), indent=2, default=str))
    else:
        console.print(render_weekly_review_personal(review))


__all__ = [
    "present_active_diet_command",
    "present_body_metrics_status_command",
    "present_budget_status_command",
    "present_daily_habits_command",
    "present_daily_macros_command",
    "present_daily_review_command",
    "present_daily_status_command",
    "present_diet_status_command",
    "present_habit_status_command",
    "present_macro_status_command",
    "present_spending_summary_command",
    "present_weekly_review_personal_command",
    "present_workout_status_command",
    "run_active_diet_command",
    "run_body_metrics_status_command",
    "run_budget_status_command",
    "run_daily_habits_command",
    "run_daily_macros_command",
    "run_daily_review_command",
    "run_daily_status_command",
    "run_diet_status_command",
    "run_habit_status_command",
    "run_macro_status_command",
    "run_spending_summary_command",
    "run_weekly_review_personal_command",
    "run_workout_status_command",
]
