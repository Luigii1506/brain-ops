from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from brain_ops.domains.projects.registry import (
    Project,
    ProjectContext,
    build_project,
    build_project_context,
    load_project_registry,
    save_project_registry,
    update_project_context,
)
from brain_ops.domains.projects.claude_md import render_claude_md
from brain_ops.application.projects import (
    execute_generate_claude_md_workflow,
    execute_list_projects_workflow,
    execute_project_context_workflow,
    execute_register_project_workflow,
    execute_update_project_context_workflow,
)
from brain_ops.errors import ConfigError


class ProjectRegistryModelTestCase(TestCase):
    def test_build_project_creates_valid_project(self) -> None:
        project = build_project("brain-ops", path="/home/user/brain-ops", stack=["python", "typer"])
        self.assertEqual(project.name, "brain-ops")
        self.assertEqual(project.path, "/home/user/brain-ops")
        self.assertEqual(project.stack, ["python", "typer"])

    def test_build_project_rejects_empty_name(self) -> None:
        with self.assertRaises(ValueError):
            build_project("", path="/tmp")

    def test_build_project_rejects_empty_path(self) -> None:
        with self.assertRaises(ValueError):
            build_project("test", path="")

    def test_build_project_strips_whitespace(self) -> None:
        project = build_project("  my-project  ", path="  /tmp/proj  ")
        self.assertEqual(project.name, "my-project")
        self.assertEqual(project.path, "/tmp/proj")

    def test_project_to_dict_and_from_dict_roundtrip(self) -> None:
        project = build_project("test", path="/tmp/test", stack=["python"], description="A test project")
        project.context = build_project_context(phase="Phase 1", pending=["item1"])
        data = project.to_dict()
        restored = Project.from_dict(data)
        self.assertEqual(restored.name, "test")
        self.assertEqual(restored.context.phase, "Phase 1")
        self.assertEqual(restored.context.pending, ["item1"])

    def test_update_project_context_updates_fields(self) -> None:
        project = build_project("test", path="/tmp")
        update_project_context(project, phase="Phase 2", pending=["do this"])
        self.assertEqual(project.context.phase, "Phase 2")
        self.assertEqual(project.context.pending, ["do this"])

    def test_update_project_context_preserves_unchanged_fields(self) -> None:
        project = build_project("test", path="/tmp")
        update_project_context(project, phase="Phase 1", decisions=["decided X"])
        update_project_context(project, phase="Phase 2")
        self.assertEqual(project.context.phase, "Phase 2")
        self.assertEqual(project.context.decisions, ["decided X"])


class ProjectRegistryPersistenceTestCase(TestCase):
    def test_save_and_load_roundtrip(self) -> None:
        with TemporaryDirectory() as temp_dir:
            registry_path = Path(temp_dir) / "projects.json"
            project = build_project("brain-ops", path="/home/user/brain-ops", stack=["python"])
            save_project_registry(registry_path, {"brain-ops": project})

            loaded = load_project_registry(registry_path)
            self.assertIn("brain-ops", loaded)
            self.assertEqual(loaded["brain-ops"].name, "brain-ops")
            self.assertEqual(loaded["brain-ops"].stack, ["python"])

    def test_load_returns_empty_when_file_missing(self) -> None:
        result = load_project_registry(Path("/tmp/nonexistent_registry_12345.json"))
        self.assertEqual(result, {})

    def test_save_creates_parent_directories(self) -> None:
        with TemporaryDirectory() as temp_dir:
            registry_path = Path(temp_dir) / "nested" / "dir" / "projects.json"
            save_project_registry(registry_path, {})
            self.assertTrue(registry_path.exists())


class RenderClaudeMdTestCase(TestCase):
    def test_renders_full_project_context(self) -> None:
        project = build_project(
            "brain-ops",
            path="/home/user/brain-ops",
            stack=["python", "typer", "sqlite"],
            description="Personal intelligence station.",
            commands={"run": "python -m brain_ops", "test": "pytest"},
        )
        update_project_context(
            project,
            phase="Phase 8 — monitoring and automation",
            pending=["monitoring domain", "API layer"],
            decisions=["Obsidian as knowledge source of truth"],
            notes="Using Codex for migration work.",
        )
        md = render_claude_md(project)

        self.assertIn("# brain-ops", md)
        self.assertIn("Personal intelligence station.", md)
        self.assertIn("python, typer, sqlite", md)
        self.assertIn("`python -m brain_ops`", md)
        self.assertIn("`pytest`", md)
        self.assertIn("Phase 8", md)
        self.assertIn("monitoring domain", md)
        self.assertIn("Obsidian as knowledge source of truth", md)
        self.assertIn("Using Codex", md)

    def test_renders_minimal_project(self) -> None:
        project = build_project("empty", path="/tmp/empty")
        md = render_claude_md(project)
        self.assertIn("# empty", md)


