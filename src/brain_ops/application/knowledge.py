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
    from brain_ops.domains.knowledge.extraction_store import load_extraction_records
    from brain_ops.storage.sqlite.entities import write_compiled_entities, write_extraction_intelligence

    vault = load_vault(config_path, dry_run=False)
    notes = _scan_vault_frontmatters(vault)
    result = compile_vault_entities(notes)
    resolved_db = db_path or (Path(vault.config.vault_path) / ".brain-ops" / "knowledge.db")
    writer = write_entities or write_compiled_entities
    total = writer(resolved_db, result)

    # Populate facts, timeline, insights from extraction records
    try:
        extractions_dir = Path(vault.config.vault_path) / ".brain-ops" / "extractions"
        records = load_extraction_records(extractions_dir)
        if records:
            write_extraction_intelligence(resolved_db, [r.to_dict() for r in records])
    except Exception:
        pass

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
    from brain_ops.domains.knowledge.registry import learn_from_ingest, load_entity_registry, save_entity_registry
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

    # Load accumulated intelligence to improve extraction
    known_entity_names: list[str] | None = None
    user_context: str | None = None
    try:
        vault_for_context = load_vault(config_path, dry_run=True)
        registry_path = Path(vault_for_context.config.vault_path) / ".brain-ops" / "entity_registry.json"
        prefs_path = Path(vault_for_context.config.vault_path) / ".brain-ops" / "preferences.json"
        registry = load_entity_registry(registry_path)
        known_entity_names = [e.canonical_name for e in registry.list_all()]
        from brain_ops.domains.knowledge.preferences import load_user_preferences
        prefs = load_user_preferences(prefs_path)
        user_context = prefs.to_prompt_context()
    except Exception:
        pass

    from brain_ops.domains.knowledge.evidence import confidence_for_source, lint_extraction, tag_evidence_strength

    used_llm = False
    raw_extraction: dict[str, object] | None = None
    lint_issues: list[str] = []
    if use_llm and llm_generate_json_fn is not None:
        try:
            prompt = build_ingest_prompt(
                text,
                source_type=source_type,
                known_entities=known_entity_names,
                user_context=user_context,
            )
            extraction = llm_generate_json_fn(prompt)
            raw_extraction = dict(extraction)

            # Lint the extraction for quality
            lint_result = lint_extraction(source_type, extraction)
            lint_issues = lint_result.issues

            plan = parse_ingest_extraction(extraction)
            used_llm = True
        except Exception:
            plan = build_deterministic_ingest_plan(text, title=title, url=url)
    else:
        plan = build_deterministic_ingest_plan(text, title=title, url=url)

    # Tag evidence strength
    evidence_strength = tag_evidence_strength(source_type)
    source_confidence = confidence_for_source(source_type)

    # Save raw source content for replay
    try:
        raw_dir = Path(vault_for_context.config.vault_path) / ".brain-ops" / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        from datetime import datetime, timezone
        slug = "".join(c if c.isalnum() or c in "-_ " else "" for c in plan.source_title)[:60].strip().replace(" ", "-").lower()
        raw_file = raw_dir / f"{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{slug}.txt"
        raw_file.write_text(text or "", encoding="utf-8")
        # Update _index.json with source title mapping
        import json as _json
        index_path = raw_dir / "_index.json"
        idx: dict[str, str] = {}
        if index_path.exists():
            idx = _json.loads(index_path.read_text(encoding="utf-8"))
        idx[plan.source_title] = str(raw_file)
        index_path.write_text(_json.dumps(idx, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass

    # Save full extraction JSON for replay and debugging
    if raw_extraction is not None:
        try:
            from brain_ops.domains.knowledge.extraction_store import save_extraction_record
            extractions_dir = Path(vault_for_context.config.vault_path) / ".brain-ops" / "extractions"
            save_extraction_record(
                extractions_dir,
                source_title=plan.source_title,
                source_url=url,
                source_type=plan.source_type,
                raw_llm_json=raw_extraction,
            )
        except Exception:
            pass

    vault = load_vault(config_path, dry_run=False)
    extra_fm: dict[str, object] = {
        "source_type": plan.source_type,
        "summary": plan.summary,
        "tldr": plan.tldr,
        "entities_mentioned": [e.name for e in plan.entities] if plan.entities else [],
        "evidence_strength": evidence_strength,
        "source_confidence": source_confidence,
    }
    if lint_issues:
        extra_fm["lint_issues"] = lint_issues
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
                "entities_count": len(plan.entities),
                "used_llm": used_llm,
                "workflow": "ingest-source",
            },
        ))

    # Learn from this ingest — update entity registry with new intelligence
    try:
        registry_path = Path(vault.config.vault_path) / ".brain-ops" / "entity_registry.json"
        registry = load_entity_registry(registry_path)
        entity_dicts = [e.to_dict() for e in plan.entities] if plan.entities else []
        rel_dicts = [r.to_dict() for r in plan.relationships] if plan.relationships else []
        learn_from_ingest(
            registry,
            entities_mentioned=entity_dicts,
            relationships=rel_dicts,
            source_domain=plan.source_type,
        )
        save_entity_registry(registry_path, registry)

        # Auto-create entity notes for candidates that don't have notes yet
        from brain_ops.domains.knowledge.entities import build_entity_body, build_entity_frontmatter
        from brain_ops.models import CreateNoteRequest
        from brain_ops.services.note_service import create_note as create_note_fn

        existing_notes = _scan_vault_frontmatters(vault)
        existing_entity_names = {
            fm.get("name") for _path, fm in existing_notes
            if fm.get("entity") is True and isinstance(fm.get("name"), str)
        }

        auto_created: list[str] = []
        for entity in registry.entities.values():
            if entity.status in ("candidate", "canonical") and entity.canonical_name not in existing_entity_names:
                if entity.source_count >= 2 or entity.relation_count >= 3:
                    try:
                        entity_type = entity.subtype or entity.entity_type or "concept"
                        fm = build_entity_frontmatter(entity_type, entity.canonical_name)
                        body = build_entity_body(entity_type, entity.canonical_name)
                        create_note_fn(
                            vault,
                            CreateNoteRequest(
                                title=entity.canonical_name,
                                note_type=entity_type,
                                tags=[],
                                extra_frontmatter=fm,
                                body_override=body,
                            ),
                        )
                        auto_created.append(entity.canonical_name)
                    except Exception:
                        pass

        if auto_created and event_sink is not None:
            event_sink.publish(new_event(
                name="entities.auto_created",
                source="application.knowledge",
                payload={
                    "count": len(auto_created),
                    "entities": auto_created,
                    "workflow": "ingest-source",
                },
            ))
    except Exception:
        pass

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
    from brain_ops.domains.knowledge.chunking import build_prioritized_context
    from brain_ops.domains.knowledge.enrichment_llm import (
        build_section_repair_prompt,
        repair_section,
        validate_note_sections,
    )
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
            sections_repaired=[],
        )

    has_content = bool(existing_body and existing_body.strip() and "## " in existing_body)
    body_is_empty_template = all(
        line.startswith("## ") or not line.strip()
        for line in (existing_body or "").splitlines()
    )

    # Smart chunking: prioritize context by subtype
    subtype = str(existing_frontmatter.get("subtype", existing_frontmatter.get("type", "person")))
    if new_info:
        new_info = build_prioritized_context(new_info, subtype, max_chars=8000)

    # Resolve writing guides for subtype-aware prompts
    from brain_ops.domains.knowledge.object_model import get_writing_guide, sections_for_subtype
    occupation = str(existing_frontmatter.get("occupation", "") or "")
    writing_guide, role_hints = get_writing_guide(subtype, occupation)

    if body_is_empty_template and auto_generate:
        entity_type = existing_frontmatter.get("type", "topic")
        sections = sections_for_subtype(subtype)
        prompt = build_generate_prompt(
            entity_name, entity_type, sections,
            writing_guide=writing_guide, role_hints=role_hints,
        )
        updated_body = llm_generate_text_fn(prompt)
    elif new_info:
        prompt = build_enrich_prompt(
            existing_body or "", new_info,
            subtype=subtype, writing_guide=writing_guide, role_hints=role_hints,
        )
        updated_body = llm_generate_text_fn(prompt)
    else:
        return EnrichmentResult(
            entity_name=entity_name,
            updated_body=existing_body or "",
            had_existing_content=has_content,
            sections_repaired=[],
        )

    # Post-validation: repair empty required sections
    sections_repaired: list[str] = []
    empty_sections = validate_note_sections(updated_body)
    for section_name in empty_sections:
        try:
            repair_prompt = build_section_repair_prompt(entity_name, section_name, updated_body)
            repair_content = llm_generate_text_fn(repair_prompt)
            updated_body = repair_section(updated_body, section_name, repair_content)
            sections_repaired.append(section_name)
        except Exception:
            pass

    # Post-enrichment dedup: remove duplicate sentences across sections
    from brain_ops.domains.knowledge.enrichment_llm import deduplicate_note_content
    updated_body = deduplicate_note_content(updated_body)

    if existing_path and existing_frontmatter is not None:
        full_content = dump_frontmatter(existing_frontmatter, updated_body)
        existing_path.write_text(full_content, encoding="utf-8")

    # Save enrichment diff
    try:
        from brain_ops.domains.knowledge.enrichment_diff import compute_enrichment_diff, save_enrichment_diff

        diff = compute_enrichment_diff(
            entity_name,
            existing_body or "",
            updated_body,
            source_url=url,
        )
        diffs_dir = Path(vault.config.vault_path) / ".brain-ops" / "enrichment_diffs"
        save_enrichment_diff(diffs_dir, diff)
    except Exception:
        pass

    # Cross-enrichment: detect and apply knowledge to related entities
    cross_enriched: list[str] = []
    try:
        from brain_ops.domains.knowledge.cross_enrichment import (
            apply_cross_enrichment,
            detect_cross_enrichment_candidates,
            save_cross_enrichment_log,
        )

        all_notes = _scan_vault_full(vault)
        for rel_path, fm, body in all_notes:
            if fm.get("entity") is not True:
                continue
            related_name = fm.get("name")
            if not isinstance(related_name, str) or related_name == entity_name:
                continue

            candidates = detect_cross_enrichment_candidates(
                entity_name, updated_body, related_name, body,
            )
            if not candidates:
                continue

            new_body, applied = apply_cross_enrichment(body, candidates, auto_only=True)
            if applied:
                related_path = vault.config.vault_path / rel_path
                full = dump_frontmatter(fm, new_body)
                related_path.write_text(full, encoding="utf-8")
                cross_enriched.append(related_name)

            # Save log regardless of whether anything was applied
            log_dir = Path(vault.config.vault_path) / ".brain-ops" / "cross_enrichment_logs"
            save_cross_enrichment_log(log_dir, entity_name, candidates, applied)
    except Exception:
        pass

    return EnrichmentResult(
        entity_name=entity_name,
        updated_body=updated_body,
        had_existing_content=has_content,
        sections_repaired=sections_repaired,
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

    # Query learning: log the query and detect knowledge gaps
    try:
        from brain_ops.domains.knowledge.query_learning import build_query_record, save_query_log, update_gap_registry

        existing_entity_names = {
            fm.get("name") for _p, fm, _b in notes
            if fm.get("entity") is True and isinstance(fm.get("name"), str)
        }
        record = build_query_record(
            query, answer, sources_used, existing_entity_names,
            had_llm_answer=llm_generate_text_fn is not None,
            filed_back=filed_path is not None,
        )
        query_log_path = Path(vault.config.vault_path) / ".brain-ops" / "query_log.jsonl"
        save_query_log(query_log_path, record)

        # Update gap registry with missing entities
        if record.entities_missing:
            gap_registry_path = Path(vault.config.vault_path) / ".brain-ops" / "gap_registry.json"
            update_gap_registry(gap_registry_path, record.entities_missing)

        # Update registry query_count (NOT source_count) for queried entities
        from brain_ops.domains.knowledge.registry import load_entity_registry, save_entity_registry

        registry_path = Path(vault.config.vault_path) / ".brain-ops" / "entity_registry.json"
        registry = load_entity_registry(registry_path)
        for entity_name in record.entities_found:
            entity = registry.get(entity_name)
            if entity is not None:
                entity.query_count = getattr(entity, "query_count", 0) + 1
        save_entity_registry(registry_path, registry)
    except Exception:
        pass

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
    "execute_audit_knowledge_workflow",
    "execute_generate_moc_workflow",
    "execute_weekly_review_workflow",
]


