"""Scheduled job definitions and run tracking."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass(slots=True)
class ScheduledJob:
    name: str
    schedule: str
    command: str
    description: str | None = None
    enabled: bool = True
    last_run: str | None = None
    last_status: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "schedule": self.schedule,
            "command": self.command,
            "description": self.description,
            "enabled": self.enabled,
            "last_run": self.last_run,
            "last_status": self.last_status,
        }

    @staticmethod
    def from_dict(data: dict[str, object]) -> ScheduledJob:
        return ScheduledJob(
            name=str(data.get("name", "")),
            schedule=str(data.get("schedule", "daily")),
            command=str(data.get("command", "")),
            description=data.get("description") if isinstance(data.get("description"), str) else None,
            enabled=bool(data.get("enabled", True)),
            last_run=data.get("last_run") if isinstance(data.get("last_run"), str) else None,
            last_status=data.get("last_status") if isinstance(data.get("last_status"), str) else None,
        )


@dataclass(slots=True, frozen=True)
class JobRunResult:
    job_name: str
    started_at: str
    status: str
    detail: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "job_name": self.job_name,
            "started_at": self.started_at,
            "status": self.status,
            "detail": self.detail,
        }


SCHEDULE_PRESETS: dict[str, str] = {
    "daily": "0 6 * * *",
    "hourly": "0 * * * *",
    "weekly": "0 6 * * 1",
}

DEFAULT_JOBS: list[ScheduledJob] = [
    ScheduledJob(
        name="check-all-sources",
        schedule="daily",
        command="brain-ops check-all-sources",
        description="Fetch all monitored sources and detect changes.",
    ),
    ScheduledJob(
        name="audit-vault",
        schedule="weekly",
        command="brain-ops audit-vault",
        description="Run vault quality checks.",
    ),
    ScheduledJob(
        name="compile-knowledge",
        schedule="daily",
        command="brain-ops compile-knowledge",
        description="Compile entity frontmatter to SQLite.",
    ),
    ScheduledJob(
        name="entity-index",
        schedule="daily",
        command="brain-ops entity-index",
        description="Regenerate the knowledge entity index.",
    ),
]


def build_scheduled_job(
    name: str,
    *,
    schedule: str,
    command: str,
    description: str | None = None,
) -> ScheduledJob:
    if not name.strip():
        raise ValueError("Job name cannot be empty.")
    if not command.strip():
        raise ValueError("Job command cannot be empty.")
    return ScheduledJob(
        name=name.strip(),
        schedule=schedule.strip(),
        command=command.strip(),
        description=description,
    )


def record_job_run(job: ScheduledJob, *, status: str, detail: str | None = None) -> JobRunResult:
    now = datetime.now(timezone.utc).isoformat()
    job.last_run = now
    job.last_status = status
    return JobRunResult(
        job_name=job.name,
        started_at=now,
        status=status,
        detail=detail,
    )


def load_job_registry(registry_path: Path) -> dict[str, ScheduledJob]:
    if not registry_path.exists():
        return {}
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}
    return {
        name: ScheduledJob.from_dict(job_data)
        for name, job_data in data.items()
        if isinstance(job_data, dict)
    }


def save_job_registry(registry_path: Path, jobs: dict[str, ScheduledJob]) -> Path:
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {name: job.to_dict() for name, job in jobs.items()}
    registry_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return registry_path


def generate_crontab_entries(jobs: dict[str, ScheduledJob]) -> str:
    lines: list[str] = ["# brain-ops scheduled jobs"]
    for job in sorted(jobs.values(), key=lambda j: j.name):
        if not job.enabled:
            continue
        cron_expr = SCHEDULE_PRESETS.get(job.schedule, job.schedule)
        lines.append(f"{cron_expr} {job.command}  # {job.name}")
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "DEFAULT_JOBS",
    "JobRunResult",
    "SCHEDULE_PRESETS",
    "ScheduledJob",
    "build_scheduled_job",
    "generate_crontab_entries",
    "load_job_registry",
    "record_job_run",
    "save_job_registry",
]