class ProjectWorkflowsTestCase(TestCase):
    def test_register_and_list_workflow(self) -> None:
        with TemporaryDirectory() as temp_dir:
            registry_path = Path(temp_dir) / "projects.json"
            loader = lambda: registry_path

            result = execute_register_project_workflow(
                name="brain-ops",
                path="/home/user/brain-ops",
                stack=["python"],
                description="Test",
                commands=None,
                load_registry_path=loader,
            )
            self.assertTrue(result.is_new)
            self.assertEqual(result.project.name, "brain-ops")

            projects = execute_list_projects_workflow(load_registry_path=loader)
            self.assertEqual(len(projects), 1)
            self.assertEqual(projects[0].name, "brain-ops")

    def test_register_existing_project_preserves_context(self) -> None:
        with TemporaryDirectory() as temp_dir:
            registry_path = Path(temp_dir) / "projects.json"
            loader = lambda: registry_path

            execute_register_project_workflow(
                name="proj", path="/tmp/proj", stack=None, description=None, commands=None,
                load_registry_path=loader,
            )
            execute_update_project_context_workflow(
                name="proj", phase="Phase 2", pending=None, decisions=None, notes=None,
                load_registry_path=loader,
            )
            result = execute_register_project_workflow(
                name="proj", path="/tmp/proj-v2", stack=["go"], description="updated",
                commands=None, load_registry_path=loader,
            )
            self.assertFalse(result.is_new)
            self.assertEqual(result.project.context.phase, "Phase 2")
            self.assertEqual(result.project.path, "/tmp/proj-v2")

    def test_project_context_workflow_raises_on_unknown(self) -> None:
        with TemporaryDirectory() as temp_dir:
            registry_path = Path(temp_dir) / "projects.json"
            with self.assertRaises(ConfigError):
                execute_project_context_workflow(
                    name="nonexistent",
                    load_registry_path=lambda: registry_path,
                )

    def test_update_context_and_retrieve(self) -> None:
        with TemporaryDirectory() as temp_dir:
            registry_path = Path(temp_dir) / "projects.json"
            loader = lambda: registry_path

            execute_register_project_workflow(
                name="test", path="/tmp/test", stack=None, description=None, commands=None,
                load_registry_path=loader,
            )
            execute_update_project_context_workflow(
                name="test", phase="Build", pending=["item A"], decisions=["use SQLite"],
                notes="some notes", load_registry_path=loader,
            )
            project = execute_project_context_workflow(name="test", load_registry_path=loader)
            self.assertEqual(project.context.phase, "Build")
            self.assertEqual(project.context.pending, ["item A"])
            self.assertEqual(project.context.decisions, ["use SQLite"])
            self.assertEqual(project.context.notes, "some notes")

    def test_generate_claude_md_workflow_writes_file(self) -> None:
        with TemporaryDirectory() as temp_dir:
            registry_path = Path(temp_dir) / "projects.json"
            output_path = Path(temp_dir) / "CLAUDE.md"
            loader = lambda: registry_path

            execute_register_project_workflow(
                name="test-proj", path=temp_dir, stack=["python"],
                description="Test project", commands={"run": "python main.py"},
                load_registry_path=loader,
            )
            result = execute_generate_claude_md_workflow(
                name="test-proj", output_path=output_path,
                load_registry_path=loader,
            )
            self.assertEqual(result.output_path, output_path)
            self.assertTrue(output_path.exists())
            content = output_path.read_text(encoding="utf-8")
            self.assertIn("# test-proj", content)
            self.assertIn("python", content)
            self.assertIn("`python main.py`", content)


if __name__ == "__main__":
    import unittest

    unittest.main()
