"""CLI orchestration helpers for monitoring source commands."""

from __future__ import annotations

import os
from pathlib import Path

from rich.console import Console
from rich.table import Table

from brain_ops.application.sources import (
    SourceCheckResult,
    execute_add_source_workflow,
    execute_check_all_sources_workflow,
    execute_check_source_workflow,
    execute_list_sources_workflow,
    execute_remove_source_workflow,
)
from brain_ops.domains.monitoring import MonitorSource


def load_source_registry_path(explicit_path: Path | None = None) -> Path:
    if explicit_path is not None:
        return explicit_path
    env_path = os.getenv("BRAIN_OPS_SOURCE_REGISTRY")
    if env_path:
        return Path(env_path)
    return Path.home() / ".brain-ops" / "sources.json"


def load_snapshots_dir(explicit_path: Path | None = None) -> Path:
    if explicit_path is not None:
        return explicit_path
    env_path = os.getenv("BRAIN_OPS_SNAPSHOTS_DIR")
    if env_path:
        return Path(env_path)
    return Path.home() / ".brain-ops" / "snapshots"


def build_source_list_table(sources: list[MonitorSource]) -> Table:
    table = Table(title="Monitored Sources")
    table.add_column("Name")
    table.add_column("URL")
    table.add_column("Type")
    table.add_column("Interval")
    for source in sources:
        table.add_row(source.name, source.url, source.source_type, source.check_interval)
    return table


def build_source_check_table(result: SourceCheckResult) -> Table:
    table = Table(title=f"Check: {result.source.name}")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("URL", result.source.url)
    table.add_row("Changes", "Yes" if result.diff.has_changes else "No")
    table.add_row("Summary", result.diff.summary)
    table.add_row("Content length", str(result.snapshot.content_length))
    table.add_row("Hash", result.snapshot.content_hash[:16] + "...")
    return table


def present_add_source_command(
    console: Console,
    *,
    name: str,
    url: str,
    source_type: str,
    selector: str | None,
    check_interval: str,
    description: str | None,
    tags: list[str] | None,
    as_json: bool,
) -> None:
    result = execute_add_source_workflow(
        name=name,
        url=url,
        source_type=source_type,
        selector=selector,
        check_interval=check_interval,
        description=description,
        tags=tags,
        load_registry_path=lambda: load_source_registry_path(),
    )
    if as_json:
        console.print_json(data=result.to_dict())
        return
    action = "Added" if result.is_new else "Updated"
    console.print(f"{action} source '{result.source.name}' ({result.source.url})")


def present_list_sources_command(
    console: Console,
    *,
    as_json: bool,
) -> None:
    sources = execute_list_sources_workflow(
        load_registry_path=lambda: load_source_registry_path(),
    )
    if as_json:
        console.print_json(data=[s.to_dict() for s in sources])
        return
    if not sources:
        console.print("No sources registered.")
        return
    console.print(build_source_list_table(sources))


def present_remove_source_command(
    console: Console,
    *,
    name: str,
    as_json: bool,
) -> None:
    source = execute_remove_source_workflow(
        name=name,
        load_registry_path=lambda: load_source_registry_path(),
    )
    if as_json:
        console.print_json(data=source.to_dict())
        return
    console.print(f"Removed source '{source.name}'")


def present_check_source_command(
    console: Console,
    *,
    name: str,
    as_json: bool,
) -> None:
    result = execute_check_source_workflow(
        name=name,
        load_registry_path=lambda: load_source_registry_path(),
        load_snapshots_dir=lambda: load_snapshots_dir(),
    )
    if as_json:
        console.print_json(data=result.to_dict())
        return
    console.print(build_source_check_table(result))


def present_check_all_sources_command(
    console: Console,
    *,
    as_json: bool,
) -> None:
    results = execute_check_all_sources_workflow(
        load_registry_path=lambda: load_source_registry_path(),
        load_snapshots_dir=lambda: load_snapshots_dir(),
    )
    if as_json:
        console.print_json(data=[r.to_dict() for r in results])
        return
    if not results:
        console.print("No sources to check.")
        return
    for result in results:
        console.print(build_source_check_table(result))
        console.print()


__all__ = [
    "build_source_check_table",
    "build_source_list_table",
    "load_snapshots_dir",
    "load_source_registry_path",
    "present_add_source_command",
    "present_check_all_sources_command",
    "present_check_source_command",
    "present_list_sources_command",
    "present_remove_source_command",
]
