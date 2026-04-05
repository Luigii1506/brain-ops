from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from brain_ops.config import VaultConfig
from brain_ops.storage.obsidian.note_writing import render_note_document, write_note_document_if_changed
from brain_ops.vault import Vault


class ObsidianNoteWritingTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        root = Path(self.tmpdir.name)
        self.vault = Vault(
            VaultConfig(
                vault_path=root,
                database_path=root / "brain_ops.db",
            )
        )
        self.path = root / "Inbox" / "Test.md"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def test_write_note_document_if_changed_skips_when_render_matches(self) -> None:
        original = render_note_document(frontmatter={"type": "note"}, body="hello")
        self.path.write_text(original, encoding="utf-8")

        operation = write_note_document_if_changed(
            self.vault,
            self.path,
            frontmatter={"type": "note"},
            body="hello",
            original_content=original,
            overwrite=True,
        )

        self.assertIsNone(operation)
        self.assertEqual(self.path.read_text(encoding="utf-8"), original)

    def test_write_note_document_if_changed_writes_when_render_differs(self) -> None:
        original = render_note_document(frontmatter={"type": "note"}, body="hello")
        self.path.write_text(original, encoding="utf-8")

        operation = write_note_document_if_changed(
            self.vault,
            self.path,
            frontmatter={"type": "note", "updated": "2026-04-04T10:00:00"},
            body="hello world",
            original_content=original,
            overwrite=True,
        )

        self.assertIsNotNone(operation)
        self.assertIn("updated", self.path.read_text(encoding="utf-8"))
        self.assertIn("hello world", self.path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
