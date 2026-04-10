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


    # -----------------------------------------------------------------------
    # TASKS
    # -----------------------------------------------------------------------

    @app.command("task")
    def task_command(
        title: str,
        project: str | None = typer.Option(None, "--project", "-p", help="Proyecto asociado."),
        priority: str = typer.Option("medium", "--priority", help="high, medium, low."),
        due: str | None = typer.Option(None, "--due", help="Fecha límite (YYYY-MM-DD)."),
        focus: str | None = typer.Option(None, "--focus", help="Fecha de foco (YYYY-MM-DD)."),
        tag: list[str] = typer.Option(None, "--tag", help="Tags (repetible)."),
        note: str | None = typer.Option(None, "--note", help="Nota adicional."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        as_json: bool = typer.Option(False, "--json", help="JSON output."),
    ) -> None:
        """Crear una tarea nueva."""
        try:
            from brain_ops.interfaces.cli.runtime import load_database_path
            from brain_ops.storage.sqlite.tasks import insert_task

            db_path = load_database_path(config_path)

            # Validar project contra registry si existe
            if project:
                try:
                    from brain_ops.interfaces.cli.projects import load_project_registry_path
                    from brain_ops.domains.projects import load_project_registry

                    registry = load_project_registry(load_project_registry_path())
                    if project not in registry:
                        console.print(f"[yellow]Aviso: proyecto '{project}' no está en el registry[/yellow]")
                except Exception:
                    pass

            task_id = insert_task(
                db_path,
                title,
                project=project,
                priority=priority,
                due_date=due,
                focus_date=focus,
                tags=tag or None,
                note=note,
                source="cli",
            )

            if as_json:
                console.print_json(data={"id": task_id, "title": title, "project": project, "priority": priority})
            else:
                proj_str = f" [{project}]" if project else ""
                due_str = f" (vence: {due})" if due else ""
                console.print(f"✓ Tarea #{task_id}{proj_str}: {title}{due_str} [{priority}]")
        except BrainOpsError as error:
            handle_error(error)

    @app.command("tasks")
    def tasks_command(
        project: str | None = typer.Option(None, "--project", "-p", help="Filtrar por proyecto. 'personal' para sin proyecto."),
        priority: str | None = typer.Option(None, "--priority", help="Filtrar por prioridad."),
        status: str | None = typer.Option(None, "--status", help="Filtrar por estado."),
        due_soon: bool = typer.Option(False, "--due-soon", help="Solo tareas que vencen en 7 días."),
        focus_today: bool = typer.Option(False, "--focus", help="Solo tareas con focus_date <= hoy."),
        all_tasks: bool = typer.Option(False, "--all", help="Incluir done y cancelled."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        as_json: bool = typer.Option(False, "--json", help="JSON output."),
    ) -> None:
        """Listar tareas pendientes."""
        try:
            from brain_ops.interfaces.cli.runtime import load_database_path
            from brain_ops.storage.sqlite.tasks import fetch_tasks

            db_path = load_database_path(config_path)
            effective_status = None if all_tasks else status
            tasks = fetch_tasks(
                db_path,
                project=project,
                status=effective_status,
                priority=priority,
                due_soon_days=7 if due_soon else None,
                focus_today=focus_today,
            )

            if as_json:
                console.print_json(data=tasks)
                return

            if not tasks:
                console.print("No hay tareas pendientes.")
                return

            from rich.table import Table

            table = Table(title="Tareas", show_lines=False)
            table.add_column("#", style="dim", width=4)
            table.add_column("Proyecto", style="cyan", width=15)
            table.add_column("Tarea", width=40)
            table.add_column("Prior.", width=6)
            table.add_column("Estado", width=8)
            table.add_column("Vence", width=12)
            table.add_column("Foco", width=12)

            priority_colors = {"high": "red", "medium": "yellow", "low": "dim"}
            status_icons = {"pending": "○", "active": "●", "done": "✓", "cancelled": "✗"}

            for t in tasks:
                pcolor = priority_colors.get(t["priority"], "")
                sicon = status_icons.get(t["status"], "?")
                table.add_row(
                    str(t["id"]),
                    t["project"] or "personal",
                    t["title"][:40],
                    f"[{pcolor}]{t['priority']}[/{pcolor}]",
                    sicon,
                    t.get("due_date") or "—",
                    t.get("focus_date") or "—",
                )

            console.print(table)
        except BrainOpsError as error:
            handle_error(error)

    @app.command("task-done")
    def task_done_command(
        task_id: int,
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
    ) -> None:
        """Marcar una tarea como completada."""
        try:
            from brain_ops.interfaces.cli.runtime import load_database_path
            from brain_ops.storage.sqlite.tasks import complete_task, fetch_task_by_id

            db_path = load_database_path(config_path)
            task = fetch_task_by_id(db_path, task_id)
            if not task:
                console.print(f"Tarea #{task_id} no encontrada.")
                return

            complete_task(db_path, task_id)
            console.print(f"✓ Tarea #{task_id} completada: {task['title']}")
        except BrainOpsError as error:
            handle_error(error)

    @app.command("task-update")
    def task_update_command(
        task_id: int,
        priority: str | None = typer.Option(None, "--priority", help="Nueva prioridad."),
        status: str | None = typer.Option(None, "--status", help="Nuevo estado."),
        due: str | None = typer.Option(None, "--due", help="Nueva fecha límite."),
        focus: str | None = typer.Option(None, "--focus", help="Nueva fecha de foco."),
        note: str | None = typer.Option(None, "--note", help="Nueva nota."),
        project: str | None = typer.Option(None, "--project", help="Cambiar proyecto."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
    ) -> None:
        """Actualizar una tarea existente."""
        try:
            from brain_ops.interfaces.cli.runtime import load_database_path
            from brain_ops.storage.sqlite.tasks import update_task

            db_path = load_database_path(config_path)
            updated = update_task(
                db_path, task_id,
                priority=priority, status=status,
                due_date=due, focus_date=focus,
                note=note, project=project,
            )
            if updated:
                console.print(f"✓ Tarea #{task_id} actualizada.")
            else:
                console.print(f"Tarea #{task_id} no encontrada o sin cambios.")
        except BrainOpsError as error:
            handle_error(error)


    # -----------------------------------------------------------------------
    # KNOWLEDGE MASTERY / SRS
    # -----------------------------------------------------------------------

    def _extract_questions(body: str) -> list[tuple[str, str]]:
        """Extract (question, answer) pairs from ## Preguntas de recuperación."""
        import re

        q_match = re.search(
            r"## Preguntas de recuperación\n(.*?)(?=\n## |\Z)",
            body, re.DOTALL,
        )
        if not q_match:
            return []

        pairs: list[tuple[str, str]] = []
        for line in q_match.group(1).strip().splitlines():
            line = line.strip()
            if not line.startswith("-"):
                continue
            # Format: - 🟢 **question** → answer
            parts = line.lstrip("- ").split("→", 1)
            if len(parts) == 2:
                question = parts[0].strip()
                answer = parts[1].strip()
                pairs.append((question, answer))
            else:
                # No → separator — treat whole line as question
                pairs.append((parts[0].strip(), ""))
        return pairs

    def _find_entity_body(vault_path: Path, name: str) -> str | None:
        """Find entity note and return its body text."""
        from brain_ops.frontmatter import split_frontmatter

        knowledge_dir = vault_path / "02 - Knowledge"
        for md in knowledge_dir.glob("*.md"):
            try:
                text = md.read_text(encoding="utf-8")
                fm, body = split_frontmatter(text)
                if fm.get("entity") is True and fm.get("name") == name:
                    return body
            except Exception:
                pass
        return None

    def _run_review_for_entity(
        console_obj, db_path: Path, vault_path: Path, name: str, difficulty: int = 0,
    ) -> dict | None:
        """Run a single entity review. Returns mastery result or None."""
        from brain_ops.storage.sqlite.mastery import record_review, fetch_entity_mastery

        body = _find_entity_body(vault_path, name)
        if body is None:
            console_obj.print(f"  Entidad '{name}' no encontrada.")
            return None

        questions = _extract_questions(body)
        level_names = {0: "nuevo", 1: "visto", 2: "recordado", 3: "explicado", 4: "dominado"}
        mastery = fetch_entity_mastery(db_path, name)
        current_level = level_names.get(mastery["mastery_level"], "?") if mastery else "sin revisar"

        console_obj.print(f"\n[bold]═══ {name} ═══[/bold] (nivel: {current_level})")
        console_obj.print()

        if questions:
            for i, (question, answer) in enumerate(questions, 1):
                console_obj.print(f"  [bold]Pregunta {i}/{len(questions)}:[/bold] {question}")
                try:
                    input("  [Presiona Enter para ver la respuesta...]")
                except EOFError:
                    pass
                if answer:
                    console_obj.print(f"  [green]Respuesta:[/green] {answer}")
                console_obj.print()
        else:
            console_obj.print("  [yellow]Sin preguntas de recuperación.[/yellow]")
            console_obj.print()

        # Get difficulty
        if difficulty == 0:
            console_obj.print("[dim]¿Qué tan bien respondiste? (1=nada, 2=poco, 3=con esfuerzo, 4=bien, 5=perfecto)[/dim]")
            try:
                difficulty = int(input("Dificultad (1-5): ").strip())
            except (ValueError, EOFError):
                difficulty = 3

        result = record_review(db_path, name, max(1, min(5, difficulty)))
        console_obj.print(
            f"  ✓ Nivel: {level_names.get(result['mastery_level'], '?')} | "
            f"Próximo: {result['next_review']} | "
            f"Revisiones: {result['times_reviewed']}"
        )
        return result

    @app.command("review-entity")
    def review_entity_command(
        name: str,
        difficulty: int = typer.Option(0, "--difficulty", "-d", help="Dificultad 1-5 (0=interactivo)."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
    ) -> None:
        """Repasar una entidad: muestra preguntas una por una, luego revela respuesta."""
        try:
            from brain_ops.interfaces.cli.runtime import load_database_path, load_validated_vault

            db_path = load_database_path(config_path)
            vault = load_validated_vault(config_path, dry_run=True)

            _run_review_for_entity(console, db_path, vault.config.vault_path, name, difficulty)

        except BrainOpsError as error:
            handle_error(error)

    @app.command("knowledge-due")
    def knowledge_due_command(
        limit: int = typer.Option(10, "--limit", help="Máximo de entidades a mostrar."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        as_json: bool = typer.Option(False, "--json", help="JSON output."),
    ) -> None:
        """Listar entidades pendientes de repaso hoy (SRS)."""
        try:
            from brain_ops.interfaces.cli.runtime import load_database_path, load_validated_vault
            from brain_ops.storage.sqlite.mastery import fetch_due_entities, fetch_new_entities

            db_path = load_database_path(config_path)
            vault = load_validated_vault(config_path, dry_run=True)

            due = fetch_due_entities(db_path, limit=limit)
            new = fetch_new_entities(db_path, vault.config.vault_path, limit=5)

            if as_json:
                console.print_json(data={"due": due, "new": new})
                return

            level_names = {0: "nuevo", 1: "visto", 2: "recordado", 3: "explicado", 4: "dominado"}

            if due:
                console.print("\n[bold]Entidades para repasar hoy:[/bold]")
                for e in due:
                    lvl = level_names.get(e["mastery_level"], "?")
                    console.print(f"  • {e['entity_name']} [{lvl}] (dificultad: {e['avg_difficulty']:.1f})")
            else:
                console.print("\n[green]No hay entidades pendientes de repaso hoy.[/green]")

            if new:
                console.print(f"\n[bold]Entidades nuevas sin revisar ({len(new)}):[/bold]")
                for n in new[:5]:
                    console.print(f"  ○ {n}")

            console.print()

        except BrainOpsError as error:
            handle_error(error)

    @app.command("knowledge-status")
    def knowledge_status_command(
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        as_json: bool = typer.Option(False, "--json", help="JSON output."),
    ) -> None:
        """Resumen del estado de dominio del conocimiento."""
        try:
            from brain_ops.interfaces.cli.runtime import load_database_path, load_validated_vault
            from brain_ops.storage.sqlite.mastery import fetch_mastery_summary, fetch_new_entities

            db_path = load_database_path(config_path)
            vault = load_validated_vault(config_path, dry_run=True)

            summary = fetch_mastery_summary(db_path)
            new = fetch_new_entities(db_path, vault.config.vault_path, limit=999)

            if as_json:
                summary["unreviewed"] = len(new)
                console.print_json(data=summary)
                return

            console.print("\n[bold]Estado de conocimiento:[/bold]")
            console.print(f"  Revisadas: {summary['total_reviewed']} entidades")
            console.print(f"  Sin revisar: {len(new)} entidades")
            console.print(f"  Pendientes hoy: {summary['due_today']}")
            console.print(f"  Dificultad promedio: {summary['avg_difficulty']:.1f}/5")
            console.print()
            console.print("[bold]Por nivel:[/bold]")
            for level, count in summary["by_level"].items():
                console.print(f"  {level}: {count}")
            console.print()

        except BrainOpsError as error:
            handle_error(error)

    @app.command("study")
    def study_command(
        count: int = typer.Option(5, "--count", "-n", help="Número de entidades a repasar."),
        topic: str | None = typer.Option(None, "--topic", "-t", help="Filtrar por tag/tema (ej: guerras-médicas, guerra-del-peloponeso)."),
        include_new: bool = typer.Option(True, "--include-new/--no-new", help="Incluir entidades nuevas si no hay suficientes pendientes."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
    ) -> None:
        """Sesión de estudio: repasa entidades con preguntas interactivas (SRS elige por ti)."""
        try:
            from brain_ops.interfaces.cli.runtime import load_database_path, load_validated_vault
            from brain_ops.storage.sqlite.mastery import fetch_due_entities, fetch_new_entities, get_entities_by_topic

            db_path = load_database_path(config_path)
            vault = load_validated_vault(config_path, dry_run=True)

            # Topic filter
            topic_set: set[str] | None = None
            if topic:
                topic_set = get_entities_by_topic(vault.config.vault_path, topic)
                if not topic_set:
                    console.print(f"\n[yellow]No se encontraron entidades con tag '{topic}'.[/yellow]\n")
                    return

            # Collect entities to study
            due = fetch_due_entities(db_path, limit=count, topic_filter=topic_set)
            entities_to_study = [e["entity_name"] for e in due]

            # Fill with new entities if not enough
            if include_new and len(entities_to_study) < count:
                remaining = count - len(entities_to_study)
                new = fetch_new_entities(db_path, vault.config.vault_path, limit=remaining, topic=topic)
                entities_to_study.extend(new)

            if not entities_to_study:
                console.print("\n[green]No hay entidades para estudiar hoy. ¡Buen trabajo![/green]\n")
                return

            topic_label = f" — tema: {topic}" if topic else ""
            console.print(f"\n[bold]═══ Sesión de estudio ({len(entities_to_study)} entidades{topic_label}) ═══[/bold]")
            console.print()

            results: list[dict] = []
            level_names = {0: "nuevo", 1: "visto", 2: "recordado", 3: "explicado", 4: "dominado"}

            for i, entity_name in enumerate(entities_to_study, 1):
                console.print(f"[dim]── Entidad {i}/{len(entities_to_study)} ──[/dim]")
                result = _run_review_for_entity(
                    console, db_path, vault.config.vault_path, entity_name,
                )
                if result:
                    results.append(result)
                console.print()

            # Summary
            if results:
                avg_diff = sum(r["avg_difficulty"] for r in results) / len(results)
                by_next: dict[str, int] = {}
                for r in results:
                    next_date = r["next_review"]
                    by_next[next_date] = by_next.get(next_date, 0) + 1

                console.print("[bold]═══ Resumen de la sesión ═══[/bold]")
                console.print(f"  Entidades repasadas: {len(results)}")
                console.print(f"  Dificultad promedio: {avg_diff:.1f}/5")
                console.print()
                console.print("[bold]Próximos repasos:[/bold]")
                for date, n in sorted(by_next.items()):
                    console.print(f"  {date}: {n} entidad{'es' if n > 1 else ''}")
                console.print()

        except BrainOpsError as error:
            handle_error(error)


__all__ = ["register_personal_commands"]
