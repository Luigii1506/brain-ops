from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from brain_ops.domains.knowledge.object_model import (
    CANONICAL_PREDICATES,
    OBJECT_KINDS,
    SUBTYPES,
    SUBTYPE_SECTIONS,
    normalize_predicate,
    resolve_object_kind,
    sections_for_subtype,
    should_promote_to_candidate,
    should_promote_to_canonical,
    build_disambiguated_name,
    needs_disambiguation,
)
from brain_ops.domains.knowledge.registry import (
    EntityRegistry,
    RegisteredEntity,
    learn_from_ingest,
    load_entity_registry,
    save_entity_registry,
)
from brain_ops.domains.knowledge.extraction_store import (
    save_extraction_record,
    load_extraction_records,
)


class NormalizePredicateTestCase(TestCase):
    def test_canonical_predicate_passes_through(self) -> None:
        self.assertEqual(normalize_predicate("parent_of"), "parent_of")
        self.assertEqual(normalize_predicate("born_in"), "born_in")

    def test_spanish_predicate_normalizes(self) -> None:
        self.assertEqual(normalize_predicate("padre de"), "parent_of")
        self.assertEqual(normalize_predicate("hijo de"), "child_of")
        self.assertEqual(normalize_predicate("maestro de"), "mentor_of")
        self.assertEqual(normalize_predicate("alumno de"), "studied_under")
        self.assertEqual(normalize_predicate("conquistó"), "conquered")
        self.assertEqual(normalize_predicate("nació en"), "born_in")

    def test_english_predicate_normalizes(self) -> None:
        self.assertEqual(normalize_predicate("student of"), "studied_under")
        self.assertEqual(normalize_predicate("father of"), "parent_of")
        self.assertEqual(normalize_predicate("wrote"), "wrote")  # "wrote" is itself canonical

    def test_unknown_predicate_defaults_to_related_to(self) -> None:
        self.assertEqual(normalize_predicate("some weird relation"), "related_to")

    def test_partial_match_works(self) -> None:
        self.assertEqual(normalize_predicate("was the father of"), "parent_of")


class SectionsForSubtypeTestCase(TestCase):
    def test_person_has_timeline_and_impact(self) -> None:
        sections = sections_for_subtype("person")
        self.assertIn("Timeline", sections)
        self.assertIn("Impact", sections)
        self.assertIn("Strategic Insights", sections)

    def test_planet_has_orbit_and_atmosphere(self) -> None:
        sections = sections_for_subtype("celestial_body")
        self.assertIn("Orbit & Position", sections)
        self.assertIn("Atmosphere & Composition", sections)

    def test_book_has_themes_and_quotes(self) -> None:
        sections = sections_for_subtype("book")
        self.assertIn("Themes", sections)
        self.assertIn("Core Ideas", sections)

    def test_emotion_has_psychological_perspectives(self) -> None:
        sections = sections_for_subtype("emotion")
        self.assertIn("Psychological Perspectives", sections)

    def test_country_has_geography_and_government(self) -> None:
        sections = sections_for_subtype("country")
        self.assertIn("Geography", sections)
        self.assertIn("Government", sections)

    def test_unknown_subtype_returns_default(self) -> None:
        sections = sections_for_subtype("unknown_thing")
        self.assertIn("Identity", sections)
        self.assertIn("Key Facts", sections)

    def test_all_subtypes_have_related_notes(self) -> None:
        for subtype, sections in SUBTYPE_SECTIONS.items():
            self.assertIn("Related notes", sections, f"{subtype} missing Related notes")


class ResolveObjectKindTestCase(TestCase):
    def test_legacy_person_resolves(self) -> None:
        self.assertEqual(resolve_object_kind("person"), ("entity", "person"))

    def test_legacy_book_resolves(self) -> None:
        self.assertEqual(resolve_object_kind("book"), ("work", "book"))

    def test_legacy_war_resolves(self) -> None:
        self.assertEqual(resolve_object_kind("war"), ("event", "war"))

    def test_known_subtype_resolves(self) -> None:
        self.assertEqual(resolve_object_kind("celestial_body"), ("entity", "celestial_body"))
        self.assertEqual(resolve_object_kind("emotion"), ("concept", "emotion"))
        self.assertEqual(resolve_object_kind("revolution"), ("event", "revolution"))

    def test_unknown_defaults_to_entity(self) -> None:
        kind, subtype = resolve_object_kind("alien_species")
        self.assertEqual(kind, "entity")


