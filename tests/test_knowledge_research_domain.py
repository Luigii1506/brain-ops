from __future__ import annotations

import unittest

from brain_ops.domains.knowledge.research import (
    RESEARCH_END,
    RESEARCH_START,
    materialize_research_document,
    merge_research_block,
    render_research_block,
    research_query_candidates,
    research_search_results,
    research_summary_text,
)
from brain_ops.models import ResearchSource


class KnowledgeResearchDomainTestCase(unittest.TestCase):
    def test_render_research_block_renders_sources_and_findings(self) -> None:
        block = render_research_block(
            "sqlite retries",
            [
                ResearchSource(
                    title="SQLite",
                    url="https://example.com/sqlite",
                    summary="Embedded relational database.",
                ),
                ResearchSource(
                    title="Retry Patterns",
                    url="https://example.com/retries",
                    summary="Idempotent retries reduce duplicate side effects.",
                ),
            ],
        )

        self.assertTrue(block.startswith(RESEARCH_START))
        self.assertIn("Query: `sqlite retries`", block)
        self.assertIn("- [SQLite](https://example.com/sqlite)", block)
        self.assertIn("#### Retry Patterns", block)
        self.assertTrue(block.endswith(RESEARCH_END))

    def test_render_and_merge_research_block_handle_empty_and_replace_cases(self) -> None:
        empty_block = render_research_block("topic", [])
        merged_empty = merge_research_block("", empty_block)
        original = "## Notes\n\nBody\n\n" + empty_block
        replacement = render_research_block(
            "new topic",
            [ResearchSource(title="Doc", url="https://example.com/doc", summary="New summary.")],
        )
        merged_replaced = merge_research_block(original, replacement)

        self.assertEqual(merged_empty, empty_block)
        self.assertIn("No external sources found.", empty_block)
        self.assertIn("No grounded findings were retrieved.", empty_block)
        self.assertIn("## Notes", merged_replaced)
        self.assertIn("Query: `new topic`", merged_replaced)
        self.assertNotIn("Query: `topic`", merged_replaced)

    def test_materialize_research_document_sets_defaults_and_merges_block(self) -> None:
        research_block = render_research_block("sqlite", [])
        frontmatter, body = materialize_research_document(
            {},
            "## Existing\n\nBody",
            research_block,
            now="2026-04-04",
        )

        self.assertEqual(frontmatter["created"], "2026-04-04")
        self.assertEqual(frontmatter["updated"], "2026-04-04")
        self.assertEqual(frontmatter["tags"], [])
        self.assertIn("## Existing", body)
        self.assertIn(RESEARCH_START, body)

    def test_research_query_candidates_and_payload_normalizers_are_resilient(self) -> None:
        candidates = research_query_candidates(
            "distributed retry idempot pattern",
            "SQLite retries",
        )
        results = research_search_results(
            [
                "ignored",
                [" SQLite ", "", 3, "Retry Guide"],
                "ignored",
                [" https://example.com/sqlite ", " ", None, "https://example.com/retry"],
            ]
        )
        summary = research_summary_text({"extract": "  useful summary  "})
        missing_summary = research_summary_text({"no_extract": "x"})

        self.assertEqual(candidates[:2], ["distributed retry idempot pattern", "SQLite retries"])
        self.assertIn("idempotence", candidates)
        self.assertIn("retry", candidates)
        self.assertIn("distributed computing", candidates)
        self.assertEqual(
            results,
            [
                ("SQLite", "https://example.com/sqlite"),
                ("Retry Guide", "https://example.com/retry"),
            ],
        )
        self.assertEqual(summary, "useful summary")
        self.assertEqual(missing_summary, "")


if __name__ == "__main__":
    unittest.main()
