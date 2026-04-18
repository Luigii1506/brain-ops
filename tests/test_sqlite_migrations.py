from __future__ import annotations

import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from brain_ops.storage.sqlite.migrations import (
    apply_migrations,
    create_backup,
    migrate_knowledge_db_with_backup,
    migration_status,
)


class MigrationOnFreshDbTestCase(TestCase):
    def test_apply_creates_table_with_all_columns(self) -> None:
        with TemporaryDirectory() as td:
            db = Path(td) / "knowledge.db"
            applied = apply_migrations(db, _force=True)
            self.assertGreater(len(applied), 0)
            conn = sqlite3.connect(str(db))
            try:
                cols = {row[1] for row in conn.execute(
                    "PRAGMA table_info(entity_relations)"
                )}
                self.assertIn("predicate", cols)
                self.assertIn("confidence", cols)
                self.assertIn("source_entity", cols)
                self.assertIn("target_entity", cols)
                # Bookkeeping table exists
                rows = conn.execute(
                    "SELECT version FROM schema_migrations"
                ).fetchall()
                versions = [r[0] for r in rows]
                self.assertIn(1, versions)
            finally:
                conn.close()


class MigrationOnLegacyDbTestCase(TestCase):
    """Simulate the real production scenario: an old DB with the legacy shape."""

    def _create_legacy_db(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path))
        try:
            # Legacy schema — no predicate / confidence columns
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

    def test_migration_adds_columns_preserving_data(self) -> None:
        with TemporaryDirectory() as td:
            db = Path(td) / "knowledge.db"
            self._create_legacy_db(db)

            apply_migrations(db, _force=True)

            conn = sqlite3.connect(str(db))
            try:
                cols = {row[1] for row in conn.execute(
                    "PRAGMA table_info(entity_relations)"
                )}
                self.assertIn("predicate", cols)
                self.assertIn("confidence", cols)
                # Data preserved
                rows = conn.execute(
                    "SELECT source_entity, target_entity, predicate FROM entity_relations"
                ).fetchall()
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0][0], "A")
                self.assertEqual(rows[0][1], "B")
                self.assertIsNone(rows[0][2])
            finally:
                conn.close()


class IdempotencyTestCase(TestCase):
    def test_repeated_apply_is_noop(self) -> None:
        with TemporaryDirectory() as td:
            db = Path(td) / "knowledge.db"
            first = apply_migrations(db, _force=True)
            second = apply_migrations(db, _force=True)
            self.assertGreater(len(first), 0)
            self.assertEqual(second, [])


class MigrationStatusTestCase(TestCase):
    def test_fresh_db_all_pending(self) -> None:
        with TemporaryDirectory() as td:
            db = Path(td) / "knowledge.db"
            status = migration_status(db)
            self.assertEqual(status.applied, ())
            self.assertGreater(len(status.pending), 0)

    def test_after_migration_no_pending(self) -> None:
        with TemporaryDirectory() as td:
            db = Path(td) / "knowledge.db"
            apply_migrations(db, _force=True)
            status = migration_status(db)
            self.assertEqual(status.pending, ())
            self.assertIn(1, status.applied)


class BackupTestCase(TestCase):
    def test_backup_when_db_exists(self) -> None:
        with TemporaryDirectory() as td:
            db = Path(td) / "knowledge.db"
            db.write_bytes(b"\x00\x01fake")
            backup = create_backup(db, tag="test")
            self.assertIsNotNone(backup)
            self.assertTrue(backup.exists())
            self.assertEqual(backup.read_bytes(), b"\x00\x01fake")
            self.assertIn("backup", backup.name)

    def test_backup_no_db(self) -> None:
        with TemporaryDirectory() as td:
            db = Path(td) / "knowledge.db"
            self.assertIsNone(create_backup(db, tag="nothing"))


class MigrateWithBackupTestCase(TestCase):
    def test_dry_run_reports_pending_without_modifying(self) -> None:
        with TemporaryDirectory() as td:
            db = Path(td) / "knowledge.db"
            db.write_bytes(b"")  # empty file (not a valid DB)
            # Actually we need a valid DB. Let's create a legacy one.
            db.unlink()
            conn = sqlite3.connect(str(db))
            conn.execute(
                "CREATE TABLE entity_relations (id INTEGER PRIMARY KEY, "
                "source_entity TEXT, target_entity TEXT, source_type TEXT)"
            )
            conn.commit()
            conn.close()

            result = migrate_knowledge_db_with_backup(db, dry_run=True, force=True)
            self.assertEqual(result["status"], "dry-run")
            self.assertGreater(len(result["pending"]), 0)
            # Column should NOT have been added
            conn = sqlite3.connect(str(db))
            try:
                cols = {row[1] for row in conn.execute(
                    "PRAGMA table_info(entity_relations)"
                )}
                self.assertNotIn("predicate", cols)
            finally:
                conn.close()

    def test_migrate_creates_backup(self) -> None:
        with TemporaryDirectory() as td:
            db = Path(td) / "knowledge.db"
            conn = sqlite3.connect(str(db))
            conn.execute(
                "CREATE TABLE entity_relations (id INTEGER PRIMARY KEY, "
                "source_entity TEXT, target_entity TEXT, source_type TEXT)"
            )
            conn.commit()
            conn.close()

            result = migrate_knowledge_db_with_backup(db, dry_run=False, force=True)
            self.assertEqual(result["status"], "migrated")
            self.assertIsNotNone(result["backup_path"])
            self.assertTrue(Path(result["backup_path"]).exists())

    def test_up_to_date(self) -> None:
        with TemporaryDirectory() as td:
            db = Path(td) / "knowledge.db"
            apply_migrations(db, _force=True)
            result = migrate_knowledge_db_with_backup(db, dry_run=False, force=True)
            self.assertEqual(result["status"], "up-to-date")
            self.assertIsNone(result["backup_path"])


class DryRunPurityTestCase(TestCase):
    """migration_status and dry_run must NEVER mutate the DB."""

    def test_status_does_not_create_bookkeeping_table(self) -> None:
        with TemporaryDirectory() as td:
            db = Path(td) / "knowledge.db"
            conn = sqlite3.connect(str(db))
            conn.execute(
                "CREATE TABLE entity_relations (id INTEGER PRIMARY KEY, "
                "source_entity TEXT, target_entity TEXT, source_type TEXT)"
            )
            conn.commit()
            conn.close()

            migration_status(db)

            conn = sqlite3.connect(str(db))
            try:
                tables = {
                    r[0] for r in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                }
                self.assertNotIn("schema_migrations", tables)
            finally:
                conn.close()

    def test_dry_run_does_not_create_bookkeeping_table(self) -> None:
        with TemporaryDirectory() as td:
            db = Path(td) / "knowledge.db"
            conn = sqlite3.connect(str(db))
            conn.execute(
                "CREATE TABLE entity_relations (id INTEGER PRIMARY KEY, "
                "source_entity TEXT, target_entity TEXT, source_type TEXT)"
            )
            conn.commit()
            conn.close()

            migrate_knowledge_db_with_backup(db, dry_run=True, force=True)

            conn = sqlite3.connect(str(db))
            try:
                tables = {
                    r[0] for r in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                }
                self.assertNotIn("schema_migrations", tables)
                cols = {row[1] for row in conn.execute(
                    "PRAGMA table_info(entity_relations)"
                )}
                self.assertNotIn("predicate", cols)
            finally:
                conn.close()
