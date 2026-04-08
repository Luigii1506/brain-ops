"""CLI orchestration helpers for personal logging commands."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from brain_ops.application import (
    execute_daily_log_workflow,
    execute_handle_input_workflow,
    execute_habit_checkin_workflow,
    execute_log_body_metrics_workflow,
    execute_log_expense_workflow,
    execute_log_meal_workflow,
    execute_log_supplement_workflow,
    execute_log_workout_workflow,
)
from brain_ops.interfaces.cli.presenters import print_rendered_with_operations
from brain_ops.interfaces.cli.runtime import load_database_path, load_event_sink, load_runtime_config
from brain_ops.models import HandleInputResult
from brain_ops.reporting_personal import (
    render_body_metrics_log,
    render_daily_log,
    render_expense_log,
    render_habit_checkin,
    render_meal_log,
    render_supplement_log,
    render_workout_log,
)


def run_log_meal_command(
    *,
    config_path: Path | None,
    meal_text: str,
    meal_type: str | None,
    dry_run: bool,
):
    return execute_log_meal_workflow(
        config_path=config_path,
        meal_text=meal_text,
        meal_type=meal_type,
        dry_run=dry_run,
        load_database_path=load_database_path,
        event_sink=load_event_sink(),
    )


def present_log_meal_command(
    console: Console,
    *,
    config_path: Path | None,
    meal_text: str,
    meal_type: str | None,
    dry_run: bool,
) -> None:
    result = run_log_meal_command(
        config_path=config_path,
        meal_text=meal_text,
        meal_type=meal_type,
        dry_run=dry_run,
    )
    print_rendered_with_operations(console, result.operations, render_meal_log(result))


def run_log_supplement_command(
    *,
    config_path: Path | None,
    supplement_name: str,
    amount: float | None,
    unit: str | None,
    note: str | None,
    dry_run: bool,
):
    return execute_log_supplement_workflow(
        config_path=config_path,
        supplement_name=supplement_name,
        amount=amount,
        unit=unit,
        note=note,
        dry_run=dry_run,
        load_database_path=load_database_path,
        event_sink=load_event_sink(),
    )


def present_log_supplement_command(
    console: Console,
    *,
    config_path: Path | None,
    supplement_name: str,
    amount: float | None,
    unit: str | None,
    note: str | None,
    dry_run: bool,
) -> None:
    result = run_log_supplement_command(
        config_path=config_path,
        supplement_name=supplement_name,
        amount=amount,
        unit=unit,
        note=note,
        dry_run=dry_run,
    )
    print_rendered_with_operations(console, result.operations, render_supplement_log(result))


def run_habit_checkin_command(
    *,
    config_path: Path | None,
    habit_name: str,
    status: str,
    note: str | None,
    dry_run: bool,
):
    return execute_habit_checkin_workflow(
        config_path=config_path,
        habit_name=habit_name,
        status=status,
        note=note,
        dry_run=dry_run,
        load_database_path=load_database_path,
        event_sink=load_event_sink(),
    )


def present_habit_checkin_command(
    console: Console,
    *,
    config_path: Path | None,
    habit_name: str,
    status: str,
    note: str | None,
    dry_run: bool,
) -> None:
    result = run_habit_checkin_command(
        config_path=config_path,
        habit_name=habit_name,
        status=status,
        note=note,
        dry_run=dry_run,
    )
    print_rendered_with_operations(console, result.operations, render_habit_checkin(result))


def run_log_body_metrics_command(
    *,
    config_path: Path | None,
    weight_kg: float | None,
    body_fat_pct: float | None,
    fat_mass_kg: float | None,
    muscle_mass_kg: float | None,
    visceral_fat: float | None,
    bmr_calories: float | None,
    arm_cm: float | None,
    waist_cm: float | None,
    thigh_cm: float | None,
    calf_cm: float | None,
    logged_at: str | None,
    note: str | None,
    dry_run: bool,
):
    return execute_log_body_metrics_workflow(
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
        load_database_path=load_database_path,
        event_sink=load_event_sink(),
    )


def present_log_body_metrics_command(
    console: Console,
    *,
    config_path: Path | None,
    weight_kg: float | None,
    body_fat_pct: float | None,
    fat_mass_kg: float | None,
    muscle_mass_kg: float | None,
    visceral_fat: float | None,
    bmr_calories: float | None,
    arm_cm: float | None,
    waist_cm: float | None,
    thigh_cm: float | None,
    calf_cm: float | None,
    logged_at: str | None,
    note: str | None,
    dry_run: bool,
) -> None:
    result = run_log_body_metrics_command(
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
        logged_at=logged_at,
        note=note,
        dry_run=dry_run,
    )
    print_rendered_with_operations(console, result.operations, render_body_metrics_log(result))


def run_log_workout_command(
    *,
    config_path: Path | None,
    workout_text: str,
    routine_name: str | None,
    duration_minutes: int | None,
    note: str | None,
    dry_run: bool,
):
    return execute_log_workout_workflow(
        config_path=config_path,
        workout_text=workout_text,
        routine_name=routine_name,
        duration_minutes=duration_minutes,
        note=note,
        dry_run=dry_run,
        load_database_path=load_database_path,
        event_sink=load_event_sink(),
    )


def present_log_workout_command(
    console: Console,
    *,
    config_path: Path | None,
    workout_text: str,
    routine_name: str | None,
    duration_minutes: int | None,
    note: str | None,
    dry_run: bool,
) -> None:
    result = run_log_workout_command(
        config_path=config_path,
        workout_text=workout_text,
        routine_name=routine_name,
        duration_minutes=duration_minutes,
        note=note,
        dry_run=dry_run,
    )
    print_rendered_with_operations(console, result.operations, render_workout_log(result))


def run_log_expense_command(
    *,
    config_path: Path | None,
    amount: float,
    category: str | None,
    merchant: str | None,
    currency: str,
    note: str | None,
    dry_run: bool,
):
    return execute_log_expense_workflow(
        config_path=config_path,
        amount=amount,
        category=category,
        merchant=merchant,
        currency=currency,
        note=note,
        dry_run=dry_run,
        load_database_path=load_database_path,
        event_sink=load_event_sink(),
    )


def present_log_expense_command(
    console: Console,
    *,
    config_path: Path | None,
    amount: float,
    category: str | None,
    merchant: str | None,
    currency: str,
    note: str | None,
    dry_run: bool,
) -> None:
    result = run_log_expense_command(
        config_path=config_path,
        amount=amount,
        category=category,
        merchant=merchant,
        currency=currency,
        note=note,
        dry_run=dry_run,
    )
    print_rendered_with_operations(console, result.operations, render_expense_log(result))


def run_daily_log_command(
    *,
    config_path: Path | None,
    text: str,
    domain: str,
    dry_run: bool,
):
    return execute_daily_log_workflow(
        config_path=config_path,
        text=text,
        domain=domain,
        dry_run=dry_run,
        load_database_path=load_database_path,
        event_sink=load_event_sink(),
    )


def present_daily_log_command(
    console: Console,
    *,
    config_path: Path | None,
    text: str,
    domain: str,
    dry_run: bool,
) -> None:
    result = run_daily_log_command(
        config_path=config_path,
        text=text,
        domain=domain,
        dry_run=dry_run,
    )
    print_rendered_with_operations(console, result.operations, render_daily_log(result))


def run_capture_command(
    *,
    config_path: Path | None,
    text: str,
    dry_run: bool,
) -> HandleInputResult:
    return execute_handle_input_workflow(
        config_path=config_path,
        text=text,
        dry_run=dry_run,
        use_llm=None,
        session_id=None,
        load_config=load_runtime_config,
        event_sink=load_event_sink(),
    )


# ---------------------------------------------------------------------------
# Domain label mapping for friendly output
# ---------------------------------------------------------------------------

_DOMAIN_LABELS: dict[str, str] = {
    "nutrition": "meal",
    "fitness": "workout",
    "expenses": "expense",
    "habits": "habit",
    "supplements": "supplement",
    "body_metrics": "body metrics",
    "daily": "journal",
    "nutrition_goals": "macro targets",
    "budget_goals": "budget target",
    "habit_goals": "habit target",
    "diet": "diet",
    "nutrition_status": "macro status",
    "budget_status": "budget status",
    "habit_status": "habit status",
    "daily_status": "daily status",
    "knowledge": "note",
}

_STORAGE_LABELS: dict[str, str] = {
    "nutrition": "SQLite (meals)",
    "fitness": "SQLite (workouts)",
    "expenses": "SQLite (expenses)",
    "habits": "SQLite (habits)",
    "supplements": "SQLite (supplements)",
    "body_metrics": "SQLite (body_metrics)",
    "daily": "SQLite (daily_logs)",
    "nutrition_goals": "SQLite (macro_targets)",
    "budget_goals": "SQLite (budget_targets)",
    "habit_goals": "SQLite (habit_targets)",
    "diet": "SQLite (diet_plans)",
    "knowledge": "Obsidian vault",
}


def _friendly_domain(result: HandleInputResult) -> str:
    domain = result.target_domain or (result.decision.domain if result.decision else "unknown")
    return _DOMAIN_LABELS.get(domain, domain)


def _storage_label(result: HandleInputResult) -> str:
    domain = result.target_domain or (result.decision.domain if result.decision else "unknown")
    return _STORAGE_LABELS.get(domain, "SQLite")


def _render_detail_lines(result: HandleInputResult) -> list[str]:
    """Build domain-specific detail lines from normalized_fields."""
    lines: list[str] = []
    nf = result.normalized_fields
    domain = result.target_domain or (result.decision.domain if result.decision else "")

    if domain == "nutrition":
        meal_type = nf.get("meal_type")
        items = nf.get("items")
        if meal_type:
            lines.append(f"  Meal type: {meal_type}")
        if isinstance(items, list):
            names = [it.get("food_name", str(it)) if isinstance(it, dict) else str(it) for it in items]
            lines.append(f"  Items: {', '.join(names)}")
        macros_parts = []
        for key, label in [("protein_g", "P"), ("carbs_g", "C"), ("fat_g", "F"), ("calories", "Cal")]:
            val = nf.get(key)
            if val is not None:
                macros_parts.append(f"{label}:{val}{'g' if key != 'calories' else ''}")
        if macros_parts:
            lines.append(f"  Macros: {' '.join(macros_parts)}")

    elif domain == "fitness":
        exercises = nf.get("exercises")
        routine = nf.get("routine_name")
        if routine:
            lines.append(f"  Routine: {routine}")
        if isinstance(exercises, list):
            parts = []
            for ex in exercises:
                if isinstance(ex, dict):
                    name = ex.get("exercise_name", "?")
                    s = ex.get("sets", "")
                    r = ex.get("reps", "")
                    w = ex.get("weight_kg")
                    desc = f"{name} {s}x{r}" if s and r else name
                    if w:
                        desc += f"@{w}kg"
                    parts.append(desc)
                else:
                    parts.append(str(ex))
            lines.append(f"  Exercises: {', '.join(parts)}")

    elif domain == "expenses":
        amount = nf.get("amount")
        currency = nf.get("currency", "MXN")
        category = nf.get("category")
        merchant = nf.get("merchant")
        if amount is not None:
            lines.append(f"  Amount: {amount} {currency}")
        if category:
            lines.append(f"  Category: {category}")
        if merchant:
            lines.append(f"  Merchant: {merchant}")

    elif domain == "habits":
        habit = nf.get("habit_name")
        status = nf.get("status", "done")
        if habit:
            lines.append(f"  Habit: {habit} ({status})")

    elif domain == "supplements":
        name = nf.get("supplement_name")
        amount = nf.get("amount")
        unit = nf.get("unit")
        if name:
            desc = name
            if amount and unit:
                desc += f" {amount}{unit}"
            lines.append(f"  Supplement: {desc}")

    elif domain == "body_metrics":
        for key, label in [("weight_kg", "Weight"), ("body_fat_pct", "Body fat"), ("waist_cm", "Waist")]:
            val = nf.get(key)
            if val is not None:
                lines.append(f"  {label}: {val}")

    elif domain == "daily":
        text_val = nf.get("text") or result.input_text
        log_domain = nf.get("domain") or nf.get("log_domain", "general")
        if text_val:
            display = text_val if len(str(text_val)) <= 60 else str(text_val)[:57] + "..."
            lines.append(f'  Entry: "{display}"')
        lines.append(f"  Domain: {log_domain}")

    # For multi-intent results show sub-result summaries
    if result.sub_results and not lines:
        for sr in result.sub_results:
            sr_domain = sr.target_domain or "unknown"
            sr_label = _DOMAIN_LABELS.get(sr_domain, sr_domain)
            executed_mark = "[ok]" if sr.executed else "[skip]"
            lines.append(f"  {executed_mark} {sr_label}: {sr.reason}")

    return lines


def render_capture_result(result: HandleInputResult, *, dry_run: bool = False) -> str:
    """Render a human-friendly capture summary."""
    domain_label = _friendly_domain(result)
    storage = _storage_label(result)

    prefix = "[dry-run] " if dry_run else ""
    status_mark = "ok" if result.executed else "routed"
    header = f"{prefix}Captured: {domain_label} ({status_mark})"

    lines = [header]
    detail = _render_detail_lines(result)
    lines.extend(detail)
    lines.append(f"  Stored in: {storage}")
    if result.confidence is not None:
        lines.append(f"  Confidence: {result.confidence:.2f}")
    if result.assistant_message:
        lines.append(f"  Message: {result.assistant_message}")
    if result.needs_follow_up and result.follow_up:
        lines.append(f"  Follow-up: {result.follow_up}")

    return "\n".join(lines)


def present_capture_unified_command(
    console: Console,
    *,
    config_path: Path | None,
    text: str,
    dry_run: bool,
    as_json: bool,
) -> None:
    from brain_ops.interfaces.cli.json_output import print_model_json

    result = run_capture_command(
        config_path=config_path,
        text=text,
        dry_run=dry_run,
    )

    if as_json:
        print_model_json(console, result)
        return

    if result.operations:
        from brain_ops.interfaces.cli.presenters import print_operations
        print_operations(console, result.operations)

    rendered = render_capture_result(result, dry_run=dry_run)
    console.print(rendered)


__all__ = [
    "present_capture_unified_command",
    "present_daily_log_command",
    "present_habit_checkin_command",
    "present_log_body_metrics_command",
    "present_log_expense_command",
    "present_log_meal_command",
    "present_log_supplement_command",
    "present_log_workout_command",
    "run_capture_command",
    "run_daily_log_command",
    "run_habit_checkin_command",
    "run_log_body_metrics_command",
    "run_log_expense_command",
    "run_log_meal_command",
    "run_log_supplement_command",
    "run_log_workout_command",
]
