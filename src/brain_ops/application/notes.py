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


def _rename_entity_for_disambiguation(
    vault: Vault,
    registry: "EntityRegistry",
    entity: "RegisteredEntity",
    registry_path: Path,
) -> None:
    """Rename an existing entity note to its disambiguated form."""
    from brain_ops.domains.knowledge.object_model import build_disambiguated_name
    from brain_ops.domains.knowledge.link_aliases import add_alias_to_frontmatter
    from brain_ops.domains.knowledge.registry import extract_base_name, save_entity_registry
    from brain_ops.frontmatter import split_frontmatter, dump_frontmatter

    old_name = entity.canonical_name
    subtype = entity.subtype or entity.entity_type
    new_name = build_disambiguated_name(old_name, subtype)

    # Find the old file
    old_path = _find_existing_entity(vault, old_name)
    if old_path is None:
        return

    # Read, update frontmatter with new name, write to new path
    content = old_path.read_text(encoding="utf-8")
    fm, body = split_frontmatter(content)
    fm["name"] = new_name
    fm["base_name"] = old_name
    if "aliases" not in fm or not isinstance(fm.get("aliases"), list):
        fm["aliases"] = []
    if old_name not in fm["aliases"]:
        fm["aliases"].append(old_name)

    # Determine folder for the entity type
    folder = vault.config.folder_for_note_type(entity.entity_type) or vault.config.folders.knowledge
    new_path = vault.note_path(folder, new_name)

    vault.write_text(new_path, dump_frontmatter(fm, body))

    # Remove old file (only if write succeeded)
    if not vault.dry_run:
        old_path.unlink()

    # Update registry
    old_entry = registry.entities.pop(old_name, None)
    if old_entry:
        old_entry.canonical_name = new_name
        if old_name not in old_entry.aliases:
            old_entry.aliases.append(old_name)
        registry.register(old_entry)

    save_entity_registry(registry_path, registry)


def _create_or_update_disambiguation_page(
    vault: Vault,
    base_name: str,
    candidates: list[tuple[str, str]],
) -> None:
    """Create or overwrite a disambiguation page for the given base name."""
    from brain_ops.domains.knowledge.entities import build_disambiguation_page

    plan = build_disambiguation_page(base_name, candidates)
    try:
        create_note(
            vault,
            CreateNoteRequest(
                title=plan.title,
                note_type=plan.entity_type,
                tags=["disambiguation"],
                extra_frontmatter=plan.frontmatter,
                body_override=plan.body,
                overwrite=True,
            ),
        )
    except Exception:
        pass


def execute_create_entity_workflow(
    vault: Vault,
    *,
    name: str,
    entity_type: str,
    tags: list[str],
    extra_frontmatter: dict[str, object] | None = None,
    event_sink: EventSink | None = None,
):
    from brain_ops.domains.knowledge.object_model import build_disambiguated_name, resolve_object_kind
    from brain_ops.domains.knowledge.registry import (
        EntityRegistry,
        RegisteredEntity,
        extract_base_name,
        load_entity_registry,
        save_entity_registry,
    )

    # Phase 1: Check for exact file collision (same name, same file)
    existing = _find_existing_entity(vault, name)
    if existing:
        raise ConfigError(
            f"Entity '{name}' already exists at {existing}. "
            "Use enrich-entity or edit the note directly instead."
        )

    # Phase 2: Check registry for base-name collisions (same name, different subtype)
    registry_path = vault.config.data_dir / "entity_registry.json"
    registry = load_entity_registry(registry_path)

    _obj_kind, new_subtype = resolve_object_kind(entity_type)
    collisions = registry.find_collisions(name)

    actual_name = name
    disambiguation_needed = False

    if collisions:
        # Only collisions with a different subtype are real collisions
        real_collisions = [c for c in collisions if c.subtype != new_subtype]
        if real_collisions:
            disambiguation_needed = True
            actual_name = build_disambiguated_name(name, new_subtype)

            # Check the disambiguated name doesn't also collide
            existing_disambig = _find_existing_entity(vault, actual_name)
            if existing_disambig:
                raise ConfigError(
                    f"Disambiguated entity '{actual_name}' already exists at {existing_disambig}."
                )

            # Rename existing colliders if they lack disambiguation suffix
            for collision in real_collisions:
                if extract_base_name(collision.canonical_name) == collision.canonical_name:
                    _rename_entity_for_disambiguation(vault, registry, collision, registry_path)
                    # Reload registry after rename
                    registry = load_entity_registry(registry_path)

    # Phase 3: Create the entity note (with possibly disambiguated name)
    plan = plan_entity_note(actual_name, entity_type=entity_type, extra_frontmatter=extra_frontmatter)
    merged_frontmatter = dict(plan.frontmatter)
    if disambiguation_needed:
        merged_frontmatter["base_name"] = name

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

    # Phase 4: Register alias and create disambiguation page
    if disambiguation_needed:
        registry = load_entity_registry(registry_path)
        registry.add_alias(actual_name, name)
        save_entity_registry(registry_path, registry)

        # Create/update disambiguation page
        all_collisions = registry.find_collisions(name)
        candidates = [
            (c.canonical_name, c.subtype or c.entity_type)
            for c in all_collisions
        ]
        _create_or_update_disambiguation_page(vault, name, candidates)

    # Auto-backlink: scan existing notes and convert plain mentions to [[wikilinks]]
    try:
        from brain_ops.domains.knowledge.backlinking import inject_backlinks

        inject_backlinks(vault.config.vault_path, actual_name)
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
