from __future__ import annotations

import unittest

from brain_ops.domains.knowledge.capture import plan_capture_note


class KnowledgeCaptureDomainTestCase(unittest.TestCase):
    def test_plan_capture_note_detects_source_and_sets_source_metadata(self) -> None:
        plan = plan_capture_note("Artículo útil https://es.wikipedia.org/wiki/SQLite")

        self.assertEqual(plan.note_type, "source")
        self.assertEqual(plan.extra_frontmatter["url"], ["https://es.wikipedia.org/wiki/SQLite"])
        self.assertEqual(plan.extra_frontmatter["source_type"], "wikipedia")
        self.assertIn("## Source", plan.body)
        self.assertIn("## Summary", plan.body)

    def test_plan_capture_note_detects_project_and_sets_active_status(self) -> None:
        plan = plan_capture_note("Proyecto brain-ops roadmap para cerrar el refactor")

        self.assertEqual(plan.note_type, "project")
        self.assertEqual(plan.extra_frontmatter["status"], "active")
        self.assertIn("## Current status", plan.body)
        self.assertIn("## Next action", plan.body)

    def test_plan_capture_note_rejects_empty_text_and_respects_forced_type(self) -> None:
        with self.assertRaises(ValueError):
            plan_capture_note("   ")

        forced = plan_capture_note(
            "Esto tiene una URL https://example.com pero quiero guardarlo como knowledge",
            force_type="knowledge",
        )

        self.assertEqual(forced.note_type, "knowledge")
        self.assertEqual(forced.extra_frontmatter["status"], "draft")
        self.assertIn("Forced type `knowledge`.", forced.reason)
        self.assertIn("## Core idea", forced.body)


if __name__ == "__main__":
    unittest.main()
