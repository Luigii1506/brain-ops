"""Tests for backlinking — auto-link existing notes when new entity is created."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from brain_ops.domains.knowledge.backlinking import inject_backlinks


class InjectBacklinksTestCase(TestCase):
    def setUp(self) -> None:
        self._tmpdir = TemporaryDirectory()
        self.vault = Path(self._tmpdir.name)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _write(self, name: str, content: str) -> Path:
        p = self.vault / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return p

    def test_links_plain_mention(self) -> None:
        self._write("Note A.md", "---\nname: A\n---\n\nEl ostracismo fue importante.")
        result = inject_backlinks(self.vault, "ostracismo")
        self.assertEqual(result.notes_linked, 1)
        content = (self.vault / "Note A.md").read_text(encoding="utf-8")
        self.assertIn("[[ostracismo]]", content)

    def test_skips_already_linked(self) -> None:
        self._write("Note B.md", "---\nname: B\n---\n\nEl [[ostracismo]] ya está linkeado.")
        result = inject_backlinks(self.vault, "ostracismo")
        self.assertEqual(result.notes_linked, 0)

    def test_skips_own_note(self) -> None:
        self._write("ostracismo.md", "---\nname: ostracismo\n---\n\nDefinición de ostracismo.")
        result = inject_backlinks(self.vault, "ostracismo")
        self.assertEqual(result.notes_linked, 0)

    def test_only_first_occurrence(self) -> None:
        self._write("Note C.md", "---\nname: C\n---\n\nostracismo primero. ostracismo segundo.")
        result = inject_backlinks(self.vault, "ostracismo")
        content = (self.vault / "Note C.md").read_text(encoding="utf-8")
        self.assertEqual(content.count("[[ostracismo]]"), 1)
        # Second one should remain plain
        self.assertIn("ostracismo segundo", content)

    def test_updates_related_frontmatter(self) -> None:
        self._write("Note D.md", "---\nname: D\nrelated:\n  - Atenas\n---\n\nEl ostracismo era votado.")
        inject_backlinks(self.vault, "ostracismo")
        content = (self.vault / "Note D.md").read_text(encoding="utf-8")
        self.assertIn("ostracismo", content)
        # Should be in related list
        self.assertIn("- ostracismo", content.lower() if "ostracismo" in content else "")

    def test_creates_related_if_null(self) -> None:
        self._write("Note E.md", "---\nname: E\nrelated: null\n---\n\nostracismo mencionado aquí.")
        inject_backlinks(self.vault, "ostracismo")
        content = (self.vault / "Note E.md").read_text(encoding="utf-8")
        self.assertIn("[[ostracismo]]", content)

    def test_case_insensitive_match(self) -> None:
        self._write("Note F.md", "---\nname: F\n---\n\nEl Ostracismo fue creado por Clístenes.")
        result = inject_backlinks(self.vault, "Ostracismo")
        self.assertEqual(result.notes_linked, 1)

    def test_multiple_notes_linked(self) -> None:
        self._write("Note G.md", "---\nname: G\n---\n\nEl ostracismo fue una herramienta.")
        self._write("Note H.md", "---\nname: H\n---\n\nSe usó el ostracismo contra Temístocles.")
        self._write("Note I.md", "---\nname: I\n---\n\nNada relevante aquí.")
        result = inject_backlinks(self.vault, "ostracismo")
        self.assertEqual(result.notes_linked, 2)
        self.assertEqual(result.notes_scanned, 3)

    def test_dry_run_no_changes(self) -> None:
        self._write("Note J.md", "---\nname: J\n---\n\nEl ostracismo existió.")
        result = inject_backlinks(self.vault, "ostracismo", dry_run=True)
        self.assertEqual(result.notes_linked, 1)
        # File should NOT be modified
        content = (self.vault / "Note J.md").read_text(encoding="utf-8")
        self.assertNotIn("[[ostracismo]]", content)

    def test_skips_excluded_dirs(self) -> None:
        self._write(".git/config.md", "---\nname: X\n---\n\nostracismo.")
        self._write(".obsidian/plugin.md", "---\nname: Y\n---\n\nostracismo.")
        self._write("Knowledge/Note.md", "---\nname: Z\n---\n\nostracismo mencionado.")
        result = inject_backlinks(self.vault, "ostracismo")
        self.assertEqual(result.notes_linked, 1)
        self.assertIn("Knowledge/Note.md", result.linked_files[0])

    def test_multi_word_entity(self) -> None:
        self._write("Note K.md", "---\nname: K\n---\n\nClístenes de Atenas creó la democracia.")
        result = inject_backlinks(self.vault, "Clístenes de Atenas")
        self.assertEqual(result.notes_linked, 1)
        content = (self.vault / "Note K.md").read_text(encoding="utf-8")
        self.assertIn("[[Clístenes de Atenas]]", content)


if __name__ == "__main__":
    import unittest

    unittest.main()
