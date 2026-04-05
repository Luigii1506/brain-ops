"""CLI orchestration helpers for knowledge/vault commands."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from brain_ops.application import (
    execute_audit_vault_workflow,
    execute_normalize_frontmatter_workflow,
    execute_process_inbox_workflow,
    execute_weekly_review_workflow,
)
from brain_ops.interfaces.cli.presenters import print_rendered_with_operations
from brain_ops.interfaces.cli.runtime import load_event_sink, load_validated_vault
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


__all__ = [
    "present_audit_vault_command",
    "present_normalize_frontmatter_command",
    "present_process_inbox_command",
    "present_weekly_review_command",
    "run_audit_vault_command",
    "run_normalize_frontmatter_command",
    "run_process_inbox_command",
    "run_weekly_review_command",
]
