from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from brain_ops import __version__
from brain_ops.config import VaultConfig, load_config
from brain_ops.constants import DEFAULT_INIT_CONFIG_PATH
from brain_ops.errors import AIProviderError, BrainOpsError, ConfigError
from brain_ops.models import CreateNoteRequest, OperationRecord, OperationStatus
from brain_ops.reporting import (
    render_applied_links,
    render_body_metrics_log,
    render_body_metrics_status,
    render_daily_habits,
    render_daily_log,
    render_daily_macros,
    render_daily_summary,
    render_enriched_note,
    render_expense_log,
    render_handle_input,
    render_habit_checkin,
    render_inbox_report,
    render_link_suggestions,
    render_meal_log,
    render_normalize_frontmatter,
    render_promoted_note,
    render_route_decision,
    render_supplement_log,
    render_spending_summary,
    render_vault_audit,
    render_weekly_review,
    render_workout_log,
    render_workout_status,
)
from brain_ops.services.audit_service import audit_vault
from brain_ops.services.apply_links_service import apply_link_suggestions
from brain_ops.services.body_metrics_service import body_metrics_status, log_body_metrics
from brain_ops.services.capture_service import capture_text
from brain_ops.services.daily_log_service import log_daily_event
from brain_ops.services.daily_summary_service import write_daily_summary
from brain_ops.services.enrich_service import enrich_note
from brain_ops.services.expenses_service import log_expense, spending_summary
from brain_ops.services.fitness_service import log_workout, workout_status
from brain_ops.services.handle_input_service import handle_input
from brain_ops.services.improve_service import improve_note
from brain_ops.services.inbox_service import process_inbox
from brain_ops.services.life_ops_service import daily_habits, habit_checkin, log_supplement
from brain_ops.services.link_service import suggest_links
from brain_ops.services.note_service import create_note
from brain_ops.services.normalize_service import normalize_frontmatter
from brain_ops.services.nutrition_service import daily_macros, log_meal
from brain_ops.services.project_service import create_project_scaffold
from brain_ops.services.promote_service import promote_note
from brain_ops.services.research_service import research_note
from brain_ops.services.review_service import generate_weekly_review
from brain_ops.services.router_service import route_input
from brain_ops.storage import initialize_database
from brain_ops.vault import Vault
from brain_ops.ai import llm_route_input

app = typer.Typer(help="brain-ops CLI")
console = Console()


OPENCLAW_MANIFEST = {
    "name": "brain-ops",
    "entrypoint": "brain",
    "preferred_natural_input_command": "handle-input",
    "preferred_natural_input_args": ["<text>", "--json"],
    "notes": [
        "Use brain-ops as the deterministic execution layer.",
        "Prefer handle-input for natural language.",
        "Prefer route-input for plan-only classification.",
    ],
    "tools": [
        {
            "name": "handle_input",
            "command": 'brain handle-input "<text>" --json',
            "purpose": "Route and execute safe actions from natural language.",
        },
        {
            "name": "route_input",
            "command": 'brain route-input "<text>" --json',
            "purpose": "Classify natural language without side effects.",
        },
        {
            "name": "daily_summary",
            "command": "brain daily-summary --date <yyyy-mm-dd>",
            "purpose": "Write structured day summaries into the Obsidian vault.",
        },
        {
            "name": "daily_macros",
            "command": "brain daily-macros --date <yyyy-mm-dd>",
            "purpose": "Read nutrition totals from SQLite.",
        },
        {
            "name": "daily_habits",
            "command": "brain daily-habits --date <yyyy-mm-dd>",
            "purpose": "Read habit status summaries from SQLite.",
        },
        {
            "name": "workout_status",
            "command": "brain workout-status --date <yyyy-mm-dd>",
            "purpose": "Read workout summaries from SQLite.",
        },
        {
            "name": "spending_summary",
            "command": "brain spending-summary --date <yyyy-mm-dd>",
            "purpose": "Read expense summaries from SQLite.",
        },
        {
            "name": "body_metrics_status",
            "command": "brain body-metrics-status --date <yyyy-mm-dd>",
            "purpose": "Read body metrics summaries from SQLite.",
        },
        {
            "name": "capture",
            "command": 'brain capture "<text>"',
            "purpose": "Create a note in the vault from natural language.",
        },
        {
            "name": "improve_note",
            "command": "brain improve-note <note_path>",
            "purpose": "Improve structure of an existing note.",
        },
        {
            "name": "research_note",
            "command": "brain research-note <note_path> --query <query>",
            "purpose": "Enrich a note with grounded research.",
        },
    ],
}


