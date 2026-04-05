from __future__ import annotations

import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from brain_ops.core.validation.common import has_any_non_none, normalize_period, resolve_iso_date
from brain_ops.errors import ConfigError
from brain_ops.models import OperationStatus
from brain_ops.storage.db import (
    connect_sqlite,
    ensure_database_parent,
    initialize_database,
    require_database_file,
    resolve_database_path,
)


class StorageDbAndValidationTestCase(TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_database_path_helpers_expand_ensure_and_require(self) -> None:
        home_relative = Path("~") / "brain_ops_test.sqlite"
        resolved = resolve_database_path(home_relative)
        self.assertNotIn("~", str(resolved))

        nested_path = self.root / "nested" / "data" / "brain_ops.sqlite"
        ensured = ensure_database_parent(nested_path)
        self.assertEqual(ensured, nested_path)
        self.assertTrue(nested_path.parent.exists())

        with self.assertRaises(ConfigError):
            require_database_file(nested_path)

        nested_path.touch()
        self.assertEqual(require_database_file(nested_path), nested_path)

    def test_connect_sqlite_closes_connection_and_enables_usage_inside_context(self) -> None:
        db_path = self.root / "test.sqlite"

        with connect_sqlite(db_path) as connection:
            connection.execute("CREATE TABLE example (id INTEGER PRIMARY KEY, value TEXT)")
            connection.execute("INSERT INTO example (value) VALUES ('ok')")
            rows = connection.execute("SELECT value FROM example").fetchall()

        self.assertEqual(rows, [("ok",)])
        with self.assertRaises(sqlite3.ProgrammingError):
            connection.execute("SELECT 1")

    def test_initialize_database_supports_dry_run_and_real_schema_creation(self) -> None:
        db_path = self.root / "data" / "brain_ops.sqlite"

        dry_run_ops = initialize_database(db_path, dry_run=True)
        self.assertEqual(len(dry_run_ops), 1)
        self.assertEqual(dry_run_ops[0].status, OperationStatus.SKIPPED)
        self.assertFalse(db_path.exists())

        first_ops = initialize_database(db_path)
        self.assertEqual(first_ops[0].status, OperationStatus.CREATED)
        self.assertTrue(db_path.exists())

        second_ops = initialize_database(db_path)
        self.assertEqual(second_ops[0].status, OperationStatus.UPDATED)

        with sqlite3.connect(db_path) as connection:
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            columns = {
                row[1]
                for row in connection.execute("PRAGMA table_info(body_metrics)").fetchall()
            }

        self.assertIn("meals", tables)
        self.assertIn("diet_plans", tables)
        self.assertIn("conversation_followups", tables)
        self.assertIn("fat_mass_kg", columns)
        self.assertIn("muscle_mass_kg", columns)
        self.assertIn("calf_cm", columns)

    def test_resolve_iso_date_normalize_period_and_non_none_helpers(self) -> None:
        fixed_now = datetime(2026, 4, 4, 9, 30, 0)

        with patch("brain_ops.core.validation.common.datetime") as datetime_mock:
            datetime_mock.now.return_value = fixed_now
            datetime_mock.fromisoformat.side_effect = datetime.fromisoformat
            self.assertEqual(resolve_iso_date(None), "2026-04-04")

        self.assertEqual(resolve_iso_date("2026-04-03"), "2026-04-03")
        with self.assertRaises(ConfigError):
            resolve_iso_date("04/03/2026")

        self.assertEqual(normalize_period(" Weekly "), "weekly")
        with self.assertRaises(ConfigError):
            normalize_period("yearly")

        self.assertTrue(has_any_non_none([None, 0, None]))
        self.assertFalse(has_any_non_none([None, None]))


if __name__ == "__main__":
    import unittest

    unittest.main()
