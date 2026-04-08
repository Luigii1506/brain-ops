from __future__ import annotations

from unittest import TestCase

from brain_ops.domains.knowledge.entities import (
    ENTITY_SCHEMAS,
    ENTITY_TYPES,
    EntityPlan,
    build_entity_body,
    build_entity_frontmatter,
    extract_entity_relations,
    is_entity_note,
    plan_entity_note,
    validate_entity_type,
)
from brain_ops.domains.knowledge.index import (
    EntityIndexEntry,
    build_entity_index_entry,
    group_index_entries_by_type,
    render_entity_index_markdown,
)
from brain_ops.domains.knowledge.relations import (
    EntityRelation,
    build_relation_adjacency,
    extract_relations_from_note,
    find_entity_connections,
    render_entity_relations_markdown,
)


class EntityTypeRegistryTestCase(TestCase):
    def test_entity_types_contains_core_types(self) -> None:
        for expected in ("person", "event", "place", "concept", "book", "author", "war", "era", "organization", "topic"):
            self.assertIn(expected, ENTITY_TYPES)

    def test_entity_schemas_exist_for_all_types(self) -> None:
        for entity_type in ENTITY_TYPES:
            self.assertIn(entity_type, ENTITY_SCHEMAS)

    def test_every_schema_has_name_as_required_field(self) -> None:
        for entity_type, schema in ENTITY_SCHEMAS.items():
            self.assertIn("name", schema.required_fields, f"{entity_type} schema missing name")

    def test_every_schema_has_sections(self) -> None:
        for entity_type, schema in ENTITY_SCHEMAS.items():
            self.assertTrue(len(schema.sections) > 0, f"{entity_type} schema has no sections")

    def test_every_schema_has_related_as_optional(self) -> None:
        for entity_type, schema in ENTITY_SCHEMAS.items():
            self.assertIn("related", schema.optional_fields, f"{entity_type} missing related field")


