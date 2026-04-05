"""API routes for project registry."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from brain_ops.domains.projects.registry import (
    build_project,
    load_project_registry,
    save_project_registry,
    update_project_context,
)

from .dependencies import resolve_project_registry_path

router = APIRouter()


class UpdateContextRequest(BaseModel):
    phase: str | None = None
    pending: list[str] | None = None
    decisions: list[str] | None = None
    notes: str | None = None


@router.get("/")
def list_projects():
    """List all registered projects."""
    registry_path = resolve_project_registry_path()
    projects = load_project_registry(registry_path)
    return [p.to_dict() for p in sorted(projects.values(), key=lambda p: p.name.lower())]


@router.get("/{name}")
def get_project(name: str):
    """Get a single project by name."""
    registry_path = resolve_project_registry_path()
    projects = load_project_registry(registry_path)
    project = projects.get(name)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project '{name}' not found.")
    return project.to_dict()


@router.get("/{name}/context")
def get_project_context(name: str):
    """Get the current context for a project."""
    registry_path = resolve_project_registry_path()
    projects = load_project_registry(registry_path)
    project = projects.get(name)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project '{name}' not found.")
    return project.context.to_dict()


@router.put("/{name}/context")
def update_project_context_endpoint(name: str, body: UpdateContextRequest):
    """Update the context for a project."""
    registry_path = resolve_project_registry_path()
    projects = load_project_registry(registry_path)
    project = projects.get(name)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project '{name}' not found.")
    update_project_context(
        project,
        phase=body.phase,
        pending=body.pending,
        decisions=body.decisions,
        notes=body.notes,
    )
    save_project_registry(registry_path, projects)
    return project.to_dict()
