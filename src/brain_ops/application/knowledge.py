"""Application workflows for knowledge-maintenance capabilities."""

from __future__ import annotations

from pathlib import Path

from dataclasses import dataclass

from brain_ops.core.events import EventSink
from brain_ops.domains.knowledge.enrichment_llm import (
    EnrichmentResult,
    build_enrich_prompt,
    build_generate_prompt,
)
from brain_ops.domains.knowledge.entities import ENTITY_SCHEMAS
from brain_ops.domains.knowledge.ingest import (
    IngestPlan,
    build_deterministic_ingest_plan,
    build_ingest_prompt,
    parse_ingest_extraction,
)
from brain_ops.domains.knowledge.search import SearchResult, search_notes
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


def _scan_vault_full(
    vault: Vault,
) -> list[tuple[str, dict[str, object], str]]:
    results: list[tuple[str, dict[str, object], str]] = []
    all_notes = list_vault_markdown_notes(vault, excluded_parts={".git", ".obsidian"})
    for path in sorted(all_notes):
        _safe_path, rel, text = read_note_text(vault, path)
        try:
            frontmatter, body = split_frontmatter(text)
        except Exception:
            continue
        results.append((str(rel), frontmatter, body))
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


@dataclass(slots=True, frozen=True)
class IngestResult:
    plan: IngestPlan
    source_note_path: Path | None
    used_llm: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "plan": self.plan.to_dict(),
            "source_note_path": str(self.source_note_path) if self.source_note_path else None,
            "used_llm": self.used_llm,
        }


def execute_ingest_source_workflow(
    *,
    text: str | None = None,
    url: str | None = None,
    title: str | None = None,
    config_path: Path | None,
    use_llm: bool = False,
    load_vault,
    llm_generate_json_fn=None,
    fetch_url=None,
    event_sink=None,
) -> IngestResult:
    from brain_ops.domains.knowledge.ingest import classify_source_type, fetch_url_content
    from brain_ops.models import CreateNoteRequest
    from brain_ops.services.note_service import create_note

    fetcher = fetch_url or fetch_url_content
    if url and not text:
        fetched_text, fetched_title = fetcher(url)
        text = fetched_text
        if not title:
            title = fetched_title

    if not text:
        raise ValueError("Either text or url must be provided for ingest.")

    source_type = classify_source_type(url, text)
    used_llm = False
    if use_llm and llm_generate_json_fn is not None:
        try:
            prompt = build_ingest_prompt(text, source_type=source_type)
            extraction = llm_generate_json_fn(prompt)
            plan = parse_ingest_extraction(extraction)
            used_llm = True
        except Exception:
            plan = build_deterministic_ingest_plan(text, title=title, url=url)
    else:
        plan = build_deterministic_ingest_plan(text, title=title, url=url)

    vault = load_vault(config_path, dry_run=False)
    extra_fm: dict[str, object] = {
        "source_type": plan.source_type,
        "summary": plan.summary,
        "tldr": plan.tldr,
        "entities_mentioned": plan.entities_mentioned,
    }
    if url:
        extra_fm["url"] = [url]
    if plan.personal_relevance:
        extra_fm["personal_relevance"] = plan.personal_relevance

    operation = create_note(
        vault,
        CreateNoteRequest(
            title=plan.source_title,
            note_type="source",
            tags=[],
            extra_frontmatter=extra_fm,
            body_override=plan.content_for_note,
        ),
    )

    if event_sink is not None:
        from brain_ops.core.events import new_event

        event_sink.publish(new_event(
            name="source.ingested",
            source="application.knowledge",
            payload={
                "title": plan.source_title,
                "source_type": plan.source_type,
                "url": url,
                "entities_count": len(plan.entities_mentioned),
                "used_llm": used_llm,
                "workflow": "ingest-source",
            },
        ))

    return IngestResult(
        plan=plan,
        source_note_path=operation.path,
        used_llm=used_llm,
    )


def execute_search_knowledge_workflow(
    *,
    query: str,
    config_path: Path | None,
    entity_only: bool = False,
    max_results: int = 20,
    load_vault,
) -> list[SearchResult]:
    vault = load_vault(config_path, dry_run=False)
    notes = _scan_vault_full(vault)
    return search_notes(notes, query, entity_only=entity_only, max_results=max_results)


