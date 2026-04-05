"""CLI orchestration helpers for scheduling commands."""

from __future__ import annotations

import os
from pathlib import Path

from rich.console import Console
from rich.table import Table

from brain_ops.core.scheduling import (
    DEFAULT_JOBS,
    ScheduledJob,
    generate_crontab_entries,
    load_job_registry,
    save_job_registry,
)


def load_job_registry_path(explicit_path: Path | None = None) -> Path:
    if explicit_path is not None:
        return explicit_path
    env_path = os.getenv("BRAIN_OPS_JOB_REGISTRY")
    if env_path:
        return Path(env_path)
    return Path.home() / ".brain-ops" / "jobs.json"


def build_job_list_table(jobs: list[ScheduledJob]) -> Table:
    table = Table(title="Scheduled Jobs")
    table.add_column("Name")
    table.add_column("Schedule")
    table.add_column("Command")
    table.add_column("Enabled")
    table.add_column("Last Run")
    table.add_column("Last Status")
    for job in jobs:
        table.add_row(
            job.name,
            job.schedule,
            job.command,
            "Yes" if job.enabled else "No",
            job.last_run or "-",
            job.last_status or "-",
        )
    return table


def present_list_jobs_command(
    console: Console,
    *,
    as_json: bool,
) -> None:
    registry_path = load_job_registry_path()
    jobs = load_job_registry(registry_path)
    job_list = sorted(jobs.values(), key=lambda j: j.name)
    if as_json:
        console.print_json(data=[j.to_dict() for j in job_list])
        return
    if not job_list:
        console.print("No jobs registered. Run init-jobs to create defaults.")
        return
    console.print(build_job_list_table(job_list))


def present_init_jobs_command(
    console: Console,
    *,
    as_json: bool,
) -> None:
    registry_path = load_job_registry_path()
    jobs = load_job_registry(registry_path)
    added = 0
    for default_job in DEFAULT_JOBS:
        if default_job.name not in jobs:
            jobs[default_job.name] = default_job
            added += 1
    save_job_registry(registry_path, jobs)
    if as_json:
        console.print_json(data={"added": added, "total": len(jobs), "registry_path": str(registry_path)})
        return
    console.print(f"Initialized {added} new job(s). Total: {len(jobs)} jobs at {registry_path}")


def present_show_crontab_command(
    console: Console,
) -> None:
    registry_path = load_job_registry_path()
    jobs = load_job_registry(registry_path)
    if not jobs:
        console.print("No jobs registered. Run init-jobs first.")
        return
    console.print(generate_crontab_entries(jobs))


__all__ = [
    "build_job_list_table",
    "load_job_registry_path",
    "present_init_jobs_command",
    "present_list_jobs_command",
    "present_show_crontab_command",
]
