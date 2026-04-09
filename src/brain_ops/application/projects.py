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

    now = datetime.now()  # local time, not UTC
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")

    # Changelog: NO auto-populate (redundante con Sessions).
    # Se genera como resumen curado via `brain refresh-project`.

    # Prepend to Decisions.md for decision entries (ADR-lite, newest first)
    if entry_type == "decision":
        decisions_path = vault_project_dir / "Decisions.md"
        if decisions_path.is_file():
            content = decisions_path.read_text(encoding="utf-8")
            existing = re.findall(r"^##+ \d+\.", content, re.MULTILINE)
            next_num = len(existing) + 1
            new_entry = (
                f"\n---\n\n## {next_num:03d}. {text}\n\n"
                f"**Fecha:** {date_str}\n"
                f"**Contexto:** (pendiente de documentar)\n"
                f"**Decisión:** {text}\n\n"
            )
            # Insert after the intro paragraph (first ---)
            first_separator = content.find("\n---\n")
            if first_separator >= 0:
                insert_pos = first_separator
                decisions_path.write_text(
                    content[:insert_pos] + new_entry + content[insert_pos:],
                    encoding="utf-8",
                )
            else:
                _append_line_to_file(decisions_path, new_entry)

    # Append to Debugging.md for bug entries (structured format)
    if entry_type == "bug":
        debugging_path = vault_project_dir / "Debugging.md"
        if debugging_path.is_file():
            _append_line_to_file(
                debugging_path,
                f"\n---\n\n## {text}\n\n"
                f"**Fecha:** {date_str}\n"
                f"**Síntoma:** (pendiente)\n"
                f"**Causa raíz:** (pendiente)\n"
                f"**Solución:** (pendiente)\n\n",
            )

    # Create/prepend to session note (newest entry first)
    sessions_dir = vault_project_dir / "Sessions"
    if sessions_dir.is_dir():
        session_file = sessions_dir / f"Sesión {date_str}.md"
        entry_line = f"- **{time_str}** [{entry_type}] {text}\n"
        heading = f"# Sesión {date_str}\n\n"
        if not session_file.exists():
            session_file.write_text(heading + entry_line, encoding="utf-8")
        else:
            content = session_file.read_text(encoding="utf-8")
            # Find the first bullet line — insert before it
            lines = content.splitlines(keepends=True)
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.startswith("- **"):
                    insert_idx = i
                    break
            else:
                # No bullets found — insert after heading
                insert_idx = len(lines)
            lines.insert(insert_idx, entry_line)
            session_file.write_text("".join(lines), encoding="utf-8")


def _append_to_changelog(path: Path, date_str: str, entry_type: str, text: str) -> None:
    """Insert entry at TOP of <!-- AUTO:START/END --> block (most recent first).

    If path points to a generic Changelog.md, redirects to a monthly file
    (e.g. Changelog 2026-04.md) in the same directory.
    """
    # Redirect to monthly file inside Changelog/ folder
    if path.name == "Changelog.md":
        month_str = date_str[:7]  # "2026-04"
        changelog_dir = path.parent / "Changelog"
        changelog_dir.mkdir(parents=True, exist_ok=True)
        monthly_path = changelog_dir / f"{month_str}.md"
        if not monthly_path.exists():
            project_name = path.parent.name
            monthly_path.write_text(
                f"---\ntype: changelog\nproject: {project_name}\nperiod: {month_str}\n---\n\n"
                f"# Changelog {month_str}\n\n<!-- AUTO:START -->\n<!-- AUTO:END -->\n",
                encoding="utf-8",
            )
        path = monthly_path

    entry_line = f"- **{date_str}** [{entry_type}] {text}"

    content = path.read_text(encoding="utf-8")
    auto_start_marker = "<!-- AUTO:START -->"
    if auto_start_marker in content:
        # Insert right AFTER AUTO:START (newest first)
        content = content.replace(
            auto_start_marker,
            f"{auto_start_marker}\n{entry_line}",
        )
        path.write_text(content, encoding="utf-8")
    else:
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"\n{auto_start_marker}\n{entry_line}\n<!-- AUTO:END -->\n")


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


