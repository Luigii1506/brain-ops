"""Application workflows for note-oriented capabilities."""

from __future__ import annotations

from pathlib import Path

from brain_ops.core.events import EventSink
from brain_ops.errors import ConfigError
from brain_ops.domains.knowledge.entities import plan_entity_note
from brain_ops.models import CreateNoteRequest
from brain_ops.services.apply_links_service import apply_link_suggestions
from brain_ops.services.capture_service import capture_text
from brain_ops.services.daily_summary_service import write_daily_summary
from brain_ops.services.enrich_service import enrich_note
from brain_ops.services.improve_service import improve_note
from brain_ops.services.link_service import suggest_links
from brain_ops.services.note_service import create_note
from brain_ops.services.project_service import create_project_scaffold
from brain_ops.services.promote_service import promote_note
from brain_ops.services.research_service import research_note
from brain_ops.vault import Vault
from .events import publish_result_events


def execute_capture_workflow(
    vault: Vault,
    *,
    text: str,
    title: str | None,
    note_type: str | None,
    tags: list[str],
    event_sink: EventSink | None = None,
):
    result = capture_text(vault, text=text, title=title, force_type=note_type, tags=tags)
    return publish_result_events("capture", source="application.notes", result=result, event_sink=event_sink)


def execute_create_note_workflow(
    vault: Vault,
    *,
    title: str,
    note_type: str,
    folder: str | None,
    template_name: str | None,
    tags: list[str],
    overwrite: bool,
    event_sink: EventSink | None = None,
):
    result = create_note(
        vault,
        CreateNoteRequest(
            title=title,
            note_type=note_type,
            folder=folder,
            template_name=template_name,
            tags=tags,
            overwrite=overwrite,
        ),
    )
    return publish_result_events("create-note", source="application.notes", result=result, event_sink=event_sink)


def execute_create_project_workflow(vault: Vault, *, name: str, event_sink: EventSink | None = None):
    result = create_project_scaffold(vault, name)
    return publish_result_events("create-project", source="application.notes", result=result, event_sink=event_sink)


def execute_daily_summary_workflow(vault: Vault, *, date: str | None, event_sink: EventSink | None = None):
    result = write_daily_summary(vault, date_text=date)
    return publish_result_events("daily-summary", source="application.notes", result=result, event_sink=event_sink)


def execute_improve_note_workflow(vault: Vault, *, note_path: Path, event_sink: EventSink | None = None):
    result = improve_note(vault, note_path=note_path)
    return publish_result_events("improve-note", source="application.notes", result=result, event_sink=event_sink)


def execute_research_note_workflow(
    vault: Vault,
    *,
    note_path: Path,
    query: str | None,
    max_sources: int,
    event_sink: EventSink | None = None,
):
    result = research_note(vault, note_path=note_path, query=query, max_sources=max_sources)
    return publish_result_events("research-note", source="application.notes", result=result, event_sink=event_sink)


def execute_link_suggestions_workflow(
    vault: Vault,
    *,
    note_path: Path,
    limit: int,
    event_sink: EventSink | None = None,
):
    result = suggest_links(vault, note_path=note_path, limit=limit)
    return publish_result_events("link-suggestions", source="application.notes", result=result, event_sink=event_sink)


def execute_apply_link_suggestions_workflow(
    vault: Vault,
    *,
    note_path: Path,
    limit: int,
    event_sink: EventSink | None = None,
):
    result = apply_link_suggestions(vault, note_path=note_path, limit=limit)
    return publish_result_events(
        "apply-link-suggestions",
        source="application.notes",
        result=result,
        event_sink=event_sink,
    )


def execute_promote_note_workflow(
    vault: Vault,
    *,
    note_path: Path,
    target_type: str | None,
    event_sink: EventSink | None = None,
):
    result = promote_note(vault, note_path=note_path, target_type=target_type)
    return publish_result_events("promote-note", source="application.notes", result=result, event_sink=event_sink)


def execute_enrich_note_workflow(
    vault: Vault,
    *,
    note_path: Path,
    query: str | None,
    max_sources: int,
    link_limit: int,
    improve: bool,
    research: bool,
    apply_links: bool,
    event_sink: EventSink | None = None,
):
    result = enrich_note(
        vault,
        note_path=note_path,
        query=query,
        max_sources=max_sources,
        link_limit=link_limit,
        improve=improve,
        research=research,
        apply_links=apply_links,
    )
    return publish_result_events("enrich-note", source="application.notes", result=result, event_sink=event_sink)


def _find_existing_entity(vault: Vault, name: str) -> Path | None:
    """Search all vault folders for an existing note with this name."""
    from brain_ops.vault import sanitize_note_title

    safe_name = sanitize_note_title(name)
    filename = f"{safe_name}.md"
    for folder in vault.config.folders.model_dump().values():
        candidate = vault.root / folder / filename
        if candidate.exists():
            return candidate
    return None


def execute_create_entity_workflow(
    vault: Vault,
    *,
    name: str,
    entity_type: str,
    tags: list[str],
    extra_frontmatter: dict[str, object] | None = None,
    event_sink: EventSink | None = None,
):
    existing = _find_existing_entity(vault, name)
    if existing:
        raise ConfigError(
            f"Entity '{name}' already exists at {existing}. "
            "Use enrich-entity or edit the note directly instead."
        )

    plan = plan_entity_note(name, entity_type=entity_type, extra_frontmatter=extra_frontmatter)
    merged_frontmatter = dict(plan.frontmatter)
    result = create_note(
        vault,
        CreateNoteRequest(
            title=plan.title,
            note_type=plan.entity_type,
            tags=tags,
            extra_frontmatter=merged_frontmatter,
            body_override=plan.body,
        ),
    )

    # Auto-backlink: scan existing notes and convert plain mentions to [[wikilinks]]
    backlink_result = None
    try:
        from brain_ops.domains.knowledge.backlinking import inject_backlinks

        backlink_result = inject_backlinks(
            vault.config.vault_path,
            name,
        )
    except Exception:
        pass

    return publish_result_events("create-entity", source="application.notes", result=result, event_sink=event_sink)


__all__ = [
    "execute_apply_link_suggestions_workflow",
    "execute_capture_workflow",
    "execute_create_entity_workflow",
    "execute_create_note_workflow",
    "execute_create_project_workflow",
    "execute_daily_summary_workflow",
    "execute_enrich_note_workflow",
    "execute_improve_note_workflow",
    "execute_link_suggestions_workflow",
    "execute_promote_note_workflow",
    "execute_research_note_workflow",
]
