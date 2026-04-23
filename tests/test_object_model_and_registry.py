from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from brain_ops.domains.knowledge.object_model import (
    CANONICAL_PREDICATES,
    OBJECT_KINDS,
    SUBTYPES,
    SUBTYPE_SECTIONS,
    SUBTYPE_WRITING_GUIDES,
    ROLE_WRITING_HINTS,
    detect_role,
    get_writing_guide,
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
    extract_base_name,
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
    def test_build_disambiguated_name_uses_spanish_label(self) -> None:
        self.assertEqual(build_disambiguated_name("Mercurio", "deity"), "Mercurio (dios)")
        self.assertEqual(build_disambiguated_name("Mercurio", "celestial_body"), "Mercurio (planeta)")
        self.assertEqual(build_disambiguated_name("Troya", "city"), "Troya (ciudad)")

    def test_build_disambiguated_name_unknown_subtype_passes_through(self) -> None:
        self.assertEqual(build_disambiguated_name("X", "alien"), "X (alien)")

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


class RoleDetectionTestCase(TestCase):
    def test_detect_military_leader(self) -> None:
        self.assertEqual(detect_role("person", "Rey de Macedonia, Faraón de Egipto"), "military_leader")

    def test_detect_philosopher(self) -> None:
        self.assertEqual(detect_role("person", "filósofo griego"), "philosopher")

    def test_detect_scientist(self) -> None:
        self.assertEqual(detect_role("person", "físico y matemático"), "scientist")

    def test_detect_author(self) -> None:
        self.assertEqual(detect_role("person", "poeta y dramaturgo"), "author")

    def test_detect_political_leader(self) -> None:
        self.assertEqual(detect_role("person", "cónsul y dictador de Roma"), "military_leader")

    def test_non_person_returns_none(self) -> None:
        self.assertIsNone(detect_role("deity", "dios del comercio"))

    def test_no_occupation_returns_none(self) -> None:
        self.assertIsNone(detect_role("person", None))

    def test_get_writing_guide_person(self) -> None:
        guide, hints = get_writing_guide("person", "conquistador")
        self.assertIn("Timeline", guide)
        self.assertIn("Campañas", hints)

    def test_get_writing_guide_deity(self) -> None:
        guide, hints = get_writing_guide("deity")
        self.assertIn("Mythology", guide)
        self.assertEqual(hints, "")

    def test_get_writing_guide_unknown_subtype(self) -> None:
        guide, hints = get_writing_guide("unknown_subtype")
        self.assertEqual(guide, "")
        self.assertEqual(hints, "")


class WritingGuideCoverageTestCase(TestCase):
    def test_key_subtypes_have_guides(self) -> None:
        important = ["person", "battle", "war", "empire", "civilization", "book",
                      "deity", "emotion", "discipline", "celestial_body", "city"]
        for subtype in important:
            self.assertIn(subtype, SUBTYPE_WRITING_GUIDES, f"Missing guide for {subtype}")

    def test_all_roles_have_hints(self) -> None:
        roles = ["military_leader", "philosopher", "scientist", "political_leader", "author"]
        for role in roles:
            self.assertIn(role, ROLE_WRITING_HINTS, f"Missing hints for {role}")


class EnrichmentPromptTestCase(TestCase):
    def test_generate_prompt_includes_sections(self) -> None:
        from brain_ops.domains.knowledge.enrichment_llm import build_generate_prompt
        prompt = build_generate_prompt("Test", "person", ("Identity", "Timeline", "Impact"))
        self.assertIn("## Identity", prompt)
        self.assertIn("## Timeline", prompt)
        self.assertIn("## Impact", prompt)

    def test_generate_prompt_includes_writing_guide(self) -> None:
        from brain_ops.domains.knowledge.enrichment_llm import build_generate_prompt
        prompt = build_generate_prompt("Test", "person", ("Identity",), writing_guide="Include campaigns")
        self.assertIn("Include campaigns", prompt)

    def test_generate_prompt_includes_role_hints(self) -> None:
        from brain_ops.domains.knowledge.enrichment_llm import build_generate_prompt
        prompt = build_generate_prompt("Test", "person", ("Identity",), role_hints="Add battles")
        self.assertIn("Add battles", prompt)

    def test_enrich_prompt_includes_subtype(self) -> None:
        from brain_ops.domains.knowledge.enrichment_llm import build_enrich_prompt
        prompt = build_enrich_prompt("content", "new info", subtype="battle")
        self.assertIn("battle", prompt)

    def test_enrich_prompt_includes_guide(self) -> None:
        from brain_ops.domains.knowledge.enrichment_llm import build_enrich_prompt
        prompt = build_enrich_prompt("content", "info", writing_guide="Include terrain")
        self.assertIn("Include terrain", prompt)


class DeduplicateTestCase(TestCase):
    def test_removes_duplicate_across_sections(self) -> None:
        from brain_ops.domains.knowledge.enrichment_llm import deduplicate_note_content
        body = (
            "## Key Facts\n"
            "- Nació en 356 a.C. en Pela, Macedonia\n"
            "- Murió en 323 a.C.\n\n"
            "## Timeline\n"
            "- Nació en 356 a.C. en Pela, Macedonia\n"
            "- **331 a.C.** — Gaugamela\n"
        )
        result = deduplicate_note_content(body)
        # Should appear once in Key Facts, removed from Timeline
        self.assertEqual(result.count("Nació en 356"), 1)
        self.assertIn("Gaugamela", result)

    def test_preserves_short_lines(self) -> None:
        from brain_ops.domains.knowledge.enrichment_llm import deduplicate_note_content
        body = "## Section A\n- short\n\n## Section B\n- short\n"
        result = deduplicate_note_content(body)
        self.assertEqual(result.count("short"), 2)

    def test_preserves_headings(self) -> None:
        from brain_ops.domains.knowledge.enrichment_llm import deduplicate_note_content
        body = "## Identity\nContent here.\n\n## Key Facts\n- Fact 1\n"
        result = deduplicate_note_content(body)
        self.assertIn("## Identity", result)
        self.assertIn("## Key Facts", result)


class ExtractBaseNameTestCase(TestCase):
    def test_strips_disambiguator(self) -> None:
        self.assertEqual(extract_base_name("Mercurio (deity)"), "Mercurio")
        self.assertEqual(extract_base_name("Urano (celestial_body)"), "Urano")

    def test_passthrough_without_disambiguator(self) -> None:
        self.assertEqual(extract_base_name("Alejandro Magno"), "Alejandro Magno")

    def test_handles_whitespace(self) -> None:
        self.assertEqual(extract_base_name("  Marte (deity) "), "Marte")


class RegistryFindCollisionsTestCase(TestCase):
    def test_finds_collisions_by_base_name(self) -> None:
        registry = EntityRegistry()
        e1 = RegisteredEntity(canonical_name="Mercurio (celestial_body)", entity_type="celestial_body", subtype="celestial_body")
        e2 = RegisteredEntity(canonical_name="Mercurio (deity)", entity_type="deity", subtype="deity")
        registry.register(e1)
        registry.register(e2)
        collisions = registry.find_collisions("Mercurio")
        self.assertEqual(len(collisions), 2)

    def test_finds_collision_with_bare_name(self) -> None:
        registry = EntityRegistry()
        e1 = RegisteredEntity(canonical_name="Urano", entity_type="deity", subtype="deity")
        registry.register(e1)
        collisions = registry.find_collisions("Urano")
        self.assertEqual(len(collisions), 1)
        self.assertEqual(collisions[0].canonical_name, "Urano")

    def test_no_collisions_returns_empty(self) -> None:
        registry = EntityRegistry()
        e1 = RegisteredEntity(canonical_name="Jupiter", entity_type="deity", subtype="deity")
        registry.register(e1)
        collisions = registry.find_collisions("Saturn")
        self.assertEqual(len(collisions), 0)


class ResolveWithContextTestCase(TestCase):
    def test_exact_match_returns_directly(self) -> None:
        registry = EntityRegistry()
        e1 = RegisteredEntity(canonical_name="Mercurio (deity)", entity_type="deity", subtype="deity")
        registry.register(e1)
        result = registry.resolve_with_context("Mercurio (deity)")
        self.assertEqual(result, "Mercurio (deity)")

    def test_single_collision_resolves(self) -> None:
        registry = EntityRegistry()
        e1 = RegisteredEntity(canonical_name="Urano", entity_type="deity", subtype="deity")
        registry.register(e1)
        result = registry.resolve_with_context("Urano")
        self.assertEqual(result, "Urano")

    def test_ambiguous_returns_candidates(self) -> None:
        registry = EntityRegistry()
        e1 = RegisteredEntity(canonical_name="Mercurio (celestial_body)", entity_type="celestial_body", subtype="celestial_body")
        e2 = RegisteredEntity(canonical_name="Mercurio (deity)", entity_type="deity", subtype="deity")
        registry.register(e1)
        registry.register(e2)
        result = registry.resolve_with_context("Mercurio")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

    def test_narrows_by_subtype(self) -> None:
        registry = EntityRegistry()
        e1 = RegisteredEntity(canonical_name="Mercurio (celestial_body)", entity_type="celestial_body", subtype="celestial_body")
        e2 = RegisteredEntity(canonical_name="Mercurio (deity)", entity_type="deity", subtype="deity")
        registry.register(e1)
        registry.register(e2)
        result = registry.resolve_with_context("Mercurio", subtype="deity")
        self.assertEqual(result, "Mercurio (deity)")

    def test_narrows_by_domain(self) -> None:
        registry = EntityRegistry()
        e1 = RegisteredEntity(canonical_name="Mercurio (celestial_body)", entity_type="celestial_body", subtype="celestial_body", domains=["astronomía"])
        e2 = RegisteredEntity(canonical_name="Mercurio (deity)", entity_type="deity", subtype="deity", domains=["mitología"])
        registry.register(e1)
        registry.register(e2)
        result = registry.resolve_with_context("Mercurio", domain="mitología")
        self.assertEqual(result, "Mercurio (deity)")

    def test_unknown_name_passes_through(self) -> None:
        registry = EntityRegistry()
        result = registry.resolve_with_context("Desconocido")
        self.assertEqual(result, "Desconocido")


class BaseNameIndexPersistenceTestCase(TestCase):
    def test_base_name_index_rebuilt_on_load(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "registry.json"
            registry = EntityRegistry()
            e1 = RegisteredEntity(canonical_name="Mercurio (deity)", entity_type="deity", subtype="deity")
            e2 = RegisteredEntity(canonical_name="Mercurio (celestial_body)", entity_type="celestial_body", subtype="celestial_body")
            registry.register(e1)
            registry.register(e2)
            save_entity_registry(path, registry)

            loaded = load_entity_registry(path)
            collisions = loaded.find_collisions("Mercurio")
            self.assertEqual(len(collisions), 2)


class DisambiguationPageTestCase(TestCase):
    def test_builds_disambiguation_page(self) -> None:
        from brain_ops.domains.knowledge.entities import build_disambiguation_page

        plan = build_disambiguation_page("Urano", [
            ("Urano (deity)", "deity"),
            ("Urano (celestial_body)", "celestial_body"),
        ])
        self.assertEqual(plan.title, "Urano")
        self.assertEqual(plan.entity_type, "disambiguation")
        self.assertFalse(plan.frontmatter["entity"])
        self.assertIn("[[Urano (deity)]]", plan.body)
        self.assertIn("[[Urano (celestial_body)]]", plan.body)
        self.assertEqual(plan.frontmatter["disambiguates"], ["Urano (deity)", "Urano (celestial_body)"])


class FormatWikilinkTestCase(TestCase):
    def test_no_registry_returns_plain_link(self) -> None:
        from brain_ops.domains.knowledge.link_aliases import format_wikilink
        self.assertEqual(format_wikilink("Urano"), "[[Urano]]")

    def test_alias_resolves_to_disambiguated(self) -> None:
        from brain_ops.domains.knowledge.link_aliases import format_wikilink
        registry = EntityRegistry()
        e = RegisteredEntity(canonical_name="Urano (deity)", entity_type="deity", subtype="deity", aliases=["Urano"])
        registry.register(e)
        result = format_wikilink("Urano", registry)
        self.assertEqual(result, "[[Urano (deity)|Urano]]")

    def test_canonical_disambiguated_shows_base(self) -> None:
        from brain_ops.domains.knowledge.link_aliases import format_wikilink
        registry = EntityRegistry()
        e = RegisteredEntity(canonical_name="Urano (deity)", entity_type="deity", subtype="deity")
        registry.register(e)
        result = format_wikilink("Urano (deity)", registry)
        self.assertEqual(result, "[[Urano (deity)|Urano]]")

    def test_non_disambiguated_entity_plain(self) -> None:
        from brain_ops.domains.knowledge.link_aliases import format_wikilink
        registry = EntityRegistry()
        e = RegisteredEntity(canonical_name="Alejandro Magno", entity_type="person", subtype="person")
        registry.register(e)
        result = format_wikilink("Alejandro Magno", registry)
        self.assertEqual(result, "[[Alejandro Magno]]")

    def test_unknown_entity_returns_plain(self) -> None:
        from brain_ops.domains.knowledge.link_aliases import format_wikilink
        registry = EntityRegistry()
        result = format_wikilink("Desconocido", registry)
        self.assertEqual(result, "[[Desconocido]]")

    def test_bare_name_collision_keeps_disambiguator_visible(self) -> None:
        """Regression: when the bare name is ALSO a canonical entity, the
        aliased form `[[X (Y)|X]]` is semantically misleading — a reader
        sees `[[X]]` display and expects the bare-name entity. Keep the
        disambiguator visible in this case.

        Real-world bug: `[[Ética (Spinoza)|Ética]]` was auto-generated in
        hundreds of notes where the prose actually meant the discipline
        (canonical `Ética`), not Spinoza's book. Fix: when both exist, use
        `[[Ética (Spinoza)]]` instead of `[[Ética (Spinoza)|Ética]]`.
        """
        from brain_ops.domains.knowledge.link_aliases import format_wikilink
        registry = EntityRegistry()
        # Bare-name canonical (e.g. the discipline "Ética")
        bare = RegisteredEntity(canonical_name="Ética", entity_type="concept", subtype="discipline")
        registry.register(bare)
        # Disambiguated canonical (e.g. Spinoza's book)
        book = RegisteredEntity(canonical_name="Ética (Spinoza)", entity_type="book", subtype="book")
        registry.register(book)

        # Formatting the disambiguated entity must NOT display as plain "Ética".
        result = format_wikilink("Ética (Spinoza)", registry)
        self.assertEqual(result, "[[Ética (Spinoza)]]")

    def test_bare_name_no_collision_uses_display_alias(self) -> None:
        """Baseline: when there is no bare-name collision, keep the friendly
        `[[X (Y)|X]]` form (this is the Urano case that already worked)."""
        from brain_ops.domains.knowledge.link_aliases import format_wikilink
        registry = EntityRegistry()
        e = RegisteredEntity(canonical_name="Urano (deity)", entity_type="deity", subtype="deity")
        registry.register(e)
        # "Urano" alone is NOT registered as a separate canonical entity.
        result = format_wikilink("Urano (deity)", registry)
        self.assertEqual(result, "[[Urano (deity)|Urano]]")

    def test_bare_name_collision_via_alias_also_guarded(self) -> None:
        """Same guard applies when the input is an alias that resolves to
        a disambiguated entity, while a bare-name canonical also exists."""
        from brain_ops.domains.knowledge.link_aliases import format_wikilink
        registry = EntityRegistry()
        bare = RegisteredEntity(canonical_name="Metafísica", entity_type="concept", subtype="discipline")
        registry.register(bare)
        book = RegisteredEntity(
            canonical_name="Metafísica (Aristóteles)",
            entity_type="book",
            subtype="book",
            aliases=["Metafísica de Aristóteles"],
        )
        registry.register(book)
        # The alias resolves to the disambiguated entity, but bare-name collides.
        result = format_wikilink("Metafísica de Aristóteles", registry)
        self.assertEqual(result, "[[Metafísica (Aristóteles)]]")


class ResolveEntityNameTestCase(TestCase):
    def test_resolves_alias_to_canonical(self) -> None:
        from brain_ops.domains.knowledge.link_aliases import resolve_entity_name
        registry = EntityRegistry()
        e = RegisteredEntity(canonical_name="Urano (deity)", entity_type="deity", aliases=["Urano"])
        registry.register(e)
        self.assertEqual(resolve_entity_name("Urano", registry), "Urano (deity)")

    def test_no_registry_passes_through(self) -> None:
        from brain_ops.domains.knowledge.link_aliases import resolve_entity_name
        self.assertEqual(resolve_entity_name("Urano"), "Urano")


class CrossEnrichDisambiguationTestCase(TestCase):
    def test_apply_cross_enrichment_uses_disambiguated_link(self) -> None:
        from brain_ops.domains.knowledge.cross_enrichment import (
            CrossEnrichmentCandidate,
            apply_cross_enrichment,
        )
        registry = EntityRegistry()
        e = RegisteredEntity(canonical_name="Urano (deity)", entity_type="deity", subtype="deity", aliases=["Urano"])
        registry.register(e)

        body = "## Key Facts\n- fact 1\n\n## Timeline\n"
        candidate = CrossEnrichmentCandidate(
            source_entity="Urano (deity)",
            target_entity="Cronos",
            content_type="fact",
            text="Cronos castró a Urano",
            target_section="Key Facts",
            confidence=0.8,
            review_level="auto",
        )
        new_body, applied = apply_cross_enrichment(body, [candidate], registry=registry)
        self.assertEqual(len(applied), 1)
        self.assertIn("[[Urano (deity)|Urano]]", new_body)
        self.assertNotIn("[[Urano (deity)]])*", new_body)


if __name__ == "__main__":
    import unittest

    unittest.main()
