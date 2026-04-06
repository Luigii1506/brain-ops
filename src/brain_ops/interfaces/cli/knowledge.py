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
    if result.plan.entities_mentioned:
        console.print(f"Entities mentioned: {', '.join(result.plan.entities_mentioned)}")
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


__all__ = [
    "present_audit_vault_command",
    "present_compile_knowledge_command",
    "present_enrich_entity_command",
    "present_entity_index_command",
    "present_ingest_source_command",
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
