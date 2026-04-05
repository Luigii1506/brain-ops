"""Application workflows for knowledge-maintenance capabilities."""

from __future__ import annotations

from pathlib import Path

from dataclasses import dataclass

from brain_ops.core.events import EventSink
from brain_ops.domains.knowledge.compile import (
    CompileResult,
    compile_vault_entities,
)
from brain_ops.domains.knowledge.index import (
    EntityIndexEntry,
    build_entity_index_entry,
    render_entity_index_markdown,
)
from brain_ops.domains.knowledge.relations import (
    EntityRelation,
    extract_relations_from_note,
    find_entity_connections,
    render_entity_relations_markdown,
)
from brain_ops.frontmatter import split_frontmatter
from brain_ops.reporting_knowledge import render_inbox_report
from brain_ops.services.audit_service import audit_vault
from brain_ops.services.inbox_service import process_inbox
from brain_ops.services.normalize_service import normalize_frontmatter
from brain_ops.services.review_service import generate_weekly_review
from brain_ops.storage.obsidian import list_vault_markdown_notes, read_note_text, write_report_text
from brain_ops.vault import Vault
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


@dataclass(slots=True, frozen=True)
class EntityIndexResult:
    entries: list[EntityIndexEntry]
    markdown: str

    def to_dict(self) -> dict[str, object]:
        return {
            "total": len(self.entries),
            "entries": [e.to_dict() for e in self.entries],
        }


@dataclass(slots=True, frozen=True)
class EntityRelationsResult:
    entity_name: str
    connections: list[str]
    all_relations: list[EntityRelation]
    markdown: str

    def to_dict(self) -> dict[str, object]:
        return {
            "entity_name": self.entity_name,
            "connections": list(self.connections),
            "total_connections": len(self.connections),
        }


def _scan_vault_frontmatters(
    vault: Vault,
) -> list[tuple[str, dict[str, object]]]:
    results: list[tuple[str, dict[str, object]]] = []
    all_notes = list_vault_markdown_notes(vault, excluded_parts={".git", ".obsidian"})
    for path in sorted(all_notes):
        _safe_path, rel, text = read_note_text(vault, path)
        try:
            frontmatter, _body = split_frontmatter(text)
        except Exception:
            continue
        results.append((str(rel), frontmatter))
    return results


def execute_entity_index_workflow(
    *,
    config_path: Path | None,
    load_vault,
) -> EntityIndexResult:
    vault = load_vault(config_path, dry_run=False)
    notes = _scan_vault_frontmatters(vault)
    entries: list[EntityIndexEntry] = []
    for rel_path, frontmatter in notes:
        entry = build_entity_index_entry(frontmatter, rel_path)
        if entry is not None:
            entries.append(entry)
    markdown = render_entity_index_markdown(entries)
    return EntityIndexResult(entries=entries, markdown=markdown)


def execute_entity_relations_workflow(
    *,
    entity_name: str,
    config_path: Path | None,
    load_vault,
) -> EntityRelationsResult:
    vault = load_vault(config_path, dry_run=False)
    notes = _scan_vault_frontmatters(vault)
    all_relations: list[EntityRelation] = []
    for _rel_path, frontmatter in notes:
        all_relations.extend(extract_relations_from_note(frontmatter))
    connections = find_entity_connections(entity_name, all_relations)
    markdown = render_entity_relations_markdown(entity_name, connections)
    return EntityRelationsResult(
        entity_name=entity_name,
        connections=connections,
        all_relations=all_relations,
        markdown=markdown,
    )


@dataclass(slots=True, frozen=True)
class KnowledgeCompileResult:
    compile_result: CompileResult
    db_path: Path
    total_entities: int

    def to_dict(self) -> dict[str, object]:
        return {
            "total_entities": self.total_entities,
            "total_relations": len(self.compile_result.relations),
            "db_path": str(self.db_path),
        }


def execute_compile_knowledge_workflow(
    *,
    config_path: Path | None,
    db_path: Path | None,
    load_vault,
    write_entities=None,
) -> KnowledgeCompileResult:
    from brain_ops.storage.sqlite.entities import write_compiled_entities

    vault = load_vault(config_path, dry_run=False)
    notes = _scan_vault_frontmatters(vault)
    result = compile_vault_entities(notes)
    resolved_db = db_path or (Path(vault.config.vault_path) / ".brain-ops" / "knowledge.db")
    writer = write_entities or write_compiled_entities
    total = writer(resolved_db, result)
    return KnowledgeCompileResult(
        compile_result=result,
        db_path=resolved_db,
        total_entities=total,
    )


__all__ = [
    "EntityIndexResult",
    "EntityRelationsResult",
    "KnowledgeCompileResult",
    "execute_audit_vault_workflow",
    "execute_compile_knowledge_workflow",
    "execute_entity_index_workflow",
    "execute_entity_relations_workflow",
    "execute_normalize_frontmatter_workflow",
    "execute_process_inbox_workflow",
    "execute_weekly_review_workflow",
]
