"""API routes for monitoring sources."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from brain_ops.domains.monitoring.sources import (
    build_monitor_source,
    load_source_registry,
    save_source_registry,
)

from .dependencies import resolve_source_registry_path

router = APIRouter()


class AddSourceRequest(BaseModel):
    url: str
    source_type: str = "web"
    selector: str | None = None
    check_interval: str = "daily"
    description: str | None = None
    tags: list[str] = []


@router.get("/")
def list_sources():
    """List all monitored sources."""
    registry_path = resolve_source_registry_path()
    sources = load_source_registry(registry_path)
    return [s.to_dict() for s in sorted(sources.values(), key=lambda s: s.name.lower())]


@router.get("/{name}")
def get_source(name: str):
    """Get a single source by name."""
    registry_path = resolve_source_registry_path()
    sources = load_source_registry(registry_path)
    source = sources.get(name)
    if source is None:
        raise HTTPException(status_code=404, detail=f"Source '{name}' not found.")
    return source.to_dict()


@router.post("/{name}")
def add_source(name: str, body: AddSourceRequest):
    """Register or update a monitored source."""
    registry_path = resolve_source_registry_path()
    sources = load_source_registry(registry_path)
    source = build_monitor_source(
        name,
        url=body.url,
        source_type=body.source_type,
        selector=body.selector,
        check_interval=body.check_interval,
        description=body.description,
        tags=body.tags,
    )
    sources[source.name] = source
    save_source_registry(registry_path, sources)
    return source.to_dict()


@router.delete("/{name}")
def remove_source(name: str):
    """Remove a monitored source."""
    registry_path = resolve_source_registry_path()
    sources = load_source_registry(registry_path)
    source = sources.pop(name, None)
    if source is None:
        raise HTTPException(status_code=404, detail=f"Source '{name}' not found.")
    save_source_registry(registry_path, sources)
    return {"removed": name}