def _extract_section_list(content: str, *headings: str) -> list[str]:
    for heading in headings:
        section = _extract_section(content, heading)
        if not section:
            continue
        items: list[str] = []
        for line in section.splitlines():
            text = line.strip()
            if not text:
                continue
            text = re.sub(r"^[-*]\s+", "", text)
            text = re.sub(r"^\d+\.\s+", "", text)
            text = text.strip()
            if text:
                items.append(text)
        if items:
            return items
    return []


def _sync_project_registry_from_vault(project: Project, vault_project_dir: Path) -> bool:
    changed = False
    root_note = None
    for candidate in [f"{project.name}.md", "Brain-Ops.md"]:
        candidate_path = vault_project_dir / candidate
        if candidate_path.is_file():
            root_note = candidate_path
            break

    if root_note is not None:
        content = root_note.read_text(encoding="utf-8")[:12000]
        phase = (
            _extract_section(content, "Foco actual")
            or _extract_section(content, "Current Focus")
            or _extract_section(content, "Current status")
            or _extract_section(content, "Estado actual")
        )
        pending = _extract_section_list(
            content,
            "Próximas acciones (top 3)",
            "Proximas acciones (top 3)",
            "Próximas acciones",
            "Proximas acciones",
            "Next actions",
            "En progreso",
            "In Progress",
        )

        if project.context.phase != phase:
            project.context.phase = phase
            changed = True
        if project.context.pending != pending:
            project.context.pending = pending
            changed = True
        if project.context.notes is not None:
            project.context.notes = None
            changed = True

    decisions_path = vault_project_dir / "Decisions.md"
    if decisions_path.is_file():
        content = decisions_path.read_text(encoding="utf-8")
        adrs = re.findall(r"^###\s+(.+)$", content, re.MULTILINE)
        if adrs:
            decisions = adrs[-7:]
        else:
            decisions = re.findall(r"^[-*]\s+(.+)$", content, re.MULTILINE)[-7:]
        if project.context.decisions != decisions:
            project.context.decisions = decisions
            changed = True

    commands = _derive_context_commands(project)
    if project.commands != commands:
        project.commands = commands
        changed = True

    return changed


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
        ("Changelog.md", 5),  # Also accepts Changelog/ folder
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
            # Changelog.md can be a file OR a Changelog/ folder
            if filename == "Changelog.md" and not file_path.is_file():
                changelog_dir = vault_project_dir / "Changelog"
                if changelog_dir.is_dir() and any(changelog_dir.iterdir()):
                    continue  # Changelog/ folder with files is fine
            if not file_path.is_file():
                issues.append(f"Falta {filename}")
                score -= penalty
            elif file_path.stat().st_size == 0:
                issues.append(f"{filename} está vacío")
                score -= penalty

        # Check for recent session notes
        sessions_dir = vault_project_dir / "Sessions"
        if sessions_dir.is_dir():
            from datetime import timedelta

            cutoff = datetime.now(tz=timezone.utc) - timedelta(days=7)
            has_recent_session = False
            # Support both "Session" and "Sesión" naming
            for session_file in list(sessions_dir.glob("Session *.md")) + list(sessions_dir.glob("Sesión *.md")):
                # Extract date from filename
                match = re.search(r"(?:Session|Sesión) (\d{4}-\d{2}-\d{2})", session_file.name)
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


# ============================================================================
# REFRESH PROJECT — regenerate auto-derivable sections
# ============================================================================

@dataclass(slots=True, frozen=True)
class ProjectRefreshResult:
    project_name: str
    refreshed: tuple[str, ...]
    skipped: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "project_name": self.project_name,
            "refreshed": list(self.refreshed),
            "skipped": list(self.skipped),
        }


def _refresh_auto_block(file_path: Path, new_content: str) -> bool:
    """Replace content between AUTO:START/END markers. Returns True if changed."""
    if not file_path.is_file():
        return False
    content = file_path.read_text(encoding="utf-8")
    start_marker = "<!-- AUTO:START -->"
    end_marker = "<!-- AUTO:END -->"
    if start_marker not in content or end_marker not in content:
        return False
    start_idx = content.index(start_marker) + len(start_marker)
    end_idx = content.index(end_marker)
    new_full = content[:start_idx] + "\n" + new_content.strip() + "\n" + content[end_idx:]
    if new_full == content:
        return False
    file_path.write_text(new_full, encoding="utf-8")
    return True


