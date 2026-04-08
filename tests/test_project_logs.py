"""Tests for project-log and session workflows."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from brain_ops.application.projects import (
    ProjectAuditResult,
    ProjectLogResult,
    ProjectSessionResult,
    _classify_entry,
    execute_audit_project_workflow,
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


class AuditProjectTestCase(TestCase):
    """Tests for execute_audit_project_workflow."""

    def setUp(self) -> None:
        self._tmpdir = TemporaryDirectory()
        self.tmp_path = Path(self._tmpdir.name)
        self.registry_path = self.tmp_path / "projects.json"
        self.db_path = self.tmp_path / "test.db"
        initialize_database(self.db_path)
        # Register a project with full context
        from brain_ops.application.projects import execute_update_project_context_workflow

        execute_register_project_workflow(
            name="brain-ops",
            path="/home/user/brain-ops",
            stack=["python"],
            description="Test project",
            commands={"run": "brain info", "test": "pytest"},
            load_registry_path=lambda: self.registry_path,
        )
        execute_update_project_context_workflow(
            name="brain-ops",
            phase="active",
            pending=["implement audit"],
            decisions=["use SQLite"],
            notes=None,
            load_registry_path=lambda: self.registry_path,
        )
        # Create vault project folder with all expected files
        self.vault_project_dir = self.tmp_path / "vault" / "04 - Projects" / "brain-ops"
        self.vault_project_dir.mkdir(parents=True)
        (self.vault_project_dir / "Brain-Ops.md").write_text(
            "# Brain-Ops\n\n## Current status\nAll good.\n",
            encoding="utf-8",
        )
        for fname in [
            "Architecture.md",
            "Decisions.md",
            "Runbook.md",
            "CLI Reference.md",
            "Workflows.md",
            "Debugging.md",
            "Changelog.md",
        ]:
            (self.vault_project_dir / fname).write_text(f"# {fname}\nContent here.\n", encoding="utf-8")

        # Create recent session note
        from datetime import datetime, timezone

        sessions_dir = self.vault_project_dir / "Sessions"
        sessions_dir.mkdir()
        today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
        (sessions_dir / f"Sesión {today}.md").write_text(
            f"# Sesión {today}\n- **10:00** [update] Started work\n",
            encoding="utf-8",
        )

        # Insert a recent project log
        insert_project_log(
            self.db_path,
            project_name="brain-ops",
            entry_type="update",
            entry_text="started audit feature",
        )

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _mock_resolve(self, config_path, project_name):
        """Patch _resolve_vault_project_dir for tests."""
        return self.vault_project_dir

    def test_audit_project_full_score(self) -> None:
        import brain_ops.application.projects as proj_mod

        original = proj_mod._resolve_vault_project_dir
        proj_mod._resolve_vault_project_dir = self._mock_resolve
        try:
            result = execute_audit_project_workflow(
                project_name="brain-ops",
                load_registry_path=lambda: self.registry_path,
                load_database_path=lambda: self.db_path,
                config_path=Path("dummy"),
            )
            self.assertEqual(result.score, 100)
            self.assertEqual(len(result.issues), 0)
        finally:
            proj_mod._resolve_vault_project_dir = original

    def test_audit_project_missing_files(self) -> None:
        import brain_ops.application.projects as proj_mod

        # Remove some files
        (self.vault_project_dir / "Architecture.md").unlink()
        (self.vault_project_dir / "Runbook.md").unlink()

        original = proj_mod._resolve_vault_project_dir
        proj_mod._resolve_vault_project_dir = self._mock_resolve
        try:
            result = execute_audit_project_workflow(
                project_name="brain-ops",
                load_registry_path=lambda: self.registry_path,
                load_database_path=lambda: self.db_path,
                config_path=Path("dummy"),
            )
            self.assertLess(result.score, 100)
            issue_text = " ".join(result.issues)
            self.assertIn("Architecture.md", issue_text)
            self.assertIn("Runbook.md", issue_text)
        finally:
            proj_mod._resolve_vault_project_dir = original


class SessionWithVaultTestCase(TestCase):
    """Tests for session workflow with vault data."""

    def setUp(self) -> None:
        self._tmpdir = TemporaryDirectory()
        self.tmp_path = Path(self._tmpdir.name)
        self.registry_path = self.tmp_path / "projects.json"
        self.db_path = self.tmp_path / "test.db"
        initialize_database(self.db_path)
        execute_register_project_workflow(
            name="brain-ops",
            path="/home/user/brain-ops",
            stack=["python"],
            description="Test project",
            commands=None,
            load_registry_path=lambda: self.registry_path,
        )
        # Create vault project folder
        self.vault_project_dir = self.tmp_path / "vault" / "04 - Projects" / "brain-ops"
        self.vault_project_dir.mkdir(parents=True)
        (self.vault_project_dir / "Brain-Ops.md").write_text(
            "# Brain-Ops\n\n## Current status\nWorking on audit feature.\n\n## Next actions\nFinish tests.\n",
            encoding="utf-8",
        )
        (self.vault_project_dir / "Decisions.md").write_text(
            "# Decisions\n\n- Use SQLite for storage\n- Use Typer for CLI\n- Use Rich for output\n",
            encoding="utf-8",
        )
        (self.vault_project_dir / "Debugging.md").write_text(
            "# Debugging\n\n## Config path not resolving on Windows\n\n- Symptom: path fails\n- Fix: use absolute path\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_session_with_vault_data(self) -> None:
        import brain_ops.application.projects as proj_mod

        original = proj_mod._resolve_vault_project_dir
        proj_mod._resolve_vault_project_dir = lambda cp, pn: self.vault_project_dir
        try:
            result = execute_session_workflow(
                project_name="brain-ops",
                load_registry_path=lambda: self.registry_path,
                load_database_path=lambda: self.db_path,
                run_git_log=lambda _: [],
                config_path=Path("dummy"),
            )
            self.assertIsNotNone(result.vault_status)
            self.assertIn("Working on audit feature", result.vault_status)
            self.assertEqual(len(result.vault_decisions), 3)
            self.assertEqual(len(result.vault_bugs), 1)
            self.assertIn("Config path not resolving on Windows", result.vault_bugs[0])
            self.assertEqual(result.vault_path, str(self.vault_project_dir))
        finally:
            proj_mod._resolve_vault_project_dir = original


class ProjectLogVaultWriteTestCase(TestCase):
    """Tests for project-log writing to vault files."""

    def setUp(self) -> None:
        self._tmpdir = TemporaryDirectory()
        self.tmp_path = Path(self._tmpdir.name)
        self.registry_path = self.tmp_path / "projects.json"
        self.db_path = self.tmp_path / "test.db"
        initialize_database(self.db_path)
        execute_register_project_workflow(
            name="brain-ops",
            path="/home/user/brain-ops",
            stack=["python"],
            description="Test project",
            commands=None,
            load_registry_path=lambda: self.registry_path,
        )
        # Create vault project folder with Changelog.md
        self.vault_project_dir = self.tmp_path / "vault" / "04 - Projects" / "brain-ops"
        self.vault_project_dir.mkdir(parents=True)
        (self.vault_project_dir / "Changelog.md").write_text(
            "# Changelog\n\n<!-- AUTO:START -->\n<!-- AUTO:END -->\n",
            encoding="utf-8",
        )
        (self.vault_project_dir / "Decisions.md").write_text(
            "# Decisiones\n\nRegistro de decisiones.\n\n---\n\n## 001. Decisión existente\n\n**Fecha:** 2026-04-01\n**Decisión:** Usar SQLite\n",
            encoding="utf-8",
        )
        (self.vault_project_dir / "Debugging.md").write_text(
            "# Debugging\n",
            encoding="utf-8",
        )
        sessions_dir = self.vault_project_dir / "Sessions"
        sessions_dir.mkdir()

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_project_log_does_not_write_to_changelog(self) -> None:
        """Changelog is no longer auto-populated (redundant with Sessions)."""
        execute_project_log_workflow(
            project_name="brain-ops",
            text="added audit feature",
            load_registry_path=lambda: self.registry_path,
            load_database_path=lambda: self.db_path,
            vault_project_dir=self.vault_project_dir,
        )
        # Changelog/ folder should NOT be created by project-log
        changelog_dir = self.vault_project_dir / "Changelog"
        self.assertFalse(changelog_dir.exists())

    def test_project_log_decision_writes_to_decisions(self) -> None:
        execute_project_log_workflow(
            project_name="brain-ops",
            text="decisión: use Pydantic v2",
            load_registry_path=lambda: self.registry_path,
            load_database_path=lambda: self.db_path,
            vault_project_dir=self.vault_project_dir,
        )
        content = (self.vault_project_dir / "Decisions.md").read_text(encoding="utf-8")
        self.assertIn("use Pydantic v2", content)
        # Newest decision should appear BEFORE the existing one
        new_pos = content.find("use Pydantic v2")
        old_pos = content.find("Decisión existente")
        self.assertGreater(old_pos, new_pos, "Newest decision should be above older ones")

    def test_project_log_bug_writes_to_debugging(self) -> None:
        execute_project_log_workflow(
            project_name="brain-ops",
            text="bug: config not loading",
            load_registry_path=lambda: self.registry_path,
            load_database_path=lambda: self.db_path,
            vault_project_dir=self.vault_project_dir,
        )
        content = (self.vault_project_dir / "Debugging.md").read_text(encoding="utf-8")
        self.assertIn("config not loading", content)

    def test_project_log_creates_session_note(self) -> None:
        execute_project_log_workflow(
            project_name="brain-ops",
            text="started work",
            load_registry_path=lambda: self.registry_path,
            load_database_path=lambda: self.db_path,
            vault_project_dir=self.vault_project_dir,
        )
        from datetime import datetime

        today = datetime.now().strftime("%Y-%m-%d")
        session_file = self.vault_project_dir / "Sessions" / f"Sesión {today}.md"
        self.assertTrue(session_file.exists())
        content = session_file.read_text(encoding="utf-8")
        self.assertIn("[update] started work", content)

    def test_project_log_skips_missing_vault(self) -> None:
        """When vault_project_dir is None, no error occurs."""
        result = execute_project_log_workflow(
            project_name="brain-ops",
            text="something",
            load_registry_path=lambda: self.registry_path,
            load_database_path=lambda: self.db_path,
            vault_project_dir=None,
        )
        self.assertEqual(result.entry_type, "update")


if __name__ == "__main__":
    import unittest

    unittest.main()
