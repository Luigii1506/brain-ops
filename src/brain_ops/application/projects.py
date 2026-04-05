"""Application workflows for project registry and context management."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from brain_ops.domains.projects import (
    Project,
    build_project,
    render_claude_md,
    update_project_context,
)
from brain_ops.domains.projects.registry import (
    load_project_registry,
    save_project_registry,
)
from brain_ops.errors import ConfigError


@dataclass(slots=True, frozen=True)
class ProjectRegistryResult:
    project: Project
    registry_path: Path
    is_new: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "project": self.project.to_dict(),
            "registry_path": str(self.registry_path),
            "is_new": self.is_new,
        }


@dataclass(slots=True, frozen=True)
class ProjectClaudeMdResult:
    project_name: str
    output_path: Path
    content: str

    def to_dict(self) -> dict[str, object]:
        return {
            "project_name": self.project_name,
            "output_path": str(self.output_path),
        }


def execute_register_project_workflow(
    *,
    name: str,
    path: str,
    stack: list[str] | None,
    description: str | None,
    commands: dict[str, str] | None,
    load_registry_path,
) -> ProjectRegistryResult:
    registry_path = load_registry_path()
    projects = load_project_registry(registry_path)
    is_new = name.strip() not in projects
    project = build_project(
        name,
        path=path,
        stack=stack,
        description=description,
        commands=commands,
    )
    if not is_new:
        existing = projects[name.strip()]
        project.context = existing.context
    projects[project.name] = project
    save_project_registry(registry_path, projects)
    return ProjectRegistryResult(
        project=project,
        registry_path=registry_path,
        is_new=is_new,
    )


def execute_list_projects_workflow(
    *,
    load_registry_path,
) -> list[Project]:
    registry_path = load_registry_path()
    projects = load_project_registry(registry_path)
    return sorted(projects.values(), key=lambda p: p.name.lower())


def execute_project_context_workflow(
    *,
    name: str,
    load_registry_path,
) -> Project:
    registry_path = load_registry_path()
    projects = load_project_registry(registry_path)
    project = projects.get(name.strip())
    if project is None:
        available = ", ".join(sorted(projects.keys())) if projects else "none"
        raise ConfigError(f"Project '{name}' not found. Available: {available}.")
    return project


def execute_update_project_context_workflow(
    *,
    name: str,
    phase: str | None,
    pending: list[str] | None,
    decisions: list[str] | None,
    notes: str | None,
    load_registry_path,
) -> Project:
    registry_path = load_registry_path()
    projects = load_project_registry(registry_path)
    project = projects.get(name.strip())
    if project is None:
        available = ", ".join(sorted(projects.keys())) if projects else "none"
        raise ConfigError(f"Project '{name}' not found. Available: {available}.")
    update_project_context(
        project,
        phase=phase,
        pending=pending,
        decisions=decisions,
        notes=notes,
    )
    save_project_registry(registry_path, projects)
    return project


def execute_generate_claude_md_workflow(
    *,
    name: str,
    output_path: Path | None,
    load_registry_path,
    write_file=None,
) -> ProjectClaudeMdResult:
    registry_path = load_registry_path()
    projects = load_project_registry(registry_path)
    project = projects.get(name.strip())
    if project is None:
        available = ", ".join(sorted(projects.keys())) if projects else "none"
        raise ConfigError(f"Project '{name}' not found. Available: {available}.")
    content = render_claude_md(project)
    resolved_output = output_path or Path(project.path) / "CLAUDE.md"
    writer = write_file or _default_write_file
    writer(resolved_output, content)
    return ProjectClaudeMdResult(
        project_name=project.name,
        output_path=resolved_output,
        content=content,
    )


def _default_write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def execute_generate_all_claude_md_workflow(
    *,
    load_registry_path,
    write_file=None,
) -> list[ProjectClaudeMdResult]:
    registry_path = load_registry_path()
    projects = load_project_registry(registry_path)
    results: list[ProjectClaudeMdResult] = []
    for project in sorted(projects.values(), key=lambda p: p.name.lower()):
        content = render_claude_md(project)
        output_path = Path(project.path) / "CLAUDE.md"
        writer = write_file or _default_write_file
        writer(output_path, content)
        results.append(ProjectClaudeMdResult(
            project_name=project.name,
            output_path=output_path,
            content=content,
        ))
    return results


__all__ = [
    "ProjectClaudeMdResult",
    "ProjectRegistryResult",
    "execute_generate_all_claude_md_workflow",
    "execute_generate_claude_md_workflow",
    "execute_list_projects_workflow",
    "execute_project_context_workflow",
    "execute_register_project_workflow",
    "execute_update_project_context_workflow",
]
