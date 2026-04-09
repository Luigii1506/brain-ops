"""Tests for search, preferences, chunking, evidence, and registry lint."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from brain_ops.domains.knowledge.search import SearchResult, search_notes
from brain_ops.domains.knowledge.preferences import UserPreferences, load_user_preferences, save_user_preferences
from brain_ops.domains.knowledge.chunking import chunk_by_headings, rank_chunks_for_subtype, build_prioritized_context
from brain_ops.domains.knowledge.coverage_check import check_coverage
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
    def test_chunk_by_headings_markdown(self) -> None:
        content_a = "Content A is here. " * 10
        content_b = "Content B is here. " * 10
        text = f"Intro text long enough.\n## Section A\n{content_a}\n## Section B\n{content_b}"
        chunks = chunk_by_headings(text)
        self.assertGreaterEqual(len(chunks), 2)

    def test_chunk_by_headings_wiki_pattern(self) -> None:
        text = "Intro paragraph with enough content here.\n" * 5 + "\nNacimiento e infancia\n[\neditar\n]\nContent about birth here with enough text to matter.\n" * 3
        chunks = chunk_by_headings(text)
        headings = [c.heading for c in chunks]
        self.assertIn("Nacimiento e infancia", headings)

    def test_chunk_by_headings_wiki_extract_section(self) -> None:
        intro = "Intro paragraph with enough content here.\n" * 12
        text = (
            intro
            + "Debate Bohr-Einstein\n"
            + "Esta sección es un extracto de\n"
            + "Debate Bohr-Einstein\n"
            + ".\n[\neditar\n]\n"
            + "Los debates Bohr-Einstein fueron una serie de disputas públicas sobre la mecánica cuántica.\n"
            + "Einstein cuestionó la interpretación probabilística y Bohr la defendió.\n"
        )
        chunks = chunk_by_headings(text)
        headings = [c.heading for c in chunks]
        self.assertIn("Debate Bohr-Einstein", headings)

    def test_chunk_by_headings_does_not_promote_plain_name_to_heading(self) -> None:
        text = (
            "Intro paragraph with enough content here.\n" * 12
            + "Niels Bohr\n"
            + "con Albert Einstein en casa de Paul Ehrenfest en Leiden.\n"
            + "Más contexto de la foto y del debate físico.\n"
        )
        chunks = chunk_by_headings(text)
        headings = [c.heading for c in chunks]
        self.assertNotIn("Niels Bohr", headings)

    def test_rank_chunks_for_person(self) -> None:
        text = "## Geography\nGeo content long enough to matter for ranking test purposes.\n## Biography\nBio content long enough to matter here for the ranking test."
        chunks = chunk_by_headings(text)
        if len(chunks) >= 2:
            ranked = rank_chunks_for_subtype(chunks, "person", max_chars=10000)
            self.assertGreater(len(ranked), 0)

    def test_build_prioritized_context(self) -> None:
        death_content = "Died in 323 BC in Babylon after a fever. " * 5
        birth_content = "Born in 356 BC in Pela Macedonia. " * 5
        text = f"## Death\n{death_content}\n## Birth\n{birth_content}"
        ctx = build_prioritized_context(text, "person", max_chars=10000)
        self.assertIn("323", ctx)

    def test_check_coverage_uses_provided_raw_chunks(self) -> None:
        raw_text = "Texto plano poco útil"
        note_body = "La nota no cubre el debate."
        raw_chunks = [
            chunk_by_headings(
                "## Debate Bohr-Einstein\nEinstein discutió con Bohr sobre la completitud de la mecánica cuántica. "
                * 5
            )[0]
        ]
        report = check_coverage(
            "Albert Einstein",
            "person",
            raw_text,
            note_body,
            raw_chunks=raw_chunks,
        )
        self.assertEqual(report.raw_headings, 1)
        self.assertEqual(report.gaps[0].heading, "Debate Bohr-Einstein")

    def test_check_coverage_uses_heading_signal_for_section_match(self) -> None:
        raw_chunks = [
            chunk_by_headings(
                "## Relatividad especial\nEl artículo desarrolla la invariancia de la velocidad de la luz."
                * 4
            )[0]
        ]
        note_body = "La nota explica la relatividad especial y su papel en la física moderna."
        report = check_coverage(
            "Albert Einstein",
            "person",
            "texto",
            note_body,
            raw_chunks=raw_chunks,
        )
        self.assertEqual(report.covered_headings, 1)
        self.assertFalse(report.gaps)


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
