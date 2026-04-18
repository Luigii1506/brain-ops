"""Campaña 0.5 — verify migrations cannot touch the real DB during tests.

These tests enforce the contract that:
1. `initialize_entity_tables` NEVER applies migrations — it only runs the
   current DDL for fresh tables.
2. `apply_migrations` respects `BRAIN_OPS_NO_MIGRATE=1` and test-runner
   detection in `sys.modules`, short-circuiting to a no-op.
3. `_force=True` bypasses both guards.
4. `check_schema_is_current` raises a clear error on legacy DBs.

If any of these tests fail, there is a real risk that running the test
suite will mutate the production DB schema.
"""

from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from brain_ops.errors import SchemaOutOfDateError
from brain_ops.storage.sqlite.entities import (
    check_schema_is_current,
    initialize_entity_tables,
)
from brain_ops.storage.sqlite.migrations import (
    _migrations_blocked,
    _test_runner_detected,
    apply_migrations,
    migrate_knowledge_db_with_backup,
)


def _create_legacy_db(db_path: Path) -> None:
    """Create a DB with the pre-Campaña-0 schema (no predicate/confidence)."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("""
            CREATE TABLE entity_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_entity TEXT NOT NULL,
                target_entity TEXT NOT NULL,
                source_type TEXT
            )
        """)
        conn.execute(
            "INSERT INTO entity_relations (source_entity, target_entity, source_type) "
            "VALUES ('A', 'B', 'person')"
        )
        conn.commit()
    finally:
        conn.close()


def _has_predicate_column(db_path: Path) -> bool:
    conn = sqlite3.connect(str(db_path))
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(entity_relations)")}
    finally:
        conn.close()
    return "predicate" in cols


class InitializeEntityTablesNeverMigratesTestCase(TestCase):
    """initialize_entity_tables on a legacy DB must NOT add migration columns."""

    def test_legacy_db_stays_legacy_after_initialize(self) -> None:
        with TemporaryDirectory() as td:
            db = Path(td) / "knowledge.db"
            _create_legacy_db(db)
            self.assertFalse(_has_predicate_column(db))

            initialize_entity_tables(db)

            # Still legacy — migration must NOT have happened
            self.assertFalse(_has_predicate_column(db))

    def test_fresh_db_gets_current_schema(self) -> None:
        """A fresh DB created by the DDL should have the current shape.

        This is how new users / new installs get a correct DB without ever
        running the migration CLI.
        """
        with TemporaryDirectory() as td:
            db = Path(td) / "knowledge.db"
            initialize_entity_tables(db)
            self.assertTrue(_has_predicate_column(db))


class CheckSchemaIsCurrentTestCase(TestCase):
    def test_legacy_db_raises_with_actionable_message(self) -> None:
        with TemporaryDirectory() as td:
            db = Path(td) / "knowledge.db"
            _create_legacy_db(db)

            with self.assertRaises(SchemaOutOfDateError) as ctx:
                check_schema_is_current(db)

            msg = str(ctx.exception)
            self.assertIn("predicate", msg)
            self.assertIn("brain migrate-knowledge-db", msg)

    def test_current_db_passes_silently(self) -> None:
        with TemporaryDirectory() as td:
            db = Path(td) / "knowledge.db"
            initialize_entity_tables(db)
            # Should not raise
            check_schema_is_current(db)

    def test_nonexistent_db_passes_silently(self) -> None:
        with TemporaryDirectory() as td:
            db = Path(td) / "doesnotexist.db"
            # Should not raise
            check_schema_is_current(db)

    def test_no_table_passes_silently(self) -> None:
        with TemporaryDirectory() as td:
            db = Path(td) / "knowledge.db"
            conn = sqlite3.connect(str(db))
            conn.commit()
            conn.close()
            # Empty DB, no table yet — no error
            check_schema_is_current(db)


class ApplyMigrationsGuardsTestCase(TestCase):
    """apply_migrations without _force must be guarded under tests."""

    def test_test_runner_detected(self) -> None:
        # We're running under pytest or unittest right now, so at least one
        # of the marker modules should be present
        self.assertTrue(_test_runner_detected())

    def test_migrations_blocked_reports_reason(self) -> None:
        blocked, reason = _migrations_blocked()
        self.assertTrue(blocked)
        self.assertTrue(reason)

    def test_apply_without_force_is_noop_under_tests(self) -> None:
        """Without _force=True, apply_migrations on a legacy DB must do nothing."""
        with TemporaryDirectory() as td:
            db = Path(td) / "knowledge.db"
            _create_legacy_db(db)
            self.assertFalse(_has_predicate_column(db))

            result = apply_migrations(db)  # no _force

            self.assertEqual(result, [])
            self.assertFalse(_has_predicate_column(db))

    def test_apply_with_force_bypasses_guards(self) -> None:
        with TemporaryDirectory() as td:
            db = Path(td) / "knowledge.db"
            _create_legacy_db(db)

            result = apply_migrations(db, _force=True)

            self.assertGreater(len(result), 0)
            self.assertTrue(_has_predicate_column(db))


class MigrateWithBackupBlockedStatusTestCase(TestCase):
    """migrate_knowledge_db_with_backup reports 'blocked' under the guard."""

    def test_blocked_without_force(self) -> None:
        with TemporaryDirectory() as td:
            db = Path(td) / "knowledge.db"
            _create_legacy_db(db)

            result = migrate_knowledge_db_with_backup(db, dry_run=False)

            self.assertEqual(result["status"], "blocked")
            self.assertIsNotNone(result["block_reason"])
            self.assertIsNone(result["backup_path"])
            self.assertGreater(len(result["pending"]), 0)
            # DB untouched
            self.assertFalse(_has_predicate_column(db))

    def test_force_migrates_and_still_backs_up(self) -> None:
        with TemporaryDirectory() as td:
            db = Path(td) / "knowledge.db"
            _create_legacy_db(db)

            result = migrate_knowledge_db_with_backup(
                db, dry_run=False, force=True,
            )

            self.assertEqual(result["status"], "migrated")
            self.assertIsNotNone(result["backup_path"])
            self.assertTrue(Path(result["backup_path"]).exists())
            self.assertTrue(_has_predicate_column(db))


class GuardsAreActiveDuringTestsTestCase(TestCase):
    """The guards must be active — either via env var or via sys.modules.

    `tests/__init__.py` and `tests/conftest.py` set the env vars for normal
    invocations (pytest, `python -m unittest tests.something`). But
    `python -m unittest discover` does NOT import the package __init__.py,
    so env vars may be absent there. The sys.modules detection (second layer)
    must catch that case.

    This test doesn't care WHICH mechanism fired — only that the guard is on.
    """

    def test_migrations_are_blocked(self) -> None:
        from brain_ops.storage.sqlite.migrations import _migrations_blocked
        blocked, reason = _migrations_blocked()
        self.assertTrue(blocked, "Migrations must be blocked under tests")
        self.assertTrue(reason, "Block reason must be reported")

    def test_real_vault_guard_is_active(self) -> None:
        from brain_ops.interfaces.cli.runtime import _real_vault_guard_active
        self.assertTrue(_real_vault_guard_active())
