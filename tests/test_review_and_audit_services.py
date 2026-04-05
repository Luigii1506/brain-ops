from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from brain_ops.config import VaultConfig
from brain_ops.services.audit_service import audit_vault
from brain_ops.services.review_service import generate_weekly_review
from brain_ops.vault import Vault


class ReviewAndAuditServicesTestCase(unittest.TestCase):
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

    def _write_note(self, relative: str, text: str) -> Path:
        path = self.vault.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_generate_weekly_review_collects_inbox_and_project_signals(self) -> None:
        self._write_note(
            f"{self.config.folders.inbox}/Pending.md",
            "---\ntype: inbox\n---\n\nPendiente",
        )
        self._write_note(
            f"{self.config.folders.projects}/Project Alpha/Architecture.md",
            "---\ntype: architecture\nproject: Project Alpha\nstatus: active\n---\n\n## Architecture\n\nCurrent state",
        )

        summary = generate_weekly_review(self.vault, stale_days=21, write_report=False)

        self.assertGreaterEqual(len(summary.inbox_notes), 1)
        self.assertTrue(any("Pending.md" in str(path) for path in summary.inbox_notes))
        self.assertGreaterEqual(len(summary.recent_changes), 1)
        self.assertEqual(len(summary.operations), 1)
        self.assertEqual(summary.operations[0].status.value, "report")

    def test_audit_vault_detects_root_note_and_missing_frontmatter(self) -> None:
        self._write_note("RootNote.md", "# Root note\n")
        self._write_note(
            f"{self.config.folders.sources}/SQLite.md",
            "---\ntype: source\n---\n\nSQLite source note",
        )

        summary = audit_vault(self.vault, write_report=False)

        self.assertGreaterEqual(summary.total_notes, 2)
        self.assertTrue(any("RootNote.md" in str(path) for path in summary.notes_in_root))
        self.assertTrue(any("RootNote.md" in str(path) for path in summary.notes_missing_frontmatter))
        self.assertEqual(len(summary.operations), 1)
        self.assertEqual(summary.operations[0].status.value, "report")


if __name__ == "__main__":
    unittest.main()
