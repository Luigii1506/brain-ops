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
from brain_ops.storage.sqlite.project_logs import (
    fetch_recent_project_logs,
    insert_project_log,
)


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


_ENTRY_TYPE_PREFIXES = [
    (("decisión:", "decision:"), "decision"),
    (("bug:",), "bug"),
    (("next:", "siguiente:"), "next"),
    (("blocker:", "bloqueo:"), "blocker"),
    (("idea:",), "idea"),
]


def _classify_entry(text: str) -> tuple[str, str]:
    """Return (entry_type, cleaned_text) based on keyword prefix."""
    lower = text.lower().strip()
    for prefixes, entry_type in _ENTRY_TYPE_PREFIXES:
        for prefix in prefixes:
            if lower.startswith(prefix):
                cleaned = text.strip()[len(prefix):].strip()
                return entry_type, cleaned
    return "update", text.strip()


@dataclass(slots=True, frozen=True)
class ProjectLogResult:
    project_name: str
    entry_type: str
    entry_text: str
    registry_updated: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "project_name": self.project_name,
            "entry_type": self.entry_type,
            "entry_text": self.entry_text,
            "registry_updated": self.registry_updated,
        }


@dataclass(slots=True, frozen=True)
class ProjectSessionResult:
    project: Project
    recent_logs: list[dict]
    recent_commits: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "project": self.project.to_dict(),
            "recent_logs": self.recent_logs,
            "recent_commits": self.recent_commits,
        }


def execute_project_log_workflow(
    *,
    project_name: str,
    text: str,
    load_registry_path,
    load_database_path,
) -> ProjectLogResult:
    registry_path = load_registry_path()
    projects = load_project_registry(registry_path)
    project = projects.get(project_name.strip())
    if project is None:
        available = ", ".join(sorted(projects.keys())) if projects else "none"
        raise ConfigError(f"Project '{project_name}' not found. Available: {available}.")

    entry_type, cleaned_text = _classify_entry(text)

    db_path = load_database_path()
    insert_project_log(
        db_path,
        project_name=project_name.strip(),
        entry_type=entry_type,
        entry_text=cleaned_text,
        source="cli",
    )

    registry_updated = False
    if entry_type == "decision":
        if project.context.decisions is None:
            project.context.decisions = []
        project.context.decisions.append(cleaned_text)
        registry_updated = True
    elif entry_type == "next":
        if project.context.pending is None:
            project.context.pending = []
        project.context.pending.append(cleaned_text)
        registry_updated = True

    if registry_updated:
        save_project_registry(registry_path, projects)

    return ProjectLogResult(
        project_name=project_name.strip(),
        entry_type=entry_type,
        entry_text=cleaned_text,
        registry_updated=registry_updated,
    )


def execute_session_workflow(
    *,
    project_name: str,
    days: int = 7,
    load_registry_path,
    load_database_path,
    run_git_log=None,
) -> ProjectSessionResult:
    registry_path = load_registry_path()
    projects = load_project_registry(registry_path)
    project = projects.get(project_name.strip())
    if project is None:
        available = ", ".join(sorted(projects.keys())) if projects else "none"
        raise ConfigError(f"Project '{project_name}' not found. Available: {available}.")

    db_path = load_database_path()
    recent_logs = fetch_recent_project_logs(db_path, project_name=project_name.strip(), days=days)

    recent_commits: list[str] = []
    if run_git_log is not None:
        recent_commits = run_git_log(project.path)
    else:
        recent_commits = _default_git_log(project.path)

    return ProjectSessionResult(
        project=project,
        recent_logs=recent_logs,
        recent_commits=recent_commits,
    )


def _default_git_log(project_path: str) -> list[str]:
    import subprocess

    project_dir = Path(project_path)
    if not project_dir.is_dir():
        return []
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "-10"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return [line for line in result.stdout.strip().splitlines() if line]
        return []
    except (subprocess.SubprocessError, FileNotFoundError):
        return []


__all__ = [
    "ProjectClaudeMdResult",
    "ProjectLogResult",
    "ProjectRegistryResult",
    "ProjectSessionResult",
    "execute_generate_all_claude_md_workflow",
    "execute_generate_claude_md_workflow",
    "execute_list_projects_workflow",
    "execute_project_context_workflow",
    "execute_project_log_workflow",
    "execute_register_project_workflow",
    "execute_session_workflow",
    "execute_update_project_context_workflow",
]
