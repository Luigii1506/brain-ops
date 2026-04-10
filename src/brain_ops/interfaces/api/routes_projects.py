"""API routes for project registry and operations."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from brain_ops.application.projects import (
    execute_audit_project_workflow,
    execute_project_log_workflow,
    execute_refresh_project_workflow,
    execute_session_workflow,
)
from brain_ops.config import load_config
from brain_ops.domains.projects.registry import (
    load_project_registry,
    save_project_registry,
    update_project_context,
)
from brain_ops.storage.sqlite.project_logs import fetch_project_logs
from brain_ops.storage.sqlite.tasks import fetch_tasks, fetch_task_by_id, insert_task

from .dependencies import (
    resolve_config_path,
    resolve_database_path,
    resolve_project_registry_path,
)

router = APIRouter()


def _normalize_task(task: dict | None) -> dict | None:
    if task is None:
        return None
    normalized = dict(task)
    tags_json = normalized.pop("tags_json", None)
    if isinstance(tags_json, str) and tags_json.strip():
        try:
            normalized["tags"] = json.loads(tags_json)
        except json.JSONDecodeError:
            normalized["tags"] = []
    else:
        normalized["tags"] = []
    return normalized


def _resolve_vault_project_dir(project_name: str) -> Path | None:
    config_path = resolve_config_path()
    if config_path is None:
        return None
    config = load_config(config_path)
    candidate = config.vault_path / "04 - Projects" / project_name
    return candidate if candidate.is_dir() else None


class UpdateContextRequest(BaseModel):
    phase: str | None = None
    pending: list[str] | None = None
    decisions: list[str] | None = None
    notes: str | None = None


class ProjectLogRequest(BaseModel):
    text: str


class CreateProjectTaskRequest(BaseModel):
    title: str
    priority: str = "medium"
    due_date: str | None = None
    focus_date: str | None = None
    tags: list[str] = Field(default_factory=list)
    note: str | None = None
    origin_text: str | None = None


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


@router.get("/{name}/logs")
def list_project_logs(name: str, limit: int = 20):
    """List recent project logs."""
    registry_path = resolve_project_registry_path()
    projects = load_project_registry(registry_path)
    if name not in projects:
        raise HTTPException(status_code=404, detail=f"Project '{name}' not found.")
    return fetch_project_logs(resolve_database_path(), project_name=name, limit=limit)


@router.post("/{name}/logs")
def create_project_log(name: str, body: ProjectLogRequest):
    """Add a project log entry."""
    try:
        result = execute_project_log_workflow(
            project_name=name,
            text=body.text,
            load_registry_path=resolve_project_registry_path,
            load_database_path=resolve_database_path,
            vault_project_dir=_resolve_vault_project_dir(name),
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.to_dict()


@router.get("/{name}/tasks")
def list_project_tasks(name: str, status: str | None = None, limit: int = 50):
    """List tasks assigned to the project."""
    registry_path = resolve_project_registry_path()
    projects = load_project_registry(registry_path)
    if name not in projects:
        raise HTTPException(status_code=404, detail=f"Project '{name}' not found.")
    tasks = fetch_tasks(resolve_database_path(), project=name, status=status, limit=limit)
    return {"items": [_normalize_task(task) for task in tasks]}


@router.post("/{name}/tasks")
def create_project_task(name: str, body: CreateProjectTaskRequest):
    """Create a task scoped to a project."""
    registry_path = resolve_project_registry_path()
    projects = load_project_registry(registry_path)
    if name not in projects:
        raise HTTPException(status_code=404, detail=f"Project '{name}' not found.")
    task_id = insert_task(
        resolve_database_path(),
        body.title,
        project=name,
        priority=body.priority,
        due_date=body.due_date,
        focus_date=body.focus_date,
        tags=body.tags,
        note=body.note,
        source="api",
        origin_text=body.origin_text,
    )
    task = _normalize_task(fetch_task_by_id(resolve_database_path(), task_id))
    if task is None:
        raise HTTPException(status_code=500, detail="Task created but could not be reloaded.")
    return task


@router.get("/{name}/session")
def get_project_session(name: str, days: int = 7):
    """Return the computed project session context."""
    try:
        result = execute_session_workflow(
            project_name=name,
            days=days,
            load_registry_path=resolve_project_registry_path,
            load_database_path=resolve_database_path,
            config_path=resolve_config_path(),
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.to_dict()


@router.get("/{name}/audit")
def get_project_audit(name: str):
    """Return the audit result for a project."""
    try:
        result = execute_audit_project_workflow(
            project_name=name,
            load_registry_path=resolve_project_registry_path,
            load_database_path=resolve_database_path,
            config_path=resolve_config_path(),
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.to_dict()


@router.post("/{name}/refresh")
def refresh_project(name: str):
    """Refresh auto-derived project documentation."""
    try:
        result = execute_refresh_project_workflow(
            project_name=name,
            load_registry_path=resolve_project_registry_path,
            load_database_path=resolve_database_path,
            config_path=resolve_config_path(),
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.to_dict()
