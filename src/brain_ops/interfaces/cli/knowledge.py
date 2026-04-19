"""CLI orchestration helpers for knowledge/vault commands."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from rich.table import Table

from brain_ops.application import (
    execute_audit_vault_workflow,
    execute_compile_knowledge_workflow,
    execute_enrich_entity_workflow,
    execute_entity_index_workflow,
    execute_entity_relations_workflow,
    execute_ingest_source_workflow,
    execute_query_knowledge_workflow,
    execute_normalize_frontmatter_workflow,
    execute_process_inbox_workflow,
    execute_search_knowledge_workflow,
    execute_weekly_review_workflow,
)
from brain_ops.interfaces.cli.presenters import print_rendered_with_operations
from brain_ops.interfaces.cli.runtime import load_event_sink, load_runtime_config, load_validated_vault
from brain_ops.reporting_knowledge import (
    render_inbox_report,
    render_normalize_frontmatter,
    render_vault_audit,
    render_weekly_review,
)


def run_process_inbox_command(
    *,
    config_path: Path | None,
    dry_run: bool,
    write_report: bool,
    improve_structure: bool,
):
    return execute_process_inbox_workflow(
        config_path=config_path,
        dry_run=dry_run,
        write_report=write_report,
        improve_structure=improve_structure,
        load_vault=load_validated_vault,
        event_sink=load_event_sink(),
    )


def run_weekly_review_command(
    *,
    config_path: Path | None,
    dry_run: bool,
    stale_days: int,
    write_report: bool,
):
    return execute_weekly_review_workflow(
        config_path=config_path,
        dry_run=dry_run,
        stale_days=stale_days,
        write_report=write_report,
        load_vault=load_validated_vault,
        event_sink=load_event_sink(),
    )


def run_audit_vault_command(
    *,
    config_path: Path | None,
    write_report: bool,
):
    return execute_audit_vault_workflow(
        config_path=config_path,
        write_report=write_report,
        load_vault=load_validated_vault,
        event_sink=load_event_sink(),
    )


def run_normalize_frontmatter_command(
    *,
    config_path: Path | None,
    dry_run: bool,
):
    return execute_normalize_frontmatter_workflow(
        config_path=config_path,
        dry_run=dry_run,
        load_vault=load_validated_vault,
        event_sink=load_event_sink(),
    )


def present_process_inbox_command(
    console: Console,
    *,
    config_path: Path | None,
    dry_run: bool,
    write_report: bool,
    improve_structure: bool,
) -> None:
    summary = run_process_inbox_command(
        config_path=config_path,
        dry_run=dry_run,
        write_report=write_report,
        improve_structure=improve_structure,
    )
    print_rendered_with_operations(console, summary.operations, render_inbox_report(summary))


def present_weekly_review_command(
    console: Console,
    *,
    config_path: Path | None,
    dry_run: bool,
    stale_days: int,
    write_report: bool,
) -> None:
    summary = run_weekly_review_command(
        config_path=config_path,
        dry_run=dry_run,
        stale_days=stale_days,
        write_report=write_report,
    )
    print_rendered_with_operations(console, summary.operations, render_weekly_review(summary))


def present_audit_vault_command(
    console: Console,
    *,
    config_path: Path | None,
    write_report: bool,
) -> None:
    summary = run_audit_vault_command(config_path=config_path, write_report=write_report)
    print_rendered_with_operations(console, summary.operations, render_vault_audit(summary))


def present_normalize_frontmatter_command(
    console: Console,
    *,
    config_path: Path | None,
    dry_run: bool,
) -> None:
    summary = run_normalize_frontmatter_command(config_path=config_path, dry_run=dry_run)
    print_rendered_with_operations(console, summary.operations, render_normalize_frontmatter(summary))


def present_ingest_source_command(
    console: Console,
    *,
    text: str | None,
    url: str | None,
    title: str | None,
    config_path: Path | None,
    use_llm: bool,
    llm_provider: str | None,
    as_json: bool,
) -> None:
    llm_json_fn = None
    if use_llm:
        llm_json_fn = _resolve_llm_json_fn(llm_provider, task="extract")

    result = execute_ingest_source_workflow(
        text=text,
        url=url,
        title=title,
        config_path=config_path,
        use_llm=use_llm,
        load_vault=load_validated_vault,
        llm_generate_json_fn=llm_json_fn,
        event_sink=load_event_sink(),
    )
    if as_json:
        console.print_json(data=result.to_dict())
        return
    console.print(f"Ingested: {result.plan.source_title}")
    if result.source_note_path:
        console.print(f"Note: {result.source_note_path}")
    if result.plan.entities:
        console.print(f"Entities mentioned: {', '.join(e.name for e in result.plan.entities)}")
    console.print(f"LLM used: {'Yes' if result.used_llm else 'No'}")
    try:
        execute_compile_knowledge_workflow(
            config_path=config_path,
            db_path=None,
            load_vault=load_validated_vault,
        )
    except Exception:
        pass


def present_search_knowledge_command(
    console: Console,
    *,
    query: str,
    config_path: Path | None,
    entity_only: bool,
    max_results: int,
    as_json: bool,
) -> None:
    results = execute_search_knowledge_workflow(
        query=query,
        config_path=config_path,
        entity_only=entity_only,
        max_results=max_results,
        load_vault=load_validated_vault,
    )
    if as_json:
        console.print_json(data=[r.to_dict() for r in results])
        return
    if not results:
        console.print(f"No results for '{query}'.")
        return
    table = Table(title=f"Search: {query}")
    table.add_column("Title")
    table.add_column("Type")
    table.add_column("Match")
    for r in results:
        table.add_row(r.title, r.entity_type or "-", r.match_context[:80])
    console.print(table)


def present_compile_knowledge_command(
    console: Console,
    *,
    config_path: Path | None,
    db_path: Path | None,
    as_json: bool,
) -> None:
    result = execute_compile_knowledge_workflow(
        config_path=config_path,
        db_path=db_path,
        load_vault=load_validated_vault,
    )
    if as_json:
        console.print_json(data=result.to_dict())
        return
    console.print(f"Compiled {result.total_entities} entities and {len(result.compile_result.relations)} relations to {result.db_path}")


def present_entity_index_command(
    console: Console,
    *,
    config_path: Path | None,
    as_json: bool,
) -> None:
    result = execute_entity_index_workflow(
        config_path=config_path,
        load_vault=load_validated_vault,
    )
    if as_json:
        console.print_json(data=result.to_dict())
        return
    console.print(result.markdown)


def present_entity_relations_command(
    console: Console,
    *,
    entity_name: str,
    config_path: Path | None,
    as_json: bool,
) -> None:
    result = execute_entity_relations_workflow(
        entity_name=entity_name,
        config_path=config_path,
        load_vault=load_validated_vault,
    )
    if as_json:
        console.print_json(data=result.to_dict())
        return
    console.print(result.markdown)


def _resolve_llm_text_fn(llm_provider: str | None, *, task: str = "extract"):
    try:
        if llm_provider:
            from brain_ops.ai.llm_client import llm_generate_text, resolve_provider
            provider = resolve_provider(llm_provider)
            return lambda prompt: llm_generate_text(provider, prompt)
        from brain_ops.ai.llm_client import resolve_smart_router
        router = resolve_smart_router()
        return lambda prompt: router.generate_text(prompt, task=task)
    except Exception:
        return None


def _resolve_llm_json_fn(llm_provider: str | None, *, task: str = "extract"):
    try:
        if llm_provider:
            from brain_ops.ai.llm_client import llm_generate_json, resolve_provider
            provider = resolve_provider(llm_provider)
            return lambda prompt: llm_generate_json(provider, prompt)
        from brain_ops.ai.llm_client import resolve_smart_router
        router = resolve_smart_router()
        return lambda prompt: router.generate_json(prompt, task=task)
    except Exception:
        return None


def present_enrich_entity_command(
    console: Console,
    *,
    entity_name: str,
    new_info: str | None,
    url: str | None,
    auto_generate: bool,
    config_path: Path | None,
    llm_provider: str | None,
    as_json: bool,
) -> None:
    task = "generate" if auto_generate else "enrich"
    result = execute_enrich_entity_workflow(
        entity_name=entity_name,
        new_info=new_info,
        url=url,
        auto_generate=auto_generate,
        config_path=config_path,
        load_vault=load_validated_vault,
        llm_generate_text_fn=_resolve_llm_text_fn(llm_provider, task=task),
    )
    if as_json:
        console.print_json(data=result.to_dict())
        return
    if result.had_existing_content:
        console.print(f"Enriched '{result.entity_name}' with new content.")
    else:
        console.print(f"Generated initial content for '{result.entity_name}'.")
    if result.sections_repaired:
        console.print(f"Repaired empty sections: {', '.join(result.sections_repaired)}")
    try:
        execute_compile_knowledge_workflow(
            config_path=config_path, db_path=None, load_vault=load_validated_vault,
        )
    except Exception:
        pass


def present_query_knowledge_command(
    console: Console,
    *,
    query: str,
    config_path: Path | None,
    file_back: bool,
    llm_provider: str | None,
    as_json: bool,
) -> None:
    result = execute_query_knowledge_workflow(
        query=query,
        config_path=config_path,
        file_back=file_back,
        load_vault=load_validated_vault,
        llm_generate_text_fn=_resolve_llm_text_fn(llm_provider, task="query"),
    )
    if as_json:
        console.print_json(data=result.to_dict())
        return
    console.print(f"\n{result.answer}\n")
    if result.sources_used:
        console.print(f"Sources: {', '.join(result.sources_used)}")
    if result.filed_back:
        console.print(f"Answer filed at: {result.filed_path}")


def present_registry_lint_command(
    console: Console,
    *,
    config_path: Path | None,
    as_json: bool,
) -> None:
    from brain_ops.domains.knowledge.registry import load_entity_registry
    from brain_ops.domains.knowledge.registry_lint import lint_registry

    vault = load_validated_vault(config_path, dry_run=False)
    registry_path = Path(vault.config.vault_path) / ".brain-ops" / "entity_registry.json"
    registry = load_entity_registry(registry_path)
    result = lint_registry(registry)
    if as_json:
        console.print_json(data=result.to_dict())
        return
    console.print(f"Registry: {result.total_entities} entities ({result.canonical_count} canonical, {result.candidate_count} candidate, {result.mention_count} mention)")
    if result.total_issues == 0:
        console.print("No issues found.")
        return
    if result.low_confidence:
        console.print(f"\nLow confidence (2+ sources but still low): {', '.join(result.low_confidence)}")
    if result.no_relations:
        console.print(f"\nNo relations: {', '.join(result.no_relations)}")
    if result.high_source_not_canonical:
        console.print(f"\nHigh source count but not canonical: {', '.join(result.high_source_not_canonical)}")
    if result.missing_subtype:
        console.print(f"\nMissing subtype: {', '.join(result.missing_subtype)}")
    if result.promotable_to_candidate:
        console.print(f"\nPromotable to candidate: {', '.join(result.promotable_to_candidate)}")
    if result.promotable_to_canonical:
        console.print(f"\nPromotable to canonical: {', '.join(result.promotable_to_canonical)}")


def present_replay_extractions_command(
    console: Console,
    *,
    config_path: Path | None,
    as_json: bool,
) -> None:
    from brain_ops.domains.knowledge.extraction_store import load_extraction_records

    vault = load_validated_vault(config_path, dry_run=False)
    extractions_dir = Path(vault.config.vault_path) / ".brain-ops" / "extractions"
    records = load_extraction_records(extractions_dir)
    if as_json:
        console.print_json(data=[r.to_dict() for r in records])
        return
    if not records:
        console.print("No extraction records found.")
        return
    from rich.table import Table

    table = Table(title=f"Extraction Records ({len(records)})")
    table.add_column("Date")
    table.add_column("Title")
    table.add_column("Type")
    table.add_column("URL")
    for r in records:
        table.add_row(
            r.created_at[:19],
            r.source_title[:50],
            r.source_type,
            str(r.source_url or "-")[:50],
        )
    console.print(table)


def present_lint_schemas_command(
    console: Console,
    *,
    config_path: Path | None,
    subtype: str | None,
    domain: str | None,
    as_json: bool,
    naming: bool,
    strict: bool,
) -> int:
    """Report schema + naming violations across the vault. Never mutates anything."""
    from brain_ops.domains.knowledge.epistemology import EPISTEMIC_GATED_DOMAINS
    from brain_ops.domains.knowledge.naming_rules import check_vault_naming
    from brain_ops.domains.knowledge.schema_validator import (
        load_frontmatter_from_vault,
        validate_vault_notes,
    )

    vault = load_validated_vault(config_path, dry_run=False)
    vault_path = Path(vault.config.vault_path)
    notes = load_frontmatter_from_vault(vault_path)

    # Optional filters (applied before validation for efficient JSON output)
    if subtype:
        notes = [n for n in notes if n[2].get("subtype") == subtype]
    if domain:
        notes = [n for n in notes if n[2].get("domain") == domain]

    report = validate_vault_notes(notes, gated_domains=EPISTEMIC_GATED_DOMAINS)

    naming_violations = []
    if naming:
        naming_violations = check_vault_naming(
            (name, fm) for (_, name, fm) in notes
        )

    payload: dict[str, object] = {
        "schema": report.to_dict(),
        "naming_violations": [v.to_dict() for v in naming_violations],
    }

    if as_json:
        console.print_json(data=payload)
    else:
        console.print(f"[bold]Schema lint[/bold] — {report.total_notes} notes checked")
        console.print(
            f"  errors: {report.error_count}   "
            f"warnings: {report.warning_count}   "
            f"info: {report.info_count}"
        )
        if report.per_subtype:
            console.print("\n[bold]Per subtype[/bold]")
            table = Table()
            table.add_column("Subtype")
            table.add_column("Notes", justify="right")
            table.add_column("With violations", justify="right")
            for st, stats in sorted(
                report.per_subtype.items(),
                key=lambda kv: -kv[1]["total"],
            ):
                table.add_row(st, str(stats["total"]), str(stats["violations"]))
            console.print(table)
        if naming:
            console.print(f"\n[bold]Naming violations[/bold]: {len(naming_violations)}")
            for v in naming_violations[:30]:
                console.print(f"  [{v.severity}] {v.note_name} — {v.rule}: {v.message}")
            if len(naming_violations) > 30:
                console.print(f"  ... ({len(naming_violations) - 30} more)")

    if strict and report.error_count > 0:
        return 1
    return 0


def present_normalize_domain_command(
    console: Console,
    *,
    config_path: Path | None,
    apply: bool,
    only_transition: list[str] | None,
    exclude_file: Path | None,
    report_path: Path | None,
    as_json: bool,
) -> None:
    """Subfase 1.1 / 1.2 — normalize non-canonical domain aliases.

    Default mode is DRY-RUN. Pass --apply to actually write changes.
    """
    import json as _json

    from brain_ops.domains.knowledge.consolidation import (
        apply_normalize_domain,
        plan_normalize_domain,
    )

    vault = load_validated_vault(config_path, dry_run=not apply)
    vault_path = Path(vault.config.vault_path)

    report = plan_normalize_domain(vault_path)

    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            _json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    if as_json and not apply:
        console.print_json(data=report.to_dict())
        return

    # Human-readable summary
    console.print(
        f"[bold]Normalize domain[/bold] — vault: {vault_path}"
    )
    console.print(
        f"  scanned: {report.total_notes_scanned}   "
        f"already canonical: {report.notes_already_canonical}   "
        f"without domain: {report.notes_without_domain}"
    )
    console.print(f"  [bold]proposed changes: {report.total_changes}[/bold]")

    transitions = report.counts_by_transition()
    if transitions:
        console.print("\n[bold]Transitions[/bold]")
        tbl = Table()
        tbl.add_column("From → To")
        tbl.add_column("Count", justify="right")
        for t, c in sorted(transitions.items(), key=lambda kv: -kv[1]):
            tbl.add_row(t, str(c))
        console.print(tbl)

    if not apply:
        console.print(
            "\n[yellow]DRY-RUN[/yellow] — no files modified. "
            "Pass --apply to write changes."
        )
        if report_path:
            console.print(f"Full report written to: {report_path}")
        return

    # APPLY path
    exclude: list[str] = []
    if exclude_file and exclude_file.exists():
        exclude = [
            line.strip() for line in exclude_file.read_text().splitlines()
            if line.strip() and not line.startswith("#")
        ]

    transitions_filter = only_transition if only_transition else None

    result = apply_normalize_domain(
        vault_path, report,
        exclude=exclude,
        transitions_filter=transitions_filter,
    )
    console.print(
        f"\n[green]APPLIED[/green] — "
        f"wrote {result['applied_count']} notes   "
        f"skipped (excluded): {len(result['skipped_excluded'])}   "
        f"skipped (filter): {len(result['skipped_filter'])}"
    )

    if as_json:
        console.print_json(data=result)


def present_fill_domain_command(
    console: Console,
    *,
    config_path: Path | None,
    apply: bool,
    exclude: list[str] | None,
    report_path: Path | None,
    as_json: bool,
) -> None:
    """Subfase 1.4a — fill missing `domain:` using high-confidence heuristics."""
    import json as _json

    from brain_ops.domains.knowledge.consolidation import (
        apply_fill_domain,
        plan_fill_domain,
    )

    vault = load_validated_vault(config_path, dry_run=not apply)
    vault_path = Path(vault.config.vault_path)

    report = plan_fill_domain(vault_path)

    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            _json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    if as_json and not apply:
        console.print_json(data=report.to_dict())
        return

    console.print(
        f"[bold]Fill domain (Subfase 1.4a)[/bold] — vault: {vault_path}\n"
        f"  scanned: {report.total_notes_scanned}   "
        f"already have domain: {report.notes_already_have_domain}   "
        f"[bold]auto-apply: {report.auto_apply_count}[/bold]   "
        f"deferred: {report.deferred_count}   "
        f"skipped: {report.skipped_count}"
    )

    counts_rule = report.counts_by_rule()
    if counts_rule:
        console.print("\n[bold]Counts by rule[/bold]")
        for r, c in sorted(counts_rule.items(), key=lambda kv: -kv[1]):
            console.print(f"  {c:4d}  {r}")

    by_sub = report.counts_by_subtype(auto_only=True)
    if by_sub:
        console.print("\n[bold]Auto-apply: subtype → domain[/bold]")
        tbl = Table()
        tbl.add_column("Subtype")
        tbl.add_column("Domain")
        tbl.add_column("Count", justify="right")
        for st in sorted(by_sub):
            for dm, cnt in sorted(by_sub[st].items()):
                tbl.add_row(st, dm, str(cnt))
        console.print(tbl)

    if not apply:
        console.print(
            "\n[yellow]DRY-RUN[/yellow] — no files modified. "
            "Pass --apply to write changes."
        )
        if report_path:
            console.print(f"Report: {report_path}")
        return

    result = apply_fill_domain(vault_path, report, exclude=exclude or [])
    console.print(
        f"\n[green]APPLIED[/green]\n"
        f"  Filled:  {result['applied_count']}\n"
        f"  Skipped: {len(result['skipped'])}"
    )


def present_fix_capitalization_command(
    console: Console,
    *,
    config_path: Path | None,
    apply: bool,
    exclude: list[str] | None,
    report_path: Path | None,
    as_json: bool,
) -> None:
    """Subfase 1.3 — fix capitalization violations in entity names."""
    import json as _json

    from brain_ops.domains.knowledge.consolidation import (
        apply_fix_capitalization,
        plan_fix_capitalization,
    )

    vault = load_validated_vault(config_path, dry_run=not apply)
    vault_path = Path(vault.config.vault_path)

    report = plan_fix_capitalization(vault_path)

    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            _json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    if as_json and not apply:
        console.print_json(data=report.to_dict())
        return

    console.print(
        f"[bold]Fix capitalization[/bold] — vault: {vault_path}\n"
        f"  scanned: {report.total_notes_scanned}   "
        f"applicable: {report.applicable_count}   "
        f"blocked: {report.blocked_count}"
    )

    if report.fixes:
        tbl = Table()
        tbl.add_column("Current")
        tbl.add_column("Proposed")
        tbl.add_column("Body refs", justify="right")
        tbl.add_column("Related", justify="right")
        tbl.add_column("Status")
        for f in report.fixes:
            status = "ok" if f.can_apply else f"BLOCKED: {f.error_message}"
            tbl.add_row(
                f.old_name,
                f.new_name,
                str(f.body_wikilink_mentions),
                str(len(f.related_entries)),
                status,
            )
        console.print(tbl)

    if not apply:
        console.print(
            "\n[yellow]DRY-RUN[/yellow] — no files modified. "
            "Pass --apply to write changes."
        )
        if report_path:
            console.print(f"Report: {report_path}")
        return

    result = apply_fix_capitalization(vault_path, report, exclude=exclude or [])
    console.print(
        f"\n[green]APPLIED[/green]\n"
        f"  Fixes applied: {len(result['applied'])}\n"
        f"  Skipped:       {len(result['skipped'])}"
    )
    for a in result["applied"]:
        console.print(
            f"  {a['old_name']} → {a['new_name']}  "
            f"(body: {a['body_files_updated']}, related: {a['related_files_updated']})"
        )
    for s in result["skipped"]:
        console.print(f"  [yellow]skip[/yellow] {s}")


def present_disambiguate_bare_command(
    console: Console,
    *,
    config_path: Path | None,
    bare_name: str,
    discriminator: str,
    apply: bool,
    report_path: Path | None,
    as_json: bool,
) -> None:
    """Subfase 1.5 — convert a bare-name entity into a disambiguation_page.

    Dry-run by default. Pass --apply to actually write changes.
    """
    import json as _json

    from brain_ops.domains.knowledge.consolidation import (
        apply_disambiguate_bare,
        plan_disambiguate_bare,
    )

    vault = load_validated_vault(config_path, dry_run=not apply)
    vault_path = Path(vault.config.vault_path)

    report = plan_disambiguate_bare(vault_path, bare_name, discriminator)

    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            _json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    if as_json and not apply:
        console.print_json(data=report.to_dict())
        return

    console.print(
        f"[bold]Disambiguate bare name[/bold]\n"
        f"  Bare:          [cyan]{report.bare_name}[/cyan]\n"
        f"  New canonical: [green]{report.new_canonical_name}[/green]\n"
        f"  Vault:         {vault_path}"
    )

    if not report.can_apply:
        console.print(f"[red]Cannot apply: {report.error_message}[/red]")
        return

    console.print(f"\n[bold]Variants after change:[/bold]")
    for v in report.existing_variants:
        console.print(f"  - {v}")

    console.print(
        f"\n[bold]Incoming references:[/bold]\n"
        f"  body wikilinks:         {report.body_wikilink_mentions} in "
        f"{len(report.body_wikilink_files)} files\n"
        f"  frontmatter `related:`  {len(report.related_entries)} files"
    )

    if report.sample_body_changes:
        console.print(f"\n[bold]Sample body contexts (first 8):[/bold]")
        for s in report.sample_body_changes:
            console.print(f"  {s}")

    console.print(f"\n[bold]Disambig page preview:[/bold]")
    console.print(report.disambig_page_preview)

    if not apply:
        console.print(
            "\n[yellow]DRY-RUN[/yellow] — no files modified. "
            "Pass --apply to write changes."
        )
        if report_path:
            console.print(f"Report: {report_path}")
        return

    result = apply_disambiguate_bare(vault_path, report)
    if not result.get("applied"):
        console.print(f"[red]Apply failed: {result.get('error')}[/red]")
        return
    console.print(
        f"\n[green]APPLIED[/green]\n"
        f"  Renamed:                {result['counts']['renamed']}\n"
        f"  Body wikilinks updated: {result['counts']['body_wikilinks_updated']}\n"
        f"  Related entries updated:{result['counts']['related_entries_updated']}\n"
        f"  Disambig page created:  {result['counts']['disambig_page_created']}"
    )


def present_migrate_knowledge_db_command(
    console: Console,
    *,
    config_path: Path | None,
    dry_run: bool,
    status: bool,
    skip_backup: bool,
    as_json: bool,
    force_migrate: bool = False,
) -> None:
    """Apply pending schema migrations to knowledge.db. Creates an automatic backup.

    --force-migrate bypasses the test-runner / env var guards. It still
    creates a backup unless --skip-backup. Exceptional use only — the normal
    user flow never needs this flag. See docs/operations/MIGRATIONS.md.
    """
    from brain_ops.storage.sqlite.migrations import (
        migrate_knowledge_db_with_backup,
        migration_status,
    )

    vault = load_validated_vault(config_path, dry_run=False)
    db_path = Path(vault.config.vault_path) / ".brain-ops" / "knowledge.db"

    if status:
        result = migration_status(db_path)
        if as_json:
            console.print_json(data=result.to_dict())
            return
        console.print(f"DB path: {db_path}")
        console.print(f"Applied: {list(result.applied) or '(none)'}")
        if result.pending:
            console.print("\nPending:")
            for version, description in result.pending:
                console.print(f"  {version:>3}  {description}")
        else:
            console.print("Pending: (none)")
        return

    result = migrate_knowledge_db_with_backup(
        db_path,
        dry_run=dry_run,
        skip_backup=skip_backup,
        force=force_migrate,
    )
    if as_json:
        console.print_json(data=result)
        return

    console.print(f"DB path: {db_path}")
    console.print(f"Status: [bold]{result['status']}[/bold]")
    if result.get("backup_path"):
        console.print(f"Backup: {result['backup_path']}")
    if result["status"] == "blocked":
        console.print(
            f"[yellow]Blocked by safety guard: {result.get('block_reason')}.[/yellow]"
        )
        console.print(
            "Unset BRAIN_OPS_NO_MIGRATE or pass --force-migrate to override."
        )
        console.print("\nPending migrations (not applied):")
        for p in result["pending"]:
            console.print(f"  {p['version']:>3}  {p['description']}")
    elif result["status"] == "dry-run":
        console.print("\nPending migrations (not applied):")
        for p in result["pending"]:
            console.print(f"  {p['version']:>3}  {p['description']}")
    elif result["status"] == "migrated":
        console.print("\nApplied migrations:")
        for a in result["applied"]:
            console.print(f"  {a['version']:>3}  {a['description']}  @ {a['applied_at']}")


def present_query_relations_command(
    console: Console,
    *,
    config_path: Path | None,
    from_entity: str | None,
    to_entity: str | None,
    predicate: str | None,
    include_legacy: bool,
    limit: int | None,
    as_json: bool,
) -> None:
    """Subfase 2.0 — query the typed-relations graph (SQLite)."""
    import json as _json

    from brain_ops.domains.knowledge.relations_query import query_relations

    if from_entity is None and to_entity is None and predicate is None:
        console.print(
            "[red]error[/red]: pass at least one of --from, --to, or --predicate."
        )
        raise typer.Exit(code=2)

    vault = load_validated_vault(config_path, dry_run=False)
    db_path = Path(vault.config.vault_path) / ".brain-ops" / "knowledge.db"

    rows = query_relations(
        db_path,
        from_entity=from_entity,
        to_entity=to_entity,
        predicate=predicate,
        include_legacy=include_legacy,
        limit=limit,
    )

    if as_json:
        console.print_json(data=[r.to_dict() for r in rows])
        return

    if not rows:
        console.print("[yellow]No results.[/yellow]")
        return

    tbl = Table()
    tbl.add_column("source")
    tbl.add_column("predicate")
    tbl.add_column("target")
    tbl.add_column("confidence")
    tbl.add_column("type")
    for r in rows:
        kind = "typed" if r.is_typed else "[dim]legacy[/dim]"
        tbl.add_row(
            r.source_entity,
            r.predicate or "[dim]—[/dim]",
            r.target_entity,
            r.confidence or "[dim]—[/dim]",
            kind,
        )
    console.print(tbl)
    console.print(f"[dim]{len(rows)} result(s).[/dim]")


def present_show_entity_relations_command(
    console: Console,
    *,
    config_path: Path | None,
    entity: str,
    only_typed: bool,
    only_legacy: bool,
    all_legacy: bool,
    as_json: bool,
) -> None:
    """Subfase 2.0 — show all relations (typed + legacy, in+out) for one entity."""
    from brain_ops.domains.knowledge.relations_query import summarize_entity_relations

    vault = load_validated_vault(config_path, dry_run=False)
    db_path = Path(vault.config.vault_path) / ".brain-ops" / "knowledge.db"
    summary = summarize_entity_relations(db_path, entity)

    if as_json:
        console.print_json(data=summary.to_dict())
        return

    # Render human-readable output
    console.print(f"[bold]=== {entity} — outgoing ===[/bold]")

    if not only_legacy:
        if summary.typed_by_predicate:
            for predicate in sorted(summary.typed_by_predicate):
                rels = summary.typed_by_predicate[predicate]
                console.print(f"\n[bold cyan]{predicate}[/bold cyan]:")
                for r in rels:
                    conf = f" [dim]({r.confidence})[/dim]" if r.confidence and r.confidence != "medium" else ""
                    console.print(f"  - {r.target_entity}{conf}")
        else:
            console.print("\n[dim]No typed relations.[/dim]")

    if not only_typed:
        if summary.legacy:
            console.print(f"\n[bold]=== {entity} — legacy (related:, untyped) ===[/bold]")
            legacy_to_show = summary.legacy if all_legacy else summary.legacy[:15]
            for r in legacy_to_show:
                console.print(f"  - {r.target_entity}")
            hidden = len(summary.legacy) - len(legacy_to_show)
            if hidden > 0:
                console.print(f"  [dim](... {hidden} more, use --all to see)[/dim]")

    if summary.incoming_typed_by_predicate or summary.incoming_legacy:
        console.print(f"\n[bold]=== {entity} — incoming ===[/bold]")
        if not only_legacy:
            for predicate in sorted(summary.incoming_typed_by_predicate):
                rels = summary.incoming_typed_by_predicate[predicate]
                console.print(f"\n[bold cyan]{predicate}[/bold cyan] (← from):")
                for r in rels:
                    console.print(f"  - {r.source_entity}")
        if not only_typed and summary.incoming_legacy:
            console.print("\n[dim]incoming legacy:[/dim]")
            incoming_to_show = summary.incoming_legacy if all_legacy else summary.incoming_legacy[:10]
            for r in incoming_to_show:
                console.print(f"  - {r.source_entity}")
            hidden = len(summary.incoming_legacy) - len(incoming_to_show)
            if hidden > 0:
                console.print(f"  [dim](... {hidden} more)[/dim]")

    # Footer summary
    console.print(
        f"\n[dim]{summary.typed_count} typed · {summary.legacy_count} legacy · "
        f"{summary.incoming_typed_count} incoming typed · "
        f"{len(summary.incoming_legacy)} incoming legacy[/dim]"
    )


import typer  # noqa: E402 — used above by present_query_relations_command


def present_apply_relations_batch_command(
    console: Console,
    *,
    config_path: Path | None,
    batch_name: str,
    apply: bool,
    allow_mentions: bool,
    as_json: bool,
) -> None:
    """Campaña 2.1 Paso 3 — apply a reviewed batch of typed-relation proposals.

    Default is dry-run. Pass `--apply` to actually write. Frontmatter-only;
    body is never mutated; MISSING_ENTITY targets are refused unless
    `--allow-mentions` is explicit.
    """
    import json as _json

    from brain_ops.domains.knowledge.relations_applier import (
        BatchLoadError, apply_batch,
    )

    vault = load_validated_vault(config_path, dry_run=not apply)
    try:
        report = apply_batch(
            batch_name, vault,
            dry_run=not apply,
            allow_mentions=allow_mentions,
        )
    except BatchLoadError as exc:
        console.print(f"[red]error[/red]: {exc}")
        raise typer.Exit(code=2)

    payload = report.to_dict()
    if as_json:
        console.print_json(data=payload)
        return

    mode = "DRY-RUN" if report.dry_run else "APPLIED"
    banner_color = "yellow" if report.dry_run else "green"
    if report.aborted:
        banner_color = "red"
        mode = "ABORTED"
    console.print(
        f"[bold {banner_color}]{mode}[/bold {banner_color}] "
        f"batch={report.batch_name}  "
        f"entities={len(report.entities)}  "
        f"applied={report.total_applied}  "
        f"skipped={report.total_skipped}"
    )
    if report.aborted:
        console.print(f"[red]ABORT REASON:[/red] {report.abort_reason}")
    if report.snapshot_path:
        console.print(f"[dim]snapshot: {report.snapshot_path}[/dim]")

    tbl = Table(title=f"Per-entity plan ({mode})")
    tbl.add_column("entity")
    tbl.add_column("baseline\ntyped", justify="right")
    tbl.add_column("proposal\ntotal", justify="right")
    tbl.add_column("to\napply", justify="right")
    tbl.add_column("already\ntyped", justify="right")
    tbl.add_column("missing\nentity", justify="right")
    tbl.add_column("not\napproved", justify="right")
    tbl.add_column("other\nskip", justify="right")
    for e in report.entities:
        tbl.add_row(
            e.entity,
            str(e.baseline_typed),
            str(e.proposal_total),
            str(len(e.applied_ids)),
            str(len(e.skipped.get("already_typed", []))),
            str(len(e.skipped.get("missing_entity", []))),
            str(len(e.skipped.get("not_approved", []))),
            str(sum(len(v) for k, v in e.skipped.items()
                    if k not in ("already_typed", "missing_entity", "not_approved"))),
        )
    console.print(tbl)

    if report.missing_entity_queue:
        console.print(
            f"\n[yellow]Missing entities (creation queue):[/yellow] "
            f"{len(report.missing_entity_queue)}"
        )
        for name in report.missing_entity_queue[:15]:
            console.print(f"  - {name}")
        if len(report.missing_entity_queue) > 15:
            console.print(
                f"  [dim]... {len(report.missing_entity_queue) - 15} more[/dim]"
            )

    if report.aborted:
        console.print(
            f"\n[bold red]ROLLBACK GUIDANCE[/bold red] — batch halted mid-run.\n"
            f"No auto-restore performed. Review the state below and decide "
            f"whether to keep the partial apply or roll back manually."
        )
        console.print(f"Entities applied before abort: {report.applied_entities}")
        console.print(f"Entity that aborted: {report.aborted_entity}")
        console.print(f"Entities not processed: {report.not_processed_entities}")
        console.print("\n[bold]Manual rollback commands:[/bold]")
        for line in report.rollback_instructions():
            console.print(f"  {line}")


def present_propose_relations_command(
    console: Console,
    *,
    config_path: Path | None,
    entity: str,
    include_existing: bool,
    output: Path | None,
    stdout: bool,
    as_json: bool,
) -> None:
    """Campaña 2.1 Paso 2 — emit a read-only proposal of typed relations.

    Never mutates the vault note. Writes a YAML proposal file (default:
    `<vault>/.brain-ops/relations-proposals/<entity>.yaml`) that a human
    reviewer edits before running `brain apply-relations-batch`.
    """
    import json as _json

    import yaml as _yaml

    from brain_ops.domains.knowledge.relations_proposer import (
        propose_relations_for_entity,
    )

    vault = load_validated_vault(config_path, dry_run=True)
    db_path = Path(vault.config.vault_path) / ".brain-ops" / "knowledge.db"

    result = propose_relations_for_entity(
        entity, vault,
        db_path=db_path if db_path.exists() else None,
        include_existing=include_existing,
    )

    payload = result.to_yaml_dict()
    serialized = (
        _json.dumps(payload, ensure_ascii=False, indent=2) if as_json
        else _yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
    )

    if stdout:
        console.print(serialized)
    else:
        target = output or (
            Path(vault.config.vault_path)
            / ".brain-ops" / "relations-proposals" / f"{entity}.yaml"
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(serialized, encoding="utf-8")
        console.print(f"[green]wrote[/green] {target}")

    high = sum(1 for p in result.proposal if p.confidence == "high")
    med = sum(1 for p in result.proposal if p.confidence == "medium")
    missing = len(result.missing_entities_if_approved)
    console.print(
        f"[dim]entity={result.entity} · baseline_typed={result.baseline.typed} · "
        f"proposed={len(result.proposal)} (high={high}, medium={med}) · "
        f"missing_entities={missing}[/dim]"
    )


__all__ = [
    "present_audit_vault_command",
    "present_compile_knowledge_command",
    "present_enrich_entity_command",
    "present_entity_index_command",
    "present_ingest_source_command",
    "present_disambiguate_bare_command",
    "present_fill_domain_command",
    "present_fix_capitalization_command",
    "present_lint_schemas_command",
    "present_migrate_knowledge_db_command",
    "present_normalize_domain_command",
    "present_apply_relations_batch_command",
    "present_propose_relations_command",
    "present_query_relations_command",
    "present_show_entity_relations_command",
    "present_registry_lint_command",
    "present_replay_extractions_command",
    "present_query_knowledge_command",
    "present_search_knowledge_command",
    "present_entity_relations_command",
    "present_normalize_frontmatter_command",
    "present_process_inbox_command",
    "present_weekly_review_command",
    "run_audit_vault_command",
    "run_normalize_frontmatter_command",
    "run_process_inbox_command",
    "run_weekly_review_command",
]
