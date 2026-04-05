"""Application workflows for system/bootstrap capabilities."""

from __future__ import annotations

from pathlib import Path

from brain_ops.config import VaultConfig
from brain_ops.constants import DEFAULT_INIT_CONFIG_PATH
from brain_ops.core.events import EventSink
from brain_ops.errors import ConfigError
from brain_ops.storage.db import resolve_database_path

from .events import publish_result_events


def execute_info_workflow(*, config_path: Path | None, load_config):
    return load_config(config_path)


def execute_init_workflow(
    *,
    vault_path: Path,
    config_output: Path = DEFAULT_INIT_CONFIG_PATH,
    force: bool,
    dry_run: bool,
    initialize_config,
    event_sink: EventSink | None = None,
):
    output_path = config_output.expanduser()
    if output_path.exists() and not force:
        raise ConfigError(f"Config already exists: {output_path}")

    result = initialize_config(
        config=VaultConfig(vault_path=vault_path),
        config_output=config_output,
        dry_run=dry_run,
    )
    return publish_result_events("init", source="application.system", result=result, event_sink=event_sink)


def execute_init_db_workflow(
    *,
    config_path: Path | None,
    dry_run: bool,
    load_config,
    initialize_database,
    event_sink: EventSink | None = None,
):
    config = load_config(config_path)
    database_path = resolve_database_path(config.database_path)
    result = initialize_database(database_path, dry_run=dry_run)
    return publish_result_events("init-db", source="application.system", result=result, event_sink=event_sink)


def execute_openclaw_manifest_workflow(*, output: Path | None, write_manifest):
    if output is None:
        return None
    return write_manifest(output)


__all__ = [
    "execute_info_workflow",
    "execute_init_db_workflow",
    "execute_init_workflow",
    "execute_openclaw_manifest_workflow",
]
