"""Tests for project-log and session workflows."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from brain_ops.application.projects import (
    ProjectLogResult,
    ProjectSessionResult,
    _classify_entry,
    execute_project_log_workflow,
    execute_register_project_workflow,
    execute_session_workflow,
)
from brain_ops.errors import ConfigError
from brain_ops.storage.db import initialize_database
from brain_ops.storage.sqlite.project_logs import (
    fetch_project_logs,
    fetch_recent_project_logs,
    insert_project_log,
)
from brain_ops.domains.projects.registry import load_project_registry


class ClassifyEntryTestCase(TestCase):
    def test_update_default(self) -> None:
        entry_type, text = _classify_entry("refactored the runtime")
        self.assertEqual(entry_type, "update")
        self.assertEqual(text, "refactored the runtime")

    def test_decision_spanish(self) -> None:
        entry_type, text = _classify_entry("decisión: usar SQLite como storage")
        self.assertEqual(entry_type, "decision")
        self.assertEqual(text, "usar SQLite como storage")

    def test_decision_english(self) -> None:
        entry_type, text = _classify_entry("decision: use SQLite as storage")
        self.assertEqual(entry_type, "decision")
        self.assertEqual(text, "use SQLite as storage")

    def test_bug(self) -> None:
        entry_type, text = _classify_entry("bug: object_model not used")
        self.assertEqual(entry_type, "bug")
        self.assertEqual(text, "object_model not used")

    def test_next(self) -> None:
        entry_type, text = _classify_entry("next: test with real data")
        self.assertEqual(entry_type, "next")
        self.assertEqual(text, "test with real data")

    def test_siguiente(self) -> None:
        entry_type, text = _classify_entry("siguiente: probar con datos reales")
        self.assertEqual(entry_type, "next")
        self.assertEqual(text, "probar con datos reales")

    def test_blocker(self) -> None:
        entry_type, text = _classify_entry("blocker: missing API key")
        self.assertEqual(entry_type, "blocker")
        self.assertEqual(text, "missing API key")

    def test_bloqueo(self) -> None:
        entry_type, text = _classify_entry("bloqueo: falta API key")
        self.assertEqual(entry_type, "blocker")
        self.assertEqual(text, "falta API key")

    def test_idea(self) -> None:
        entry_type, text = _classify_entry("idea: add dashboard")
        self.assertEqual(entry_type, "idea")
        self.assertEqual(text, "add dashboard")

    def test_case_insensitive(self) -> None:
        entry_type, text = _classify_entry("BUG: something broke")
        self.assertEqual(entry_type, "bug")
        self.assertEqual(text, "something broke")


class ProjectLogStorageTestCase(TestCase):
    def setUp(self) -> None:
        self._tmpdir = TemporaryDirectory()
        self.db_path = Path(self._tmpdir.name) / "test.db"
        initialize_database(self.db_path)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_insert_and_fetch(self) -> None:
        insert_project_log(
            self.db_path,
            project_name="brain-ops",
            entry_type="update",
            entry_text="refactored runtime",
        )
        logs = fetch_project_logs(self.db_path, project_name="brain-ops")
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["project_name"], "brain-ops")
        self.assertEqual(logs[0]["entry_type"], "update")
        self.assertEqual(logs[0]["entry_text"], "refactored runtime")
        self.assertEqual(logs[0]["source"], "cli")

    def test_fetch_respects_limit(self) -> None:
        for i in range(5):
            insert_project_log(
                self.db_path,
                project_name="proj",
                entry_type="update",
                entry_text=f"entry {i}",
            )
        logs = fetch_project_logs(self.db_path, project_name="proj", limit=3)
        self.assertEqual(len(logs), 3)

    def test_fetch_filters_by_project(self) -> None:
        insert_project_log(self.db_path, project_name="proj-a", entry_type="update", entry_text="a")
        insert_project_log(self.db_path, project_name="proj-b", entry_type="update", entry_text="b")
        logs = fetch_project_logs(self.db_path, project_name="proj-a")
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["entry_text"], "a")

    def test_fetch_recent_returns_recent_only(self) -> None:
        insert_project_log(
            self.db_path,
            project_name="proj",
            entry_type="update",
            entry_text="recent entry",
        )
        logs = fetch_recent_project_logs(self.db_path, project_name="proj", days=7)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["entry_text"], "recent entry")


class ProjectLogWorkflowTestCase(TestCase):
    def setUp(self) -> None:
        self._tmpdir = TemporaryDirectory()
        self.tmp_path = Path(self._tmpdir.name)
        self.registry_path = self.tmp_path / "projects.json"
        self.db_path = self.tmp_path / "test.db"
        initialize_database(self.db_path)
        # Register a test project
        execute_register_project_workflow(
            name="brain-ops",
            path="/home/user/brain-ops",
            stack=["python"],
            description="Test project",
            commands=None,
            load_registry_path=lambda: self.registry_path,
        )

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_log_update(self) -> None:
        result = execute_project_log_workflow(
            project_name="brain-ops",
            text="refactored runtime",
            load_registry_path=lambda: self.registry_path,
            load_database_path=lambda: self.db_path,
        )
        self.assertEqual(result.entry_type, "update")
        self.assertEqual(result.entry_text, "refactored runtime")
        self.assertFalse(result.registry_updated)

    def test_log_decision_updates_registry(self) -> None:
        result = execute_project_log_workflow(
            project_name="brain-ops",
            text="decisión: usar registry como source of truth",
            load_registry_path=lambda: self.registry_path,
            load_database_path=lambda: self.db_path,
        )
        self.assertEqual(result.entry_type, "decision")
        self.assertTrue(result.registry_updated)
        # Verify registry was updated
        projects = load_project_registry(self.registry_path)
        self.assertIn("usar registry como source of truth", projects["brain-ops"].context.decisions)

    def test_log_next_updates_registry(self) -> None:
        result = execute_project_log_workflow(
            project_name="brain-ops",
            text="next: test with real data",
            load_registry_path=lambda: self.registry_path,
            load_database_path=lambda: self.db_path,
        )
        self.assertEqual(result.entry_type, "next")
        self.assertTrue(result.registry_updated)
        projects = load_project_registry(self.registry_path)
        self.assertIn("test with real data", projects["brain-ops"].context.pending)

    def test_log_bug_no_registry_update(self) -> None:
        result = execute_project_log_workflow(
            project_name="brain-ops",
            text="bug: something broke",
            load_registry_path=lambda: self.registry_path,
            load_database_path=lambda: self.db_path,
        )
        self.assertEqual(result.entry_type, "bug")
        self.assertFalse(result.registry_updated)

    def test_log_unknown_project_raises(self) -> None:
        with self.assertRaises(ConfigError):
            execute_project_log_workflow(
                project_name="nonexistent",
                text="something",
                load_registry_path=lambda: self.registry_path,
                load_database_path=lambda: self.db_path,
            )

    def test_log_stored_in_sqlite(self) -> None:
        execute_project_log_workflow(
            project_name="brain-ops",
            text="bug: something broke",
            load_registry_path=lambda: self.registry_path,
            load_database_path=lambda: self.db_path,
        )
        logs = fetch_project_logs(self.db_path, project_name="brain-ops")
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["entry_type"], "bug")
        self.assertEqual(logs[0]["entry_text"], "something broke")


class SessionWorkflowTestCase(TestCase):
    def setUp(self) -> None:
        self._tmpdir = TemporaryDirectory()
        self.tmp_path = Path(self._tmpdir.name)
        self.registry_path = self.tmp_path / "projects.json"
        self.db_path = self.tmp_path / "test.db"
        initialize_database(self.db_path)
        execute_register_project_workflow(
            name="brain-ops",
            path="/home/user/brain-ops",
            stack=["python", "typer"],
            description="Personal intelligence station",
            commands={"run": "brain info", "test": "pytest"},
            load_registry_path=lambda: self.registry_path,
        )

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_session_returns_project_data(self) -> None:
        result = execute_session_workflow(
            project_name="brain-ops",
            load_registry_path=lambda: self.registry_path,
            load_database_path=lambda: self.db_path,
            run_git_log=lambda _: [],
        )
        self.assertIsInstance(result, ProjectSessionResult)
        self.assertEqual(result.project.name, "brain-ops")
        self.assertEqual(result.project.description, "Personal intelligence station")

    def test_session_includes_recent_logs(self) -> None:
        insert_project_log(
            self.db_path,
            project_name="brain-ops",
            entry_type="update",
            entry_text="refactored runtime",
        )
        result = execute_session_workflow(
            project_name="brain-ops",
            load_registry_path=lambda: self.registry_path,
            load_database_path=lambda: self.db_path,
            run_git_log=lambda _: [],
        )
        self.assertEqual(len(result.recent_logs), 1)
        self.assertEqual(result.recent_logs[0]["entry_text"], "refactored runtime")

    def test_session_includes_git_log(self) -> None:
        fake_commits = ["abc1234 Add feature X", "def5678 Fix bug Y"]
        result = execute_session_workflow(
            project_name="brain-ops",
            load_registry_path=lambda: self.registry_path,
            load_database_path=lambda: self.db_path,
            run_git_log=lambda _: fake_commits,
        )
        self.assertEqual(result.recent_commits, fake_commits)

    def test_session_unknown_project_raises(self) -> None:
        with self.assertRaises(ConfigError):
            execute_session_workflow(
                project_name="nonexistent",
                load_registry_path=lambda: self.registry_path,
                load_database_path=lambda: self.db_path,
                run_git_log=lambda _: [],
            )

    def test_session_to_dict(self) -> None:
        result = execute_session_workflow(
            project_name="brain-ops",
            load_registry_path=lambda: self.registry_path,
            load_database_path=lambda: self.db_path,
            run_git_log=lambda _: ["abc Fix thing"],
        )
        data = result.to_dict()
        self.assertEqual(data["project"]["name"], "brain-ops")
        self.assertEqual(data["recent_commits"], ["abc Fix thing"])
        self.assertIsInstance(data["recent_logs"], list)


if __name__ == "__main__":
    import unittest

    unittest.main()