def _load_vault(config_path: Path | None, dry_run: bool) -> Vault:
    config = load_config(config_path)
    vault = Vault(config=config, dry_run=dry_run)
    vault.validate()
    return vault


def _print_operations(operations: list[OperationRecord]) -> None:
    table = Table(title="Operations")
    table.add_column("Status")
    table.add_column("Action")
    table.add_column("Path")
    table.add_column("Detail")
    for operation in operations:
        table.add_row(
            operation.status.value,
            operation.action,
            str(operation.path),
            operation.detail,
        )
    console.print(table)


def _handle_error(error: BrainOpsError) -> None:
    console.print(f"[red]Error:[/red] {error}")
    raise typer.Exit(code=1)


@app.command()
def info(config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML.")) -> None:
    """Show resolved project and vault configuration."""
    try:
        config = load_config(config_path)
    except BrainOpsError as error:
        _handle_error(error)
        return

    table = Table(title=f"brain-ops {__version__}")
    table.add_column("Setting")
    table.add_column("Value")
    table.add_row("Vault path", str(config.vault_path))
    table.add_row("Timezone", config.default_timezone)
    table.add_row("Template dir", str(config.template_dir))
    table.add_row("Data dir", str(config.data_dir))
    table.add_row("Database path", str(config.database_path))
    table.add_row("AI provider", config.ai.provider)
    table.add_row("Ollama host", config.ai.ollama_host)
    table.add_row("Orchestrator", config.ai.orchestrator)
    table.add_row("Inbox folder", config.folders.inbox)
    table.add_row("Projects folder", config.folders.projects)
    table.add_row("Reports folder", config.folders.reports)
    console.print(table)


@app.command("openclaw-manifest")
def openclaw_manifest_command(
    as_json: bool = typer.Option(True, "--json/--no-json", help="Print the manifest as JSON."),
    output: Path | None = typer.Option(None, "--output", help="Optional file path to write the manifest JSON."),
) -> None:
    """Print the preferred OpenClaw integration manifest for brain-ops."""
    if output is not None:
        output_path = output.expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(OPENCLAW_MANIFEST, indent=2) + "\n", encoding="utf-8")
        console.print(f"Wrote OpenClaw manifest to {output_path}")
        if not as_json:
            return
    if as_json:
        console.print_json(data=OPENCLAW_MANIFEST)
        return

    table = Table(title="OpenClaw Manifest")
    table.add_column("Tool")
    table.add_column("Command")
    table.add_column("Purpose")
    for tool in OPENCLAW_MANIFEST["tools"]:
        table.add_row(tool["name"], tool["command"], tool["purpose"])
    console.print(table)


