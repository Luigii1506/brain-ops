"""Tests for search, preferences, chunking, evidence, and registry lint."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from brain_ops.domains.knowledge.search import SearchResult, search_notes
from brain_ops.domains.knowledge.preferences import UserPreferences, load_user_preferences, save_user_preferences
from brain_ops.domains.knowledge.chunking import chunk_by_headings, rank_chunks_for_subtype, build_prioritized_context
from brain_ops.domains.knowledge.evidence import (
    confidence_for_source,
    is_strong_for,
    is_weak_for,
    lint_extraction,
    tag_evidence_strength,
    should_enrich_canonical,
)
from brain_ops.domains.knowledge.registry import EntityRegistry, RegisteredEntity
from brain_ops.domains.knowledge.registry_lint import lint_registry


class SearchNotesTestCase(TestCase):
    def test_search_by_title(self) -> None:
        notes = [
            ("a.md", {"entity": True, "type": "person", "name": "Alejandro"}, "content"),
            ("b.md", {"entity": True, "type": "place", "name": "Grecia"}, "content"),
        ]
        results = search_notes(notes, "Alejandro")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Alejandro")

    def test_search_by_body_content(self) -> None:
        notes = [("a.md", {"name": "Test"}, "This mentions Macedonia and battles")]
        results = search_notes(notes, "Macedonia")
        self.assertEqual(len(results), 1)

    def test_search_entity_only(self) -> None:
        notes = [
            ("a.md", {"entity": True, "type": "person", "name": "A"}, "x"),
            ("b.md", {"type": "source", "name": "B"}, "x A x"),
        ]
        results = search_notes(notes, "x", entity_only=True)
        self.assertEqual(len(results), 1)

    def test_search_respects_max_results(self) -> None:
        notes = [(f"{i}.md", {"name": f"N{i}"}, "match") for i in range(10)]
        results = search_notes(notes, "match", max_results=3)
        self.assertEqual(len(results), 3)


class PreferencesTestCase(TestCase):
    def test_default_preferences(self) -> None:
        prefs = UserPreferences()
        self.assertEqual(prefs.language, "spanish")
        self.assertIn("history", prefs.interests)

    def test_save_and_load_roundtrip(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "prefs.json"
            prefs = UserPreferences(language="english", interests=["math"])
            save_user_preferences(path, prefs)
            loaded = load_user_preferences(path)
            self.assertEqual(loaded.language, "english")
            self.assertEqual(loaded.interests, ["math"])

    def test_to_prompt_context(self) -> None:
        prefs = UserPreferences()
        ctx = prefs.to_prompt_context()
        self.assertIn("spanish", ctx)
        self.assertIn("history", ctx)


class ChunkingTestCase(TestCase):
    def test_chunk_by_headings(self) -> None:
        text = "Intro text\n## Section A\nContent A\n## Section B\nContent B"
        chunks = chunk_by_headings(text)
        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[0].heading, "Introduction")
        self.assertEqual(chunks[1].heading, "Section A")

    def test_rank_chunks_for_person(self) -> None:
        text = "Intro\n## Geography\nGeo content\n## Biography\nBio content long enough to matter here"
        chunks = chunk_by_headings(text)
        ranked = rank_chunks_for_subtype(chunks, "person", max_chars=10000)
        headings = [c.heading for c in ranked]
        # Biography should rank higher for person
        self.assertIn("Biography", headings)

    def test_build_prioritized_context(self) -> None:
        text = "Intro text here\n## Death\nDied in 323\n## Birth\nBorn in 356"
        ctx = build_prioritized_context(text, "person", max_chars=10000)
        self.assertIn("Intro text", ctx)
        self.assertIn("323", ctx)


class EvidenceTestCase(TestCase):
    def test_confidence_scores(self) -> None:
        self.assertGreater(confidence_for_source("encyclopedia"), confidence_for_source("thread"))
        self.assertGreater(confidence_for_source("research_paper"), confidence_for_source("news"))

    def test_evidence_strength_tags(self) -> None:
        self.assertEqual(tag_evidence_strength("encyclopedia"), "strong")
        self.assertEqual(tag_evidence_strength("article"), "moderate")
        self.assertEqual(tag_evidence_strength("thread"), "weak")

    def test_strong_and_weak_for(self) -> None:
        self.assertTrue(is_strong_for("encyclopedia", "facts"))
        self.assertTrue(is_weak_for("thread", "canonical_facts"))

    def test_should_enrich_canonical(self) -> None:
        self.assertTrue(should_enrich_canonical("encyclopedia"))
        self.assertFalse(should_enrich_canonical("thread"))

    def test_lint_extraction_encyclopedia(self) -> None:
        good = {"title": "T", "tldr": "X", "summary": "S", "entities": [{"name": "A"}, {"name": "B"}], "core_facts": ["f1", "f2", "f3"], "relationships": [{"s": "a"}]}
        result = lint_extraction("encyclopedia", good)
        self.assertTrue(result.passed)

    def test_lint_extraction_missing_fields(self) -> None:
        bad = {"title": "", "tldr": "", "summary": ""}
        result = lint_extraction("encyclopedia", bad)
        self.assertFalse(result.passed)
        self.assertGreater(len(result.issues), 0)


class RegistryLintTestCase(TestCase):
    def test_lint_detects_issues(self) -> None:
        registry = EntityRegistry()
        registry.register(RegisteredEntity(
            canonical_name="Test", entity_type="person",
            source_count=3, relation_count=0, status="mention",
        ))
        result = lint_registry(registry)
        self.assertEqual(result.total_entities, 1)
        self.assertIn("Test", result.no_relations)
        self.assertIn("Test", result.promotable_to_candidate)

    def test_lint_clean_registry(self) -> None:
        registry = EntityRegistry()
        registry.register(RegisteredEntity(
            canonical_name="Good", entity_type="person",
            source_count=5, relation_count=5, status="canonical",
            confidence="high", object_kind="entity", subtype="person",
        ))
        result = lint_registry(registry)
        self.assertEqual(result.total_issues, 0)


if __name__ == "__main__":
    import unittest

    unittest.main()
