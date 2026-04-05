"""Typer command registration for note and knowledge workflows."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from brain_ops.errors import BrainOpsError

from .knowledge import (
    present_audit_vault_command,
    present_compile_knowledge_command,
    present_entity_index_command,
    present_entity_relations_command,
    present_normalize_frontmatter_command,
    present_ingest_source_command,
    present_process_inbox_command,
    present_search_knowledge_command,
    present_weekly_review_command,
)
from .notes import (
    coerce_note_workflow_error,
    present_apply_link_suggestions_command,
    present_capture_command,
    present_create_entity_command,
    present_create_note_command,
    present_create_project_command,
    present_enrich_note_command,
    present_improve_note_command,
    present_link_suggestions_command,
    present_promote_note_command,
    present_research_note_command,
)


def register_note_and_knowledge_commands(app: typer.Typer, console: Console, handle_error) -> None:
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
            present_create_note_command(
                console,
                config_path=config_path,
                title=title,
                note_type=note_type,
                folder=folder,
                template_name=template_name,
                tags=tags or [],
                overwrite=overwrite,
                dry_run=dry_run,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("create-project")
    def create_project_command(
        name: str,
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing files."),
    ) -> None:
        """Create a project workspace and its core notes."""
        try:
            present_create_project_command(
                console,
                config_path=config_path,
                name=name,
                dry_run=dry_run,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("create-entity")
    def create_entity_command(
        name: str,
        entity_type: str = typer.Option(..., "--type", help="Entity type: person, event, place, concept, book, author, war, era, organization, topic."),
        tags: list[str] = typer.Option(None, "--tag", help="Repeatable tag option."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing files."),
    ) -> None:
        """Create a structured knowledge entity note with typed frontmatter."""
        try:
            present_create_entity_command(
                console,
                config_path=config_path,
                name=name,
                entity_type=entity_type,
                tags=tags or [],
                dry_run=dry_run,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("entity-index")
    def entity_index_command(
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Generate an index of all knowledge entities in the vault."""
        try:
            present_entity_index_command(
                console,
                config_path=config_path,
                as_json=as_json,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("entity-relations")
    def entity_relations_command(
        name: str,
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Show entities connected to a given entity via relationships."""
        try:
            present_entity_relations_command(
                console,
                entity_name=name,
                config_path=config_path,
                as_json=as_json,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("ingest-source")
    def ingest_source_command(
        text: str,
        title: str | None = typer.Option(None, "--title", help="Override the inferred title."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        use_llm: bool = typer.Option(False, "--use-llm", help="Use Ollama to extract entities and summary."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Ingest raw text into a structured source note, optionally using LLM for extraction."""
        try:
            present_ingest_source_command(
                console,
                text=text,
                title=title,
                config_path=config_path,
                use_llm=use_llm,
                as_json=as_json,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("search-knowledge")
    def search_knowledge_command(
        query: str,
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        entity_only: bool = typer.Option(False, "--entity-only", help="Search only entity notes."),
        max_results: int = typer.Option(20, "--max", min=1, help="Maximum results to return."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Search knowledge entities and notes by content."""
        try:
            present_search_knowledge_command(
                console,
                query=query,
                config_path=config_path,
                entity_only=entity_only,
                max_results=max_results,
                as_json=as_json,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("compile-knowledge")
    def compile_knowledge_command(
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        db_path: Path | None = typer.Option(None, "--db", help="Output SQLite database path. Defaults to {vault}/.brain-ops/knowledge.db."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Compile all knowledge entities from Obsidian frontmatter into a queryable SQLite database."""
        try:
            present_compile_knowledge_command(
                console,
                config_path=config_path,
                db_path=db_path,
                as_json=as_json,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("process-inbox")
    def process_inbox_command(
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing files."),
        write_report: bool = typer.Option(False, "--write-report", help="Persist a markdown report in the reports folder."),
        improve_structure: bool = typer.Option(True, "--improve-structure/--no-improve-structure", help="Wrap loose inbox content into a typed structure before moving."),
    ) -> None:
        """Normalize inbox notes and move only clearly classified notes."""
        try:
            present_process_inbox_command(
                console,
                config_path=config_path,
                dry_run=dry_run,
                write_report=write_report,
                improve_structure=improve_structure,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("weekly-review")
    def weekly_review_command(
        stale_days: int = typer.Option(21, "--stale-days", help="Project notes older than this are marked stale."),
        write_report: bool = typer.Option(False, "--write-report", help="Persist a markdown report in the reports folder."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing files."),
    ) -> None:
        """Generate a weekly review report for the vault."""
        try:
            present_weekly_review_command(
                console,
                config_path=config_path,
                dry_run=dry_run,
                stale_days=stale_days,
                write_report=write_report,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("audit-vault")
    def audit_vault_command(
        write_report: bool = typer.Option(False, "--write-report", help="Persist a markdown report in the reports folder."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
    ) -> None:
        """Audit the vault structure and note quality without modifying content."""
        try:
            present_audit_vault_command(
                console,
                config_path=config_path,
                write_report=write_report,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("normalize-frontmatter")
    def normalize_frontmatter_command(
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing files."),
    ) -> None:
        """Normalize frontmatter across the vault using folder-aware defaults and type aliases."""
        try:
            present_normalize_frontmatter_command(
                console,
                config_path=config_path,
                dry_run=dry_run,
            )
        except BrainOpsError as error:
            handle_error(error)

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
            present_capture_command(
                console,
                config_path=config_path,
                text=text,
                title=title,
                note_type=note_type,
                tags=tags or [],
                dry_run=dry_run,
            )
        except (BrainOpsError, ValueError) as error:
            handle_error(coerce_note_workflow_error(error))

    @app.command("improve-note")
    def improve_note_command(
        note_path: Path,
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing files."),
    ) -> None:
        """Improve the structure of an existing note without inventing new facts."""
        try:
            present_improve_note_command(
                console,
                config_path=config_path,
                note_path=note_path,
                dry_run=dry_run,
            )
        except BrainOpsError as error:
            handle_error(error)

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
            present_research_note_command(
                console,
                config_path=config_path,
                note_path=note_path,
                query=query,
                max_sources=max_sources,
                dry_run=dry_run,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("link-suggestions")
    def link_suggestions_command(
        note_path: Path,
        limit: int = typer.Option(8, "--limit", help="Maximum number of suggestions to return."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
    ) -> None:
        """Suggest likely internal links for a note using vault-local heuristics."""
        try:
            present_link_suggestions_command(
                console,
                config_path=config_path,
                note_path=note_path,
                limit=limit,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("apply-link-suggestions")
    def apply_link_suggestions_command(
        note_path: Path,
        limit: int = typer.Option(3, "--limit", help="Maximum number of suggestions to apply."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing files."),
    ) -> None:
        """Apply likely internal links into a note using the current suggestion heuristics."""
        try:
            present_apply_link_suggestions_command(
                console,
                config_path=config_path,
                note_path=note_path,
                limit=limit,
                dry_run=dry_run,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("promote-note")
    def promote_note_command(
        note_path: Path,
        target_type: str | None = typer.Option(None, "--target-type", help="Optional explicit promotion target."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing files."),
    ) -> None:
        """Promote an existing note into a more durable artifact."""
        try:
            present_promote_note_command(
                console,
                config_path=config_path,
                note_path=note_path,
                target_type=target_type,
                dry_run=dry_run,
            )
        except (BrainOpsError, ValueError) as error:
            handle_error(coerce_note_workflow_error(error))

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
            present_enrich_note_command(
                console,
                config_path=config_path,
                note_path=note_path,
                query=query,
                max_sources=max_sources,
                link_limit=link_limit,
                improve=improve,
                research=research,
                apply_links=apply_links,
                dry_run=dry_run,
            )
        except BrainOpsError as error:
            handle_error(error)


__all__ = ["register_note_and_knowledge_commands"]
