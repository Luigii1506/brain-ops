"""CLI orchestration helpers for note workflow commands."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from brain_ops.application import (
    execute_apply_link_suggestions_workflow,
    execute_capture_workflow,
    execute_create_note_workflow,
    execute_create_project_workflow,
    execute_daily_summary_workflow,
    execute_enrich_note_workflow,
    execute_improve_note_workflow,
    execute_link_suggestions_workflow,
    execute_promote_note_workflow,
    execute_research_note_workflow,
)
from brain_ops.errors import BrainOpsError, ConfigError
from brain_ops.interfaces.cli.messages import (
    capture_result_lines,
    improve_result_lines,
    research_result_lines,
)
from brain_ops.interfaces.cli.presenters import (
    print_lines_with_single_operation,
    print_json_or_rendered_with_operations,
    print_operations,
    print_rendered_with_operations,
    print_rendered_with_single_operation,
)
from brain_ops.interfaces.cli.runtime import load_event_sink, load_validated_vault
from brain_ops.reporting_knowledge import (
    render_applied_links,
    render_daily_summary,
    render_enriched_note,
    render_link_suggestions,
    render_promoted_note,
)


def run_capture_command(
    *,
    config_path: Path | None,
    text: str,
    title: str | None,
    note_type: str | None,
    tags: list[str],
    dry_run: bool,
) :
    vault = load_validated_vault(config_path, dry_run=dry_run)
    return execute_capture_workflow(
        vault,
        text=text,
        title=title,
        note_type=note_type,
        tags=tags,
        event_sink=load_event_sink(),
    )


def run_create_note_command(
    *,
    config_path: Path | None,
    title: str,
    note_type: str,
    folder: str | None,
    template_name: str | None,
    tags: list[str],
    overwrite: bool,
    dry_run: bool,
) :
    vault = load_validated_vault(config_path, dry_run=dry_run)
    return execute_create_note_workflow(
        vault,
        title=title,
        note_type=note_type,
        folder=folder,
        template_name=template_name,
        tags=tags,
        overwrite=overwrite,
        event_sink=load_event_sink(),
    )


def run_create_project_command(
    *,
    config_path: Path | None,
    name: str,
    dry_run: bool,
) :
    vault = load_validated_vault(config_path, dry_run=dry_run)
    return execute_create_project_workflow(vault, name=name, event_sink=load_event_sink())


def run_daily_summary_command(
    *,
    config_path: Path | None,
    date: str | None,
    dry_run: bool,
    as_json: bool,
) :
    vault = load_validated_vault(config_path, dry_run=dry_run)
    return execute_daily_summary_workflow(vault, date=date, event_sink=load_event_sink())


def run_improve_note_command(
    *,
    config_path: Path | None,
    note_path: Path,
    dry_run: bool,
) :
    vault = load_validated_vault(config_path, dry_run=dry_run)
    return execute_improve_note_workflow(vault, note_path=note_path, event_sink=load_event_sink())


def run_research_note_command(
    *,
    config_path: Path | None,
    note_path: Path,
    query: str | None,
    max_sources: int,
    dry_run: bool,
) :
    vault = load_validated_vault(config_path, dry_run=dry_run)
    return execute_research_note_workflow(
        vault,
        note_path=note_path,
        query=query,
        max_sources=max_sources,
        event_sink=load_event_sink(),
    )


def run_link_suggestions_command(
    *,
    config_path: Path | None,
    note_path: Path,
    limit: int,
) :
    vault = load_validated_vault(config_path, dry_run=False)
    return execute_link_suggestions_workflow(
        vault,
        note_path=note_path,
        limit=limit,
        event_sink=load_event_sink(),
    )


def run_apply_link_suggestions_command(
    *,
    config_path: Path | None,
    note_path: Path,
    limit: int,
    dry_run: bool,
) :
    vault = load_validated_vault(config_path, dry_run=dry_run)
    return execute_apply_link_suggestions_workflow(
        vault,
        note_path=note_path,
        limit=limit,
        event_sink=load_event_sink(),
    )


def run_promote_note_command(
    *,
    config_path: Path | None,
    note_path: Path,
    target_type: str | None,
    dry_run: bool,
) :
    vault = load_validated_vault(config_path, dry_run=dry_run)
    return execute_promote_note_workflow(
        vault,
        note_path=note_path,
        target_type=target_type,
        event_sink=load_event_sink(),
    )


def run_enrich_note_command(
    *,
    config_path: Path | None,
    note_path: Path,
    query: str | None,
    max_sources: int,
    link_limit: int,
    improve: bool,
    research: bool,
    apply_links: bool,
    dry_run: bool,
) :
    vault = load_validated_vault(config_path, dry_run=dry_run)
    return execute_enrich_note_workflow(
        vault,
        note_path=note_path,
        query=query,
        max_sources=max_sources,
        link_limit=link_limit,
        improve=improve,
        research=research,
        apply_links=apply_links,
        event_sink=load_event_sink(),
    )


def present_capture_command(
    console: Console,
    *,
    config_path: Path | None,
    text: str,
    title: str | None,
    note_type: str | None,
    tags: list[str],
    dry_run: bool,
) -> None:
    result = run_capture_command(
        config_path=config_path,
        text=text,
        title=title,
        note_type=note_type,
        tags=tags,
        dry_run=dry_run,
    )
    print_lines_with_single_operation(console, result.operation, capture_result_lines(result))


def present_create_note_command(
    console: Console,
    *,
    config_path: Path | None,
    title: str,
    note_type: str,
    folder: str | None,
    template_name: str | None,
    tags: list[str],
    overwrite: bool,
    dry_run: bool,
) -> None:
    operation = run_create_note_command(
        config_path=config_path,
        title=title,
        note_type=note_type,
        folder=folder,
        template_name=template_name,
        tags=tags,
        overwrite=overwrite,
        dry_run=dry_run,
    )
    print_operations(console, [operation])


def present_create_project_command(
    console: Console,
    *,
    config_path: Path | None,
    name: str,
    dry_run: bool,
) -> None:
    operations = run_create_project_command(config_path=config_path, name=name, dry_run=dry_run)
    print_operations(console, operations)


def present_daily_summary_command(
    console: Console,
    *,
    config_path: Path | None,
    date: str | None,
    dry_run: bool,
    as_json: bool,
) -> None:
    result = run_daily_summary_command(config_path=config_path, date=date, dry_run=dry_run, as_json=as_json)
    print_json_or_rendered_with_operations(
        console,
        as_json=as_json,
        value=result,
        operations=result.operations,
        rendered=render_daily_summary(result),
    )


def present_improve_note_command(
    console: Console,
    *,
    config_path: Path | None,
    note_path: Path,
    dry_run: bool,
) -> None:
    result = run_improve_note_command(config_path=config_path, note_path=note_path, dry_run=dry_run)
    print_lines_with_single_operation(console, result.operation, improve_result_lines(result))


def present_research_note_command(
    console: Console,
    *,
    config_path: Path | None,
    note_path: Path,
    query: str | None,
    max_sources: int,
    dry_run: bool,
) -> None:
    result = run_research_note_command(
        config_path=config_path,
        note_path=note_path,
        query=query,
        max_sources=max_sources,
        dry_run=dry_run,
    )
    print_lines_with_single_operation(console, result.operation, research_result_lines(result))


def present_link_suggestions_command(
    console: Console,
    *,
    config_path: Path | None,
    note_path: Path,
    limit: int,
) -> None:
    result = run_link_suggestions_command(config_path=config_path, note_path=note_path, limit=limit)
    print_rendered_with_single_operation(console, result.operation, render_link_suggestions(result))


def present_apply_link_suggestions_command(
    console: Console,
    *,
    config_path: Path | None,
    note_path: Path,
    limit: int,
    dry_run: bool,
) -> None:
    result = run_apply_link_suggestions_command(
        config_path=config_path,
        note_path=note_path,
        limit=limit,
        dry_run=dry_run,
    )
    print_rendered_with_single_operation(console, result.operation, render_applied_links(result))


def present_promote_note_command(
    console: Console,
    *,
    config_path: Path | None,
    note_path: Path,
    target_type: str | None,
    dry_run: bool,
) -> None:
    result = run_promote_note_command(
        config_path=config_path,
        note_path=note_path,
        target_type=target_type,
        dry_run=dry_run,
    )
    print_rendered_with_operations(console, result.operations, render_promoted_note(result))


def present_enrich_note_command(
    console: Console,
    *,
    config_path: Path | None,
    note_path: Path,
    query: str | None,
    max_sources: int,
    link_limit: int,
    improve: bool,
    research: bool,
    apply_links: bool,
    dry_run: bool,
) -> None:
    result = run_enrich_note_command(
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
    print_rendered_with_operations(console, result.operations, render_enriched_note(result))


def coerce_note_workflow_error(error: BrainOpsError | ValueError) -> BrainOpsError:
    """Normalize legacy ValueError branches into CLI-facing config errors."""
    return error if isinstance(error, BrainOpsError) else ConfigError(str(error))


__all__ = [
    "coerce_note_workflow_error",
    "present_apply_link_suggestions_command",
    "present_capture_command",
    "present_create_note_command",
    "present_create_project_command",
    "present_daily_summary_command",
    "present_enrich_note_command",
    "present_improve_note_command",
    "present_link_suggestions_command",
    "present_promote_note_command",
    "present_research_note_command",
    "run_apply_link_suggestions_command",
    "run_capture_command",
    "run_create_note_command",
    "run_create_project_command",
    "run_daily_summary_command",
    "run_enrich_note_command",
    "run_improve_note_command",
    "run_link_suggestions_command",
    "run_promote_note_command",
    "run_research_note_command",
]
