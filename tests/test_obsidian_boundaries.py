from __future__ import annotations

import tempfile
from datetime import datetime
from pathlib import Path
from unittest import TestCase

from brain_ops.config import AIConfig, FolderConfig, VaultConfig
from brain_ops.models import OperationStatus
from brain_ops.storage.obsidian.note_loading import (
    load_note_document,
    load_optional_note_document,
    read_note_text,
    relative_note_path,
    resolve_note_document_path,
)
from brain_ops.storage.obsidian.note_paths import (
    build_note_path,
    resolve_folder,
    resolve_inbox_destination_path,
    resolve_note_path,
)
from brain_ops.storage.obsidian.report_writing import (
    build_in_memory_report_operation,
    build_report_operation,
    timestamped_report_name,
    write_report_text,
)
from brain_ops.vault import Vault


class ObsidianBoundariesTestCase(TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.config = VaultConfig(
            vault_path=root / "vault",
            data_dir=root / "data",
            database_path=root / "data" / "brain_ops.db",
            folders=FolderConfig(),
            ai=AIConfig(enable_llm_routing=False),
        )
        self.vault = Vault(config=self.config, dry_run=False)
        self.vault.root.mkdir(parents=True, exist_ok=True)
        for folder_name in self.config.folders.model_dump().values():
            (self.vault.root / folder_name).mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_note_loading_helpers_resolve_read_and_parse_documents(self) -> None:
        note_path = self.vault.root / self.config.folders.knowledge / "Idea.md"
        note_path.write_text("---\ntype: knowledge\nproject: BrainOps\n---\nBody text", encoding="utf-8")

        safe_path, relative = resolve_note_document_path(self.vault, Path(self.config.folders.knowledge) / "Idea.md")
        self.assertEqual(safe_path, note_path.resolve())
        self.assertEqual(relative, Path(self.config.folders.knowledge) / "Idea.md")
        self.assertEqual(relative_note_path(self.vault, note_path), Path(self.config.folders.knowledge) / "Idea.md")

        read_safe, read_relative, text = read_note_text(self.vault, note_path)
        self.assertEqual(read_safe, note_path.resolve())
        self.assertEqual(read_relative, Path(self.config.folders.knowledge) / "Idea.md")
        self.assertIn("Body text", text)

        loaded_safe, loaded_relative, frontmatter, body = load_note_document(self.vault, note_path)
        self.assertEqual(loaded_safe, note_path.resolve())
        self.assertEqual(loaded_relative, Path(self.config.folders.knowledge) / "Idea.md")
        self.assertEqual(frontmatter["type"], "knowledge")
        self.assertEqual(frontmatter["project"], "BrainOps")
        self.assertEqual(body.strip(), "Body text")

    def test_load_optional_note_document_handles_missing_and_present_notes(self) -> None:
        missing_path = Path(self.config.folders.sources) / "Missing.md"
        safe_path, relative, frontmatter, body = load_optional_note_document(self.vault, missing_path)
        self.assertEqual(safe_path, (self.vault.root / missing_path).resolve())
        self.assertEqual(relative, missing_path)
        self.assertEqual(frontmatter, {})
        self.assertEqual(body, "")

        existing_path = self.vault.root / self.config.folders.sources / "Source.md"
        existing_path.write_text("---\ntype: source\n---\nSource body", encoding="utf-8")
        safe_path, relative, frontmatter, body = load_optional_note_document(self.vault, existing_path)
        self.assertEqual(relative, Path(self.config.folders.sources) / "Source.md")
        self.assertEqual(frontmatter["type"], "source")
        self.assertEqual(body.strip(), "Source body")

    def test_note_path_helpers_resolve_default_explicit_and_inbox_destinations(self) -> None:
        knowledge_path = build_note_path(self.vault, self.config.folders.knowledge, "Idea")
        self.assertEqual(knowledge_path, self.vault.root / self.config.folders.knowledge / "Idea.md")

        self.assertEqual(resolve_folder(self.config, "command", None), f"{self.config.folders.systems}/Commands")
        self.assertEqual(resolve_folder(self.config, "security_note", None), f"{self.config.folders.systems}/Security")
        self.assertEqual(resolve_folder(self.config, "knowledge", None), self.config.folders.knowledge)
        self.assertEqual(resolve_folder(self.config, "knowledge", "Custom"), "Custom")

        resolved = resolve_note_path(self.vault, "knowledge", "Idea")
        self.assertEqual(resolved, self.vault.root / self.config.folders.knowledge / "Idea.md")

        ambiguous = resolve_inbox_destination_path(
            self.vault,
            Path("idea.md"),
            {"type": "architecture", "project": "BrainOps"},
            ambiguous_project_types={"architecture", "project"},
        )
        self.assertEqual(
            ambiguous,
            self.vault.root / self.config.folders.projects / "BrainOps" / "idea.md",
        )

        unresolved = resolve_inbox_destination_path(
            self.vault,
            Path("idea.md"),
            {"type": "architecture"},
            ambiguous_project_types={"architecture", "project"},
        )
        self.assertIsNone(unresolved)

        standard = resolve_inbox_destination_path(
            self.vault,
            Path("source-note.md"),
            {"type": "source"},
            ambiguous_project_types={"architecture", "project"},
        )
        self.assertEqual(
            standard,
            self.vault.root / self.config.folders.sources / "source-note.md",
        )

    def test_report_writing_helpers_write_and_shape_operations(self) -> None:
        report_name = timestamped_report_name("weekly-review", now=datetime(2026, 4, 4, 9, 30, 15))
        self.assertEqual(report_name, "weekly-review-20260404-093015")

        operation = write_report_text(self.vault, report_name, "Report body")
        self.assertEqual(operation.action, "write")
        self.assertEqual(operation.status, OperationStatus.CREATED)
        report_path = self.vault.root / self.config.folders.reports / f"{report_name}.md"
        self.assertTrue(report_path.exists())
        self.assertEqual(report_path.read_text(encoding="utf-8"), "Report body")

        report_op = build_report_operation(report_path, "generated report")
        self.assertEqual(report_op.action, "report")
        self.assertEqual(report_op.status, OperationStatus.REPORT)
        self.assertEqual(report_op.path, report_path)

        memory_op = build_in_memory_report_operation(self.vault, "rendered in memory")
        self.assertEqual(memory_op.action, "report")
        self.assertEqual(memory_op.status, OperationStatus.REPORT)
        self.assertEqual(memory_op.path, self.vault.root)


if __name__ == "__main__":
    import unittest

    unittest.main()