class PromotionRulesTestCase(TestCase):
    def test_high_importance_promotes_to_candidate(self) -> None:
        self.assertTrue(should_promote_to_candidate(1, 0, "high"))

    def test_multiple_sources_promotes_to_candidate(self) -> None:
        self.assertTrue(should_promote_to_candidate(2, 0, "medium"))

    def test_single_low_source_stays_mention(self) -> None:
        self.assertFalse(should_promote_to_candidate(1, 0, "medium"))

    def test_dedicated_note_promotes_to_canonical(self) -> None:
        self.assertTrue(should_promote_to_canonical(1, 0, has_dedicated_note=True))

    def test_enough_sources_and_relations_promotes(self) -> None:
        self.assertTrue(should_promote_to_canonical(3, 2, has_dedicated_note=False))


class DisambiguationTestCase(TestCase):
    def test_build_disambiguated_name(self) -> None:
        self.assertEqual(build_disambiguated_name("Mercurio", "planet"), "Mercurio (planet)")

    def test_needs_disambiguation(self) -> None:
        self.assertTrue(needs_disambiguation("Mercurio", ["planet", "deity"]))
        self.assertFalse(needs_disambiguation("Alejandro Magno", ["person"]))


class EntityRegistryTestCase(TestCase):
    def test_register_and_resolve(self) -> None:
        registry = EntityRegistry()
        entity = RegisteredEntity(canonical_name="Alejandro Magno", entity_type="person")
        registry.register(entity)
        self.assertEqual(registry.resolve("Alejandro Magno"), "Alejandro Magno")

    def test_alias_resolution(self) -> None:
        registry = EntityRegistry()
        entity = RegisteredEntity(canonical_name="Alejandro Magno", entity_type="person", aliases=["Alexander the Great"])
        registry.register(entity)
        self.assertEqual(registry.resolve("Alexander the Great"), "Alejandro Magno")

    def test_learn_from_ingest_creates_and_promotes(self) -> None:
        registry = EntityRegistry()
        entities = [
            {"name": "Alejandro Magno", "type": "person", "importance": "high"},
            {"name": "Aristóteles", "type": "person", "importance": "medium"},
        ]
        rels = [
            {"subject": "Alejandro Magno", "predicate": "studied_under", "object": "Aristóteles"},
        ]
        new = learn_from_ingest(registry, entities_mentioned=entities, relationships=rels)
        self.assertEqual(len(new), 2)
        ale = registry.get("Alejandro Magno")
        self.assertIsNotNone(ale)
        self.assertEqual(ale.status, "candidate")
        self.assertEqual(ale.object_kind, "entity")
        self.assertEqual(ale.subtype, "person")

    def test_learn_from_ingest_increments_on_repeat(self) -> None:
        registry = EntityRegistry()
        entities = [{"name": "Test", "type": "person", "importance": "medium"}]
        learn_from_ingest(registry, entities_mentioned=entities, relationships=[])
        learn_from_ingest(registry, entities_mentioned=entities, relationships=[])
        learn_from_ingest(registry, entities_mentioned=entities, relationships=[])
        entity = registry.get("Test")
        self.assertEqual(entity.source_count, 3)
        self.assertIn(entity.status, ("candidate", "canonical"))

    def test_save_and_load_roundtrip(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "registry.json"
            registry = EntityRegistry()
            entity = RegisteredEntity(
                canonical_name="Test", entity_type="person",
                status="canonical", object_kind="entity", subtype="person",
            )
            registry.register(entity)
            save_entity_registry(path, registry)

            loaded = load_entity_registry(path)
            restored = loaded.get("Test")
            self.assertIsNotNone(restored)
            self.assertEqual(restored.status, "canonical")
            self.assertEqual(restored.object_kind, "entity")


class ExtractionStoreTestCase(TestCase):
    def test_save_and_load_roundtrip(self) -> None:
        with TemporaryDirectory() as temp_dir:
            extractions_dir = Path(temp_dir) / "extractions"
            save_extraction_record(
                extractions_dir,
                source_title="Test Article",
                source_url="https://example.com",
                source_type="article",
                raw_llm_json={"title": "Test", "core_facts": ["fact 1"]},
            )
            records = load_extraction_records(extractions_dir)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].source_title, "Test Article")
            self.assertEqual(records[0].raw_llm_json["core_facts"], ["fact 1"])

    def test_load_from_empty_dir_returns_empty(self) -> None:
        records = load_extraction_records(Path("/tmp/nonexistent_12345"))
        self.assertEqual(records, [])


if __name__ == "__main__":
    import unittest

    unittest.main()
