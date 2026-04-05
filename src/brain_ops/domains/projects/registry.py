"""Project registry and context models."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class ProjectContext:
    phase: str | None = None
    pending: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    notes: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "phase": self.phase,
            "pending": list(self.pending),
            "decisions": list(self.decisions),
            "notes": self.notes,
        }

    @staticmethod
    def from_dict(data: dict[str, object]) -> ProjectContext:
        return ProjectContext(
            phase=data.get("phase") if isinstance(data.get("phase"), str) else None,
            pending=list(data.get("pending", [])),
            decisions=list(data.get("decisions", [])),
            notes=data.get("notes") if isinstance(data.get("notes"), str) else None,
        )


@dataclass(slots=True)
class Project:
    name: str
    path: str
    stack: list[str] = field(default_factory=list)
    description: str | None = None
    commands: dict[str, str] = field(default_factory=dict)
    context: ProjectContext = field(default_factory=ProjectContext)

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "path": self.path,
            "stack": list(self.stack),
            "description": self.description,
            "commands": dict(self.commands),
            "context": self.context.to_dict(),
        }

    @staticmethod
    def from_dict(data: dict[str, object]) -> Project:
        return Project(
            name=str(data.get("name", "")),
            path=str(data.get("path", "")),
            stack=list(data.get("stack", [])),
            description=data.get("description") if isinstance(data.get("description"), str) else None,
            commands=dict(data.get("commands", {})),
            context=ProjectContext.from_dict(data.get("context", {})) if isinstance(data.get("context"), dict) else ProjectContext(),
        )


def build_project(
    name: str,
    *,
    path: str,
    stack: list[str] | None = None,
    description: str | None = None,
    commands: dict[str, str] | None = None,
) -> Project:
    if not name.strip():
        raise ValueError("Project name cannot be empty.")
    if not path.strip():
        raise ValueError("Project path cannot be empty.")
    return Project(
        name=name.strip(),
        path=path.strip(),
        stack=stack or [],
        description=description,
        commands=commands or {},
    )


def build_project_context(
    *,
    phase: str | None = None,
    pending: list[str] | None = None,
    decisions: list[str] | None = None,
    notes: str | None = None,
) -> ProjectContext:
    return ProjectContext(
        phase=phase,
        pending=pending or [],
        decisions=decisions or [],
        notes=notes,
    )


def update_project_context(
    project: Project,
    *,
    phase: str | None = None,
    pending: list[str] | None = None,
    decisions: list[str] | None = None,
    notes: str | None = None,
) -> Project:
    ctx = project.context
    if phase is not None:
        ctx.phase = phase
    if pending is not None:
        ctx.pending = pending
    if decisions is not None:
        ctx.decisions = decisions
    if notes is not None:
        ctx.notes = notes
    return project


def load_project_registry(registry_path: Path) -> dict[str, Project]:
    if not registry_path.exists():
        return {}
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}
    return {
        name: Project.from_dict(project_data)
        for name, project_data in data.items()
        if isinstance(project_data, dict)
    }


def save_project_registry(registry_path: Path, projects: dict[str, Project]) -> Path:
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {name: project.to_dict() for name, project in projects.items()}
    registry_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return registry_path


__all__ = [
    "Project",
    "ProjectContext",
    "build_project",
    "build_project_context",
    "load_project_registry",
    "save_project_registry",
    "update_project_context",
]