@app.command()
def init(
    vault_path: Path = typer.Option(..., "--vault-path", help="Path to the Obsidian vault."),
    config_output: Path = typer.Option(DEFAULT_INIT_CONFIG_PATH, "--config-output", help="Where to write the YAML config."),
    force: bool = typer.Option(False, "--force", help="Overwrite existing config."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing files."),
) -> None:
    """Write a local config file and create the expected vault folders."""
    config = VaultConfig(vault_path=vault_path)
    output_path = config_output.expanduser()
    existed_before = output_path.exists()
    if output_path.exists() and not force:
        _handle_error(ConfigError(f"Config already exists: {output_path}"))

    vault = Vault(config=config, dry_run=dry_run)
    operations: list[OperationRecord] = []
    if not dry_run:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(config.to_yaml(), encoding="utf-8")
    operations.append(
        OperationRecord(
            action="write",
            path=output_path,
            detail="updated config file" if existed_before else "created config file",
            status=OperationStatus.UPDATED if existed_before else OperationStatus.CREATED,
        )
    )
    operations.extend(vault.ensure_structure())
    _print_operations(operations)


@app.command("init-db")
def init_db_command(
    config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing files."),
) -> None:
    """Initialize the local sqlite database for structured life-ops data."""
    try:
        config = load_config(config_path)
        operations = initialize_database(config.database_path, dry_run=dry_run)
    except BrainOpsError as error:
        _handle_error(error)
        return

    _print_operations(operations)


@app.command("log-meal")
def log_meal_command(
    meal_text: str,
    meal_type: str | None = typer.Option(None, "--meal-type", help="Optional meal type like breakfast, lunch, dinner, snack."),
    config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing to SQLite."),
) -> None:
    """Log a structured meal into SQLite using a simple semicolon-separated format."""
    try:
        config = load_config(config_path)
        result = log_meal(config.database_path, meal_text, meal_type=meal_type, dry_run=dry_run)
    except BrainOpsError as error:
        _handle_error(error)
        return

    _print_operations(result.operations)
    console.print(render_meal_log(result))


@app.command("daily-macros")
def daily_macros_command(
    date: str | None = typer.Option(None, "--date", help="Date in YYYY-MM-DD format. Defaults to today."),
    config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
    as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
) -> None:
    """Show macro totals for a given date from SQLite."""
    try:
        config = load_config(config_path)
        summary = daily_macros(config.database_path, date_text=date)
    except BrainOpsError as error:
        _handle_error(error)
        return

    if as_json:
        console.print_json(summary.model_dump_json(indent=2))
        return
    console.print(render_daily_macros(summary))


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
        config = load_config(config_path)
        result = log_supplement(
            config.database_path,
            supplement_name,
            amount=amount,
            unit=unit,
            note=note,
            dry_run=dry_run,
        )
    except BrainOpsError as error:
        _handle_error(error)
        return

    _print_operations(result.operations)
    console.print(render_supplement_log(result))


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
        config = load_config(config_path)
        result = habit_checkin(
            config.database_path,
            habit_name,
            status=status,
            note=note,
            dry_run=dry_run,
        )
    except BrainOpsError as error:
        _handle_error(error)
        return

    _print_operations(result.operations)
    console.print(render_habit_checkin(result))


@app.command("daily-habits")
def daily_habits_command(
    date: str | None = typer.Option(None, "--date", help="Date in YYYY-MM-DD format. Defaults to today."),
    config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
    as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
) -> None:
    """Show habit check-ins for a given date from SQLite."""
    try:
        config = load_config(config_path)
        summary = daily_habits(config.database_path, date_text=date)
    except BrainOpsError as error:
        _handle_error(error)
        return

    if as_json:
        console.print_json(summary.model_dump_json(indent=2))
        return
    console.print(render_daily_habits(summary))


@app.command("log-body-metrics")
def log_body_metrics_command(
    weight_kg: float | None = typer.Option(None, "--weight-kg", help="Body weight in kilograms."),
    body_fat_pct: float | None = typer.Option(None, "--body-fat-pct", help="Body fat percentage."),
    waist_cm: float | None = typer.Option(None, "--waist-cm", help="Waist circumference in centimeters."),
    note: str | None = typer.Option(None, "--note", help="Optional freeform note."),
    config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing to SQLite."),
) -> None:
    """Log body metrics into SQLite."""
    try:
        config = load_config(config_path)
        result = log_body_metrics(
            config.database_path,
            weight_kg=weight_kg,
            body_fat_pct=body_fat_pct,
            waist_cm=waist_cm,
            note=note,
            dry_run=dry_run,
        )
    except BrainOpsError as error:
        _handle_error(error)
        return

    _print_operations(result.operations)
    console.print(render_body_metrics_log(result))


@app.command("body-metrics-status")
def body_metrics_status_command(
    date: str | None = typer.Option(None, "--date", help="Date in YYYY-MM-DD format. Defaults to today."),
    config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
    as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
) -> None:
    """Show the latest body metrics snapshot for a given date."""
    try:
        config = load_config(config_path)
        summary = body_metrics_status(config.database_path, date_text=date)
    except BrainOpsError as error:
        _handle_error(error)
        return

    if as_json:
        console.print_json(summary.model_dump_json(indent=2))
        return
    console.print(render_body_metrics_status(summary))


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
        config = load_config(config_path)
        result = log_workout(
            config.database_path,
            workout_text,
            routine_name=routine_name,
            duration_minutes=duration_minutes,
            note=note,
            dry_run=dry_run,
        )
    except BrainOpsError as error:
        _handle_error(error)
        return

    _print_operations(result.operations)
    console.print(render_workout_log(result))


@app.command("workout-status")
def workout_status_command(
    date: str | None = typer.Option(None, "--date", help="Date in YYYY-MM-DD format. Defaults to today."),
    config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
    as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
) -> None:
    """Show workout summary for a given date from SQLite."""
    try:
        config = load_config(config_path)
        summary = workout_status(config.database_path, date_text=date)
    except BrainOpsError as error:
        _handle_error(error)
        return

    if as_json:
        console.print_json(summary.model_dump_json(indent=2))
        return
    console.print(render_workout_status(summary))


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
        config = load_config(config_path)
        result = log_expense(
            config.database_path,
            amount,
            category=category,
            merchant=merchant,
            currency=currency,
            note=note,
            dry_run=dry_run,
        )
    except BrainOpsError as error:
        _handle_error(error)
        return

    _print_operations(result.operations)
    console.print(render_expense_log(result))


@app.command("spending-summary")
def spending_summary_command(
    date: str | None = typer.Option(None, "--date", help="Date in YYYY-MM-DD format. Defaults to today."),
    currency: str = typer.Option("MXN", "--currency", help="Currency code, defaults to MXN."),
    config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
    as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
) -> None:
    """Show spending totals for a given date from SQLite."""
    try:
        config = load_config(config_path)
        summary = spending_summary(config.database_path, date_text=date, currency=currency)
    except BrainOpsError as error:
        _handle_error(error)
        return

    if as_json:
        console.print_json(summary.model_dump_json(indent=2))
        return
    console.print(render_spending_summary(summary))


@app.command("daily-log")
def daily_log_command(
    text: str,
    domain: str = typer.Option("general", "--domain", help="Logical domain label for the event."),
    config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing to SQLite."),
) -> None:
    """Log a generic daily event into SQLite."""
    try:
        config = load_config(config_path)
        result = log_daily_event(config.database_path, text, domain=domain, dry_run=dry_run)
    except BrainOpsError as error:
        _handle_error(error)
        return

    _print_operations(result.operations)
    console.print(render_daily_log(result))


@app.command("daily-summary")
def daily_summary_command(
    date: str | None = typer.Option(None, "--date", help="Date in YYYY-MM-DD format. Defaults to today."),
    config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing to the vault."),
    as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
) -> None:
    """Write the structured daily summary block from SQLite into the daily note in Obsidian."""
    try:
        vault = _load_vault(config_path, dry_run=dry_run)
        result = write_daily_summary(vault, date_text=date)
    except BrainOpsError as error:
        _handle_error(error)
        return

    if as_json:
        console.print_json(result.model_dump_json(indent=2))
        return
    _print_operations(result.operations)
    console.print(render_daily_summary(result))


@app.command("route-input")
def route_input_command(
    text: str,
    as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
    use_llm: bool = typer.Option(False, "--use-llm", help="Use Ollama-assisted routing instead of only heuristics."),
) -> None:
    """Classify a natural-language input into the most likely command/domain."""
    try:
        if use_llm:
            heuristic_result = route_input(text)
            config = load_config(config_path)
            try:
                llm_result = llm_route_input(config.ai, text)
                result = _pick_route_result(text, heuristic_result, llm_result)
            except AIProviderError as error:
                result = heuristic_result
                result.reason = f"{result.reason} Heuristic fallback after Ollama error: {error}"
        else:
            result = route_input(text)
    except BrainOpsError as error:
        _handle_error(error)
        return
    if as_json:
        console.print_json(result.model_dump_json(indent=2))
        return
    console.print(render_route_decision(result))


def _pick_route_result(text: str, heuristic_result, llm_result):
    if heuristic_result.command == llm_result.command:
        llm_result.reason = f"{llm_result.reason} Confirmed by heuristic routing."
        llm_result.routing_source = "hybrid"
        return llm_result

    sparse_structured_override = (
        heuristic_result.command == "daily-log"
        and llm_result.command.startswith("log-")
        and set(llm_result.extracted_fields.keys()) <= {"date"}
    )
    if sparse_structured_override:
        heuristic_result.reason = (
            f"{heuristic_result.reason} Kept heuristic result because the LLM override lacked enough structured fields."
        )
        heuristic_result.routing_source = "hybrid"
        return heuristic_result

    if llm_result.confidence >= heuristic_result.confidence + 0.15:
        llm_result.reason = f"{llm_result.reason} Selected over heuristic routing."
        llm_result.routing_source = "hybrid"
        return llm_result

    heuristic_result.reason = f"{heuristic_result.reason} Kept heuristic result after comparing with LLM routing."
    heuristic_result.routing_source = "hybrid"
    return heuristic_result


@app.command("handle-input")
def handle_input_command(
    text: str,
    config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without side effects."),
    as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    use_llm: bool | None = typer.Option(None, "--use-llm/--no-use-llm", help="Override config and allow Ollama-assisted routing."),
) -> None:
    """Route a natural-language input and execute the safest matching action when possible."""
    try:
        config = load_config(config_path)
        result = handle_input(config, text, dry_run=dry_run, use_llm=use_llm)
    except BrainOpsError as error:
        _handle_error(error)
        return

    if as_json:
        console.print_json(result.model_dump_json(indent=2))
        return
    if result.operations:
        _print_operations(result.operations)
    console.print(render_handle_input(result))


@app.command("create-note")
def create_note_command(
    title: str,
    note_type: str = typer.Option("permanent_note", "--type", help="Frontmatter note type."),
    folder: str | None = typer.Option(None, "--folder", help="Custom destination folder inside the vault."),
    template_name: str | None = typer.Option(None, "--template", help="Template file name."),
    tags: list[str] = typer.Option(None, "--tag", help="Repeatable tag option."),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite if the note already exists."),
    config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing files."),
) -> None:
    """Create a single note from a template."""
    try:
        vault = _load_vault(config_path, dry_run=dry_run)
        operation = create_note(
            vault,
            CreateNoteRequest(
                title=title,
                note_type=note_type,
                folder=folder,
                template_name=template_name,
                tags=tags or [],
                overwrite=overwrite,
            ),
        )
    except BrainOpsError as error:
        _handle_error(error)
        return

    _print_operations([operation])


@app.command("create-project")
def create_project_command(
    name: str,
    config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing files."),
) -> None:
    """Create a project workspace and its core notes."""
    try:
        vault = _load_vault(config_path, dry_run=dry_run)
        operations = create_project_scaffold(vault, name)
    except BrainOpsError as error:
        _handle_error(error)
        return

    _print_operations(operations)


@app.command("process-inbox")
def process_inbox_command(
    config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing files."),
    write_report: bool = typer.Option(False, "--write-report", help="Persist a markdown report in the reports folder."),
    improve_structure: bool = typer.Option(True, "--improve-structure/--no-improve-structure", help="Wrap loose inbox content into a typed structure before moving."),
) -> None:
    """Normalize inbox notes and move only clearly classified notes."""
    try:
        vault = _load_vault(config_path, dry_run=dry_run)
        summary = process_inbox(vault, improve_structure=improve_structure)
        if write_report:
            report_path = vault.report_path("inbox-processing-report")
            summary.operations.append(vault.write_text(report_path, render_inbox_report(summary), overwrite=True))
    except BrainOpsError as error:
        _handle_error(error)
        return

    _print_operations(summary.operations)
    console.print(render_inbox_report(summary))


@app.command("weekly-review")
def weekly_review_command(
    stale_days: int = typer.Option(21, "--stale-days", help="Project notes older than this are marked stale."),
    write_report: bool = typer.Option(False, "--write-report", help="Persist a markdown report in the reports folder."),
    config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing files."),
) -> None:
    """Generate a weekly review report for the vault."""
    try:
        vault = _load_vault(config_path, dry_run=dry_run)
        summary = generate_weekly_review(vault, stale_days=stale_days, write_report=write_report)
    except BrainOpsError as error:
        _handle_error(error)
        return

    _print_operations(summary.operations)
    console.print(render_weekly_review(summary))


@app.command("audit-vault")
def audit_vault_command(
    write_report: bool = typer.Option(False, "--write-report", help="Persist a markdown report in the reports folder."),
    config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
) -> None:
    """Audit the vault structure and note quality without modifying content."""
    try:
        vault = _load_vault(config_path, dry_run=False)
        summary = audit_vault(vault, write_report=write_report)
    except BrainOpsError as error:
        _handle_error(error)
        return

    _print_operations(summary.operations)
    console.print(render_vault_audit(summary))


@app.command("normalize-frontmatter")
def normalize_frontmatter_command(
    config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing files."),
) -> None:
    """Normalize frontmatter across the vault using folder-aware defaults and type aliases."""
    try:
        vault = _load_vault(config_path, dry_run=dry_run)
        summary = normalize_frontmatter(vault)
    except BrainOpsError as error:
        _handle_error(error)
        return

    _print_operations(summary.operations)
    console.print(render_normalize_frontmatter(summary))


@app.command("capture")
def capture_command(
    text: str,
    title: str | None = typer.Option(None, "--title", help="Optional explicit note title."),
    note_type: str | None = typer.Option(None, "--type", help="Optional explicit type override."),
    tags: list[str] = typer.Option(None, "--tag", help="Repeatable tag option."),
    config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing files."),
) -> None:
    """Capture natural language into a structured note."""
    try:
        vault = _load_vault(config_path, dry_run=dry_run)
        result = capture_text(vault, text=text, title=title, force_type=note_type, tags=tags or [])
    except (BrainOpsError, ValueError) as error:
        _handle_error(error if isinstance(error, BrainOpsError) else ConfigError(str(error)))
        return

    _print_operations([result.operation])
    console.print(f"Captured as `{result.note_type}`: {result.title}")
    console.print(f"Reason: {result.reason}")


@app.command("improve-note")
def improve_note_command(
    note_path: Path,
    config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing files."),
) -> None:
    """Improve the structure of an existing note without inventing new facts."""
    try:
        vault = _load_vault(config_path, dry_run=dry_run)
        result = improve_note(vault, note_path=note_path)
    except BrainOpsError as error:
        _handle_error(error)
        return

    _print_operations([result.operation])
    console.print(f"Improved `{result.note_type}` note: {result.path}")
    console.print(f"Reason: {result.reason}")


@app.command("research-note")
def research_note_command(
    note_path: Path,
    query: str | None = typer.Option(None, "--query", help="Optional explicit research query."),
    max_sources: int = typer.Option(3, "--max-sources", help="Maximum external sources to attach."),
    config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing files."),
) -> None:
    """Enrich a note with grounded external research and source attribution."""
    try:
        vault = _load_vault(config_path, dry_run=dry_run)
        result = research_note(vault, note_path=note_path, query=query, max_sources=max_sources)
    except BrainOpsError as error:
        _handle_error(error)
        return

    _print_operations([result.operation])
    console.print(f"Researched note: {result.path}")
    console.print(f"Query: {result.query}")
    console.print(f"Sources attached: {len(result.sources)}")
    console.print(f"Reason: {result.reason}")


@app.command("link-suggestions")
def link_suggestions_command(
    note_path: Path,
    limit: int = typer.Option(8, "--limit", help="Maximum number of suggestions to return."),
    config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
) -> None:
    """Suggest likely internal links for a note using vault-local heuristics."""
    try:
        vault = _load_vault(config_path, dry_run=False)
        result = suggest_links(vault, note_path=note_path, limit=limit)
    except BrainOpsError as error:
        _handle_error(error)
        return

    _print_operations([result.operation])
    console.print(render_link_suggestions(result))


@app.command("apply-link-suggestions")
def apply_link_suggestions_command(
    note_path: Path,
    limit: int = typer.Option(3, "--limit", help="Maximum number of suggestions to apply."),
    config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing files."),
) -> None:
    """Apply likely internal links into a note using the current suggestion heuristics."""
    try:
        vault = _load_vault(config_path, dry_run=dry_run)
        result = apply_link_suggestions(vault, note_path=note_path, limit=limit)
    except BrainOpsError as error:
        _handle_error(error)
        return

    _print_operations([result.operation])
    console.print(render_applied_links(result))


@app.command("promote-note")
def promote_note_command(
    note_path: Path,
    target_type: str | None = typer.Option(None, "--target-type", help="Optional explicit promotion target."),
    config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing files."),
) -> None:
    """Promote an existing note into a more durable artifact."""
    try:
        vault = _load_vault(config_path, dry_run=dry_run)
        result = promote_note(vault, note_path=note_path, target_type=target_type)
    except (BrainOpsError, ValueError) as error:
        _handle_error(error if isinstance(error, BrainOpsError) else ConfigError(str(error)))
        return

    _print_operations(result.operations)
    console.print(render_promoted_note(result))


@app.command("enrich-note")
def enrich_note_command(
    note_path: Path,
    query: str | None = typer.Option(None, "--query", help="Optional explicit research query."),
    max_sources: int = typer.Option(3, "--max-sources", help="Maximum external sources to attach."),
    link_limit: int = typer.Option(3, "--link-limit", help="Maximum number of links to apply."),
    improve: bool = typer.Option(True, "--improve/--no-improve", help="Improve note structure before other steps."),
    research: bool = typer.Option(True, "--research/--no-research", help="Attach grounded research."),
    apply_links: bool = typer.Option(True, "--apply-links/--no-apply-links", help="Insert likely internal links."),
    config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing files."),
) -> None:
    """Run the current note enrichment pipeline on a single note."""
    try:
        vault = _load_vault(config_path, dry_run=dry_run)
        result = enrich_note(
            vault,
            note_path=note_path,
            query=query,
            max_sources=max_sources,
            link_limit=link_limit,
            improve=improve,
            research=research,
            apply_links=apply_links,
        )
    except BrainOpsError as error:
        _handle_error(error)
        return

    _print_operations(result.operations)
    console.print(render_enriched_note(result))


if __name__ == "__main__":
    app()
