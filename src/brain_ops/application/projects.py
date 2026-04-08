"""Application workflows for project registry and context management."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
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
    vault_status: str | None = None
    vault_decisions: tuple[str, ...] = ()
    vault_bugs: tuple[str, ...] = ()
    vault_path: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "project": self.project.to_dict(),
            "recent_logs": self.recent_logs,
            "recent_commits": self.recent_commits,
            "vault_status": self.vault_status,
            "vault_decisions": list(self.vault_decisions),
            "vault_bugs": list(self.vault_bugs),
            "vault_path": self.vault_path,
        }


def execute_project_log_workflow(
    *,
    project_name: str,
    text: str,
    load_registry_path,
    load_database_path,
    vault_project_dir: Path | None = None,
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

    # Write to vault files (best-effort)
    _write_vault_log(vault_project_dir, entry_type, cleaned_text)

    return ProjectLogResult(
        project_name=project_name.strip(),
        entry_type=entry_type,
        entry_text=cleaned_text,
        registry_updated=registry_updated,
    )


def _write_vault_log(
    vault_project_dir: Path | None,
    entry_type: str,
    text: str,
) -> None:
    """Best-effort append to vault project files."""
    if vault_project_dir is None or not vault_project_dir.is_dir():
        return

    now = datetime.now(tz=timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")

    # Append to Changelog.md (within AUTO markers)
    changelog_path = vault_project_dir / "Changelog.md"
    if changelog_path.is_file():
        _append_to_changelog(changelog_path, date_str, entry_type, text)

    # Append to Decisions.md for decision entries
    if entry_type == "decision":
        decisions_path = vault_project_dir / "Decisions.md"
        if decisions_path.is_file():
            _append_line_to_file(
                decisions_path,
                f"\n- **{date_str}** — {text}\n",
            )

    # Append to Debugging.md for bug entries
    if entry_type == "bug":
        debugging_path = vault_project_dir / "Debugging.md"
        if debugging_path.is_file():
            _append_line_to_file(
                debugging_path,
                f"\n- **{date_str}** — {text}\n",
            )

    # Create/append to session note
    sessions_dir = vault_project_dir / "Sessions"
    if sessions_dir.is_dir():
        session_file = sessions_dir / f"Session {date_str}.md"
        if not session_file.exists():
            session_file.write_text(
                f"# Session {date_str}\n\n",
                encoding="utf-8",
            )
        _append_line_to_file(
            session_file,
            f"- **{time_str}** [{entry_type}] {text}\n",
        )


def _append_to_changelog(path: Path, date_str: str, entry_type: str, text: str) -> None:
    """Append entry within <!-- AUTO:START/END --> markers, or at the end."""
    content = path.read_text(encoding="utf-8")
    entry_line = f"- **{date_str}** [{entry_type}] {text}"

    auto_end_marker = "<!-- AUTO:END -->"
    if auto_end_marker in content:
        content = content.replace(
            auto_end_marker,
            f"{entry_line}\n{auto_end_marker}",
        )
        path.write_text(content, encoding="utf-8")
    else:
        auto_start = "<!-- AUTO:START -->"
        with open(path, "a", encoding="utf-8") as f:
            if auto_start not in content:
                f.write(f"\n{auto_start}\n")
            f.write(f"{entry_line}\n")


def _append_line_to_file(path: Path, line: str) -> None:
    """Append a line to an existing file."""
    with open(path, "a", encoding="utf-8") as f:
        f.write(line)


# ---------------------------------------------------------------------------
# Vault reading helpers for session
# ---------------------------------------------------------------------------


def _extract_section(content: str, heading: str, max_chars: int = 2000) -> str | None:
    """Extract content under a markdown heading (## level)."""
    pattern = rf"(?:^|\n)##\s+{re.escape(heading)}\s*\n(.*?)(?=\n##\s|\Z)"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        text = match.group(1).strip()
        return text[:max_chars] if text else None
    return None


def _read_vault_project_data(
    vault_project_dir: Path,
    project_name: str,
) -> tuple[str | None, list[str], list[str]]:
    """Read vault project files and return (status, decisions, bugs)."""
    vault_status: str | None = None
    vault_decisions: list[str] = []
    vault_bugs: list[str] = []

    # Try project root note
    for candidate in [f"{project_name}.md", "Brain-Ops.md"]:
        root_note = vault_project_dir / candidate
        if root_note.is_file():
            content = root_note.read_text(encoding="utf-8")[:4000]
            # Try multiple heading names for current state
            for heading in ("Current Focus", "Current status", "In Progress"):
                status = _extract_section(content, heading)
                if status:
                    vault_status = status
                    break
            next_actions = _extract_section(content, "Next Actions")
            if not next_actions:
                next_actions = _extract_section(content, "Next actions")
            if next_actions and not vault_status:
                vault_status = next_actions
            elif next_actions:
                vault_status = f"{vault_status}\n\nNext actions:\n{next_actions}"
            # Extract blockers
            blockers = _extract_section(content, "Blockers")
            if blockers:
                vault_status = f"{vault_status}\n\nBlockers:\n{blockers}" if vault_status else blockers
            break

    # Read Decisions.md — extract ADR titles (lines starting with "### ")
    decisions_path = vault_project_dir / "Decisions.md"
    if decisions_path.is_file():
        content = decisions_path.read_text(encoding="utf-8")
        # Prefer ADR titles (### headings) over bullets
        adrs = re.findall(r"^###\s+(.+)$", content, re.MULTILINE)
        if adrs:
            vault_decisions = adrs[-5:]
        else:
            items = re.findall(r"^[-*]\s+(.+)$", content, re.MULTILINE)
            vault_decisions = items[-5:] if items else []

    # Read Debugging.md — extract problem titles (## headings), not all bullets
    debugging_path = vault_project_dir / "Debugging.md"
    if debugging_path.is_file():
        content = debugging_path.read_text(encoding="utf-8")
        # Extract section headings as bug summaries — they're the problem titles
        headings = re.findall(r"^##\s+(?!General)(.+)$", content, re.MULTILINE)
        vault_bugs = headings[:5] if headings else []

    return vault_status, vault_decisions, vault_bugs


def _resolve_vault_project_dir(
    config_path: Path | None,
    project_name: str,
) -> Path | None:
    """Resolve vault project directory from config, returning None on failure."""
    if config_path is None:
        return None
    try:
        from brain_ops.config import load_config

        config = load_config(config_path)
        vault_dir = config.vault_path / "04 - Projects" / project_name
        if vault_dir.is_dir():
            return vault_dir
    except Exception:
        pass
    return None


def execute_session_workflow(
    *,
    project_name: str,
    days: int = 7,
    load_registry_path,
    load_database_path,
    run_git_log=None,
    config_path: Path | None = None,
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

    # Read vault project data
    vault_status: str | None = None
    vault_decisions: tuple[str, ...] = ()
    vault_bugs: tuple[str, ...] = ()
    vault_path_str: str | None = None

    vault_project_dir = _resolve_vault_project_dir(config_path, project.name)
    if vault_project_dir is not None:
        vault_path_str = str(vault_project_dir)
        status, decisions, bugs = _read_vault_project_data(vault_project_dir, project.name)
        vault_status = status
        vault_decisions = tuple(decisions)
        vault_bugs = tuple(bugs)

    return ProjectSessionResult(
        project=project,
        recent_logs=recent_logs,
        recent_commits=recent_commits,
        vault_status=vault_status,
        vault_decisions=vault_decisions,
        vault_bugs=vault_bugs,
        vault_path=vault_path_str,
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


# ---------------------------------------------------------------------------
# Audit project workflow
# ---------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class ProjectAuditResult:
    project_name: str
    issues: tuple[str, ...]
    score: int  # 0-100

    def to_dict(self) -> dict[str, object]:
        return {
            "project_name": self.project_name,
            "issues": list(self.issues),
            "score": self.score,
        }


def execute_audit_project_workflow(
    *,
    project_name: str,
    load_registry_path,
    load_database_path,
    config_path: Path | None = None,
) -> ProjectAuditResult:
    registry_path = load_registry_path()
    projects = load_project_registry(registry_path)
    project = projects.get(project_name.strip())
    if project is None:
        available = ", ".join(sorted(projects.keys())) if projects else "none"
        raise ConfigError(f"Project '{project_name}' not found. Available: {available}.")

    issues: list[str] = []
    score = 100

    # Resolve vault project directory
    vault_project_dir = _resolve_vault_project_dir(config_path, project.name)

    # --- Vault file checks ---
    expected_files: list[tuple[str, int]] = [
        ("Architecture.md", 7),
        ("Decisions.md", 5),
        ("Runbook.md", 7),
        ("CLI Reference.md", 5),
        ("Workflows.md", 5),
        ("Debugging.md", 5),
        ("Changelog.md", 5),
    ]

    # Check for project root note
    root_note_found = False
    if vault_project_dir is not None:
        for candidate in [f"{project.name}.md", "Brain-Ops.md"]:
            if (vault_project_dir / candidate).is_file():
                root_note_found = True
                break
    if not root_note_found:
        issues.append("Missing project root note (Brain-Ops.md or {name}.md)")
        score -= 10

    if vault_project_dir is not None:
        for filename, penalty in expected_files:
            file_path = vault_project_dir / filename
            if not file_path.is_file():
                issues.append(f"Missing {filename}")
                score -= penalty
            elif file_path.stat().st_size == 0:
                issues.append(f"{filename} is empty")
                score -= penalty

        # Check for recent session notes
        sessions_dir = vault_project_dir / "Sessions"
        if sessions_dir.is_dir():
            from datetime import timedelta

            cutoff = datetime.now(tz=timezone.utc) - timedelta(days=7)
            has_recent_session = False
            for session_file in sessions_dir.glob("Session *.md"):
                # Extract date from filename
                match = re.search(r"Session (\d{4}-\d{2}-\d{2})", session_file.name)
                if match:
                    try:
                        file_date = datetime.strptime(match.group(1), "%Y-%m-%d").replace(
                            tzinfo=timezone.utc
                        )
                        if file_date >= cutoff:
                            has_recent_session = True
                            break
                    except ValueError:
                        pass
            if not has_recent_session:
                issues.append("No session notes in last 7 days")
                score -= 5
        else:
            issues.append("No Sessions/ folder")
            score -= 5
    else:
        issues.append("Vault project folder not found")
        score -= 15

    # --- SQLite checks ---
    try:
        db_path = load_database_path()
        recent_logs = fetch_recent_project_logs(db_path, project_name=project_name.strip(), days=7)
        if not recent_logs:
            issues.append("No project logs in last 7 days")
            score -= 5
    except Exception:
        issues.append("Could not read project logs from database")
        score -= 5

    # --- Registry checks ---
    if not project.context.phase:
        issues.append("Registry has no phase set")
        score -= 5
    if not project.context.pending:
        issues.append("Registry has no pending items")
        score -= 3
    if not project.context.decisions:
        issues.append("Registry has no decisions")
        score -= 3
    if not project.commands:
        issues.append("Registry has no commands defined")
        score -= 3

    score = max(score, 0)

    return ProjectAuditResult(
        project_name=project_name.strip(),
        issues=tuple(issues),
        score=score,
    )


__all__ = [
    "ProjectAuditResult",
    "ProjectClaudeMdResult",
    "ProjectLogResult",
    "ProjectRegistryResult",
    "ProjectSessionResult",
    "execute_audit_project_workflow",
    "execute_generate_all_claude_md_workflow",
    "execute_generate_claude_md_workflow",
    "execute_list_projects_workflow",
    "execute_project_context_workflow",
    "execute_project_log_workflow",
    "execute_register_project_workflow",
    "execute_session_workflow",
    "execute_update_project_context_workflow",
]
