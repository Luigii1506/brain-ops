"""Runtime helpers for CLI commands."""

from __future__ import annotations

import os
from pathlib import Path

from brain_ops.config import VaultConfig, load_config
from brain_ops.core.events import EventSink, JsonlFileEventSink
from brain_ops.errors import BrainOpsError
from brain_ops.storage.db import resolve_database_path
from brain_ops.vault import Vault


def load_runtime_config(config_path: Path | None) -> VaultConfig:
    return load_config(config_path)


def load_database_path(config_path: Path | None) -> Path:
    return resolve_database_path(load_runtime_config(config_path).database_path)


def load_validated_vault(config_path: Path | None, *, dry_run: bool) -> Vault:
    config = load_runtime_config(config_path)
    vault = Vault(config=config, dry_run=dry_run)
    vault.validate()
    return vault


def load_event_sink() -> EventSink | None:
    event_log_path = os.getenv("BRAIN_OPS_EVENT_LOG")
    if not event_log_path:
        return None
    return JsonlFileEventSink(Path(event_log_path))


def load_event_log_path(event_log_path: Path | None) -> Path:
    path = event_log_path or (Path(os.environ["BRAIN_OPS_EVENT_LOG"]) if os.getenv("BRAIN_OPS_EVENT_LOG") else None)
    if path is None:
        raise BrainOpsError("Event log path is required. Pass --path or set BRAIN_OPS_EVENT_LOG.")
    expanded_path = path.expanduser()
    if not expanded_path.exists():
        raise BrainOpsError(f"Event log does not exist: {expanded_path}")
    return expanded_path


def load_alert_output_dir(output_path: Path | None, *, event_log_path: Path) -> Path:
    if output_path is not None:
        return output_path.expanduser().parent
    configured_dir = os.getenv("BRAIN_OPS_ALERT_OUTPUT_DIR")
    if configured_dir:
        return Path(configured_dir).expanduser()
    return event_log_path.parent / "alerts"


__all__ = ["load_alert_output_dir", "load_database_path", "load_event_log_path", "load_event_sink", "load_runtime_config", "load_validated_vault"]