def _generate_cli_reference(project_path: str | None) -> str:
    """Generate CLI reference from brain --help."""
    import subprocess
    try:
        result = subprocess.run(
            ["brain", "--help"],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return ""


def _derive_context_commands(project: Project) -> dict[str, str]:
    commands = dict(project.commands)
    project_dir = Path(project.path)
    if project_dir.is_dir() and (project_dir / "uv.lock").is_file() and (project_dir / "tests").is_dir():
        commands["test"] = "uv run python -m unittest discover -s tests -v"
    return commands


def build_agent_context_pack(result: ProjectSessionResult) -> str:
    """Build the compact project briefing used by agents and auto context packs."""
    project = result.project
    sections: list[str] = []

    header = f"Project: {project.name}"
    if project.description:
        header += f" — {project.description}"
    if project.stack:
        header += f"\nStack: {', '.join(project.stack)}"
    sections.append(header)

    if result.vault_status:
        sections.append(f"Status: {result.vault_status[:500]}")

    commands = _derive_context_commands(project)
    if commands:
        cmd_lines = [f"  {label}: {cmd}" for label, cmd in commands.items()]
        sections.append("Commands:\n" + "\n".join(cmd_lines))

    decisions = list(result.vault_decisions or []) or list(project.context.decisions or [])
    if decisions:
        sections.append("Recent decisions:\n" + "\n".join(f"  - {d}" for d in decisions[-3:]))

    visible_logs = [
        log
        for log in (result.recent_logs or [])
        if log.get("entry_type") not in {"bug", "blocker", "next"}
    ]
    if visible_logs:
        log_lines = []
        for log in visible_logs[:5]:
            date_part = log["logged_at"][:10] if log.get("logged_at") else "?"
            log_lines.append(f"  [{date_part}] {log['entry_type']}: {log['entry_text'][:80]}")
        sections.append("Recent activity:\n" + "\n".join(log_lines))

    if result.recent_commits:
        sections.append("Recent commits:\n" + "\n".join(f"  {c}" for c in result.recent_commits[:3]))

    return "\n\n".join(sections)


def _generate_context_pack_content(
    project_name: str,
    load_registry_path,
    load_database_path,
    config_path=None,
) -> str:
    """Generate context pack content using the session workflow."""
    try:
        result = execute_session_workflow(
            project_name=project_name,
            load_registry_path=load_registry_path,
            load_database_path=load_database_path,
            config_path=config_path,
        )
        context = build_agent_context_pack(result)
        return (
            context.replace("Project:", "Proyecto:")
            .replace("\nStatus:", "\nEstado:")
            .replace("\nCommands:", "\nComandos:")
            .replace("\nRecent decisions:", "\nDecisiones recientes:")
            .replace("\nRecent activity:", "\nActividad reciente:")
            .replace("\nRecent commits:", "\nCommits recientes:")
        )
    except Exception:
        return ""


def _count_tests(project_path: str | None) -> int | None:
    """Count passing tests."""
    if not project_path:
        return None
    import subprocess
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/", "-q", "--co"],
            capture_output=True, text=True, timeout=30,
            cwd=project_path,
        )
        if result.returncode == 0:
            # Count lines that look like test items
            lines = [l for l in result.stdout.strip().splitlines() if "::" in l]
            return len(lines)
    except Exception:
        pass
    return None


