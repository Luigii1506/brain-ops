"""Runtime helpers for CLI commands."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from brain_ops.config import VaultConfig, load_config
from brain_ops.core.events import EventSink, JsonlFileEventSink
from brain_ops.errors import BrainOpsError, RealVaultAccessError
from brain_ops.storage.db import resolve_database_path
from brain_ops.vault import Vault


# Campaña 0.5 safety — mirror of the test-runner detection in
# storage/sqlite/migrations. Kept duplicated (rather than imported) to
# keep this module free of storage-layer dependencies.
_TEST_RUNNER_MODULES: frozenset[str] = frozenset({
    "pytest",
    "_pytest",
    "unittest.loader",
    "unittest.runner",
})


def _test_runner_detected() -> bool:
    return any(m in sys.modules for m in _TEST_RUNNER_MODULES)


def _real_vault_guard_active() -> bool:
    """True if the real-vault guard should block access to the production vault.

    Active if BRAIN_OPS_BLOCK_REAL_VAULT=1 OR a test runner is detected.
    Belt-and-suspenders: env var is set by tests/conftest.py, and sys.modules
    detection catches cases where conftest did not run.
    """
    if os.environ.get("BRAIN_OPS_BLOCK_REAL_VAULT") == "1":
        return True
    return _test_runner_detected()


def _real_vault_paths() -> tuple[Path, Path] | None:
    """Return (real_vault_path, real_db_path) from the default config, if it exists.

    Returns None if the default config cannot be loaded — in that case we
    cannot tell whether a given path is the real vault, so we fail open.
    """
    try:
        from brain_ops.constants import DEFAULT_INIT_CONFIG_PATH
        cfg = load_config(DEFAULT_INIT_CONFIG_PATH)
        return Path(cfg.vault_path).resolve(), Path(cfg.database_path).resolve()
    except Exception:
        return None


def load_runtime_config(config_path: Path | None) -> VaultConfig:
    return load_config(config_path)


def load_database_path(config_path: Path | None) -> Path:
    return resolve_database_path(load_runtime_config(config_path).database_path)


def load_validated_vault(config_path: Path | None, *, dry_run: bool) -> Vault:
    config = load_runtime_config(config_path)

    if _real_vault_guard_active():
        real_paths = _real_vault_paths()
        if real_paths is not None:
            real_vault_path, _real_db_path = real_paths
            try:
                requested_vault = Path(config.vault_path).resolve()
            except Exception:
                requested_vault = Path(config.vault_path)
            if requested_vault == real_vault_path:
                raise RealVaultAccessError(
                    f"Blocked access to the real vault at {real_vault_path} "
                    f"while the safety guard is active. "
                    f"This is almost certainly a test or import that should use "
                    f"a temporary path instead. "
                    f"Unset BRAIN_OPS_BLOCK_REAL_VAULT to disable the guard."
                )

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
