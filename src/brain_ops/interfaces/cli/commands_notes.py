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
    present_enrich_entity_command,
    present_ingest_source_command,
    present_normalize_frontmatter_command,
    present_process_inbox_command,
    present_query_knowledge_command,
    present_registry_lint_command,
    present_replay_extractions_command,
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
        text: str | None = typer.Argument(None, help="Raw text to ingest. Omit if using --url."),
        url: str | None = typer.Option(None, "--url", help="URL to download and ingest."),
        title: str | None = typer.Option(None, "--title", help="Override the inferred title."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        use_llm: bool = typer.Option(False, "--use-llm", help="Use LLM to extract entities and summary."),
        llm_provider: str | None = typer.Option(None, "--llm-provider", help="LLM provider: ollama, deepseek, gemini, openai."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Ingest raw text or a URL into a structured source note with LLM extraction."""
        try:
            present_ingest_source_command(
                console,
                text=text,
                url=url,
                title=title,
                config_path=config_path,
                use_llm=use_llm,
                llm_provider=llm_provider,
                as_json=as_json,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("enrich-entity")
    def enrich_entity_command(
        name: str,
        new_info: str | None = typer.Option(None, "--info", help="New information to integrate into the entity."),
        url: str | None = typer.Option(None, "--url", help="URL to download and use as enrichment source."),
        auto_generate: bool = typer.Option(False, "--auto-generate", help="Generate initial content if entity is empty."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        llm_provider: str | None = typer.Option(None, "--llm-provider", help="LLM provider: ollama, deepseek, gemini, openai."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Enrich an existing entity with new info, a URL, or auto-generate content using LLM."""
        try:
            present_enrich_entity_command(
                console,
                entity_name=name,
                new_info=new_info,
                url=url,
                auto_generate=auto_generate,
                config_path=config_path,
                llm_provider=llm_provider,
                as_json=as_json,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("query-knowledge")
    def query_knowledge_command(
        query: str,
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        file_back: bool = typer.Option(False, "--file-back", help="Save the answer as a new note in the wiki."),
        llm_provider: str | None = typer.Option(None, "--llm-provider", help="LLM provider: ollama, deepseek, gemini, openai."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Ask a question and get an answer synthesized from your knowledge base."""
        try:
            present_query_knowledge_command(
                console,
                query=query,
                config_path=config_path,
                file_back=file_back,
                llm_provider=llm_provider,
                as_json=as_json,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("reconcile")
    def reconcile_command(
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Reconcile direct edits — sync registry, compile, and detect issues after manual changes."""
        try:
            from brain_ops.application.knowledge import execute_compile_knowledge_workflow
            from brain_ops.domains.knowledge.registry import RegisteredEntity, load_entity_registry, save_entity_registry
            from brain_ops.domains.knowledge.object_model import resolve_object_kind
            from brain_ops.frontmatter import split_frontmatter
            from brain_ops.interfaces.cli.runtime import load_validated_vault
            from brain_ops.storage.obsidian import list_vault_markdown_notes, read_note_text

            vault = load_validated_vault(config_path, dry_run=False)
            registry_path = Path(vault.config.vault_path) / ".brain-ops" / "entity_registry.json"
            registry = load_entity_registry(registry_path)

            # Scan vault and sync registry
            synced = 0
            created = 0
            for note_path in list_vault_markdown_notes(vault, excluded_parts={".git", ".obsidian"}):
                _safe, rel, text = read_note_text(vault, note_path)
                try:
                    fm, body = split_frontmatter(text)
                except Exception:
                    continue
                if fm.get("entity") is not True:
                    continue
                name = fm.get("name")
                if not isinstance(name, str) or not name.strip():
                    continue
                name = name.strip()

                existing = registry.get(name)
                entity_type = str(fm.get("type", "concept"))
                object_kind = fm.get("object_kind")
                subtype = fm.get("subtype")

                if existing is None:
                    ok, st = resolve_object_kind(entity_type)
                    entity = RegisteredEntity(
                        canonical_name=name,
                        entity_type=entity_type,
                        status="canonical",
                        object_kind=str(object_kind) if object_kind else ok,
                        subtype=str(subtype) if subtype else st,
                        source_count=1,
                    )
                    # Count relations from frontmatter
                    related = fm.get("related")
                    if isinstance(related, list):
                        entity.relation_count = len(related)
                        entity.frequent_relations = [str(r) for r in related if isinstance(r, str)][:20]
                    registry.register(entity)
                    created += 1
                else:
                    # Sync status and relations
                    if existing.status == "mention":
                        existing.status = "canonical"
                    if not existing.object_kind and object_kind:
                        existing.object_kind = str(object_kind)
                    if not existing.subtype and subtype:
                        existing.subtype = str(subtype)
                    related = fm.get("related")
                    if isinstance(related, list):
                        existing.relation_count = len(related)
                        existing.frequent_relations = [str(r) for r in related if isinstance(r, str)][:20]
                    synced += 1

            save_entity_registry(registry_path, registry)

            # Compile knowledge
            execute_compile_knowledge_workflow(
                config_path=config_path, db_path=None, load_vault=load_validated_vault,
            )

            result = {
                "registry_synced": synced,
                "registry_created": created,
                "total_registry": len(registry.entities),
            }

            if as_json:
                console.print_json(data=result)
                return
            console.print(f"Reconciled: {synced} synced, {created} new in registry. Total: {len(registry.entities)} entities.")
            console.print("Knowledge compiled to SQLite.")
        except BrainOpsError as error:
            handle_error(error)

    @app.command("suggest-entities")
    def suggest_entities_command(
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        max_results: int = typer.Option(15, "--max", min=1, help="Max suggestions."),
        action_filter: str | None = typer.Option(None, "--action", help="Filter by action: create, enrich, split."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Suggest next entities to create, enrich, or split — combining all signals."""
        try:
            import json as json_mod
            from brain_ops.application.knowledge import execute_audit_knowledge_workflow
            from brain_ops.domains.knowledge.registry import load_entity_registry
            from brain_ops.domains.knowledge.suggestions import suggest_next_entities
            from brain_ops.interfaces.cli.runtime import load_validated_vault

            vault = load_validated_vault(config_path, dry_run=False)
            registry_path = Path(vault.config.vault_path) / ".brain-ops" / "entity_registry.json"
            registry = load_entity_registry(registry_path)
            registry_data = {name: entity.to_dict() for name, entity in registry.entities.items()}

            # Load existing entity names
            from brain_ops.frontmatter import split_frontmatter
            from brain_ops.storage.obsidian import list_vault_markdown_notes, read_note_text
            existing_names: set[str] = set()
            for note_path in list_vault_markdown_notes(vault, excluded_parts={".git", ".obsidian"}):
                _safe, rel, text = read_note_text(vault, note_path)
                try:
                    fm, _body = split_frontmatter(text)
                    if fm.get("entity") is True and isinstance(fm.get("name"), str):
                        existing_names.add(fm["name"].strip())
                except Exception:
                    pass

            # Load gap registry
            gap_data = None
            gap_path = Path(vault.config.vault_path) / ".brain-ops" / "gap_registry.json"
            if gap_path.exists():
                gap_data = json_mod.loads(gap_path.read_text(encoding="utf-8"))

            # Run audit for quality signals
            audit_data = execute_audit_knowledge_workflow(config_path=config_path, load_vault=load_validated_vault)

            suggestions = suggest_next_entities(
                registry_data, existing_names,
                gap_registry=gap_data,
                audit_data=audit_data,
                max_suggestions=max_results,
            )

            if action_filter:
                suggestions = [s for s in suggestions if s.action == action_filter]

            if as_json:
                console.print_json(data=[s.to_dict() for s in suggestions])
                return
            if not suggestions:
                console.print("No suggestions. Your knowledge base is well-covered!")
                return

            # Group by action
            from rich.table import Table
            for action_type in ["create", "enrich", "split"]:
                group = [s for s in suggestions if s.action == action_type]
                if not group:
                    continue
                table = Table(title=f"{action_type.upper()}")
                table.add_column("#")
                table.add_column("Name")
                table.add_column("Score")
                table.add_column("Reasons")
                for i, s in enumerate(group, 1):
                    table.add_row(str(i), s.canonical_name, f"{s.score:.1f}", "; ".join(s.reasons[:3]))
                console.print(table)
                console.print()

        except BrainOpsError as error:
            handle_error(error)

    @app.command("audit-knowledge")
    def audit_knowledge_command(
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Run comprehensive health check on the knowledge base."""
        try:
            from brain_ops.application.knowledge import execute_audit_knowledge_workflow
            from brain_ops.interfaces.cli.runtime import load_validated_vault

            result = execute_audit_knowledge_workflow(
                config_path=config_path,
                load_vault=load_validated_vault,
            )
            if as_json:
                console.print_json(data=result)
                return

            console.print(f"\n[bold]Knowledge Audit[/bold]")
            console.print(f"Entities: {result['total_entities']} | Sources: {result['total_sources']} | Relations: {result['total_relations']}")
            console.print()

            issues = 0
            for key in ["empty_identity", "empty_key_facts", "empty_timeline", "empty_relationships",
                        "no_source_coverage", "missing_object_kind", "missing_subtype",
                        "old_model_sections", "missing_related_frontmatter", "orphan_entities"]:
                items = result.get(key, [])
                if items:
                    label = key.replace("_", " ").title()
                    console.print(f"[yellow]⚠ {label}:[/yellow] {', '.join(items)}")
                    issues += len(items)

            if result.get("unmaterialized_candidates"):
                console.print(f"\n[cyan]💡 Candidates to materialize:[/cyan] {', '.join(result['unmaterialized_candidates'])}")
            if result.get("entities_needing_enrichment"):
                console.print(f"[cyan]💡 Need enrichment:[/cyan] {', '.join(result['entities_needing_enrichment'])}")

            console.print(f"\nTotal issues: {issues} | Suggestions: {len(result.get('unmaterialized_candidates', [])) + len(result.get('entities_needing_enrichment', []))}")

        except BrainOpsError as error:
            handle_error(error)

    @app.command("generate-moc")
    def generate_moc_command(
        topic: str,
        seed: list[str] = typer.Option(None, "--seed", help="Seed entity names to build the MOC around."),
        description: str | None = typer.Option(None, "--description", help="MOC description."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
    ) -> None:
        """Auto-generate a Map of Content from the knowledge graph."""
        try:
            from brain_ops.application.knowledge import execute_generate_moc_workflow
            from brain_ops.interfaces.cli.runtime import load_validated_vault

            path = execute_generate_moc_workflow(
                topic=topic,
                config_path=config_path,
                seed_names=seed or None,
                description=description,
                load_vault=load_validated_vault,
            )
            console.print(f"Generated MOC at: {path}")
        except BrainOpsError as error:
            handle_error(error)

    @app.command("registry-lint")
    def registry_lint_command(
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Run health checks on the entity registry."""
        try:
            present_registry_lint_command(console, config_path=config_path, as_json=as_json)
        except BrainOpsError as error:
            handle_error(error)

    @app.command("list-extractions")
    def list_extractions_command(
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """List all saved LLM extraction records for replay and debugging."""
        try:
            present_replay_extractions_command(console, config_path=config_path, as_json=as_json)
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
