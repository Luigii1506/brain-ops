from __future__ import annotations

import unittest
from collections import Counter
from pathlib import Path

from brain_ops.domains.knowledge.linking import (
    build_note_terms,
    existing_wikilinks,
    insert_links,
    materialize_linked_document,
    score_terms,
    suggest_link_candidate,
    tokenize,
)


class KnowledgeLinkingDomainTestCase(unittest.TestCase):
    def test_insert_links_reuses_links_section_and_avoids_duplicates(self) -> None:
        body = "## Core idea\n\nSQLite is embedded.\n\n## Links\n\n- [[Existing Note]]"
        updated = insert_links(body, ["Existing Note", "Retry Patterns"])

        self.assertIn("- [[Existing Note]]", updated)
        self.assertIn("- [[Retry Patterns]]", updated)
        self.assertEqual(updated.count("[[Existing Note]]"), 1)

    def test_insert_links_appends_links_section_when_missing(self) -> None:
        body = "## Core idea\n\nSQLite is embedded."
        updated = insert_links(body, ["SQLite Fundamentals"])

        self.assertIn("## Links", updated)
        self.assertTrue(updated.endswith("- [[SQLite Fundamentals]]"))

    def test_materialize_linked_document_sets_defaults_and_updates_body(self) -> None:
        frontmatter, body = materialize_linked_document(
            {},
            "## Core idea\n\nSQLite is embedded.",
            ["SQLite Fundamentals"],
            now="2026-04-04",
        )

        self.assertEqual(frontmatter["created"], "2026-04-04")
        self.assertEqual(frontmatter["updated"], "2026-04-04")
        self.assertEqual(frontmatter["tags"], [])
        self.assertIn("[[SQLite Fundamentals]]", body)

    def test_tokenize_and_build_note_terms_ignore_stopwords_urls_and_research_block(self) -> None:
        terms = tokenize("The retry logic for SQLite and distributed systems")
        built = build_note_terms(
            "SQLite Retry Guide",
            {"aliases": ["Idempotent retries"]},
            "## Core idea\n\nSee https://example.com\n\n<!-- brain-ops:research:start -->ignored<!-- brain-ops:research:end -->\nDistributed retry logic.",
        )

        self.assertIn("sqlite", terms)
        self.assertIn("retry", terms)
        self.assertNotIn("the", terms)
        self.assertIn("idempotent", built)
        self.assertIn("distributed", built)
        self.assertNotIn("https", built)
        self.assertNotIn("research", built)

    def test_score_terms_and_candidate_suggestion_require_meaningful_overlap(self) -> None:
        target_terms = Counter({"sqlite": 2, "retry": 2, "idempotent": 1})
        candidate_terms = Counter({"sqlite": 1, "retry": 2, "patterns": 1})
        score, reason = score_terms(
            target_terms,
            candidate_terms,
            "Retry Patterns",
            "This note references Retry Patterns in passing.",
        )

        suggestion = suggest_link_candidate(
            path=Path("Knowledge/Retry Patterns.md"),
            candidate_name="Retry Patterns",
            candidate_frontmatter={"aliases": ["Retries"]},
            candidate_body="Retry patterns for SQLite systems.",
            target_terms=target_terms,
            existing_links=existing_wikilinks("Already linked to [[Existing]]."),
            target_body="This note references Retry Patterns in passing.",
        )
        duplicate = suggest_link_candidate(
            path=Path("Knowledge/Retry Patterns.md"),
            candidate_name="Retry Patterns",
            candidate_frontmatter={},
            candidate_body="Retry patterns for SQLite systems.",
            target_terms=target_terms,
            existing_links={"Retry Patterns"},
            target_body="This note references Retry Patterns in passing.",
        )

        self.assertGreater(score, 0)
        self.assertIn("shared terms:", reason)
        self.assertIn("candidate title appears in note body", reason)
        self.assertIsNotNone(suggestion)
        assert suggestion is not None
        self.assertEqual(suggestion.path, Path("Knowledge/Retry Patterns.md"))
        self.assertGreater(suggestion.score, 0)
        self.assertIn("shared terms:", suggestion.reason)
        self.assertIsNone(duplicate)


if __name__ == "__main__":
    unittest.main()