def execute_audit_knowledge_workflow(
    *,
    config_path: Path | None,
    load_vault,
) -> dict[str, object]:
    from brain_ops.domains.knowledge.knowledge_audit import audit_knowledge
    from brain_ops.domains.knowledge.registry import load_entity_registry

    vault = load_vault(config_path, dry_run=False)
    notes = _scan_vault_full(vault)
    source_notes = [
        (str(rel), fm)
        for rel, fm, _body in notes
        if fm.get("type") == "source"
    ]
    entity_notes = [
        (str(rel), fm, body)
        for rel, fm, body in notes
        if fm.get("entity") is True
    ]

    registry_path = Path(vault.config.vault_path) / ".brain-ops" / "entity_registry.json"
    registry = load_entity_registry(registry_path)
    registry_data = {name: entity.to_dict() for name, entity in registry.entities.items()}

    result = audit_knowledge(entity_notes, source_notes, registry_data)
    return result.to_dict()


def execute_generate_moc_workflow(
    *,
    topic: str,
    config_path: Path | None,
    seed_names: list[str] | None = None,
    description: str | None = None,
    output_path: Path | None = None,
    load_vault,
) -> Path:
    from brain_ops.domains.knowledge.moc_generator import generate_moc, preserve_manual_sections, render_moc_markdown

    vault = load_vault(config_path, dry_run=False)
    notes = _scan_vault_full(vault)
    moc = generate_moc(topic, notes, seed_names=seed_names, description=description)
    new_markdown = render_moc_markdown(moc)

    resolved_path = output_path or (vault.config.vault_path / vault.config.folders.maps / f"MOC - {topic}.md")
    resolved_path.parent.mkdir(parents=True, exist_ok=True)

    # Preserve manual edits if file already exists
    if resolved_path.exists():
        existing = resolved_path.read_text(encoding="utf-8")
        final_markdown = preserve_manual_sections(existing, new_markdown)
    else:
        final_markdown = new_markdown

    resolved_path.write_text(final_markdown, encoding="utf-8")
    return resolved_path
