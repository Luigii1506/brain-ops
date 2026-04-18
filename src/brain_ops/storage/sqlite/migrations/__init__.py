"""SQLite schema migration framework for knowledge.db.

Every migration is a module in this package that exposes:

    VERSION: int               # monotonically increasing integer
    DESCRIPTION: str           # one-line human-readable description
    def up(conn: sqlite3.Connection) -> None: ...
    def down(conn: sqlite3.Connection) -> None: ...   # optional

The registry (`MIGRATIONS`) lists migrations in order. `apply_migrations`
reads the `schema_migrations` bookkeeping table, runs pending migrations
in a transaction each, and records successes.

Backups are the caller's responsibility — see `migrate_knowledge_db_with_backup`.

Safety model (Campaña 0.5):
--------------------------

Migrations NEVER run as a side effect of importing or initialising a DB.
They run in exactly two situations:

1. The user explicitly invokes `brain migrate-knowledge-db`.
2. A caller explicitly passes `_force=True` to `apply_migrations` (internal
   / test-only escape hatch — never set by the user-facing CLI command
   except via `--force-migrate`, which still creates a backup).

Additionally:
- BRAIN_OPS_NO_MIGRATE=1 short-circuits `apply_migrations` to a no-op.
- The function auto-detects test runners in `sys.modules` and treats them
  as if BRAIN_OPS_NO_MIGRATE were set.

See `docs/operations/MIGRATIONS.md`.
"""

from __future__ import annotations

import datetime as _dt
import logging
import os
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Protocol

from . import m001_predicate_column


logger = logging.getLogger(__name__)


# Modules that, if present in sys.modules, indicate a test runner is active.
# These are the BELT of belt-and-suspenders (conftest sets env vars as
# SUSPENDERS). If either triggers, we skip migrations.
_TEST_RUNNER_MODULES: frozenset[str] = frozenset({
    "pytest",
    "_pytest",
    "unittest.loader",
    "unittest.runner",
})


def _test_runner_detected() -> bool:
    """True if sys.modules shows signs of a test runner being active.

    Checks for pytest-specific modules and unittest submodules that are only
    imported during test discovery/execution (NOT when user code merely does
    `from unittest import TestCase`).
    """
    return any(m in sys.modules for m in _TEST_RUNNER_MODULES)


def _migrations_blocked() -> tuple[bool, str]:
    """Determine whether migrations should be skipped.

    Returns (blocked, reason). `reason` is logged for traceability.
    """
    if os.environ.get("BRAIN_OPS_NO_MIGRATE") == "1":
        return True, "BRAIN_OPS_NO_MIGRATE=1"
    if _test_runner_detected():
        present = sorted(m for m in _TEST_RUNNER_MODULES if m in sys.modules)
        return True, f"test runner detected: {present}"
    return False, ""


class _Migration(Protocol):
    VERSION: int
    DESCRIPTION: str

    def up(self, conn: sqlite3.Connection) -> None: ...


MIGRATIONS: tuple[ModuleType, ...] = (
    m001_predicate_column,
)


