"""API routes for monitoring sources."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from brain_ops.domains.monitoring.sources import load_source_registry

from .dependencies import resolve_source_registry_path

router = APIRouter()


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
