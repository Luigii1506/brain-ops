"""Application workflows for knowledge-maintenance capabilities."""

from __future__ import annotations

from pathlib import Path

from brain_ops.core.events import EventSink
from brain_ops.reporting_knowledge import render_inbox_report
from brain_ops.services.audit_service import audit_vault
from brain_ops.services.inbox_service import process_inbox
from brain_ops.services.normalize_service import normalize_frontmatter
from brain_ops.services.review_service import generate_weekly_review
from brain_ops.storage.obsidian import write_report_text
from .events import publish_result_events


def execute_process_inbox_workflow(
    *,
    config_path: Path | None,
    dry_run: bool,
    write_report: bool,
    improve_structure: bool,
    load_vault,
    event_sink: EventSink | None = None,
):
    vault = load_vault(config_path, dry_run=dry_run)
    summary = process_inbox(vault, improve_structure=improve_structure)
    if write_report:
        summary.operations.append(
            write_report_text(vault, "inbox-processing-report", render_inbox_report(summary))
        )
    return publish_result_events("process-inbox", source="application.knowledge", result=summary, event_sink=event_sink)


def execute_weekly_review_workflow(
    *,
    config_path: Path | None,
    dry_run: bool,
    stale_days: int,
    write_report: bool,
    load_vault,
    event_sink: EventSink | None = None,
):
    vault = load_vault(config_path, dry_run=dry_run)
    result = generate_weekly_review(vault, stale_days=stale_days, write_report=write_report)
    return publish_result_events("weekly-review", source="application.knowledge", result=result, event_sink=event_sink)


def execute_audit_vault_workflow(
    *,
    config_path: Path | None,
    write_report: bool,
    load_vault,
    event_sink: EventSink | None = None,
):
    vault = load_vault(config_path, dry_run=False)
    result = audit_vault(vault, write_report=write_report)
    return publish_result_events("audit-vault", source="application.knowledge", result=result, event_sink=event_sink)


def execute_normalize_frontmatter_workflow(
    *,
    config_path: Path | None,
    dry_run: bool,
    load_vault,
    event_sink: EventSink | None = None,
):
    vault = load_vault(config_path, dry_run=dry_run)
    result = normalize_frontmatter(vault)
    return publish_result_events(
        "normalize-frontmatter",
        source="application.knowledge",
        result=result,
        event_sink=event_sink,
    )


__all__ = [
    "execute_audit_vault_workflow",
    "execute_normalize_frontmatter_workflow",
    "execute_process_inbox_workflow",
    "execute_weekly_review_workflow",
]