_BOOKKEEPING_DDL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL,
    description TEXT
)
"""


@dataclass(slots=True, frozen=True)
class MigrationStatus:
    applied: tuple[int, ...]
    pending: tuple[tuple[int, str], ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "applied": list(self.applied),
            "pending": [
                {"version": v, "description": d} for v, d in self.pending
            ],
        }


@dataclass(slots=True, frozen=True)
class AppliedMigration:
    version: int
    description: str
    applied_at: str

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "description": self.description,
            "applied_at": self.applied_at,
        }


def _ensure_bookkeeping(conn: sqlite3.Connection) -> None:
    conn.execute(_BOOKKEEPING_DDL)


def _bookkeeping_exists(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
    ).fetchone()
    return row is not None


def _applied_versions_readonly(conn: sqlite3.Connection) -> set[int]:
    """Read applied versions WITHOUT creating the bookkeeping table."""
    if not _bookkeeping_exists(conn):
        return set()
    rows = conn.execute("SELECT version FROM schema_migrations").fetchall()
    return {int(r[0]) for r in rows}


def _applied_versions(conn: sqlite3.Connection) -> set[int]:
    """Read applied versions and ensure the bookkeeping table exists."""
    _ensure_bookkeeping(conn)
    rows = conn.execute("SELECT version FROM schema_migrations").fetchall()
    return {int(r[0]) for r in rows}


def migration_status(db_path: Path) -> MigrationStatus:
    """Return applied + pending migrations without mutating anything."""
    if not db_path.exists():
        # All migrations are pending on a fresh DB
        return MigrationStatus(
            applied=(),
            pending=tuple((m.VERSION, m.DESCRIPTION) for m in MIGRATIONS),
        )
    conn = sqlite3.connect(str(db_path))
    try:
        applied = _applied_versions_readonly(conn)
    finally:
        conn.close()
    pending = tuple(
        (m.VERSION, m.DESCRIPTION) for m in MIGRATIONS if m.VERSION not in applied
    )
    return MigrationStatus(
        applied=tuple(sorted(applied)),
        pending=pending,
    )


def apply_migrations(db_path: Path, *, _force: bool = False) -> list[AppliedMigration]:
    """Apply all pending migrations idempotently. Safe to call repeatedly.

    Parameters
    ----------
    db_path
        Path to the SQLite DB.
    _force
        Internal escape hatch. When True, bypasses the safety guards
        (`BRAIN_OPS_NO_MIGRATE` env var and test-runner detection). The
        user-facing CLI exposes this as `--force-migrate`, which STILL
        creates an automatic backup — see `migrate_knowledge_db_with_backup`.
        Tests that legitimately need to exercise migrations on temp DBs
        must pass `_force=True`.

    Safety
    ------
    Without `_force=True`, migrations are skipped in two situations:
    - `BRAIN_OPS_NO_MIGRATE=1` is set in the environment.
    - A test runner is detected via `sys.modules`.

    In both cases this function logs the reason and returns an empty list
    without touching the DB at all.
    """
    if not _force:
        blocked, reason = _migrations_blocked()
        if blocked:
            logger.warning(
                "apply_migrations skipped (db=%s): %s. "
                "Use brain migrate-knowledge-db --force-migrate to override.",
                db_path, reason,
            )
            return []

    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    applied: list[AppliedMigration] = []
    try:
        _ensure_bookkeeping(conn)
        existing = _applied_versions(conn)
        for migration in MIGRATIONS:
            version = migration.VERSION
            if version in existing:
                continue
            conn.execute("BEGIN")
            try:
                migration.up(conn)
                now = _dt.datetime.now(tz=_dt.timezone.utc).isoformat()
                conn.execute(
                    "INSERT INTO schema_migrations (version, applied_at, description) VALUES (?, ?, ?)",
                    (version, now, migration.DESCRIPTION),
                )
                conn.commit()
                applied.append(AppliedMigration(
                    version=version,
                    description=migration.DESCRIPTION,
                    applied_at=now,
                ))
            except Exception:
                conn.rollback()
                raise
    finally:
        conn.close()
    return applied


def backup_db_path(db_path: Path, *, tag: str) -> Path:
    """Compute a backup path next to the original DB."""
    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    return db_path.with_name(f"{db_path.stem}-backup-{stamp}-{tag}{db_path.suffix}")


def create_backup(db_path: Path, *, tag: str = "pre-migration") -> Path | None:
    """Copy the DB file to a timestamped backup. Returns the backup path.

    Returns None if the source DB does not exist (nothing to back up).
    """
    if not db_path.exists():
        return None
    dest = backup_db_path(db_path, tag=tag)
    dest.write_bytes(db_path.read_bytes())
    return dest


def migrate_knowledge_db_with_backup(
    db_path: Path,
    *,
    dry_run: bool = False,
    skip_backup: bool = False,
    force: bool = False,
) -> dict[str, object]:
    """High-level helper for the CLI.

    Parameters
    ----------
    db_path
        Path to the SQLite DB.
    dry_run
        If True, report pending migrations without touching anything.
    skip_backup
        Skip the automatic backup (not recommended).
    force
        Bypass env var / test runner guards. Still creates a backup
        unless skip_backup=True. Used only via the CLI `--force-migrate`
        flag; the normal user flow never needs this.

    Returns a structured dict with keys:
      - status: "dry-run" | "migrated" | "up-to-date" | "blocked"
      - applied: list of AppliedMigration dicts (empty when dry-run)
      - pending: list of {version, description} dicts
      - backup_path: str | None
      - block_reason: str | None
    """
    # If guards are active and force=False, report that migrations are blocked.
    # This is different from "up-to-date" — pending exists but cannot run.
    if not force:
        blocked, reason = _migrations_blocked()
        if blocked:
            status = migration_status(db_path)
            return {
                "status": "blocked",
                "applied": [],
                "pending": [
                    {"version": v, "description": d} for v, d in status.pending
                ],
                "backup_path": None,
                "block_reason": reason,
            }

    status = migration_status(db_path)
    if not status.pending:
        return {
            "status": "up-to-date",
            "applied": [],
            "pending": [],
            "backup_path": None,
            "block_reason": None,
        }

    if dry_run:
        return {
            "status": "dry-run",
            "applied": [],
            "pending": [
                {"version": v, "description": d} for v, d in status.pending
            ],
            "backup_path": None,
            "block_reason": None,
        }

    backup_path: Path | None = None
    if not skip_backup:
        backup_path = create_backup(db_path, tag="pre-migration")

    applied = apply_migrations(db_path, _force=force)
    return {
        "status": "migrated",
        "applied": [a.to_dict() for a in applied],
        "pending": [],
        "backup_path": str(backup_path) if backup_path else None,
        "block_reason": None,
    }


__all__ = [
    "AppliedMigration",
    "MIGRATIONS",
    "MigrationStatus",
    "apply_migrations",
    "backup_db_path",
    "create_backup",
    "migrate_knowledge_db_with_backup",
    "migration_status",
]