def execute_enrich_entity_workflow(
    *,
    entity_name: str,
    new_info: str | None = None,
    url: str | None = None,
    auto_generate: bool = False,
    config_path: Path | None,
    load_vault,
    llm_generate_text_fn=None,
    fetch_url=None,
) -> EnrichmentResult:
    from brain_ops.frontmatter import dump_frontmatter

    if url and not new_info:
        from brain_ops.domains.knowledge.ingest import fetch_url_content

        fetcher = fetch_url or fetch_url_content
        fetched_text, _title = fetcher(url)
        new_info = fetched_text

    vault = load_vault(config_path, dry_run=False)
    notes = _scan_vault_full(vault)

    existing_note = None
    existing_body = None
    existing_frontmatter = None
    existing_path = None
    for rel_path, fm, body in notes:
        if fm.get("entity") is True and fm.get("name") == entity_name:
            existing_note = rel_path
            existing_body = body
            existing_frontmatter = fm
            existing_path = vault.config.vault_path / rel_path
            break

    if existing_note is None:
        from brain_ops.errors import ConfigError
        raise ConfigError(f"Entity '{entity_name}' not found in vault.")

    if llm_generate_text_fn is None:
        return EnrichmentResult(
            entity_name=entity_name,
            updated_body=existing_body or "",
            had_existing_content=bool(existing_body and existing_body.strip()),
        )

    has_content = bool(existing_body and existing_body.strip() and "## " in existing_body)
    body_is_empty_template = all(
        line.startswith("## ") or not line.strip()
        for line in (existing_body or "").splitlines()
    )

    if body_is_empty_template and auto_generate:
        entity_type = existing_frontmatter.get("type", "topic")
        schema = ENTITY_SCHEMAS.get(entity_type)
        sections = schema.sections if schema else ("Overview",)
        prompt = build_generate_prompt(entity_name, entity_type, sections)
        updated_body = llm_generate_text_fn(prompt)
    elif new_info:
        prompt = build_enrich_prompt(existing_body or "", new_info)
        updated_body = llm_generate_text_fn(prompt)
    else:
        return EnrichmentResult(
            entity_name=entity_name,
            updated_body=existing_body or "",
            had_existing_content=has_content,
        )

    if existing_path and existing_frontmatter is not None:
        full_content = dump_frontmatter(existing_frontmatter, updated_body)
        existing_path.write_text(full_content, encoding="utf-8")

    return EnrichmentResult(
        entity_name=entity_name,
        updated_body=updated_body,
        had_existing_content=has_content,
    )


@dataclass(slots=True, frozen=True)
class QueryResult:
    query: str
    answer: str
    sources_used: list[str]
    filed_back: bool
    filed_path: Path | None

    def to_dict(self) -> dict[str, object]:
        return {
            "query": self.query,
            "answer": self.answer,
            "sources_used": list(self.sources_used),
            "filed_back": self.filed_back,
            "filed_path": str(self.filed_path) if self.filed_path else None,
        }


QUERY_SYNTHESIS_PROMPT = """You are a personal knowledge assistant. Answer the user's question using ONLY the knowledge base content provided below.

Question: {query}

Knowledge base context:
---
{context}
---

Rules:
- Answer based ONLY on the provided context. If the context doesn't have enough info, say so.
- Use wikilinks [[Entity Name]] when referencing entities in the knowledge base.
- Be concise but thorough.
- If the question is about relationships between entities, explain the connections.
- Answer in the same language as the question.

Answer:"""


def execute_query_knowledge_workflow(
    *,
    query: str,
    config_path: Path | None,
    file_back: bool = False,
    max_context_notes: int = 10,
    load_vault,
    llm_generate_text_fn=None,
) -> QueryResult:
    from brain_ops.models import CreateNoteRequest
    from brain_ops.services.note_service import create_note

    vault = load_vault(config_path, dry_run=False)
    notes = _scan_vault_full(vault)
    search_results = search_notes(notes, query, max_results=max_context_notes)

    if not search_results:
        return QueryResult(
            query=query,
            answer=f"No relevant notes found for '{query}'.",
            sources_used=[],
            filed_back=False,
            filed_path=None,
        )

    context_parts: list[str] = []
    sources_used: list[str] = []
    for sr in search_results:
        for rel_path, fm, body in notes:
            if rel_path == sr.relative_path:
                name = fm.get("name", rel_path)
                context_parts.append(f"### {name}\n{body[:2000]}")
                sources_used.append(str(name))
                break

    if llm_generate_text_fn is None:
        answer_parts = [f"Found {len(search_results)} relevant notes:"]
        for sr in search_results:
            answer_parts.append(f"- [[{sr.title}]]: {sr.match_context}")
        answer = "\n".join(answer_parts)
    else:
        context = "\n\n".join(context_parts)
        prompt = QUERY_SYNTHESIS_PROMPT.format(query=query, context=context[:12000])
        answer = llm_generate_text_fn(prompt)

    filed_path = None
    if file_back and llm_generate_text_fn is not None:
        safe_title = query[:60].strip()
        body = f"> **Query:** {query}\n\n## Answer\n\n{answer}\n\n## Sources\n\n"
        body += "\n".join(f"- [[{s}]]" for s in sources_used)
        body += "\n\n## Related notes\n"
        operation = create_note(
            vault,
            CreateNoteRequest(
                title=f"Q - {safe_title}",
                note_type="knowledge",
                tags=["query-answer"],
                extra_frontmatter={"query": query, "sources_count": len(sources_used)},
                body_override=body,
            ),
        )
        filed_path = operation.path

    return QueryResult(
        query=query,
        answer=answer,
        sources_used=sources_used,
        filed_back=filed_path is not None,
        filed_path=filed_path,
    )


__all__ = [
    "EntityIndexResult",
    "EntityRelationsResult",
    "EnrichmentResult",
    "IngestResult",
    "KnowledgeCompileResult",
    "QueryResult",
    "execute_audit_vault_workflow",
    "execute_compile_knowledge_workflow",
    "execute_enrich_entity_workflow",
    "execute_entity_index_workflow",
    "execute_entity_relations_workflow",
    "execute_ingest_source_workflow",
    "execute_normalize_frontmatter_workflow",
    "execute_process_inbox_workflow",
    "execute_query_knowledge_workflow",
    "execute_search_knowledge_workflow",
    "execute_weekly_review_workflow",
]
