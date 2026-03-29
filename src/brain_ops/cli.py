from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from brain_ops import __version__
from brain_ops.config import VaultConfig, load_config
from brain_ops.constants import DEFAULT_INIT_CONFIG_PATH
from brain_ops.errors import BrainOpsError, ConfigError
from brain_ops.models import CreateNoteRequest, OperationRecord, OperationStatus
from brain_ops.reporting import (
    render_inbox_report,
    render_link_suggestions,
    render_normalize_frontmatter,
    render_vault_audit,
    render_weekly_review,
)
from brain_ops.services.audit_service import audit_vault
from brain_ops.services.capture_service import capture_text
from brain_ops.services.improve_service import improve_note
from brain_ops.services.inbox_service import process_inbox
from brain_ops.services.link_service import suggest_links
from brain_ops.services.note_service import create_note
from brain_ops.services.normalize_service import normalize_frontmatter
from brain_ops.services.project_service import create_project_scaffold
from brain_ops.services.research_service import research_note
from brain_ops.services.review_service import generate_weekly_review
from brain_ops.vault import Vault

app = typer.Typer(help="brain-ops CLI")
console = Console()


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
    table.add_row("Inbox folder", config.folders.inbox)
    table.add_row("Projects folder", config.folders.projects)
    table.add_row("Reports folder", config.folders.reports)
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


if __name__ == "__main__":
    app()
