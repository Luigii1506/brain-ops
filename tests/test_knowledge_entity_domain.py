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
        self.assertIn("## Biography", body)
        self.assertIn("## Key contributions", body)
        self.assertIn("## Related notes", body)

    def test_event_body_has_expected_sections(self) -> None:
        body = build_entity_body("event", "Batalla de Gaugamela")
        self.assertIn("## Context", body)
        self.assertIn("## What happened", body)
        self.assertIn("## Consequences", body)

    def test_place_body_has_expected_sections(self) -> None:
        body = build_entity_body("place", "Grecia")
        self.assertIn("## Overview", body)
        self.assertIn("## History", body)
        self.assertIn("## Geography", body)

    def test_unknown_type_returns_minimal_body(self) -> None:
        body = build_entity_body("unknown_type", "Test")
        self.assertEqual(body, "# Test\n")


class PlanEntityNoteTestCase(TestCase):
    def test_plan_returns_complete_entity_plan(self) -> None:
        plan = plan_entity_note("Alejandro Magno", entity_type="person")
        self.assertIsInstance(plan, EntityPlan)
        self.assertEqual(plan.title, "Alejandro Magno")
        self.assertEqual(plan.entity_type, "person")
        self.assertEqual(plan.frontmatter["type"], "person")
        self.assertEqual(plan.frontmatter["name"], "Alejandro Magno")
        self.assertIs(plan.frontmatter["entity"], True)
        self.assertIn("## Biography", plan.body)

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


if __name__ == "__main__":
    import unittest

    unittest.main()
