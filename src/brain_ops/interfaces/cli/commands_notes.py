"""Typer command registration for note and knowledge workflows."""

from __future__ import annotations

import enum
from pathlib import Path

import typer
from rich.console import Console

from brain_ops.errors import BrainOpsError


class LLMModeChoice(str, enum.Enum):
    """Campaña 2.2B Paso 5 — CLI enum para --mode.

    - cheap: pattern extractor only (default, preserves 2.2A)
    - strict: pattern + LLM con cita textual literal
    - deep: pattern + LLM permitiendo inferencias contextuales medium
    """
    cheap = "cheap"
    strict = "strict"
    deep = "deep"

from .knowledge import (
    present_apply_relations_batch_command,
    present_audit_vault_command,
    present_batch_propose_relations_command,
    present_compile_knowledge_command,
    present_disambiguate_bare_command,
    present_entity_index_command,
    present_entity_relations_command,
    present_enrich_entity_command,
    present_fill_domain_command,
    present_query_relations_command,
    present_show_entity_relations_command,
    present_fix_capitalization_command,
    present_ingest_source_command,
    present_lint_schemas_command,
    present_migrate_knowledge_db_command,
    present_normalize_domain_command,
    present_normalize_frontmatter_command,
    present_process_inbox_command,
    present_propose_relations_command,
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

    @app.command("full-enrich")
    def full_enrich_command(
        name: str,
        url: str = typer.Option(..., "--url", help="URL to download and fully process."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        llm_provider: str | None = typer.Option(None, "--llm-provider", help="LLM provider for enrichment."),
        max_gap_passes: int = typer.Option(3, "--max-gap-passes", min=1, help="Max additional passes to fill gaps."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Full enrichment pipeline: multi-pass + coverage check + auto-fill gaps. Guarantees quality."""
        try:
            from datetime import datetime, timezone
            from subprocess import run as subprocess_run
            from brain_ops.domains.knowledge.ingest import fetch_url_document
            from brain_ops.domains.knowledge.multi_pass import plan_multi_pass_chunks, render_pass_context
            from brain_ops.domains.knowledge.coverage_check import check_coverage
            from brain_ops.domains.knowledge.chunking import chunk_by_headings
            from brain_ops.domains.knowledge.source_blocks import (
                extract_planning_chunks,
                save_chunk_sidecar,
            )
            from brain_ops.frontmatter import split_frontmatter
            from brain_ops.interfaces.cli.runtime import load_validated_vault
            from brain_ops.storage.obsidian import list_vault_markdown_notes, read_note_text

            vault = load_validated_vault(config_path, dry_run=False)
            vault_path = vault.config.vault_path
            cfg = str(config_path or "config/vault.yaml")

            # Step 1: Fetch and save raw
            console.print(f"[bold]Step 1/4: Downloading source[/bold]")
            fetched = fetch_url_document(url)
            raw_content = fetched.text
            raw_dir = vault_path / ".brain-ops" / "raw"
            raw_dir.mkdir(parents=True, exist_ok=True)
            slug = "".join(c if c.isalnum() or c in "-_ " else "" for c in name)[:60].strip().replace(" ", "-").lower()
            now = datetime.now(timezone.utc)
            raw_file = raw_dir / f"{now.strftime('%Y%m%d-%H%M%S')}-{slug}-full.txt"
            raw_file.write_text(raw_content, encoding="utf-8")
            # Update _index.json
            import json
            index_path = raw_dir / "_index.json"
            index_data: dict[str, str] = {}
            if index_path.exists():
                index_data = json.loads(index_path.read_text(encoding="utf-8"))
            index_data[name] = str(raw_file)
            index_path.write_text(json.dumps(index_data, indent=2, ensure_ascii=False), encoding="utf-8")
            source_profile, planning_chunks = extract_planning_chunks(
                url=url,
                html=fetched.html,
                article_title=fetched.title,
            )
            if planning_chunks:
                save_chunk_sidecar(raw_file, source_profile=source_profile, chunks=planning_chunks)
            console.print(f"  Raw saved: {len(raw_content)} chars")

            # Step 2: Multi-pass enrich
            console.print(f"\n[bold]Step 2/4: Multi-pass enrichment[/bold]")
            passes = plan_multi_pass_chunks(
                planning_chunks or chunk_by_headings(raw_content),
                fallback_text=raw_content,
            )
            console.print(f"  Planned {len(passes)} passes")

            for enrich_pass in passes:
                context = render_pass_context(enrich_pass)
                console.print(f"  Pass {enrich_pass.pass_number}/{len(passes)}: {enrich_pass.focus[:50]} ({enrich_pass.total_chars} chars)")
                cmd = ["brain", "enrich-entity", name, "--info", context, "--config", cfg]
                if llm_provider:
                    cmd.extend(["--llm-provider", llm_provider])
                result = subprocess_run(cmd, capture_output=True, text=True, timeout=120)
                if result.returncode == 0:
                    console.print(f"    ✓ completed")
                else:
                    console.print(f"    ✗ failed: {result.stderr[:100]}")

            # Step 3: Check coverage
            console.print(f"\n[bold]Step 3/4: Coverage check[/bold]")
            entity_body = None
            entity_subtype = "person"
            for note_path in list_vault_markdown_notes(vault, excluded_parts={".git", ".obsidian"}):
                _safe, rel, text = read_note_text(vault, note_path)
                try:
                    fm, body = split_frontmatter(text)
                    if fm.get("entity") is True and fm.get("name") == name:
                        entity_body = body
                        entity_subtype = str(fm.get("subtype", fm.get("type", "person")))
                        break
                except Exception:
                    pass

            if entity_body is None:
                console.print("  Entity note not found after enrichment.")
                return

            effective_chunks = planning_chunks or chunk_by_headings(raw_content)
            report = check_coverage(
                name,
                entity_subtype,
                raw_content,
                entity_body or "",
                raw_chunks=effective_chunks,
            )
            console.print(f"  Coverage: {report.coverage_pct:.0f}% ({report.covered_headings}/{report.raw_headings} sections)")

            high_gaps = [g for g in report.gaps if g.priority == "high"]
            medium_gaps = [g for g in report.gaps if g.priority == "medium" and g.char_count >= 500]
            important_gaps = high_gaps + medium_gaps[:5]

            if not important_gaps:
                console.print("  No important gaps detected.")
            else:
                console.print(f"  Found {len(important_gaps)} important gaps")

                # Step 4: Fill gaps
                console.print(f"\n[bold]Step 4/4: Filling gaps[/bold]")
                gap_passes = 0
                for gap in important_gaps[:max_gap_passes]:
                    gap_passes += 1
                    console.print(f"  Gap pass {gap_passes}: {gap.heading[:50]} ({gap.char_count} chars)")

                    # Find the chunk content for this gap from raw
                    gap_content = None
                    for chunk in effective_chunks:
                        if chunk.heading == gap.heading:
                            gap_content = chunk.text
                            break

                    if gap_content:
                        cmd = ["brain", "enrich-entity", name, "--info", gap_content, "--config", cfg]
                        if llm_provider:
                            cmd.extend(["--llm-provider", llm_provider])
                        result = subprocess_run(cmd, capture_output=True, text=True, timeout=120)
                        if result.returncode == 0:
                            console.print(f"    ✓ gap filled")
                        else:
                            console.print(f"    ✗ failed: {result.stderr[:100]}")

            # Final: post-process
            console.print(f"\n[bold]Post-processing[/bold]")
            subprocess_run(["brain", "post-process", name, "--source-url", url, "--config", cfg],
                         capture_output=True, text=True, timeout=60)
            console.print(f"  ✓ post-processed")

            # Summary
            console.print(f"\n[bold]Full enrich complete:[/bold]")
            console.print(f"  Entity: {name}")
            console.print(f"  Source: {len(raw_content)} chars")
            console.print(f"  Passes: {len(passes)} + {gap_passes if important_gaps else 0} gap fills")
            console.print(f"  Raw saved, source note created, registry synced, compiled")

        except BrainOpsError as error:
            handle_error(error)

    @app.command("check-coverage")
    def check_coverage_command(
        name: str,
        raw_file: Path | None = typer.Option(None, "--raw", help="Path to raw source file. If not provided, looks in .brain-ops/raw/"),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Check what content from the raw source is missing from the entity note."""
        try:
            from brain_ops.domains.knowledge.coverage_check import check_coverage
            from brain_ops.domains.knowledge.source_blocks import load_chunk_sidecar
            from brain_ops.frontmatter import split_frontmatter
            from brain_ops.interfaces.cli.runtime import load_validated_vault
            from brain_ops.storage.obsidian import list_vault_markdown_notes, read_note_text

            vault = load_validated_vault(config_path, dry_run=False)

            # Find entity note
            entity_body = None
            entity_subtype = "person"
            for note_path in list_vault_markdown_notes(vault, excluded_parts={".git", ".obsidian"}):
                _safe, rel, text = read_note_text(vault, note_path)
                try:
                    fm, body = split_frontmatter(text)
                    if fm.get("entity") is True and fm.get("name") == name:
                        entity_body = body
                        entity_subtype = str(fm.get("subtype", fm.get("type", "person")))
                        break
                except Exception:
                    pass

            if entity_body is None:
                console.print(f"Entity '{name}' not found.")
                return

            # Find raw source
            raw_text = None
            resolved_raw_file = None
            if raw_file and raw_file.exists():
                resolved_raw_file = raw_file
                raw_text = raw_file.read_text(encoding="utf-8")
            else:
                raw_dir = vault.config.vault_path / ".brain-ops" / "raw"
                if raw_dir.exists():
                    # Priority 1: check _index.json for exact mapping
                    import json
                    index_path = raw_dir / "_index.json"
                    if index_path.exists():
                        index_data = json.loads(index_path.read_text(encoding="utf-8"))
                        if name in index_data:
                            mapped_path = Path(index_data[name])
                            if mapped_path.exists():
                                resolved_raw_file = mapped_path
                                raw_text = mapped_path.read_text(encoding="utf-8")

                    # Priority 2: slug-based fallback
                    if raw_text is None:
                        import unicodedata
                        def _strip_accents(s: str) -> str:
                            return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
                        slug = _strip_accents(name.lower()).replace(" ", "-").replace("(", "").replace(")", "")
                        slug_parts = slug.split("-")
                        slug_short = "-".join(slug_parts[:3]) if len(slug_parts) > 3 else slug
                        for f in sorted(raw_dir.glob("*.txt"), reverse=True):
                            fname = _strip_accents(f.name.lower())
                            if slug in fname or slug_short in fname:
                                resolved_raw_file = f
                                raw_text = f.read_text(encoding="utf-8")
                                break
                            fname_core = fname.split("-", 1)[-1].rsplit(".", 1)[0] if "-" in fname else fname
                            if fname_core and len(fname_core) >= 4 and fname_core in slug:
                                resolved_raw_file = f
                                raw_text = f.read_text(encoding="utf-8")
                                break

            if raw_text is None:
                console.print(f"No raw source found for '{name}'. Run post-process with --source-url first.")
                return

            raw_chunks = None
            if resolved_raw_file is not None:
                _source_profile, raw_chunks = load_chunk_sidecar(resolved_raw_file)

            report = check_coverage(
                name,
                entity_subtype,
                raw_text,
                entity_body,
                raw_chunks=raw_chunks,
            )

            if as_json:
                console.print_json(data=report.to_dict())
                return

            console.print(f"\n[bold]Coverage: {name}[/bold]")
            console.print(f"Raw headings: {report.raw_headings} | Covered: {report.covered_headings} | Coverage: {report.coverage_pct:.0f}%")
            console.print(f"Needs second pass: {'Yes' if report.needs_second_pass else 'No'}")

            if report.gaps:
                console.print(f"\n[yellow]Gaps ({len(report.gaps)}):[/yellow]")
                for gap in report.gaps:
                    marker = "🔴" if gap.priority == "high" else "🟡" if gap.priority == "medium" else "⚪"
                    console.print(f"  {marker} {gap.heading} ({gap.char_count} chars) — {gap.sample[:80]}...")
            else:
                console.print("\nNo significant gaps detected.")

        except BrainOpsError as error:
            handle_error(error)

    @app.command("multi-enrich")
    def multi_enrich_command(
        name: str,
        url: str = typer.Option(..., "--url", help="URL to download and process in multiple passes."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        llm_provider: str | None = typer.Option(None, "--llm-provider", help="LLM provider for each pass."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Enrich an entity from a URL in multiple passes to cover the full source."""
        try:
            from brain_ops.domains.knowledge.chunking import chunk_by_headings
            from brain_ops.domains.knowledge.ingest import fetch_url_document
            from brain_ops.domains.knowledge.multi_pass import plan_multi_pass_chunks, render_pass_context
            from brain_ops.domains.knowledge.source_blocks import (
                extract_planning_chunks,
                save_chunk_sidecar,
            )

            from brain_ops.interfaces.cli.runtime import load_validated_vault
            vault = load_validated_vault(config_path, dry_run=False)
            vault_path = vault.config.vault_path

            # Fetch and save raw
            fetched = fetch_url_document(url)
            raw_content = fetched.text
            from datetime import datetime, timezone
            raw_dir = vault_path / ".brain-ops" / "raw"
            raw_dir.mkdir(parents=True, exist_ok=True)
            slug = "".join(c if c.isalnum() or c in "-_ " else "" for c in name)[:60].strip().replace(" ", "-").lower()
            raw_file = raw_dir / f"{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{slug}-full.txt"
            raw_file.write_text(raw_content, encoding="utf-8")
            # Update _index.json
            import json
            index_path = raw_dir / "_index.json"
            index_data: dict[str, str] = {}
            if index_path.exists():
                index_data = json.loads(index_path.read_text(encoding="utf-8"))
            index_data[name] = str(raw_file)
            index_path.write_text(json.dumps(index_data, indent=2, ensure_ascii=False), encoding="utf-8")
            source_profile, planning_chunks = extract_planning_chunks(
                url=url,
                html=fetched.html,
                article_title=fetched.title,
            )
            if planning_chunks:
                save_chunk_sidecar(raw_file, source_profile=source_profile, chunks=planning_chunks)
            console.print(f"Raw source saved: {len(raw_content)} chars")

            # Plan passes
            passes = plan_multi_pass_chunks(
                planning_chunks or chunk_by_headings(raw_content),
                fallback_text=raw_content,
            )
            console.print(f"Planned {len(passes)} enrichment passes")

            if as_json:
                console.print_json(data={"raw_chars": len(raw_content), "passes": [p.to_dict() for p in passes]})
                return

            # Execute each pass
            for enrich_pass in passes:
                context = render_pass_context(enrich_pass)
                console.print(f"\nPass {enrich_pass.pass_number}/{len(passes)}: {enrich_pass.focus} ({enrich_pass.total_chars} chars)")

                from subprocess import run as subprocess_run
                cmd_parts = ["brain", "enrich-entity", name, "--info", context]
                if config_path:
                    cmd_parts.extend(["--config", str(config_path)])
                else:
                    cmd_parts.extend(["--config", "config/vault.yaml"])
                if llm_provider:
                    cmd_parts.extend(["--llm-provider", llm_provider])
                result = subprocess_run(cmd_parts, capture_output=True, text=True, timeout=120)
                if result.returncode == 0:
                    console.print(f"  Pass {enrich_pass.pass_number} completed")
                else:
                    console.print(f"  Pass {enrich_pass.pass_number} failed: {result.stderr[:200]}")

            console.print(f"\nMulti-enrich complete: {len(passes)} passes on '{name}'")
        except BrainOpsError as error:
            handle_error(error)

    @app.command("plan-direct-enrich")
    def plan_direct_enrich_command(
        name: str,
        url: str = typer.Option(..., "--url", help="URL to download and plan for direct agent enrichment."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        subtype: str | None = typer.Option(None, "--subtype", help="Override entity subtype when planning priorities."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Prepare the full deterministic pipeline for agent-driven direct enrichment."""
        try:
            import json
            from datetime import datetime, timezone

            from brain_ops.domains.knowledge import build_direct_enrich_plan, save_direct_enrich_plan
            from brain_ops.domains.knowledge.ingest import fetch_url_document
            from brain_ops.domains.knowledge.source_blocks import (
                extract_planning_chunks,
                save_chunk_sidecar,
            )
            from brain_ops.frontmatter import split_frontmatter
            from brain_ops.interfaces.cli.runtime import load_validated_vault
            from brain_ops.storage.obsidian import list_vault_markdown_notes, read_note_text

            vault = load_validated_vault(config_path, dry_run=False)
            vault_path = vault.config.vault_path

            fetched = fetch_url_document(url)
            raw_content = fetched.text
            raw_dir = vault_path / ".brain-ops" / "raw"
            raw_dir.mkdir(parents=True, exist_ok=True)
            slug = "".join(c if c.isalnum() or c in "-_ " else "" for c in name)[:60].strip().replace(" ", "-").lower()
            raw_file = raw_dir / f"{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{slug}-full.txt"
            raw_file.write_text(raw_content, encoding="utf-8")

            index_path = raw_dir / "_index.json"
            index_data: dict[str, str] = {}
            if index_path.exists():
                index_data = json.loads(index_path.read_text(encoding="utf-8"))
            index_data[name] = str(raw_file)
            index_path.write_text(json.dumps(index_data, indent=2, ensure_ascii=False), encoding="utf-8")

            resolved_subtype = subtype or "person"
            for note_path in list_vault_markdown_notes(vault, excluded_parts={".git", ".obsidian"}):
                _safe, _rel, text = read_note_text(vault, note_path)
                try:
                    fm, _body = split_frontmatter(text)
                except Exception:
                    continue
                if fm.get("entity") is True and fm.get("name") == name:
                    resolved_subtype = str(fm.get("subtype", fm.get("type", resolved_subtype)))
                    break

            source_profile, planning_chunks = extract_planning_chunks(
                url=url,
                html=fetched.html,
                article_title=fetched.title,
            )
            if planning_chunks:
                save_chunk_sidecar(raw_file, source_profile=source_profile, chunks=planning_chunks)

            plan = build_direct_enrich_plan(
                entity_name=name,
                source_url=url,
                raw_text=raw_content,
                raw_file=raw_file,
                subtype=resolved_subtype,
                planning_chunks=planning_chunks,
                source_profile=source_profile,
            )
            plan_path = save_direct_enrich_plan(vault_path / ".brain-ops" / "direct-enrich", plan)
            payload = {**plan.to_dict(), "plan_file": str(plan_path)}

            if as_json:
                console.print_json(data=payload)
                return

            console.print(f"[bold]Direct enrich plan:[/bold] {name}")
            console.print(f"  Raw source saved: {raw_file}")
            console.print(f"  Plan file: {plan_path}")
            console.print(f"  Mode: {plan.mode} | Subtype: {plan.subtype} | Raw chars: {plan.raw_chars}")
            console.print(f"  Planned passes: {len(plan.pass_plans)}")
            for enrich_pass in plan.pass_plans:
                console.print(
                    f"    Pass {enrich_pass.pass_number}: {enrich_pass.focus} "
                    f"({enrich_pass.total_chars} chars, {len(enrich_pass.headings)} headings)"
                )
            if plan.ranked_chunks:
                console.print("  Top ranked chunks:")
                for chunk in plan.ranked_chunks[:8]:
                    console.print(f"    - {chunk.heading} ({chunk.char_count} chars)")
            console.print("  Workflow:")
            for step in plan.workflow_steps:
                console.print(f"    - {step}")

        except BrainOpsError as error:
            handle_error(error)

    @app.command("post-process")
    def post_process_command(
        name: str,
        source_url: str | None = typer.Option(None, "--source-url", help="URL used to enrich this entity."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Post-process a directly edited entity — emit event, create source note, log extraction."""
        try:
            import json as json_mod
            from datetime import datetime, timezone
            from brain_ops.frontmatter import split_frontmatter
            from brain_ops.interfaces.cli.runtime import load_validated_vault, load_event_sink
            from brain_ops.storage.obsidian import list_vault_markdown_notes, read_note_text

            vault = load_validated_vault(config_path, dry_run=False)
            actions: list[str] = []

            # Find the entity note
            entity_fm = None
            entity_body = None
            entity_path = None
            for note_path in list_vault_markdown_notes(vault, excluded_parts={".git", ".obsidian"}):
                _safe, rel, text = read_note_text(vault, note_path)
                try:
                    fm, body = split_frontmatter(text)
                    if fm.get("entity") is True and fm.get("name") == name:
                        entity_fm = fm
                        entity_body = body
                        entity_path = str(rel)
                        break
                except Exception:
                    pass

            if entity_fm is None:
                console.print(f"Entity '{name}' not found in vault.")
                return

            now = datetime.now(timezone.utc)
            vault_path = vault.config.vault_path

            # 0. Save raw source content if URL provided
            if source_url:
                try:
                    from brain_ops.domains.knowledge.ingest import fetch_url_document
                    from brain_ops.domains.knowledge.source_blocks import (
                        extract_planning_chunks,
                        save_chunk_sidecar,
                    )
                    fetched = fetch_url_document(source_url)
                    raw_content = fetched.text
                    raw_dir = vault_path / ".brain-ops" / "raw"
                    raw_dir.mkdir(parents=True, exist_ok=True)
                    slug = "".join(c if c.isalnum() or c in "-_ " else "" for c in name)[:60].strip().replace(" ", "-").lower()
                    raw_file = raw_dir / f"{now.strftime('%Y%m%d-%H%M%S')}-{slug}.txt"
                    raw_file.write_text(raw_content, encoding="utf-8")
                    # Update _index.json
                    index_path = raw_dir / "_index.json"
                    idx: dict[str, str] = {}
                    if index_path.exists():
                        idx = json_mod.loads(index_path.read_text(encoding="utf-8"))
                    idx[name] = str(raw_file)
                    index_path.write_text(json_mod.dumps(idx, indent=2, ensure_ascii=False), encoding="utf-8")
                    source_profile, planning_chunks = extract_planning_chunks(
                        url=source_url,
                        html=fetched.html,
                        article_title=fetched.title,
                    )
                    if planning_chunks:
                        save_chunk_sidecar(raw_file, source_profile=source_profile, chunks=planning_chunks)
                    actions.append(f"raw source saved ({len(raw_content)} chars)")
                except Exception:
                    pass

            # 1. Emit event to event log
            try:
                event_sink = load_event_sink()
                if event_sink is not None:
                    from brain_ops.core.events import new_event
                    event_sink.publish(new_event(
                        name="entity.direct_edit",
                        source="application.knowledge",
                        payload={
                            "entity_name": name,
                            "source_url": source_url,
                            "workflow": "post-process-direct-edit",
                        },
                    ))
                    actions.append("event emitted")
            except Exception:
                pass

            # 2. Create source note stub if URL provided
            if source_url:
                try:
                    from urllib.parse import urlparse
                    from brain_ops.domains.knowledge.link_aliases import format_wikilink
                    from brain_ops.domains.knowledge.registry import load_entity_registry as _load_reg

                    _reg_path = vault_path / ".brain-ops" / "entity_registry.json"
                    _reg = _load_reg(_reg_path)
                    _entity_link = format_wikilink(name, _reg)

                    domain = urlparse(source_url).netloc.replace("www.", "").split(".")[0].title()
                    source_title = f"{name} - {domain}"
                    source_path = vault_path / "01 - Sources" / f"{source_title}.md"
                    if not source_path.exists():
                        source_content = f"""---
type: source
source_type: encyclopedia
status: processed
created: '{now.strftime("%Y-%m-%dT%H:%M:%S")}'
updated: '{now.strftime("%Y-%m-%dT%H:%M:%S")}'
tags: []
url:
  - {source_url}
enriched_entities:
  - {name}
evidence_strength: strong
source_confidence: 0.9
entity: false
---

> Source used to enrich {_entity_link}

## Source

- URL: [{source_title}]({source_url})
- Enriched: {_entity_link}

## Related notes
"""
                        source_path.write_text(source_content, encoding="utf-8")
                        actions.append(f"source note created: {source_title}")
                except Exception:
                    pass

            # 3. Save extraction log entry
            try:
                from brain_ops.domains.knowledge import build_direct_edit_extraction
                from brain_ops.domains.knowledge.extraction_store import save_extraction_record
                extractions_dir = vault_path / ".brain-ops" / "extractions"
                extraction = build_direct_edit_extraction(
                    entity_fm,
                    entity_body or "",
                    name=name,
                    source_url=source_url,
                )
                save_extraction_record(
                    extractions_dir,
                    source_title=name,
                    source_url=source_url,
                    source_type="direct_edit",
                    raw_llm_json=extraction,
                    prompt_version="direct_agent_v2",
                )
                actions.append("extraction record saved")
            except Exception:
                pass

            # 4. Run reconcile (registry sync + compile)
            from brain_ops.domains.knowledge.registry import RegisteredEntity, load_entity_registry, save_entity_registry
            from brain_ops.domains.knowledge.object_model import resolve_object_kind
            from brain_ops.application.knowledge import execute_compile_knowledge_workflow

            registry_path = vault_path / ".brain-ops" / "entity_registry.json"
            registry = load_entity_registry(registry_path)
            entity_type = str(entity_fm.get("type", "concept"))
            existing = registry.get(name)
            if existing is None:
                ok, st = resolve_object_kind(entity_type)
                entity = RegisteredEntity(
                    canonical_name=name,
                    entity_type=entity_type,
                    status="canonical",
                    object_kind=str(entity_fm.get("object_kind", ok)),
                    subtype=str(entity_fm.get("subtype", st)),
                    source_count=1,
                )
                related = entity_fm.get("related")
                if isinstance(related, list):
                    entity.relation_count = len(related)
                    entity.frequent_relations = [str(r) for r in related if isinstance(r, str)][:20]
                registry.register(entity)
                actions.append("registered in entity registry (new)")
            else:
                existing.status = "canonical"
                related = entity_fm.get("related")
                if isinstance(related, list):
                    existing.relation_count = len(related)
                    existing.frequent_relations = [str(r) for r in related if isinstance(r, str)][:20]
                actions.append("registry synced")
            save_entity_registry(registry_path, registry)

            # 5. Compile
            execute_compile_knowledge_workflow(
                config_path=config_path, db_path=None, load_vault=load_validated_vault,
            )
            actions.append("knowledge compiled")

            # 6. Wikify: convert plain-text mentions of this entity to [[wikilinks]] across the vault
            try:
                from brain_ops.domains.knowledge.backlinking import inject_backlinks
                bl_result = inject_backlinks(vault.config.vault_path, name)
                if bl_result.notes_linked > 0:
                    actions.append(f"wikified ({bl_result.notes_linked} notes)")
            except Exception:
                pass

            # 7. Auto cross-enrich: fix Related notes for this entity AND entities it mentions
            try:
                import re as _re
                from brain_ops.domains.knowledge.link_aliases import format_wikilink as _fmt_wl
                from brain_ops.domains.knowledge.registry import load_entity_registry as _load_reg2

                _pp_reg_path = vault_path / ".brain-ops" / "entity_registry.json"
                _pp_reg = _load_reg2(_pp_reg_path)

                knowledge_path = vault.config.folder_path("knowledge")
                _entity_names: set[str] = set()
                for _f in knowledge_path.glob("*.md"):
                    _t = _f.read_text(encoding="utf-8")
                    if _re.search(r"^entity:\s*true", _t, _re.MULTILINE):
                        _entity_names.add(_f.stem)

                cross_fixed = 0
                # Check this entity + all entities it mentions
                _this_note = knowledge_path / f"{name}.md"
                _notes_to_check = [_this_note]
                if _this_note.exists():
                    _this_text = _this_note.read_text(encoding="utf-8")
                    _mentioned = {l.strip() for l in _re.findall(r"\[\[([^\]|]+)", _this_text)} & _entity_names
                    for _m in _mentioned:
                        _mp = knowledge_path / f"{_m}.md"
                        if _mp.exists() and _mp != _this_note:
                            _notes_to_check.append(_mp)

                for _np in _notes_to_check:
                    _text = _np.read_text(encoding="utf-8")
                    if not _re.search(r"^entity:\s*true", _text, _re.MULTILINE):
                        continue
                    _all_links = {l.strip() for l in _re.findall(r"\[\[([^\]|]+)", _text)}
                    _body_entities = _all_links & _entity_names
                    _related_links: set[str] = set()
                    _in_rel = False
                    for _line in _text.split("\n"):
                        if _line.strip() == "## Related notes":
                            _in_rel = True
                            continue
                        if _in_rel:
                            if _line.startswith("## "):
                                break
                            for _lk in _re.findall(r"\[\[([^\]|]+)", _line):
                                _related_links.add(_lk.strip())
                    _missing = _body_entities - _related_links - {_np.stem}
                    if _missing:
                        _lines = _text.split("\n")
                        _idx = None
                        for _i, _ln in enumerate(_lines):
                            if _ln.strip() == "## Related notes":
                                _j = _i + 1
                                while _j < len(_lines) and not _lines[_j].startswith("## "):
                                    _j += 1
                                _idx = _j
                                break
                        if _idx is not None:
                            _new = [f"- {_fmt_wl(_m, _pp_reg)}" for _m in sorted(_missing)]
                            _lines = _lines[:_idx] + _new + _lines[_idx:]
                            _np.write_text("\n".join(_lines), encoding="utf-8")
                            cross_fixed += len(_missing)

                if cross_fixed > 0:
                    actions.append(f"cross-enriched ({cross_fixed} links)")
            except Exception:
                pass

            result = {"entity": name, "actions": actions}
            if as_json:
                console.print_json(data=result)
                return
            console.print(f"Post-processed '{name}': {', '.join(actions)}")

        except BrainOpsError as error:
            handle_error(error)

    @app.command("reconcile")
    def reconcile_command(
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
        skip_wikify: bool = typer.Option(False, "--skip-wikify", help="Do not auto-convert plain-text mentions to [[wikilinks]]. Body-safe mode."),
        skip_cross_enrich: bool = typer.Option(False, "--skip-cross-enrich", help="Do not auto-add missing entities to 'Related notes' sections. Body-safe mode."),
    ) -> None:
        """Reconcile direct edits — sync registry, compile, and detect issues after manual changes.

        By default runs: registry sync → compile to SQLite → wikify → cross-enrich.
        With both --skip-wikify and --skip-cross-enrich, no note bodies are modified
        — only frontmatter-read paths and SQLite writes run. Use the skip flags
        during bulk consolidation campaigns (see docs/operations/CAMPAIGN_1_OPERATIONS.md).
        """
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

            # Scan vault and sync registry.
            # Exclude dot-directories including .brain-ops (contains snapshot
            # backups that would otherwise re-register stale entity names
            # after renames/disambiguations).
            synced = 0
            created = 0
            for note_path in list_vault_markdown_notes(
                vault, excluded_parts={".git", ".obsidian", ".brain-ops"},
            ):
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

            # Detect potential disambiguation conflicts
            from brain_ops.domains.knowledge.registry import extract_base_name
            ambiguous: dict[str, list[str]] = {}
            for canonical_name in registry.entities:
                base = extract_base_name(canonical_name).lower()
                ambiguous.setdefault(base, []).append(canonical_name)
            disambiguation_warnings = {
                base: names for base, names in ambiguous.items()
                if len(names) > 1 and all(extract_base_name(n) == n for n in names)
            }

            # Compile knowledge
            execute_compile_knowledge_workflow(
                config_path=config_path, db_path=None, load_vault=load_validated_vault,
            )

            # Wikify: convert plain-text mentions to [[wikilinks]] for all entities (2+ word names)
            # Skipped when --skip-wikify is passed (body-safe mode).
            wikified_total = 0
            if not skip_wikify:
                try:
                    import re as _wk_re
                    from brain_ops.domains.knowledge.backlinking import inject_backlinks

                    knowledge_path = vault.config.folder_path("knowledge")
                    _wk_entities = []
                    for _f in sorted(knowledge_path.glob("*.md")):
                        _t = _f.read_text(encoding="utf-8")
                        if _wk_re.search(r"^entity:\s*true", _t, _wk_re.MULTILINE):
                            _name = _f.stem
                            if len(_name.split()) >= 2:
                                _wk_entities.append(_name)

                    for _name in _wk_entities:
                        _bl = inject_backlinks(vault.config.vault_path, _name)
                        wikified_total += _bl.notes_linked
                except Exception:
                    pass

            # Cross-enrich: fix Related notes for all entities
            # Skipped when --skip-cross-enrich is passed (body-safe mode).
            cross_fixed_total = 0
            if not skip_cross_enrich:
                try:
                    import re as _ce_re
                    from brain_ops.domains.knowledge.link_aliases import format_wikilink as _ce_fmt

                    _ce_reg_path = Path(vault.config.vault_path) / ".brain-ops" / "entity_registry.json"
                    _ce_reg = load_entity_registry(_ce_reg_path)

                    knowledge_path = vault.config.folder_path("knowledge")
                    _ce_entity_names: set[str] = set()
                    for _f in knowledge_path.glob("*.md"):
                        _t = _f.read_text(encoding="utf-8")
                        if _ce_re.search(r"^entity:\s*true", _t, _ce_re.MULTILINE):
                            _ce_entity_names.add(_f.stem)

                    for _np in sorted(knowledge_path.glob("*.md")):
                        _text = _np.read_text(encoding="utf-8")
                        if not _ce_re.search(r"^entity:\s*true", _text, _ce_re.MULTILINE):
                            continue
                        _all_links = {l.strip() for l in _ce_re.findall(r"\[\[([^\]|]+)", _text)}
                        _body_entities = _all_links & _ce_entity_names
                        _related_links: set[str] = set()
                        _in_rel = False
                        for _line in _text.split("\n"):
                            if _line.strip() == "## Related notes":
                                _in_rel = True
                                continue
                            if _in_rel:
                                if _line.startswith("## "):
                                    break
                                for _lk in _ce_re.findall(r"\[\[([^\]|]+)", _line):
                                    _related_links.add(_lk.strip())
                        _missing = _body_entities - _related_links - {_np.stem}
                        if _missing:
                            _lines = _text.split("\n")
                            _idx = None
                            for _i, _ln in enumerate(_lines):
                                if _ln.strip() == "## Related notes":
                                    _j = _i + 1
                                    while _j < len(_lines) and not _lines[_j].startswith("## "):
                                        _j += 1
                                    _idx = _j
                                    break
                            if _idx is not None:
                                _new = [f"- {_ce_fmt(_m, _ce_reg)}" for _m in sorted(_missing)]
                                _lines = _lines[:_idx] + _new + _lines[_idx:]
                                _np.write_text("\n".join(_lines), encoding="utf-8")
                                cross_fixed_total += len(_missing)
                except Exception:
                    pass

            result = {
                "registry_synced": synced,
                "registry_created": created,
                "total_registry": len(registry.entities),
                "disambiguation_warnings": len(disambiguation_warnings),
                "wikified": wikified_total,
                "wikify_skipped": skip_wikify,
                "cross_enriched": cross_fixed_total,
                "cross_enrich_skipped": skip_cross_enrich,
            }

            if as_json:
                console.print_json(data=result)
                return
            console.print(f"Reconciled: {synced} synced, {created} new in registry. Total: {len(registry.entities)} entities.")
            console.print("Knowledge compiled to SQLite.")
            if skip_wikify:
                console.print("[dim]Wikify skipped (--skip-wikify).[/dim]")
            elif wikified_total > 0:
                console.print(f"Wikified: {wikified_total} plain-text mentions converted to wikilinks.")
            if skip_cross_enrich:
                console.print("[dim]Cross-enrich skipped (--skip-cross-enrich).[/dim]")
            elif cross_fixed_total > 0:
                console.print(f"Cross-enriched: {cross_fixed_total} missing links added to Related notes.")
            if disambiguation_warnings:
                console.print(f"\n[yellow]⚠ {len(disambiguation_warnings)} potential name collision(s) detected:[/yellow]")
                for base, names in sorted(disambiguation_warnings.items()):
                    console.print(f"  [cyan]{base}[/cyan]: {', '.join(names)}")
                console.print("[yellow]  Use `brain create-entity` with the same name + different type to auto-disambiguate.[/yellow]")
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

    @app.command("show-entity-relations")
    def show_entity_relations_command(
        entity: str = typer.Argument(..., help="Entity name (exact match)."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        only_typed: bool = typer.Option(False, "--only-typed", help="Show only typed relations."),
        only_legacy: bool = typer.Option(False, "--only-legacy", help="Show only legacy `related:` rows."),
        all_legacy: bool = typer.Option(False, "--all", help="Show all legacy rows (default truncates to 15)."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Subfase 2.0 — display all relations (in+out, typed+legacy) for an entity."""
        try:
            present_show_entity_relations_command(
                console,
                config_path=config_path,
                entity=entity,
                only_typed=only_typed,
                only_legacy=only_legacy,
                all_legacy=all_legacy,
                as_json=as_json,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("query-relations")
    def query_relations_command(
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        from_entity: str | None = typer.Option(None, "--from", help="Filter by source entity."),
        to_entity: str | None = typer.Option(None, "--to", help="Filter by target entity."),
        predicate: str | None = typer.Option(None, "--predicate", help="Filter by canonical predicate."),
        include_legacy: bool = typer.Option(False, "--include-legacy", help="Include untyped `related:` rows."),
        limit: int | None = typer.Option(None, "--limit", help="Cap number of results."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Subfase 2.0 — query the typed relations graph in knowledge.db."""
        try:
            present_query_relations_command(
                console,
                config_path=config_path,
                from_entity=from_entity,
                to_entity=to_entity,
                predicate=predicate,
                include_legacy=include_legacy,
                limit=limit,
                as_json=as_json,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("batch-propose-relations")
    def batch_propose_relations_command(
        batch_name: str = typer.Option(..., "--batch-name", help="Batch directory name under .brain-ops/relations-proposals/batch-<name>/."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        subtype: str | None = typer.Option(None, "--subtype", help="Filter entities by subtype (e.g. person, deity)."),
        domain: str | None = typer.Option(None, "--domain", help="Filter entities by domain (e.g. filosofia, historia)."),
        include: list[str] = typer.Option(None, "--include", help="Include only these entity names (repeatable)."),
        exclude: list[str] = typer.Option(None, "--exclude", help="Exclude these entity names (repeatable)."),
        limit: int | None = typer.Option(None, "--limit", help="Cap number of entities processed."),
        include_empty: bool = typer.Option(
            False, "--include-empty",
            help="Also emit proposals for notes where the proposer found no triples "
                 "(normally skipped to keep the batch reviewable).",
        ),
        overwrite: bool = typer.Option(
            False, "--overwrite",
            help="Overwrite an existing batch directory with the same name. "
                 "Off by default to avoid clobbering reviewer edits.",
        ),
        as_json: bool = typer.Option(False, "--json", help="Emit JSON report."),
        mode: LLMModeChoice = typer.Option(
            LLMModeChoice.cheap, "--mode",
            help="LLM mode: cheap (pattern only, default, 2.2A behavior), "
                 "strict (pattern + LLM with literal-quote evidence), "
                 "deep (pattern + LLM permitting medium-confidence "
                 "contextual inferences — use only on notes explicitly "
                 "blocked by strict).",
        ),
    ) -> None:
        """Campaña 2.1 Paso 4 — build a batch of typed-relation proposals."""
        try:
            present_batch_propose_relations_command(
                console,
                config_path=config_path,
                batch_name=batch_name,
                subtype=subtype,
                domain=domain,
                include=include or [],
                exclude=exclude or [],
                limit=limit,
                include_empty=include_empty,
                overwrite=overwrite,
                as_json=as_json,
                mode=mode.value,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("apply-relations-batch")
    def apply_relations_batch_command(
        batch_name: str = typer.Argument(..., help="Batch name (directory under .brain-ops/relations-proposals/batch-<name>/)."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        apply: bool = typer.Option(
            False, "--apply",
            help="Actually write changes. Default is dry-run.",
        ),
        allow_mentions: bool = typer.Option(
            False, "--allow-mentions",
            help="Also apply triples whose object is MISSING_ENTITY. "
                 "Off by default (Campaña 2.1 clarification #1).",
        ),
        as_json: bool = typer.Option(False, "--json", help="Emit JSON report."),
    ) -> None:
        """Campaña 2.1 Paso 3 — apply a reviewed batch of typed-relation proposals."""
        try:
            present_apply_relations_batch_command(
                console,
                config_path=config_path,
                batch_name=batch_name,
                apply=apply,
                allow_mentions=allow_mentions,
                as_json=as_json,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("propose-relations")
    def propose_relations_command(
        entity: str = typer.Argument(..., help="Entity name (exact match)."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        include_existing: bool = typer.Option(
            False, "--include-existing",
            help="Also propose triples that are already typed in the note "
                 "(useful to inspect proposer behavior on piloted notes).",
        ),
        output: Path | None = typer.Option(
            None, "--output",
            help="Override output path. Default: "
                 "<vault>/.brain-ops/relations-proposals/<entity>.yaml",
        ),
        stdout: bool = typer.Option(
            False, "--stdout",
            help="Print the proposal YAML to stdout instead of writing a file.",
        ),
        as_json: bool = typer.Option(
            False, "--json",
            help="Emit JSON instead of YAML.",
        ),
        mode: LLMModeChoice = typer.Option(
            LLMModeChoice.cheap, "--mode",
            help="LLM mode: cheap (pattern only, default, 2.2A behavior), "
                 "strict (pattern + LLM with literal-quote evidence), "
                 "deep (pattern + LLM permitting medium-confidence "
                 "contextual inferences — use only on notes explicitly "
                 "blocked by strict).",
        ),
    ) -> None:
        """Campaña 2.1 Paso 2 — propose typed relations for an entity (read-only)."""
        try:
            present_propose_relations_command(
                console,
                config_path=config_path,
                entity=entity,
                include_existing=include_existing,
                output=output,
                stdout=stdout,
                as_json=as_json,
                mode=mode.value,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("fill-domain")
    def fill_domain_command(
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        apply: bool = typer.Option(False, "--apply", help="Actually write changes. Default is dry-run."),
        exclude: list[str] = typer.Option(None, "--exclude", help="Entity name (or relative path) to skip. Repeatable."),
        report_path: Path | None = typer.Option(None, "--report", help="Write the full JSON report to this path."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Subfase 1.4a — auto-fill missing `domain:` (high-confidence rules only)."""
        try:
            present_fill_domain_command(
                console,
                config_path=config_path,
                apply=apply,
                exclude=exclude if exclude else None,
                report_path=report_path,
                as_json=as_json,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("fix-capitalization")
    def fix_capitalization_command(
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        apply: bool = typer.Option(False, "--apply", help="Actually write changes. Default is dry-run."),
        exclude: list[str] = typer.Option(None, "--exclude", help="Entity old-name to skip. Repeatable."),
        report_path: Path | None = typer.Option(None, "--report", help="Write the full JSON report to this path."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Subfase 1.3 — rename entities with wrong capitalization (dry-run by default)."""
        try:
            present_fix_capitalization_command(
                console,
                config_path=config_path,
                apply=apply,
                exclude=exclude if exclude else None,
                report_path=report_path,
                as_json=as_json,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("disambiguate-bare")
    def disambiguate_bare_command(
        bare_name: str = typer.Argument(..., help="The bare entity name to convert (e.g. 'Tebas')."),
        discriminator: str = typer.Option(..., "--discriminator", help="The suffix for the renamed entity (e.g. 'Grecia' → 'Tebas (Grecia)')."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        apply: bool = typer.Option(False, "--apply", help="Actually write changes. Default is dry-run."),
        report_path: Path | None = typer.Option(None, "--report", help="Write the full JSON report to this path."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Subfase 1.5 — convert a bare-name entity into a disambiguation page (dry-run by default)."""
        try:
            present_disambiguate_bare_command(
                console,
                config_path=config_path,
                bare_name=bare_name,
                discriminator=discriminator,
                apply=apply,
                report_path=report_path,
                as_json=as_json,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("normalize-domain")
    def normalize_domain_command(
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        apply: bool = typer.Option(False, "--apply", help="Actually write changes. Default is dry-run."),
        only_transition: list[str] = typer.Option(None, "--only", help="Apply only this transition. Repeatable. Example: --only 'philosophy → filosofia'"),
        exclude_file: Path | None = typer.Option(None, "--exclude", help="File with one note_path per line to skip."),
        report_path: Path | None = typer.Option(None, "--report", help="Write the full JSON report to this path."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Subfase 1.1/1.2 — normalize non-canonical domain aliases (dry-run by default)."""
        try:
            present_normalize_domain_command(
                console,
                config_path=config_path,
                apply=apply,
                only_transition=only_transition if only_transition else None,
                exclude_file=exclude_file,
                report_path=report_path,
                as_json=as_json,
            )
        except BrainOpsError as error:
            handle_error(error)

    @app.command("lint-schemas")
    def lint_schemas_command(
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        subtype: str | None = typer.Option(None, "--subtype", help="Filter by entity subtype."),
        domain: str | None = typer.Option(None, "--domain", help="Filter by entity domain."),
        naming: bool = typer.Option(False, "--naming", help="Include naming-rule violations."),
        strict: bool = typer.Option(False, "--strict", help="Exit code 1 if errors found."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Report schema and naming violations across Knowledge notes (read-only)."""
        try:
            exit_code = present_lint_schemas_command(
                console,
                config_path=config_path,
                subtype=subtype,
                domain=domain,
                naming=naming,
                strict=strict,
                as_json=as_json,
            )
            if exit_code:
                raise typer.Exit(code=exit_code)
        except BrainOpsError as error:
            handle_error(error)

    @app.command("migrate-knowledge-db")
    def migrate_knowledge_db_command(
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        dry_run: bool = typer.Option(False, "--dry-run", help="List pending migrations without applying."),
        status: bool = typer.Option(False, "--status", help="Show applied and pending migrations."),
        skip_backup: bool = typer.Option(False, "--skip-backup", help="Skip automatic backup (not recommended)."),
        force_migrate: bool = typer.Option(False, "--force-migrate", help="Bypass env var / test runner guards. Still creates backup. Exceptional use only."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Apply pending schema migrations to the knowledge.db with automatic backup."""
        try:
            present_migrate_knowledge_db_command(
                console,
                config_path=config_path,
                dry_run=dry_run,
                status=status,
                skip_backup=skip_backup,
                force_migrate=force_migrate,
                as_json=as_json,
            )
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

    @app.command("capture-note")
    def capture_note_command(
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


    @app.command("fix-links")
    def fix_links_command(
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing files."),
        include_risky: bool = typer.Option(False, "--include-risky", help="Incluir aliases ambiguos (Roma, Egipto, Grecia)."),
        as_json: bool = typer.Option(False, "--json", help="Print structured JSON output."),
    ) -> None:
        """Corregir links ambiguos: [[Persia]] → [[Imperio Persa|Persia]], etc."""
        try:
            from brain_ops.domains.knowledge.link_aliases import fix_ambiguous_links
            from brain_ops.interfaces.cli.runtime import load_validated_vault

            vault = load_validated_vault(config_path, dry_run=dry_run)
            result = fix_ambiguous_links(vault.config.vault_path, dry_run=dry_run, include_risky=include_risky)

            if as_json:
                console.print_json(data=result.to_dict())
                return

            if result.fixes:
                console.print(f"\n[bold]{'[dry-run] ' if dry_run else ''}Links corregidos:[/bold]")
                seen_files: set[str] = set()
                for file_path, old, new in result.fixes:
                    if file_path not in seen_files:
                        console.print(f"\n  [cyan]{file_path}[/cyan]")
                        seen_files.add(file_path)
                    console.print(f"    {old} → {new}")
                console.print(f"\n[bold]Total:[/bold] {len(result.fixes)} links en {result.notes_fixed} notas")
            else:
                console.print("No se encontraron links ambiguos para corregir.")
        except BrainOpsError as error:
            handle_error(error)


    # ── sync-quotes ──────────────────────────────────────────────────

    @app.command("sync-quotes")
    def sync_quotes_command(
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        dry_run: bool = typer.Option(False, "--dry-run", help="Preview changes without writing."),
    ) -> None:
        """Sync ^quote- blocks from entity notes into Frases MOC collections in maps folder."""
        try:
            import re
            from brain_ops.interfaces.cli.runtime import load_validated_vault

            vault = load_validated_vault(config_path, dry_run=False)
            vault_path = Path(vault.config.vault_path)
            knowledge_path = vault.config.folder_path("knowledge")
            maps_path = vault.config.folder_path("maps")

            # ── 1. Scan all entity notes for ^quote-* blocks ──
            quote_pattern = re.compile(r"\^(quote-[a-z0-9-]+)")
            tema_pattern = re.compile(r"tema::\s*(.+)")

            quotes: list[dict] = []
            for note_path in sorted(knowledge_path.glob("*.md")):
                text = note_path.read_text(encoding="utf-8")
                blocks = quote_pattern.findall(text)
                if not blocks:
                    continue
                entity_name = note_path.stem
                for block_id in blocks:
                    # Find tema near this block
                    idx = text.find("^" + block_id)
                    if idx < 0:
                        continue
                    chunk = text[idx : idx + 600]
                    tema_match = tema_pattern.search(chunk)
                    temas_raw = tema_match.group(1).strip() if tema_match else ""
                    temas = [t.strip().lower() for t in temas_raw.split(",") if t.strip()]
                    quotes.append({
                        "entity": entity_name,
                        "block_id": block_id,
                        "temas": temas,
                    })

            # ── 2. Scan MOC files for existing refs ──
            moc_ref_pattern = re.compile(r"!\[\[([^#]+)#\^([^\]]+)\]\]")
            moc_files: dict[str, set[str]] = {}
            for moc_path in sorted(maps_path.glob("Frases - *.md")):
                text = moc_path.read_text(encoding="utf-8")
                refs = set()
                for _entity, block_id in moc_ref_pattern.findall(text):
                    refs.add(block_id)
                moc_files[moc_path.stem] = refs

            # ── 3. Tema → MOC mapping ──
            tema_to_moc: dict[str, str] = {
                "liderazgo": "Frases - Liderazgo y poder",
                "poder": "Frases - Liderazgo y poder",
                "imperio": "Frases - Liderazgo y poder",
                "democracia": "Frases - Liderazgo y poder",
                "justicia": "Frases - Liderazgo y poder",
                "política": "Frases - Liderazgo y poder",
                "decisión": "Frases - Liderazgo y poder",
                "libertad": "Frases - Liderazgo y poder",
                "reforma": "Frases - Liderazgo y poder",
                "guerra": "Frases - Guerra y estrategia",
                "estrategia": "Frases - Guerra y estrategia",
                "táctica": "Frases - Guerra y estrategia",
                "valor": "Frases - Guerra y estrategia",
                "venganza": "Frases - Guerra y estrategia",
                "soberbia": "Frases - Guerra y estrategia",
                "prudencia": "Frases - Guerra y estrategia",
                "diplomacia": "Frases - Guerra y estrategia",
                "filosofía": "Frases - Filosofía y sabiduría",
                "sabiduría": "Frases - Filosofía y sabiduría",
                "ciencia": "Frases - Filosofía y sabiduría",
                "verdad": "Frases - Filosofía y sabiduría",
                "religión": "Frases - Filosofía y sabiduría",
                "determinismo": "Frases - Filosofía y sabiduría",
                "educación": "Frases - Filosofía y sabiduría",
                "creatividad": "Frases - Filosofía y sabiduría",
                "muerte": "Frases - Muerte y legado",
                "legado": "Frases - Muerte y legado",
                "tragedia": "Frases - Muerte y legado",
                "dignidad": "Frases - Muerte y legado",
                "reflexión": "Frases - Muerte y legado",
                "humor": "Frases - Humor e ingenio",
                "ingenio": "Frases - Humor e ingenio",
                "ironía": "Frases - Humor e ingenio",
                "argumentación": "Frases - Humor e ingenio",
            }

            # ── 4. Find orphaned quotes and assign to MOCs ──
            all_moc_refs: set[str] = set()
            for refs in moc_files.values():
                all_moc_refs.update(refs)

            # Group additions by MOC
            additions: dict[str, list[str]] = {}
            orphaned: list[dict] = []
            for q in quotes:
                if q["block_id"] in all_moc_refs:
                    continue
                # Determine target MOC from first matching tema
                target_moc = None
                for tema in q["temas"]:
                    if tema in tema_to_moc:
                        target_moc = tema_to_moc[tema]
                        break
                if target_moc is None and q["temas"]:
                    # Default: first tema gets mapped to most relevant MOC
                    target_moc = "Frases - Filosofía y sabiduría"
                elif target_moc is None:
                    target_moc = "Frases - Filosofía y sabiduría"

                ref_line = f'\n![[{q["entity"]}#^{q["block_id"]}]]'
                additions.setdefault(target_moc, []).append(ref_line)
                orphaned.append(q)

            # ── 5. Report ──
            console.print(f"\n[bold]Frases sync report[/bold]")
            console.print(f"  Total quotes found: {len(quotes)}")
            console.print(f"  Already in MOCs: {len(quotes) - len(orphaned)}")
            console.print(f"  Orphaned (to add): {len(orphaned)}")
            console.print(f"  MOC files: {len(moc_files)}")

            if not orphaned:
                console.print("\n[green]All quotes are synced. Nothing to do.[/green]")
                return

            console.print(f"\n[bold]Additions:[/bold]")
            for moc_name, refs in sorted(additions.items()):
                console.print(f"  [cyan]{moc_name}[/cyan]: +{len(refs)} quotes")

            if dry_run:
                console.print("\n[yellow][dry-run] No files modified.[/yellow]")
                for q in orphaned:
                    console.print(f"  {q['entity']}#^{q['block_id']} → {tema_to_moc.get(q['temas'][0] if q['temas'] else '', 'Filosofía')}")
                return

            # ── 6. Write additions to MOC files ──
            for moc_name, refs in additions.items():
                moc_path = maps_path / f"{moc_name}.md"
                if moc_path.exists():
                    text = moc_path.read_text(encoding="utf-8")
                    # Append before the end
                    text = text.rstrip() + "\n" + "\n".join(refs) + "\n"
                    moc_path.write_text(text, encoding="utf-8")
                else:
                    # Create new MOC
                    header = f"""---
type: moc
subtype: quote_collection
created: '2026-04-11'
tags: [frases]
---

# {moc_name}

Colección temática de frases célebres.
"""
                    content = header + "\n".join(refs) + "\n"
                    moc_path.write_text(content, encoding="utf-8")
                    console.print(f"  [green]Created new MOC: {moc_name}.md[/green]")

            console.print(f"\n[green]Synced {len(orphaned)} quotes to {len(additions)} MOC files.[/green]")

        except BrainOpsError as error:
            handle_error(error)


    # ── check-books ──────────────────────────────────────────────────

    @app.command("check-books")
    def check_books_command(
        book_name: str | None = typer.Argument(None, help="Book name to check (without .md). If omitted, checks all."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
    ) -> None:
        """Check books against current entities — find gaps, new entities, and improvement opportunities."""
        try:
            import re
            from brain_ops.interfaces.cli.runtime import load_validated_vault

            vault = load_validated_vault(config_path, dry_run=False)
            vault_path = Path(vault.config.vault_path)
            knowledge_path = vault.config.folder_path("knowledge")
            books_path = vault_path / "08 - Books"

            if not books_path.exists():
                console.print("[red]No 08 - Books/ folder found.[/red]")
                return

            # ── 1. Load all entity names and their related fields ──
            entity_names: set[str] = set()
            entity_tags: dict[str, list[str]] = {}
            entity_words: dict[str, int] = {}
            for note_path in knowledge_path.glob("*.md"):
                text = note_path.read_text(encoding="utf-8")
                if not re.search(r"^entity:\s*true", text, re.MULTILINE):
                    continue
                name = note_path.stem
                entity_names.add(name)
                entity_words[name] = len(text.split())
                tags_match = re.findall(r"^  - (.+)$", text, re.MULTILINE)
                entity_tags[name] = [t.strip().strip("'\"") for t in tags_match]

            # ── 2. Find book files ──
            book_files: list[Path] = []
            if book_name:
                for f in books_path.rglob("*.md"):
                    if f.stem.lower() == book_name.lower() or book_name.lower() in f.stem.lower():
                        book_files.append(f)
                if not book_files:
                    console.print(f"[red]Book '{book_name}' not found.[/red]")
                    return
            else:
                book_files = [
                    f for f in books_path.rglob("*.md")
                    if f.stem != "Biblioteca"
                ]

            # ── 3. Analyze each book ──
            for book_path in sorted(book_files):
                text = book_path.read_text(encoding="utf-8")
                book_stem = book_path.stem
                words = len(text.split())

                # Extract wikilinks from book
                book_links = set(re.findall(r"\[\[([^\]|]+)", text))
                # Normalize link targets
                book_links = {l.strip() for l in book_links}

                # Classify links
                existing = book_links & entity_names
                missing = book_links - entity_names
                # Remove non-entity targets (folders, maps, etc.)
                missing = {m for m in missing if not m.startswith("MOC") and m != "Biblioteca"}

                # Extract book tags/related from frontmatter
                book_related = set()
                in_related = False
                for line in text.split("\n"):
                    if line.strip().startswith("related:"):
                        in_related = True
                        continue
                    if in_related:
                        if line.strip().startswith("- "):
                            rel = line.strip().lstrip("- ").strip().strip("'\"")
                            book_related.add(rel)
                        elif not line.strip().startswith("-"):
                            in_related = False

                # Find entities that SHOULD be in the book but aren't mentioned
                # Based on: entities whose tags overlap with book tags
                book_tags_set = set()
                in_tags = False
                for line in text.split("\n"):
                    if line.strip().startswith("tags:"):
                        # Inline tags: [a, b, c]
                        inline = re.search(r"\[(.+)\]", line)
                        if inline:
                            book_tags_set = {t.strip() for t in inline.group(1).split(",")}
                        else:
                            in_tags = True
                        continue
                    if in_tags:
                        if line.strip().startswith("- "):
                            book_tags_set.add(line.strip().lstrip("- ").strip().strip("'\""))
                        elif not line.strip().startswith("-"):
                            in_tags = False

                # Find candidate entities by tag overlap
                candidates: list[tuple[str, int]] = []
                for ename, etags in entity_tags.items():
                    if ename in book_links:
                        continue
                    overlap = book_tags_set & set(etags)
                    if overlap and entity_words.get(ename, 0) > 300:
                        candidates.append((ename, entity_words.get(ename, 0)))
                candidates.sort(key=lambda x: -x[1])

                # Check standards
                has_tesis = "**Tesis:**" in text or "Tesis:" in text
                has_reflection = "## Reflexión" in text
                has_questions = "💭" in text
                has_nav = "📖" in text

                # ── 4. Report ──
                console.print(f"\n[bold]📖 {book_stem}[/bold]")
                console.print(f"  Palabras: {words:,}")
                console.print(f"  Entidades referenciadas: {len(existing)} (existen) + {len(missing)} (no existen)")

                # Standards check
                standards = []
                if not has_tesis:
                    standards.append("[red]✗[/red] Falta tesis")
                if not has_reflection:
                    standards.append("[red]✗[/red] Falta reflexión")
                if not has_questions:
                    standards.append("[red]✗[/red] Falta 💭 preguntas por acto")
                if not has_nav:
                    standards.append("[red]✗[/red] Falta navegación 📖")
                if standards:
                    console.print(f"  Estándar: {' · '.join(standards)}")
                else:
                    console.print("  Estándar: [green]✓ Completo[/green]")

                # Missing entities (red links)
                if missing:
                    console.print(f"\n  [yellow]Links rojos ({len(missing)}):[/yellow]")
                    for m in sorted(missing)[:15]:
                        console.print(f"    [[{m}]] — no existe")

                # New entity candidates
                if candidates:
                    console.print(f"\n  [cyan]Entidades candidatas a incorporar ({len(candidates)}):[/cyan]")
                    for name, w in candidates[:10]:
                        console.print(f"    [[{name}]] ({w:,} palabras)")

                console.print("")

        except BrainOpsError as error:
            handle_error(error)


    # ── cross-enrich ─────────────────────────────────────────────────

    @app.command("cross-enrich")
    def cross_enrich_command(
        entity_name: str | None = typer.Argument(None, help="Entity to check. If omitted, checks all."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        fix: bool = typer.Option(False, "--fix", help="Auto-add missing links to Related notes."),
    ) -> None:
        """Find entities mentioned in text but missing from Related notes, and optionally fix them."""
        try:
            import re
            from brain_ops.interfaces.cli.runtime import load_validated_vault
            from brain_ops.domains.knowledge.link_aliases import format_wikilink
            from brain_ops.domains.knowledge.registry import load_entity_registry

            vault = load_validated_vault(config_path, dry_run=False)
            knowledge_path = vault.config.folder_path("knowledge")

            # Load registry for disambiguation
            registry_path = vault.config.data_dir / "entity_registry.json"
            registry = load_entity_registry(registry_path)

            # ── 1. Load all entity names (use stem, which includes disambiguator) ──
            entity_names: set[str] = set()
            for f in knowledge_path.glob("*.md"):
                text = f.read_text(encoding="utf-8")
                if re.search(r"^entity:\s*true", text, re.MULTILINE):
                    entity_names.add(f.stem)

            # ── 2. Select files to check ──
            if entity_name:
                targets = [knowledge_path / f"{entity_name}.md"]
                if not targets[0].exists():
                    console.print(f"[red]Entity '{entity_name}' not found.[/red]")
                    return
            else:
                targets = sorted(knowledge_path.glob("*.md"))

            # ── 3. Analyze each entity ──
            total_gaps = 0
            total_fixed = 0
            results: list[tuple[str, set[str]]] = []

            for note_path in targets:
                text = note_path.read_text(encoding="utf-8")
                if not re.search(r"^entity:\s*true", text, re.MULTILINE):
                    continue

                name = note_path.stem

                # Find all wikilinks in the full text
                all_links = {l.strip() for l in re.findall(r"\[\[([^\]|]+)", text)}

                # Find links only in Related notes section
                related_links: set[str] = set()
                in_related = False
                for line in text.split("\n"):
                    if line.strip() == "## Related notes":
                        in_related = True
                        continue
                    if in_related:
                        if line.startswith("## "):
                            break
                        for link in re.findall(r"\[\[([^\]|]+)", line):
                            related_links.add(link.strip())

                # Find entities mentioned in body but NOT in Related notes
                body_entity_links = all_links & entity_names
                missing_from_related = body_entity_links - related_links - {name}

                if missing_from_related:
                    results.append((name, missing_from_related))
                    total_gaps += len(missing_from_related)

            # ── 4. Report ──
            console.print(f"\n[bold]Cross-enrichment report[/bold]")
            console.print(f"  Entities checked: {len(targets)}")
            console.print(f"  With gaps: {len(results)}")
            console.print(f"  Total missing links: {total_gaps}")

            if not results:
                console.print("\n[green]All entities are properly cross-linked.[/green]")
                return

            for name, missing in sorted(results, key=lambda x: -len(x[1])):
                console.print(f"\n  [cyan]{name}[/cyan] — missing {len(missing)} from Related notes:")
                for m in sorted(missing):
                    console.print(f"    + {format_wikilink(m, registry)}")

            # ── 5. Fix if requested ──
            if fix:
                for name, missing in results:
                    note_path = knowledge_path / f"{name}.md"
                    text = note_path.read_text(encoding="utf-8")

                    # Find the Related notes section and append
                    lines = text.split("\n")
                    insert_idx = None
                    for i, line in enumerate(lines):
                        if line.strip() == "## Related notes":
                            # Find last line of the section
                            j = i + 1
                            while j < len(lines) and not lines[j].startswith("## "):
                                j += 1
                            insert_idx = j
                            break

                    if insert_idx is not None:
                        new_lines = [f"- {format_wikilink(m, registry)}" for m in sorted(missing)]
                        lines = lines[:insert_idx] + new_lines + lines[insert_idx:]
                        note_path.write_text("\n".join(lines), encoding="utf-8")
                        total_fixed += len(missing)

                console.print(f"\n[green]Fixed {total_fixed} missing links across {len(results)} entities.[/green]")
            else:
                console.print(f"\n[yellow]Run with --fix to auto-add missing links.[/yellow]")

        except BrainOpsError as error:
            handle_error(error)

    @app.command("wikify")
    def wikify_command(
        entity_name: str | None = typer.Argument(None, help="Entity to wikify. If omitted, processes all entities."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        dry_run: bool = typer.Option(False, "--dry-run", help="Preview changes without writing files."),
        min_words: int = typer.Option(2, "--min-words", help="Minimum words in entity name for batch mode (avoids false positives with common words like 'Poder'). Set to 1 to include all."),
    ) -> None:
        """Convert plain-text mentions of entity names to [[wikilinks]] across the vault.

        Scans all notes for plain-text mentions of entity names and converts the
        first occurrence in each note to a wikilink.  Handles disambiguated
        entities (e.g. 'Urano (planeta)' matches plain 'Urano').

        Without arguments, processes every registered entity in the vault.
        By default, only processes entities whose names have 2+ words to avoid
        false positives with common single words. Use --min-words 1 for all.
        """
        try:
            import re
            from brain_ops.interfaces.cli.runtime import load_validated_vault
            from brain_ops.domains.knowledge.backlinking import inject_backlinks

            vault = load_validated_vault(config_path, dry_run=dry_run)
            knowledge_path = vault.config.folder_path("knowledge")
            vault_path = vault.config.vault_path

            if entity_name:
                # Single entity mode — always process regardless of min_words
                note_path = knowledge_path / f"{entity_name}.md"
                if not note_path.exists():
                    console.print(f"[red]Entity '{entity_name}' not found.[/red]")
                    return
                entities = [entity_name]
            else:
                # Batch mode: all entities, filtered by min_words
                entities = []
                for f in sorted(knowledge_path.glob("*.md")):
                    text = f.read_text(encoding="utf-8")
                    if re.search(r"^entity:\s*true", text, re.MULTILINE):
                        name = f.stem
                        word_count = len(name.split())
                        if word_count >= min_words:
                            entities.append(name)

            total_linked = 0
            total_notes = 0
            results: list[tuple[str, int, tuple[str, ...]]] = []

            console.print(f"\n[bold]Wikify: scanning {len(entities)} entities (min-words={min_words})...[/bold]")

            for name in entities:
                result = inject_backlinks(
                    vault_path,
                    name,
                    dry_run=dry_run,
                )
                if result.notes_linked > 0:
                    results.append((name, result.notes_linked, result.linked_files))
                    total_linked += result.notes_linked
                    total_notes = max(total_notes, result.notes_scanned)

            if not results:
                console.print("[green]All entity mentions are already wikilinked.[/green]")
                return

            # Report
            action = "Would link" if dry_run else "Linked"
            console.print(f"\n[bold]{action} {total_linked} plain-text mentions across {len(results)} entities:[/bold]")
            for name, count, files in sorted(results, key=lambda x: -x[1]):
                console.print(f"  [cyan]{name}[/cyan] → {count} notes")
                if entity_name:  # Show details only for single-entity mode
                    for f in files:
                        console.print(f"    {f}")

            if dry_run:
                console.print(f"\n[yellow]Dry run — no files changed. Run without --dry-run to apply.[/yellow]")

        except BrainOpsError as error:
            handle_error(error)

    @app.command("semantic-relations")
    def semantic_relations_command(
        entity_name: str = typer.Argument(..., help="Entity to analyze."),
        config_path: Path | None = typer.Option(None, "--config", help="Path to vault config YAML."),
        fix: bool = typer.Option(False, "--fix", help="Auto-add high-confidence existing relation suggestions."),
        bidirectional: bool = typer.Option(False, "--bidirectional", help="Also add reciprocal links in destination entity notes."),
        min_confidence: float = typer.Option(0.7, "--min-confidence", help="Minimum confidence for --fix."),
    ) -> None:
        """Suggest semantic relationships and missing entity candidates for an entity."""
        try:
            import re
            from brain_ops.domains.knowledge.semantic_relations import (
                add_semantic_related_links,
                build_reciprocal_semantic_suggestion,
                suggest_semantic_relations,
            )
            from brain_ops.frontmatter import split_frontmatter
            from brain_ops.interfaces.cli.runtime import load_validated_vault

            vault = load_validated_vault(config_path, dry_run=False)
            knowledge_path = vault.config.folder_path("knowledge")
            note_path = knowledge_path / f"{entity_name}.md"
            if not note_path.exists():
                console.print(f"[red]Entity '{entity_name}' not found.[/red]")
                return

            entity_notes = {}
            for path in knowledge_path.glob("*.md"):
                text = path.read_text(encoding="utf-8")
                if not re.search(r"^entity:\s*true", text, re.MULTILINE):
                    continue
                fm, body = split_frontmatter(text)
                entity_notes[path.stem] = (path, fm, body)

            text = note_path.read_text(encoding="utf-8")
            suggestions = suggest_semantic_relations(entity_name, text, entity_notes)
            existing = [s for s in suggestions if s.exists]
            missing = [s for s in suggestions if not s.exists]

            console.print(f"\n[bold]Semantic relation report[/bold]: {entity_name}")
            console.print(f"  Existing relation suggestions: {len(existing)}")
            console.print(f"  Missing entity candidates: {len(missing)}")

            if existing:
                console.print("\n  [cyan]Existing entities to relate:[/cyan]")
                for s in existing[:20]:
                    console.print(f"    + [[{s.name}]] — {s.predicate} ({s.confidence:.2f}) — {s.reason}")

            if missing:
                console.print("\n  [yellow]Candidate entities to create:[/yellow]")
                for s in missing[:20]:
                    console.print(f"    + [[{s.name}]] ({s.confidence:.2f}) — {s.reason}")

            if fix:
                updated, applied = add_semantic_related_links(text, suggestions, min_confidence=min_confidence)
                if applied:
                    note_path.write_text(updated, encoding="utf-8")
                    console.print(f"\n[green]Applied {len(applied)} semantic relation links.[/green]")

                    if bidirectional:
                        reciprocal_count = 0
                        for suggestion in applied:
                            target = entity_notes.get(suggestion.name)
                            if target is None:
                                continue
                            target_path = target[0]
                            target_text = target_path.read_text(encoding="utf-8")
                            reciprocal = build_reciprocal_semantic_suggestion(entity_name, suggestion)
                            target_updated, target_applied = add_semantic_related_links(
                                target_text,
                                [reciprocal],
                                min_confidence=min_confidence,
                            )
                            if target_applied:
                                target_path.write_text(target_updated, encoding="utf-8")
                                reciprocal_count += len(target_applied)
                        console.print(f"[green]Applied {reciprocal_count} reciprocal semantic links.[/green]")
                elif bidirectional:
                    console.print("\n[yellow]No high-confidence links to apply, so no reciprocal links were added.[/yellow]")
                else:
                    console.print("\n[yellow]No high-confidence existing relation links to apply.[/yellow]")
            elif existing:
                console.print("\n[yellow]Run with --fix to add high-confidence existing relation links.[/yellow]")

        except BrainOpsError as error:
            handle_error(error)


__all__ = ["register_note_and_knowledge_commands"]
