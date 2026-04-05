from __future__ import annotations

import unittest
from pathlib import Path

from brain_ops.domains.knowledge.inbox import normalize_inbox_note, plan_inbox_disposition
from brain_ops.domains.knowledge.promotion import (
    build_promoted_knowledge_body,
    default_target_type,
    ensure_related_note_link,
    extract_sections,
    materialize_source_promotion,
    materialize_stub_promotion,
    normalize_promoted_title,
)


class KnowledgePromotionAndInboxTestCase(unittest.TestCase):
    def test_promotion_helpers_extract_and_normalize_expected_values(self) -> None:
        self.assertEqual(default_target_type("source", {}), "knowledge")
        self.assertEqual(default_target_type("knowledge", {"status": "stub"}), "knowledge")
        self.assertEqual(default_target_type("project", {}), "project")
        self.assertEqual(normalize_promoted_title("SN- SQLite Notes "), "SQLite Notes")

        sections = extract_sections(
            "## Summary\n\nShort summary.\n\n## Key ideas\n\n- One\n- Two\n"
        )
        self.assertEqual(sections["Summary"], "Short summary.")
        self.assertEqual(sections["Key ideas"], "- One\n- Two")

    def test_promotion_materialization_adds_related_link_and_updates_frontmatter(self) -> None:
        frontmatter = {"type": "source", "tags": ["db"]}
        body = "## Source\n\nSQLite docs"

        updated_frontmatter, updated_body = materialize_source_promotion(
            frontmatter,
            body,
            "SQLite Fundamentals",
            now="2026-04-04",
        )

        self.assertEqual(updated_frontmatter["created"], "2026-04-04")
        self.assertEqual(updated_frontmatter["updated"], "2026-04-04")
        self.assertEqual(updated_frontmatter["promoted_to"], "SQLite Fundamentals")
        self.assertIn("[[SQLite Fundamentals]]", updated_body)
        self.assertIn("## Related notes", updated_body)

        stub_frontmatter, stub_body = materialize_stub_promotion(
            {"status": "stub"},
            "## Core idea\n\nTest",
            now="2026-04-04",
        )
        self.assertEqual(stub_frontmatter["status"], "draft")
        self.assertEqual(stub_frontmatter["type"], "knowledge")
        self.assertEqual(stub_frontmatter["created"], "2026-04-04")
        self.assertEqual(stub_body, "## Core idea\n\nTest")

    def test_promoted_knowledge_body_and_related_link_are_stable(self) -> None:
        body = build_promoted_knowledge_body(
            promoted_title="SQLite Fundamentals",
            source_title="SQLite Source",
            summary="SQLite is an embedded database.",
            key_ideas="- Serverless\n- File-based",
            source_block="Original excerpt",
            original_body="Different original body",
        )

        linked_once = ensure_related_note_link("## Related notes\n", "SQLite Fundamentals")
        linked_twice = ensure_related_note_link(linked_once, "SQLite Fundamentals")

        self.assertIn("# SQLite Fundamentals", body)
        self.assertIn("## Core idea", body)
        self.assertIn("- [[SQLite Source]]", body)
        self.assertIn("## Source context", body)
        self.assertEqual(linked_once, linked_twice)

    def test_inbox_normalization_infers_type_enriches_frontmatter_and_structures_body(self) -> None:
        note_type, frontmatter, body, normalized = normalize_inbox_note(
            {},
            "Artículo útil https://example.com/sqlite",
            improve_structure=True,
        )

        self.assertEqual(note_type, "source")
        self.assertTrue(normalized)
        self.assertEqual(frontmatter["type"], "source")
        self.assertEqual(frontmatter["url"], ["https://example.com/sqlite"])
        self.assertEqual(frontmatter["source_type"], "web")
        self.assertIn("## Source", body)
        self.assertIn("## Summary", body)

    def test_inbox_disposition_covers_none_same_path_and_move(self) -> None:
        source_path = Path("Inbox/note.md")
        moved_path = Path("Knowledge/note.md")

        unresolved = plan_inbox_disposition(
            source_path=source_path,
            destination_path=None,
            note_type="knowledge",
            normalized=True,
        )
        same_path = plan_inbox_disposition(
            source_path=source_path,
            destination_path=source_path,
            note_type="knowledge",
            normalized=False,
        )
        moved = plan_inbox_disposition(
            source_path=source_path,
            destination_path=moved_path,
            note_type="knowledge",
            normalized=True,
        )

        self.assertFalse(unresolved.should_move)
        self.assertTrue(unresolved.left_in_inbox)
        self.assertIn("No unambiguous destination folder.", unresolved.result.reason)

        self.assertFalse(same_path.should_move)
        self.assertTrue(same_path.left_in_inbox)
        self.assertEqual(same_path.result.destination_path, source_path)
        self.assertIn("Already in destination folder.", same_path.result.reason)

        self.assertTrue(moved.should_move)
        self.assertFalse(moved.left_in_inbox)
        self.assertTrue(moved.result.moved)
        self.assertEqual(moved.result.destination_path, moved_path)


if __name__ == "__main__":
    unittest.main()