class ValidateEntityTypeTestCase(TestCase):
    def test_valid_type_returns_normalized(self) -> None:
        self.assertEqual(validate_entity_type("Person"), "person")
        self.assertEqual(validate_entity_type("  EVENT  "), "event")

    def test_invalid_type_raises_value_error(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            validate_entity_type("spaceship")
        self.assertIn("spaceship", str(ctx.exception))
        self.assertIn("person", str(ctx.exception))


class BuildEntityFrontmatterTestCase(TestCase):
    def test_person_frontmatter_includes_type_name_and_entity_flag(self) -> None:
        fm = build_entity_frontmatter("person", "Alejandro Magno")
        self.assertEqual(fm["type"], "person")
        self.assertEqual(fm["name"], "Alejandro Magno")
        self.assertIs(fm["entity"], True)

    def test_person_frontmatter_includes_optional_fields_as_none(self) -> None:
        fm = build_entity_frontmatter("person", "Aristóteles")
        self.assertIn("born", fm)
        self.assertIn("nationality", fm)
        self.assertIn("related", fm)
        self.assertIsNone(fm["born"])

    def test_extra_frontmatter_overrides_defaults(self) -> None:
        fm = build_entity_frontmatter("person", "Napoleón", extra={"born": "1769", "nationality": "Francia"})
        self.assertEqual(fm["born"], "1769")
        self.assertEqual(fm["nationality"], "Francia")

    def test_place_frontmatter_includes_place_specific_fields(self) -> None:
        fm = build_entity_frontmatter("place", "Grecia")
        self.assertIn("capital", fm)
        self.assertIn("continent", fm)
        self.assertIn("population", fm)


class BuildEntityBodyTestCase(TestCase):
    def test_person_body_has_expected_sections(self) -> None:
        body = build_entity_body("person", "Alejandro Magno")
        self.assertIn("## Identity", body)
        self.assertIn("## Key Facts", body)
        self.assertIn("## Timeline", body)
        self.assertIn("## Relationships", body)
        self.assertIn("## Related notes", body)

    def test_event_body_has_expected_sections(self) -> None:
        body = build_entity_body("event", "Batalla de Gaugamela")
        self.assertIn("## Identity", body)
        self.assertIn("## Key Facts", body)
        self.assertIn("## Impact", body)

    def test_place_body_has_expected_sections(self) -> None:
        body = build_entity_body("place", "Grecia")
        self.assertIn("## Identity", body)
        self.assertIn("## Key Facts", body)
        self.assertIn("## Strategic Insights", body)

    def test_unknown_type_returns_default_sections(self) -> None:
        body = build_entity_body("unknown_type", "Test")
        self.assertIn("## Identity", body)
        self.assertIn("## Key Facts", body)


class PlanEntityNoteTestCase(TestCase):
    def test_plan_returns_complete_entity_plan(self) -> None:
        plan = plan_entity_note("Alejandro Magno", entity_type="person")
        self.assertIsInstance(plan, EntityPlan)
        self.assertEqual(plan.title, "Alejandro Magno")
        self.assertEqual(plan.entity_type, "person")
        self.assertEqual(plan.frontmatter["type"], "person")
        self.assertEqual(plan.frontmatter["name"], "Alejandro Magno")
        self.assertIs(plan.frontmatter["entity"], True)
        self.assertIn("## Identity", plan.body)

    def test_plan_normalizes_entity_type(self) -> None:
        plan = plan_entity_note("Grecia", entity_type="PLACE")
        self.assertEqual(plan.entity_type, "place")

    def test_plan_strips_whitespace_from_name(self) -> None:
        plan = plan_entity_note("  Napoleón  ", entity_type="person")
        self.assertEqual(plan.title, "Napoleón")

    def test_plan_rejects_invalid_entity_type(self) -> None:
        with self.assertRaises(ValueError):
            plan_entity_note("Test", entity_type="invalid")

    def test_plan_merges_extra_frontmatter(self) -> None:
        plan = plan_entity_note(
            "Batalla de las Termópilas",
            entity_type="event",
            extra_frontmatter={"date": "480 BC", "location": "Termópilas"},
        )
        self.assertEqual(plan.frontmatter["date"], "480 BC")
        self.assertEqual(plan.frontmatter["location"], "Termópilas")


class ExtractEntityRelationsTestCase(TestCase):
    def test_extracts_list_of_related_entities(self) -> None:
        fm = {"related": ["Aristóteles", "Darío III", "Imperio Persa"]}
        self.assertEqual(extract_entity_relations(fm), ["Aristóteles", "Darío III", "Imperio Persa"])

    def test_extracts_single_string_related(self) -> None:
        fm = {"related": "Alejandro Magno"}
        self.assertEqual(extract_entity_relations(fm), ["Alejandro Magno"])

    def test_returns_empty_list_when_no_related(self) -> None:
        self.assertEqual(extract_entity_relations({}), [])
        self.assertEqual(extract_entity_relations({"related": None}), [])
        self.assertEqual(extract_entity_relations({"related": []}), [])

    def test_filters_empty_strings(self) -> None:
        fm = {"related": ["Alejandro", "", "  ", "Darío"]}
        self.assertEqual(extract_entity_relations(fm), ["Alejandro", "Darío"])


class IsEntityNoteTestCase(TestCase):
    def test_returns_true_when_entity_flag_is_true(self) -> None:
        self.assertTrue(is_entity_note({"entity": True, "type": "person"}))

    def test_returns_false_when_entity_flag_missing(self) -> None:
        self.assertFalse(is_entity_note({"type": "person"}))

    def test_returns_false_when_entity_flag_is_false(self) -> None:
        self.assertFalse(is_entity_note({"entity": False}))


class BuildEntityIndexEntryTestCase(TestCase):
    def test_builds_entry_from_entity_frontmatter(self) -> None:
        fm = {"entity": True, "type": "person", "name": "Napoleón"}
        entry = build_entity_index_entry(fm, "02 - Knowledge/Napoleón.md")
        self.assertIsNotNone(entry)
        self.assertEqual(entry.title, "Napoleón")
        self.assertEqual(entry.entity_type, "person")
        self.assertEqual(entry.relative_path, "02 - Knowledge/Napoleón.md")

    def test_returns_none_for_non_entity_note(self) -> None:
        fm = {"type": "source"}
        self.assertIsNone(build_entity_index_entry(fm, "01 - Sources/article.md"))

    def test_accepts_any_subtype_for_entity(self) -> None:
        fm = {"entity": True, "type": "spaceship", "name": "Enterprise"}
        entry = build_entity_index_entry(fm, "test.md")
        self.assertIsNotNone(entry)
        self.assertEqual(entry.entity_type, "spaceship")

    def test_uses_relative_path_as_title_when_name_missing(self) -> None:
        fm = {"entity": True, "type": "concept"}
        entry = build_entity_index_entry(fm, "02 - Knowledge/idea.md")
        self.assertIsNotNone(entry)
        self.assertEqual(entry.title, "02 - Knowledge/idea.md")


class GroupIndexEntriesTestCase(TestCase):
    def test_groups_entries_by_type_and_sorts_by_title(self) -> None:
        entries = [
            EntityIndexEntry(title="Zeno", entity_type="person", relative_path="z.md"),
            EntityIndexEntry(title="Aristóteles", entity_type="person", relative_path="a.md"),
            EntityIndexEntry(title="Grecia", entity_type="place", relative_path="g.md"),
        ]
        groups = group_index_entries_by_type(entries)
        self.assertEqual(list(groups.keys()), ["person", "place"])
        self.assertEqual([e.title for e in groups["person"]], ["Aristóteles", "Zeno"])

    def test_empty_list_returns_empty_groups(self) -> None:
        self.assertEqual(group_index_entries_by_type([]), {})


class RenderEntityIndexMarkdownTestCase(TestCase):
    def test_renders_grouped_markdown_with_wikilinks(self) -> None:
        entries = [
            EntityIndexEntry(title="Napoleón", entity_type="person", relative_path="n.md"),
            EntityIndexEntry(title="Francia", entity_type="place", relative_path="f.md"),
        ]
        md = render_entity_index_markdown(entries)
        self.assertIn("# Knowledge Entity Index", md)
        self.assertIn("Total entities: 2", md)
        self.assertIn("## Person (1)", md)
        self.assertIn("## Place (1)", md)
        self.assertIn("[[Napoleón]]", md)
        self.assertIn("[[Francia]]", md)

    def test_renders_empty_state_when_no_entries(self) -> None:
        md = render_entity_index_markdown([])
        self.assertIn("No entities found.", md)


class ExtractRelationsFromNoteTestCase(TestCase):
    def test_extracts_relations_from_entity_with_related_field(self) -> None:
        fm = {"entity": True, "type": "person", "name": "Alejandro Magno", "related": ["Aristóteles", "Darío III"]}
        rels = extract_relations_from_note(fm)
        self.assertEqual(len(rels), 2)
        self.assertEqual(rels[0].source, "Alejandro Magno")
        self.assertEqual(rels[0].target, "Aristóteles")
        self.assertEqual(rels[0].source_type, "person")

    def test_returns_empty_for_non_entity(self) -> None:
        fm = {"type": "source", "name": "Article"}
        self.assertEqual(extract_relations_from_note(fm), [])

    def test_returns_empty_when_no_name(self) -> None:
        fm = {"entity": True, "type": "person"}
        self.assertEqual(extract_relations_from_note(fm), [])


class BuildRelationAdjacencyTestCase(TestCase):
    def test_builds_bidirectional_adjacency(self) -> None:
        rels = [
            EntityRelation(source="A", target="B"),
            EntityRelation(source="A", target="C"),
            EntityRelation(source="B", target="C"),
        ]
        adj = build_relation_adjacency(rels)
        self.assertEqual(adj["A"], ["B", "C"])
        self.assertIn("A", adj["B"])
        self.assertIn("C", adj["B"])
        self.assertEqual(sorted(adj["C"]), ["A", "B"])


class FindEntityConnectionsTestCase(TestCase):
    def test_finds_all_connections_for_entity(self) -> None:
        rels = [
            EntityRelation(source="Alejandro", target="Aristóteles"),
            EntityRelation(source="Alejandro", target="Darío"),
            EntityRelation(source="César", target="Cleopatra"),
        ]
        connections = find_entity_connections("Alejandro", rels)
        self.assertEqual(connections, ["Aristóteles", "Darío"])

    def test_finds_reverse_connections(self) -> None:
        rels = [EntityRelation(source="Aristóteles", target="Alejandro")]
        connections = find_entity_connections("Alejandro", rels)
        self.assertEqual(connections, ["Aristóteles"])

    def test_returns_empty_when_no_connections(self) -> None:
        rels = [EntityRelation(source="César", target="Cleopatra")]
        self.assertEqual(find_entity_connections("Alejandro", rels), [])


class RenderEntityRelationsMarkdownTestCase(TestCase):
    def test_renders_connections_with_wikilinks(self) -> None:
        md = render_entity_relations_markdown("Alejandro Magno", ["Aristóteles", "Darío III"])
        self.assertIn("# Relations: Alejandro Magno", md)
        self.assertIn("Connected entities: 2", md)
        self.assertIn("[[Aristóteles]]", md)
        self.assertIn("[[Darío III]]", md)

    def test_renders_empty_state(self) -> None:
        md = render_entity_relations_markdown("Alejandro Magno", [])
        self.assertIn("No connections found.", md)


if __name__ == "__main__":
    import unittest

    unittest.main()
