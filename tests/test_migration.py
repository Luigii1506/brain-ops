"""Tests for 4-layer project documentation migration and layered layout operations."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from brain_ops.application.projects import (
    execute_audit_project_workflow,
    execute_migrate_project_docs_workflow,
    execute_project_log_workflow,
    execute_register_project_workflow,
    execute_update_project_context_workflow,
    split_decisions_to_adrs,
)
from brain_ops.domains.projects.doc_layout import DocLayout, resolve_doc_path
from brain_ops.domains.projects.registry import (
    Project,
    load_project_registry,
    save_project_registry,
)
from brain_ops.errors import ConfigError
from brain_ops.storage.db import initialize_database


class DocLayoutResolveTestCase(TestCase):
    """Tests for resolve_doc_path helper."""

    def test_flat_root_note_returns_project_dir(self) -> None:
        base = Path("/vault/04 - Projects/my-proj")
        result = resolve_doc_path(base, "root_note", "flat")
        self.assertEqual(result, base)

    def test_layered_root_note_returns_canonical(self) -> None:
        base = Path("/vault/04 - Projects/my-proj")
        result = resolve_doc_path(base, "root_note", DocLayout.LAYERED_V1)
        self.assertEqual(result, base / "00 - Canonical")

    def test_layered_sessions_returns_operations(self) -> None:
        base = Path("/vault/04 - Projects/my-proj")
        result = resolve_doc_path(base, "sessions", DocLayout.LAYERED_V1)
        self.assertEqual(result, base / "02 - Operations/SESSIONS")

    def test_layered_decisions_returns_adr_dir(self) -> None:
        base = Path("/vault/04 - Projects/my-proj")
        result = resolve_doc_path(base, "decisions", DocLayout.LAYERED_V1)
        self.assertEqual(result, base / "00 - Canonical/ADR")


class ProjectDocLayoutFieldTestCase(TestCase):
    """Tests for doc_layout field on Project model."""

    def test_default_doc_layout_is_flat(self) -> None:
        p = Project(name="test", path="/tmp")
        self.assertEqual(p.doc_layout, "flat")

    def test_doc_layout_roundtrip(self) -> None:
        p = Project(name="test", path="/tmp", doc_layout="layered-v1")
        data = p.to_dict()
        self.assertEqual(data["doc_layout"], "layered-v1")
        restored = Project.from_dict(data)
        self.assertEqual(restored.doc_layout, "layered-v1")

    def test_doc_layout_defaults_for_old_registry(self) -> None:
        """Existing registry entries without doc_layout default to flat."""
        data = {"name": "old-project", "path": "/tmp"}
        p = Project.from_dict(data)
        self.assertEqual(p.doc_layout, "flat")


class SplitDecisionsToAdrsTestCase(TestCase):
    """Tests for splitting monolithic Decisions.md into individual ADR files."""

    def setUp(self) -> None:
        self._tmpdir = TemporaryDirectory()
        self.tmp_path = Path(self._tmpdir.name)
        self.adr_dir = self.tmp_path / "ADR"
        self.adr_dir.mkdir()

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_split_decisions_creates_individual_files(self) -> None:
        decisions_content = (
            "# Decisiones\n\nRegistro de decisiones.\n\n"
            "---\n\n## 001. Use SQLite\n\n"
            "**Fecha:** 2026-03-15\n"
            "**Contexto:** Need a lightweight database\n"
            "**Decisión:** Use SQLite\n"
            "**Tradeoffs:** No multi-user support\n"
            "**Consecuencias:** Fast local queries\n\n"
            "---\n\n## 002. Use Typer for CLI\n\n"
            "**Fecha:** 2026-03-20\n"
            "**Contexto:** Need a CLI framework\n"
            "**Decisión:** Use Typer for CLI\n"
        )
        decisions_path = self.tmp_path / "Decisions.md"
        decisions_path.write_text(decisions_content, encoding="utf-8")

        result = split_decisions_to_adrs(decisions_path, self.adr_dir, "brain-ops")

        self.assertEqual(len(result), 2)
        self.assertTrue((self.adr_dir / "ADR-001.md").exists())
        self.assertTrue((self.adr_dir / "ADR-002.md").exists())

        content_001 = (self.adr_dir / "ADR-001.md").read_text(encoding="utf-8")
        self.assertIn("Use SQLite", content_001)
        self.assertIn("adr_number: 1", content_001)
        self.assertIn("project: brain-ops", content_001)

    def test_split_handles_empty_file(self) -> None:
        decisions_path = self.tmp_path / "Decisions.md"
        decisions_path.write_text("# Decisiones\n\nNo decisions yet.\n", encoding="utf-8")
        result = split_decisions_to_adrs(decisions_path, self.adr_dir, "test")
        self.assertEqual(len(result), 0)


class MigrateProjectDocsTestCase(TestCase):
    """Tests for the full migration workflow."""

    def setUp(self) -> None:
        self._tmpdir = TemporaryDirectory()
        self.tmp_path = Path(self._tmpdir.name)
        self.registry_path = self.tmp_path / "projects.json"
        self.db_path = self.tmp_path / "test.db"
        initialize_database(self.db_path)

        # Register project
        execute_register_project_workflow(
            name="brain-ops",
            path="/home/user/brain-ops",
            stack=["python"],
            description="Test project",
            commands=None,
            load_registry_path=lambda: self.registry_path,
        )

        # Create flat vault structure
        self.vault_project_dir = self.tmp_path / "vault" / "04 - Projects" / "brain-ops"
        self.vault_project_dir.mkdir(parents=True)

        (self.vault_project_dir / "Brain-Ops.md").write_text(
            "---\ntype: project\nstatus: active\n---\n# Brain-Ops\n\n## Current status\nAll good.\n",
            encoding="utf-8",
        )
        (self.vault_project_dir / "Architecture.md").write_text("# Architecture\n", encoding="utf-8")
        (self.vault_project_dir / "Decisions.md").write_text(
            "# Decisiones\n\nRegistro.\n\n---\n\n## 001. Use SQLite\n\n"
            "**Fecha:** 2026-03-15\n**Contexto:** Need DB\n**Decisión:** Use SQLite\n",
            encoding="utf-8",
        )
        (self.vault_project_dir / "Debugging.md").write_text("# Debugging\n", encoding="utf-8")
        (self.vault_project_dir / "Runbook.md").write_text("# Runbook\n", encoding="utf-8")
        (self.vault_project_dir / "Workflows.md").write_text("# Workflows\n", encoding="utf-8")
        (self.vault_project_dir / "CLI Reference.md").write_text(
            "# CLI\n\n<!-- AUTO:START -->\nhelp\n<!-- AUTO:END -->\n", encoding="utf-8"
        )
        (self.vault_project_dir / "Changelog.md").write_text("# Changelog\n", encoding="utf-8")

        sessions_dir = self.vault_project_dir / "Sessions"
        sessions_dir.mkdir()
        today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
        (sessions_dir / f"Sesión {today}.md").write_text(f"# Sesión {today}\n", encoding="utf-8")

        context_dir = self.vault_project_dir / "Context Packs"
        context_dir.mkdir()
        (context_dir / "brain-ops Context Pack.md").write_text("# Context\n", encoding="utf-8")

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _mock_resolve(self, config_path, project_name):
        return self.vault_project_dir

    def test_dry_run_reports_moves(self) -> None:
        import brain_ops.application.projects as proj_mod

        original = proj_mod._resolve_vault_project_dir
        proj_mod._resolve_vault_project_dir = self._mock_resolve
        try:
            result = execute_migrate_project_docs_workflow(
                project_name="brain-ops",
                load_registry_path=lambda: self.registry_path,
                config_path=Path("dummy"),
                dry_run=True,
            )
            self.assertTrue(len(result.moves) > 0)
            self.assertEqual(result.adrs_split, 0)
            # Flat files should still exist
            self.assertTrue((self.vault_project_dir / "Brain-Ops.md").exists())
        finally:
            proj_mod._resolve_vault_project_dir = original

    def test_full_migration(self) -> None:
        import brain_ops.application.projects as proj_mod

        original = proj_mod._resolve_vault_project_dir
        proj_mod._resolve_vault_project_dir = self._mock_resolve
        try:
            result = execute_migrate_project_docs_workflow(
                project_name="brain-ops",
                load_registry_path=lambda: self.registry_path,
                config_path=Path("dummy"),
            )

            # Root note moved
            self.assertFalse((self.vault_project_dir / "Brain-Ops.md").exists())
            self.assertTrue((self.vault_project_dir / "00 - Canonical" / "PROJECT.md").exists())
            # Alias added
            content = (self.vault_project_dir / "00 - Canonical" / "PROJECT.md").read_text()
            self.assertIn("aliases:", content)

            # Architecture moved
            self.assertFalse((self.vault_project_dir / "Architecture.md").exists())
            self.assertTrue((self.vault_project_dir / "00 - Canonical" / "ARCHITECTURE.md").exists())

            # Decisions split into ADRs
            self.assertFalse((self.vault_project_dir / "Decisions.md").exists())
            self.assertTrue((self.vault_project_dir / "00 - Canonical" / "ADR" / "ADR-001.md").exists())
            self.assertEqual(result.adrs_split, 1)

            # Sessions moved
            self.assertFalse((self.vault_project_dir / "Sessions").exists())
            sessions_dir = self.vault_project_dir / "02 - Operations" / "SESSIONS"
            self.assertTrue(sessions_dir.is_dir())
            self.assertTrue(any(sessions_dir.iterdir()))

            # New scaffold files created
            self.assertTrue((self.vault_project_dir / "00 - Canonical" / "INVARIANTS.md").exists())
            self.assertTrue((self.vault_project_dir / "03 - Direction" / "PRIORITIES.md").exists())

            # Registry updated
            projects = load_project_registry(self.registry_path)
            self.assertEqual(projects["brain-ops"].doc_layout, "layered-v1")
        finally:
            proj_mod._resolve_vault_project_dir = original

    def test_migration_rejects_already_layered(self) -> None:
        # Set doc_layout to layered-v1
        projects = load_project_registry(self.registry_path)
        projects["brain-ops"].doc_layout = "layered-v1"
        save_project_registry(self.registry_path, projects)

        import brain_ops.application.projects as proj_mod

        original = proj_mod._resolve_vault_project_dir
        proj_mod._resolve_vault_project_dir = self._mock_resolve
        try:
            with self.assertRaises(ConfigError):
                execute_migrate_project_docs_workflow(
                    project_name="brain-ops",
                    load_registry_path=lambda: self.registry_path,
                    config_path=Path("dummy"),
                )
        finally:
            proj_mod._resolve_vault_project_dir = original


class LayeredVaultLogWriteTestCase(TestCase):
    """Tests for project-log writing to layered vault structure."""

    def setUp(self) -> None:
        self._tmpdir = TemporaryDirectory()
        self.tmp_path = Path(self._tmpdir.name)
        self.registry_path = self.tmp_path / "projects.json"
        self.db_path = self.tmp_path / "test.db"
        initialize_database(self.db_path)

        # Register project with layered layout
        execute_register_project_workflow(
            name="brain-ops",
            path="/home/user/brain-ops",
            stack=["python"],
            description="Test project",
            commands=None,
            load_registry_path=lambda: self.registry_path,
        )
        projects = load_project_registry(self.registry_path)
        projects["brain-ops"].doc_layout = "layered-v1"
        save_project_registry(self.registry_path, projects)

        # Create layered vault structure
        self.vault_project_dir = self.tmp_path / "vault" / "04 - Projects" / "brain-ops"
        self.vault_project_dir.mkdir(parents=True)
        for subdir in [
            "00 - Canonical/ADR",
            "00 - Canonical/REFERENCE",
            "02 - Operations/DEBUGGING",
            "02 - Operations/SESSIONS",
            "02 - Operations/CONTEXT_PACKS",
        ]:
            (self.vault_project_dir / subdir).mkdir(parents=True)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_decision_creates_adr_file(self) -> None:
        execute_project_log_workflow(
            project_name="brain-ops",
            text="decisión: use Pydantic v2",
            load_registry_path=lambda: self.registry_path,
            load_database_path=lambda: self.db_path,
            vault_project_dir=self.vault_project_dir,
        )
        adr_dir = self.vault_project_dir / "00 - Canonical" / "ADR"
        adr_files = list(adr_dir.glob("ADR-*.md"))
        self.assertEqual(len(adr_files), 1)
        content = adr_files[0].read_text(encoding="utf-8")
        self.assertIn("use Pydantic v2", content)
        self.assertIn("adr_number: 1", content)

    def test_sequential_decisions_increment_number(self) -> None:
        for text in ["decisión: first", "decisión: second"]:
            execute_project_log_workflow(
                project_name="brain-ops",
                text=text,
                load_registry_path=lambda: self.registry_path,
                load_database_path=lambda: self.db_path,
                vault_project_dir=self.vault_project_dir,
            )
        adr_dir = self.vault_project_dir / "00 - Canonical" / "ADR"
        self.assertTrue((adr_dir / "ADR-001.md").exists())
        self.assertTrue((adr_dir / "ADR-002.md").exists())

    def test_bug_creates_known_issues_file(self) -> None:
        execute_project_log_workflow(
            project_name="brain-ops",
            text="bug: config not loading",
            load_registry_path=lambda: self.registry_path,
            load_database_path=lambda: self.db_path,
            vault_project_dir=self.vault_project_dir,
        )
        issues_path = self.vault_project_dir / "02 - Operations" / "DEBUGGING" / "known-issues.md"
        self.assertTrue(issues_path.exists())
        content = issues_path.read_text(encoding="utf-8")
        self.assertIn("config not loading", content)

    def test_session_note_in_operations(self) -> None:
        execute_project_log_workflow(
            project_name="brain-ops",
            text="started work",
            load_registry_path=lambda: self.registry_path,
            load_database_path=lambda: self.db_path,
            vault_project_dir=self.vault_project_dir,
        )
        today = datetime.now().strftime("%Y-%m-%d")
        session_file = self.vault_project_dir / "02 - Operations" / "SESSIONS" / f"Sesión {today}.md"
        self.assertTrue(session_file.exists())
        content = session_file.read_text(encoding="utf-8")
        self.assertIn("[update] started work", content)


class LayeredAuditTestCase(TestCase):
    """Tests for audit with layered layout."""

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
            commands={"test": "pytest"},
            load_registry_path=lambda: self.registry_path,
        )
        execute_update_project_context_workflow(
            name="brain-ops",
            phase="active",
            pending=["something"],
            decisions=["use SQLite"],
            notes=None,
            load_registry_path=lambda: self.registry_path,
        )
        projects = load_project_registry(self.registry_path)
        projects["brain-ops"].doc_layout = "layered-v1"
        save_project_registry(self.registry_path, projects)

        # Create full layered vault structure
        self.vault_project_dir = self.tmp_path / "vault" / "04 - Projects" / "brain-ops"
        self.vault_project_dir.mkdir(parents=True)

        canonical = self.vault_project_dir / "00 - Canonical"
        canonical.mkdir()
        (canonical / "PROJECT.md").write_text("# Brain-Ops\n\n## Current status\nAll good.\n", encoding="utf-8")
        (canonical / "ARCHITECTURE.md").write_text("# Architecture\nContent.\n", encoding="utf-8")
        (canonical / "INVARIANTS.md").write_text("# Invariants\nContent.\n", encoding="utf-8")

        adr_dir = canonical / "ADR"
        adr_dir.mkdir()
        (adr_dir / "ADR-001.md").write_text("# ADR-001. Use SQLite\n\n## Decision\nUse SQLite\n", encoding="utf-8")

        ref_dir = canonical / "REFERENCE"
        ref_dir.mkdir()
        (ref_dir / "CLI.md").write_text("# CLI\n\n<!-- AUTO:START -->\nhelp\n<!-- AUTO:END -->\n", encoding="utf-8")

        ops = self.vault_project_dir / "02 - Operations"
        (ops / "RUNBOOKS").mkdir(parents=True)
        (ops / "RUNBOOKS" / "Runbook.md").write_text("# Runbook\nContent.\n", encoding="utf-8")
        (ops / "SESSIONS").mkdir(parents=True)
        today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
        (ops / "SESSIONS" / f"Sesión {today}.md").write_text(f"# Sesión {today}\n", encoding="utf-8")

        direction = self.vault_project_dir / "03 - Direction"
        direction.mkdir()
        (direction / "PRIORITIES.md").write_text("# Priorities\nContent.\n", encoding="utf-8")

        from brain_ops.storage.sqlite.project_logs import insert_project_log
        insert_project_log(self.db_path, project_name="brain-ops", entry_type="update", entry_text="test")

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _mock_resolve(self, config_path, project_name):
        return self.vault_project_dir

    def test_audit_layered_full_score(self) -> None:
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
            self.assertEqual(result.score, 100, f"Issues: {result.issues}")
            self.assertEqual(len(result.issues), 0)
        finally:
            proj_mod._resolve_vault_project_dir = original


if __name__ == "__main__":
    import unittest

    unittest.main()