def execute_refresh_project_workflow(
    *,
    project_name: str,
    load_registry_path,
    load_database_path,
    config_path=None,
) -> ProjectRefreshResult:
    """Refresh auto-derivable sections of project docs without destroying manual content."""
    registry_path = load_registry_path()
    registry = load_project_registry(registry_path)
    project = registry.get(project_name.strip())
    if project is None:
        raise ConfigError(f"Proyecto '{project_name}' no encontrado en el registry.")

    vault_project_dir = _resolve_vault_project_dir(config_path, project.name)
    if vault_project_dir is None:
        return ProjectRefreshResult(
            project_name=project.name,
            refreshed=(),
            skipped=("vault folder not found",),
        )

    refreshed: list[str] = []
    skipped: list[str] = []

    if _sync_project_registry_from_vault(project, vault_project_dir):
        registry[project.name] = project
        save_project_registry(registry_path, registry)
        refreshed.append("Project registry context")
    else:
        skipped.append("Project registry context (sin cambios)")

    # 1. Refresh Context Pack
    context_pack_dir = vault_project_dir / "Context Packs"
    context_pack_dir.mkdir(parents=True, exist_ok=True)
    pack_path = context_pack_dir / f"{project.name} Context Pack.md"
    try:
        pack_content = _generate_context_pack_content(
            project_name=project.name,
            load_registry_path=load_registry_path,
            load_database_path=load_database_path,
            config_path=config_path,
        )
        if pack_content:
            if pack_path.exists():
                if _refresh_auto_block(pack_path, pack_content):
                    refreshed.append("Context Pack (auto-block)")
                else:
                    skipped.append("Context Pack (sin cambios)")
            else:
                from datetime import date
                pack_path.write_text(
                    f"---\ntype: context_pack\nproject: {project.name}\n"
                    f"actualizado: {date.today().isoformat()}\n---\n\n"
                    f"# {project.name} — Context Pack\n\n"
                    f"<!-- AUTO:START -->\n{pack_content}\n<!-- AUTO:END -->\n",
                    encoding="utf-8",
                )
                refreshed.append("Context Pack (creado)")
        else:
            skipped.append("Context Pack (no se pudo generar)")
    except Exception:
        skipped.append("Context Pack (error)")

    # 2. Refresh Brain-Ops.md auto sections (test count, entity count)
    root_note = None
    for candidate in [f"{project.name}.md", "Brain-Ops.md"]:
        p = vault_project_dir / candidate
        if p.is_file():
            root_note = p
            break
    if root_note:
        test_count = _count_tests(project.path)
        if test_count is not None:
            content = root_note.read_text(encoding="utf-8")
            import re
            # Update test count in any format like "**NNN tests**"
            new_content = re.sub(
                r"\*\*\d+ tests?\*\*",
                f"**{test_count} tests**",
                content,
            )
            if new_content != content:
                root_note.write_text(new_content, encoding="utf-8")
                refreshed.append(f"Brain-Ops.md (tests: {test_count})")
            else:
                skipped.append("Brain-Ops.md (sin cambios)")
        else:
            skipped.append("Brain-Ops.md (no se pudo contar tests)")
    else:
        skipped.append("Brain-Ops.md (no encontrado)")

    # 3. Refresh CLI Reference auto block if it has AUTO markers
    cli_ref = vault_project_dir / "CLI Reference.md"
    if cli_ref.is_file():
        cli_help = _generate_cli_reference(project.path)
        if cli_help and _refresh_auto_block(cli_ref, f"```\n{cli_help}\n```"):
            refreshed.append("CLI Reference.md (auto-block)")
        else:
            skipped.append("CLI Reference.md (sin marcadores AUTO o sin cambios)")
    else:
        skipped.append("CLI Reference.md (no encontrado)")

    return ProjectRefreshResult(
        project_name=project.name,
        refreshed=tuple(refreshed),
        skipped=tuple(skipped),
    )


__all__ = [
    "ProjectAuditResult",
    "ProjectClaudeMdResult",
    "ProjectLogResult",
    "ProjectRegistryResult",
    "ProjectSessionResult",
    "build_agent_context_pack",
    "execute_audit_project_workflow",
    "execute_generate_all_claude_md_workflow",
    "execute_generate_claude_md_workflow",
    "execute_list_projects_workflow",
    "execute_project_context_workflow",
    "execute_project_log_workflow",
    "execute_refresh_project_workflow",
    "execute_register_project_workflow",
    "execute_session_workflow",
    "execute_update_project_context_workflow",
]
