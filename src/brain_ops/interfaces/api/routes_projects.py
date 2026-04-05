"""API routes for project registry."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from brain_ops.domains.projects.registry import load_project_registry

from .dependencies import resolve_project_registry_path

router = APIRouter()


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
