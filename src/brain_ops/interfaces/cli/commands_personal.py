"""Typer command registration for personal workflows."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from brain_ops.errors import BrainOpsError

from .personal import (
    present_active_diet_command,
    present_body_metrics_status_command,
    present_budget_status_command,
    present_daily_habits_command,
    present_daily_macros_command,
    present_daily_review_command,
    present_daily_status_command,
    present_diet_status_command,
    present_habit_status_command,
    present_macro_status_command,
    present_spending_summary_command,
    present_weekly_review_personal_command,
    present_workout_status_command,
)
from .personal_logging import (
    present_capture_unified_command,
    present_daily_log_command,
    present_habit_checkin_command,
    present_log_body_metrics_command,
    present_log_expense_command,
    present_log_meal_command,
    present_log_supplement_command,
    present_log_workout_command,
)
from .personal_management import (
    present_create_diet_plan_command,
    present_set_active_diet_command,
    present_set_budget_target_command,
    present_set_habit_target_command,
    present_set_macro_targets_command,
    present_update_diet_meal_command,
)


def register_personal_commands(app: typer.Typer, console: Console, handle_error) -> None:
    @app.command("capture")
    def capture_command(
        text: str,
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        dry_run: bool = typer.Option(False, "--dry-run", help="Preview without storing anything."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Capture natural-language personal data (meals, workouts, expenses, habits, journal, etc.)."""
        try:
            present_capture_unified_command(
                console,
                config_path=config_path,
                text=text,
                dry_run=dry_run,
                as_json=as_json,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("log-meal")
    def log_meal_command(
        meal_text: str,
        meal_type: str | None = typer.Option(None, "--meal-type", help="Optional meal type like breakfast, lunch, dinner, snack."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing to SQLite."),
    ) -> None:
        """Log a structured meal into SQLite using a simple semicolon-separated format."""
        try:
            present_log_meal_command(
                console,
                config_path=config_path,
                meal_text=meal_text,
                meal_type=meal_type,
                dry_run=dry_run,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("daily-macros")
    def daily_macros_command(
        date: str | None = typer.Option(None, "--date", help="Date in YYYY-MM-DD format. Defaults to today."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Show macro totals for a given date from SQLite."""
        try:
            present_daily_macros_command(console, config_path=config_path, date=date, as_json=as_json)
        except BrainOpsError as error:
            handle_error(error)

    @app.command("set-macro-targets")
    def set_macro_targets_command(
        calories: float | None = typer.Option(None, "--calories", help="Daily calories target."),
        protein_g: float | None = typer.Option(None, "--protein-g", help="Daily protein target in grams."),
        carbs_g: float | None = typer.Option(None, "--carbs-g", help="Daily carbs target in grams."),
        fat_g: float | None = typer.Option(None, "--fat-g", help="Daily fat target in grams."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing to SQLite."),
    ) -> None:
        """Store daily macro targets in SQLite."""
        try:
            present_set_macro_targets_command(
                console,
                config_path=config_path,
                calories=calories,
                protein_g=protein_g,
                carbs_g=carbs_g,
                fat_g=fat_g,
                dry_run=dry_run,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("macro-status")
    def macro_status_command(
        date: str | None = typer.Option(None, "--date", help="Date in YYYY-MM-DD format. Defaults to today."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Compare daily macro totals against the stored macro target."""
        try:
            present_macro_status_command(console, config_path=config_path, date=date, as_json=as_json)
        except BrainOpsError as error:
            handle_error(error)

    @app.command("create-diet-plan")
    def create_diet_plan_command(
        name: str,
        meal: list[str] = typer.Option(
            ...,
            "--meal",
            help="Meal spec like 'breakfast|3 huevos; 100g avena p:13 c:68 f:7 cal:389' or 'breakfast|Desayuno fuerte|...'. Repeat for multiple meals.",
        ),
        notes: str | None = typer.Option(None, "--notes", help="Optional plan notes."),
        activate: bool = typer.Option(False, "--activate", help="Set the new diet plan as active immediately."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing to SQLite."),
    ) -> None:
        """Create a named diet plan with expected meals and macros."""
        try:
            present_create_diet_plan_command(
                console,
                config_path=config_path,
                name=name,
                meal=meal,
                notes=notes,
                activate=activate,
                dry_run=dry_run,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("set-active-diet")
    def set_active_diet_command(
        name: str,
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing to SQLite."),
    ) -> None:
        """Set an existing diet plan as the active diet."""
        try:
            present_set_active_diet_command(
                console,
                config_path=config_path,
                name=name,
                dry_run=dry_run,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("active-diet")
    def active_diet_command(
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Show the currently active diet plan."""
        try:
            present_active_diet_command(console, config_path=config_path, as_json=as_json)
        except BrainOpsError as error:
            handle_error(error)

    @app.command("diet-status")
    def diet_status_command(
        date: str | None = typer.Option(None, "--date", help="Reference date in YYYY-MM-DD format. Defaults to today."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Compare daily intake against the active diet plan."""
        try:
            present_diet_status_command(console, config_path=config_path, date=date, as_json=as_json)
        except BrainOpsError as error:
            handle_error(error)

    @app.command("update-diet-meal")
    def update_diet_meal_command(
        meal_type: str = typer.Option(..., "--meal-type", help="Meal type like breakfast, lunch, or dinner."),
        items: str = typer.Option(..., "--items", help="Items string using the same meal item syntax as log-meal."),
        mode: str = typer.Option("replace", "--mode", help="Update mode: replace or append."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing to SQLite."),
    ) -> None:
        """Replace or append items in one meal of the active diet plan."""
        try:
            present_update_diet_meal_command(
                console,
                config_path=config_path,
                meal_type=meal_type,
                items=items,
                mode=mode,
                dry_run=dry_run,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("log-supplement")
    def log_supplement_command(
        supplement_name: str,
        amount: float | None = typer.Option(None, "--amount", help="Optional numeric amount."),
        unit: str | None = typer.Option(None, "--unit", help="Optional unit like mg, g, caps, ml."),
        note: str | None = typer.Option(None, "--note", help="Optional freeform note."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing to SQLite."),
    ) -> None:
        """Log supplement intake into SQLite."""
        try:
            present_log_supplement_command(
                console,
                config_path=config_path,
                supplement_name=supplement_name,
                amount=amount,
                unit=unit,
                note=note,
                dry_run=dry_run,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("habit-checkin")
    def habit_checkin_command(
        habit_name: str,
        status: str = typer.Option("done", "--status", help="Habit status: done, partial, skipped."),
        note: str | None = typer.Option(None, "--note", help="Optional freeform note."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing to SQLite."),
    ) -> None:
        """Log a habit check-in into SQLite."""
        try:
            present_habit_checkin_command(
                console,
                config_path=config_path,
                habit_name=habit_name,
                status=status,
                note=note,
                dry_run=dry_run,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("daily-habits")
    def daily_habits_command(
        date: str | None = typer.Option(None, "--date", help="Date in YYYY-MM-DD format. Defaults to today."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Show habit check-ins for a given date from SQLite."""
        try:
            present_daily_habits_command(console, config_path=config_path, date=date, as_json=as_json)
        except BrainOpsError as error:
            handle_error(error)

    @app.command("set-habit-target")
    def set_habit_target_command(
        habit_name: str,
        target_count: int = typer.Option(..., "--target-count", help="Required target count for the period."),
        period: str = typer.Option("daily", "--period", help="Target period: daily, weekly, monthly."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing to SQLite."),
    ) -> None:
        """Store a habit target in SQLite."""
        try:
            present_set_habit_target_command(
                console,
                config_path=config_path,
                habit_name=habit_name,
                target_count=target_count,
                period=period,
                dry_run=dry_run,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("habit-status")
    def habit_status_command(
        period: str = typer.Option("daily", "--period", help="Status period: daily, weekly, monthly."),
        date: str | None = typer.Option(None, "--date", help="Reference date in YYYY-MM-DD format. Defaults to today."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Compare habit completion counts against stored habit targets."""
        try:
            present_habit_status_command(
                console,
                config_path=config_path,
                period=period,
                date=date,
                as_json=as_json,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("log-body-metrics")
    def log_body_metrics_command(
        weight_kg: float | None = typer.Option(None, "--weight-kg", help="Body weight in kilograms."),
        body_fat_pct: float | None = typer.Option(None, "--body-fat-pct", help="Body fat percentage."),
        fat_mass_kg: float | None = typer.Option(None, "--fat-mass-kg", help="Fat mass in kilograms."),
        muscle_mass_kg: float | None = typer.Option(None, "--muscle-mass-kg", help="Muscle mass in kilograms."),
        visceral_fat: float | None = typer.Option(None, "--visceral-fat", help="Visceral fat score."),
        bmr_calories: float | None = typer.Option(None, "--bmr-calories", help="Basal metabolic rate calories."),
        arm_cm: float | None = typer.Option(None, "--arm-cm", help="Arm circumference in centimeters."),
        waist_cm: float | None = typer.Option(None, "--waist-cm", help="Waist circumference in centimeters."),
        thigh_cm: float | None = typer.Option(None, "--thigh-cm", help="Thigh circumference in centimeters."),
        calf_cm: float | None = typer.Option(None, "--calf-cm", help="Calf circumference in centimeters."),
        logged_at: str | None = typer.Option(None, "--logged-at", help="Optional snapshot datetime in ISO format."),
        note: str | None = typer.Option(None, "--note", help="Optional freeform note."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing to SQLite."),
    ) -> None:
        """Log body metrics into SQLite."""
        try:
            present_log_body_metrics_command(
                console,
                config_path=config_path,
                weight_kg=weight_kg,
                body_fat_pct=body_fat_pct,
                fat_mass_kg=fat_mass_kg,
                muscle_mass_kg=muscle_mass_kg,
                visceral_fat=visceral_fat,
                bmr_calories=bmr_calories,
                arm_cm=arm_cm,
                waist_cm=waist_cm,
                thigh_cm=thigh_cm,
                calf_cm=calf_cm,
                note=note,
                logged_at=logged_at,
                dry_run=dry_run,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("body-metrics-status")
    def body_metrics_status_command(
        date: str | None = typer.Option(None, "--date", help="Date in YYYY-MM-DD format. Defaults to today."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Show the latest body metrics snapshot for a given date."""
        try:
            present_body_metrics_status_command(console, config_path=config_path, date=date, as_json=as_json)
        except BrainOpsError as error:
            handle_error(error)

    @app.command("log-workout")
    def log_workout_command(
        workout_text: str,
        routine_name: str | None = typer.Option(None, "--routine-name", help="Optional routine name like push, pull, legs."),
        duration_minutes: int | None = typer.Option(None, "--duration-minutes", help="Optional workout duration."),
        note: str | None = typer.Option(None, "--note", help="Optional freeform note."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing to SQLite."),
    ) -> None:
        """Log a workout session using entries like 'Press banca 4x8@80kg; Dominadas 3x10@bodyweight'."""
        try:
            present_log_workout_command(
                console,
                config_path=config_path,
                workout_text=workout_text,
                routine_name=routine_name,
                duration_minutes=duration_minutes,
                note=note,
                dry_run=dry_run,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("workout-status")
    def workout_status_command(
        date: str | None = typer.Option(None, "--date", help="Date in YYYY-MM-DD format. Defaults to today."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Show workout summary for a given date from SQLite."""
        try:
            present_workout_status_command(console, config_path=config_path, date=date, as_json=as_json)
        except BrainOpsError as error:
            handle_error(error)

    @app.command("log-expense")
    def log_expense_command(
        amount: float,
        category: str | None = typer.Option(None, "--category", help="Optional expense category."),
        merchant: str | None = typer.Option(None, "--merchant", help="Optional merchant or payee."),
        currency: str = typer.Option("MXN", "--currency", help="Currency code, defaults to MXN."),
        note: str | None = typer.Option(None, "--note", help="Optional freeform note."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing to SQLite."),
    ) -> None:
        """Log an expense into SQLite."""
        try:
            present_log_expense_command(
                console,
                config_path=config_path,
                amount=amount,
                category=category,
                merchant=merchant,
                currency=currency,
                note=note,
                dry_run=dry_run,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("spending-summary")
    def spending_summary_command(
        date: str | None = typer.Option(None, "--date", help="Date in YYYY-MM-DD format. Defaults to today."),
        currency: str = typer.Option("MXN", "--currency", help="Currency code, defaults to MXN."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Show spending totals for a given date from SQLite."""
        try:
            present_spending_summary_command(
                console,
                config_path=config_path,
                date=date,
                currency=currency,
                as_json=as_json,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("set-budget-target")
    def set_budget_target_command(
        amount: float,
        period: str = typer.Option("weekly", "--period", help="Budget period: daily, weekly, monthly."),
        category: str | None = typer.Option(None, "--category", help="Optional category-specific budget."),
        currency: str = typer.Option("MXN", "--currency", help="Currency code, defaults to MXN."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing to SQLite."),
    ) -> None:
        """Store a budget target in SQLite."""
        try:
            present_set_budget_target_command(
                console,
                config_path=config_path,
                amount=amount,
                period=period,
                category=category,
                currency=currency,
                dry_run=dry_run,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("budget-status")
    def budget_status_command(
        period: str = typer.Option("weekly", "--period", help="Budget period: daily, weekly, monthly."),
        date: str | None = typer.Option(None, "--date", help="Reference date in YYYY-MM-DD format. Defaults to today."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Compare spending totals against stored budget targets."""
        try:
            present_budget_status_command(
                console,
                config_path=config_path,
                period=period,
                date=date,
                as_json=as_json,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("daily-log")
    def daily_log_command(
        text: str,
        domain: str = typer.Option("general", "--domain", help="Logical domain label for the event."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing to SQLite."),
    ) -> None:
        """Log a generic daily event into SQLite."""
        try:
            present_daily_log_command(
                console,
                config_path=config_path,
                text=text,
                domain=domain,
                dry_run=dry_run,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("daily-status")
    def daily_status_command(
        date: str | None = typer.Option(None, "--date", help="Date in YYYY-MM-DD format. Defaults to today."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Show a compact cross-domain state snapshot for the day."""
        try:
            present_daily_status_command(console, config_path=config_path, date=date, as_json=as_json)
        except BrainOpsError as error:
            handle_error(error)

    @app.command("daily-review")
    def daily_review_command(
        date: str | None = typer.Option(None, "--date", help="Date in YYYY-MM-DD format. Defaults to today."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Show a scored daily review with highlights, gaps, and suggestions."""
        try:
            present_daily_review_command(console, config_path=config_path, date=date, as_json=as_json)
        except BrainOpsError as error:
            handle_error(error)

    @app.command("week-review")
    def week_review_command(
        date: str | None = typer.Option(None, "--date", help="End date in YYYY-MM-DD format. Defaults to today."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Show a weekly personal review with trends across 7 days of data."""
        try:
            present_weekly_review_personal_command(console, config_path=config_path, date=date, as_json=as_json)
        except BrainOpsError as error:
            handle_error(error)


__all__ = ["register_personal_commands"]
