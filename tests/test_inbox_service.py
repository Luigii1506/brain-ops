from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from brain_ops.config import VaultConfig
from brain_ops.services.inbox_service import process_inbox
from brain_ops.vault import Vault


class InboxServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        root = Path(self.temp_dir.name)
        self.config = VaultConfig(
            vault_path=root / "vault",
            database_path=root / "brain_ops.db",
        )
        self.vault = Vault(self.config)
        self.vault.root.mkdir(parents=True, exist_ok=True)
        self.vault.ensure_structure()

    def _write_inbox_note(self, name: str, text: str) -> Path:
        path = self.vault.note_path(self.config.folders.inbox, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_process_inbox_normalizes_and_moves_source_note(self) -> None:
        source_path = self._write_inbox_note("SQLite Source", "Artículo útil https://example.com/sqlite")

        summary = process_inbox(self.vault, improve_structure=True)

        destination = self.vault.note_path(self.config.folders.sources, "SQLite Source")
        self.assertEqual(summary.scanned, 1)
        self.assertEqual(summary.normalized, 1)
        self.assertEqual(summary.moved, 1)
        self.assertEqual(summary.left_in_inbox, 0)
        self.assertFalse(source_path.exists())
        self.assertTrue(destination.exists())
        moved_text = destination.read_text(encoding="utf-8")
        self.assertIn("type: source", moved_text)
        self.assertIn("## Source", moved_text)
        self.assertEqual(summary.items[0].destination_path, destination)
        self.assertTrue(summary.items[0].moved)

    def test_process_inbox_leaves_ambiguous_project_note_in_inbox(self) -> None:
        inbox_path = self._write_inbox_note(
            "Architecture Note",
            "---\ntype: architecture\n---\n\nPending structure",
        )

        summary = process_inbox(self.vault, improve_structure=False)

        self.assertEqual(summary.scanned, 1)
        self.assertEqual(summary.moved, 0)
        self.assertEqual(summary.left_in_inbox, 1)
        self.assertTrue(inbox_path.exists())
        self.assertFalse(summary.items[0].moved)
        self.assertIn("No unambiguous destination folder", summary.items[0].reason)


if __name__ == "__main__":
    unittest.main()
