"""CLI orchestration helpers for system/bootstrap commands."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from brain_ops.application import (
    execute_info_workflow,
    execute_init_db_workflow,
    execute_init_workflow,
)
from brain_ops.constants import DEFAULT_INIT_CONFIG_PATH
from brain_ops.storage import initialize_database

from .runtime import load_event_sink, load_runtime_config
from .setup import initialize_cli_config
from .tables import build_info_table


def present_info_command(
    console: Console,
    *,
    version: str,
    config_path: Path | None,
) -> None:
    config = execute_info_workflow(config_path=config_path, load_config=load_runtime_config)
    console.print(build_info_table(version, config))


def present_init_command(
    console: Console,
    *,
    vault_path: Path,
    config_output: Path = DEFAULT_INIT_CONFIG_PATH,
    force: bool,
    dry_run: bool,
    print_operations,
) -> None:
    operations = execute_init_workflow(
        vault_path=vault_path,
        config_output=config_output,
        force=force,
        dry_run=dry_run,
        initialize_config=initialize_cli_config,
        event_sink=load_event_sink(),
    )
    print_operations(console, operations)


def present_init_db_command(
    console: Console,
    *,
    config_path: Path | None,
    dry_run: bool,
    print_operations,
) -> None:
    operations = execute_init_db_workflow(
        config_path=config_path,
        dry_run=dry_run,
        load_config=load_runtime_config,
        initialize_database=initialize_database,
        event_sink=load_event_sink(),
    )
    print_operations(console, operations)


__all__ = [
    "present_info_command",
    "present_init_command",
    "present_init_db_command",
]
