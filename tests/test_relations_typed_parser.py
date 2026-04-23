"""Tests for relations_typed parser — Step 1 of Campaña 2.0."""

from __future__ import annotations

from unittest import TestCase

from brain_ops.domains.knowledge.relations_typed import (
    RelationsParseResult,
    TypedRelation,
    parse_relationships,
)


class AbsentOrEmptyFieldTestCase(TestCase):
    def test_absent_relationships_field_returns_empty(self) -> None:
        result = parse_relationships("Aristóteles", {"name": "Aristóteles"})
        self.assertEqual(result.typed, [])
        self.assertEqual(result.errors, [])
        self.assertFalse(result.has_errors)

    def test_empty_list_returns_empty(self) -> None:
        result = parse_relationships("X", {"relationships": []})
        self.assertEqual(result.typed, [])
        self.assertEqual(result.errors, [])

    def test_non_list_relationships_flagged(self) -> None:
        result = parse_relationships("X", {"relationships": "not a list"})
        self.assertEqual(result.typed, [])
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].kind, "invalid_shape")


class CompactInlineFormatTestCase(TestCase):
    def test_single_inline_dict_parses(self) -> None:
        fm = {"relationships": [
            {"predicate": "studied_under", "object": "Platón"},
        ]}
        result = parse_relationships("Aristóteles", fm)
        self.assertEqual(len(result.typed), 1)
        r = result.typed[0]
        self.assertEqual(r.source, "Aristóteles")
        self.assertEqual(r.predicate, "studied_under")
        self.assertEqual(r.object, "Platón")
        self.assertEqual(r.confidence, "medium")
        self.assertIsNone(r.reason)

    def test_multiple_entries(self) -> None:
        fm = {"relationships": [
            {"predicate": "studied_under", "object": "Platón"},
            {"predicate": "mentor_of", "object": "Alejandro Magno"},
            {"predicate": "author_of", "object": "Ética a Nicómaco"},
        ]}
        result = parse_relationships("Aristóteles", fm)
        self.assertEqual(len(result.typed), 3)
        self.assertEqual(result.typed[0].predicate, "studied_under")
        self.assertEqual(result.typed[2].object, "Ética a Nicómaco")


class ExpandedFormatTestCase(TestCase):
    def test_entry_with_reason_and_confidence(self) -> None:
        fm = {"relationships": [
            {
                "predicate": "reacted_against",
                "object": "Platón",
                "reason": "Crítica a la teoría de las Formas",
                "confidence": "high",
            },
        ]}
        result = parse_relationships("Aristóteles", fm)
        self.assertEqual(len(result.typed), 1)
        r = result.typed[0]
        self.assertEqual(r.reason, "Crítica a la teoría de las Formas")
        self.assertEqual(r.confidence, "high")

    def test_entry_with_date_and_source_id(self) -> None:
        fm = {"relationships": [
            {
                "predicate": "mentor_of",
                "object": "Alejandro Magno",
                "date": "343-336 a.C.",
                "source_id": "plutarco_alexander",
            },
        ]}
        result = parse_relationships("Aristóteles", fm)
        r = result.typed[0]
        self.assertEqual(r.date, "343-336 a.C.")
        self.assertEqual(r.source_id, "plutarco_alexander")

    def test_unknown_keys_preserved_in_extra(self) -> None:
        fm = {"relationships": [
            {
                "predicate": "studied_under",
                "object": "Platón",
                "custom_field": "value",
                "another": 42,
            },
        ]}
        result = parse_relationships("Aristóteles", fm)
        r = result.typed[0]
        self.assertEqual(r.extra, {"custom_field": "value", "another": 42})


class InvalidPredicateTestCase(TestCase):
    def test_unknown_predicate_flagged(self) -> None:
        fm = {"relationships": [
            {"predicate": "makes_burritos_with", "object": "Platón"},
        ]}
        result = parse_relationships("Aristóteles", fm)
        self.assertEqual(result.typed, [])
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].kind, "unknown_predicate")
        self.assertIn("makes_burritos_with", result.errors[0].message)

    def test_valid_and_invalid_predicates_mixed(self) -> None:
        fm = {"relationships": [
            {"predicate": "studied_under", "object": "Platón"},
            {"predicate": "bogus", "object": "Random"},
            {"predicate": "mentor_of", "object": "Alejandro Magno"},
        ]}
        result = parse_relationships("Aristóteles", fm)
        self.assertEqual(len(result.typed), 2)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual([r.predicate for r in result.typed],
                         ["studied_under", "mentor_of"])


class ReligionPredicatesCampana2TestCase(TestCase):
    """Campaña 2 religion-domain predicate governance.

    These 12 predicates were added so the religion-domain frontmatter
    migration (founded_by, has_branch, uses_text, celebrated_by,
    branch_of, related_concept, contrasts_with, emerged_in,
    practiced_in, plus the inverses founder_of, text_of, celebrates)
    is fully ingestable by the typed-graph compiler.
    """

    def test_all_religion_predicates_accepted(self) -> None:
        religion_predicates = [
            "founded_by", "founder_of",
            "uses_text", "text_of",
            "has_branch", "branch_of",
            "celebrates", "celebrated_by",
            "practiced_in",
            "related_concept", "contrasts_with",
            "emerged_in",
        ]
        fm = {"relationships": [
            {"predicate": p, "object": f"Target{i}"}
            for i, p in enumerate(religion_predicates)
        ]}
        result = parse_relationships("Cristianismo", fm)
        self.assertEqual(
            len(result.typed),
            len(religion_predicates),
            f"Expected all {len(religion_predicates)} religion predicates accepted; "
            f"errors: {[(e.kind, e.message) for e in result.errors]}",
        )
        self.assertEqual(result.errors, [])
        self.assertEqual(
            [r.predicate for r in result.typed],
            religion_predicates,
        )

    def test_religion_predicates_in_canonical_dict(self) -> None:
        from brain_ops.domains.knowledge.object_model import CANONICAL_PREDICATES
        for p in (
            "founded_by", "founder_of", "uses_text", "text_of",
            "has_branch", "branch_of", "celebrates", "celebrated_by",
            "practiced_in", "related_concept", "contrasts_with", "emerged_in",
        ):
            self.assertIn(p, CANONICAL_PREDICATES, f"{p} missing from CANONICAL_PREDICATES")

    def test_religion_predicate_with_confidence_and_reason(self) -> None:
        fm = {"relationships": [
            {
                "predicate": "founded_by",
                "object": "Jesucristo",
                "confidence": "high",
                "reason": "Tradición fundacional cristiana",
            },
            {
                "predicate": "has_branch",
                "object": "Catolicismo",
                "confidence": "high",
            },
            {
                "predicate": "contrasts_with",
                "object": "Politeísmo",
                "confidence": "medium",
            },
        ]}
        result = parse_relationships("Cristianismo", fm)
        self.assertEqual(len(result.typed), 3)
        self.assertEqual(result.typed[0].predicate, "founded_by")
        self.assertEqual(result.typed[0].confidence, "high")
        self.assertEqual(result.typed[0].reason, "Tradición fundacional cristiana")
        self.assertEqual(result.typed[2].confidence, "medium")


class MissingFieldTestCase(TestCase):
    def test_missing_predicate_flagged(self) -> None:
        fm = {"relationships": [{"object": "Platón"}]}
        result = parse_relationships("Aristóteles", fm)
        self.assertEqual(result.typed, [])
        self.assertEqual(result.errors[0].kind, "missing_field")
        self.assertIn("predicate", result.errors[0].message)

    def test_missing_object_flagged(self) -> None:
        fm = {"relationships": [{"predicate": "studied_under"}]}
        result = parse_relationships("Aristóteles", fm)
        self.assertEqual(result.typed, [])
        self.assertEqual(result.errors[0].kind, "missing_field")
        self.assertIn("object", result.errors[0].message)

    def test_empty_string_predicate_flagged(self) -> None:
        fm = {"relationships": [{"predicate": "   ", "object": "Platón"}]}
        result = parse_relationships("Aristóteles", fm)
        self.assertEqual(result.typed, [])
        self.assertEqual(result.errors[0].kind, "missing_field")

    def test_non_dict_entry_flagged(self) -> None:
        fm = {"relationships": ["just a string"]}
        result = parse_relationships("X", fm)
        self.assertEqual(result.typed, [])
        self.assertEqual(result.errors[0].kind, "invalid_shape")


class ConfidenceValidationTestCase(TestCase):
    def test_invalid_confidence_defaults_to_medium(self) -> None:
        fm = {"relationships": [
            {"predicate": "studied_under", "object": "Platón", "confidence": "certain"},
        ]}
        result = parse_relationships("X", fm)
        self.assertEqual(result.typed[0].confidence, "medium")
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].kind, "invalid_confidence")

    def test_all_valid_confidence_levels(self) -> None:
        for level in ("high", "medium", "low"):
            fm = {"relationships": [
                {"predicate": "studied_under", "object": "Platón", "confidence": level},
            ]}
            result = parse_relationships("X", fm)
            self.assertEqual(result.typed[0].confidence, level)
            self.assertEqual(result.errors, [])


class DedupTestCase(TestCase):
    def test_exact_duplicate_dedupe_by_predicate_object(self) -> None:
        fm = {"relationships": [
            {"predicate": "studied_under", "object": "Platón"},
            {"predicate": "studied_under", "object": "Platón"},
        ]}
        result = parse_relationships("Aristóteles", fm)
        self.assertEqual(len(result.typed), 1)
        self.assertEqual(len(result.duplicates), 1)

    def test_same_object_different_predicates_coexist(self) -> None:
        """User-approved design: multiple predicates to same target are legitimate."""
        fm = {"relationships": [
            {"predicate": "allied_with", "object": "Marco Antonio"},
            {"predicate": "opposed", "object": "Marco Antonio"},
        ]}
        result = parse_relationships("Augusto", fm)
        self.assertEqual(len(result.typed), 2)
        self.assertEqual(len(result.duplicates), 0)
        predicates = {r.predicate for r in result.typed}
        self.assertEqual(predicates, {"allied_with", "opposed"})

    def test_dedup_key_is_source_predicate_object(self) -> None:
        """Three relations, but only one dedup collision."""
        fm = {"relationships": [
            {"predicate": "influenced", "object": "Tomás de Aquino"},
            {"predicate": "influenced", "object": "Averroes"},
            {"predicate": "influenced", "object": "Tomás de Aquino"},  # dupe of first
        ]}
        result = parse_relationships("Aristóteles", fm)
        self.assertEqual(len(result.typed), 2)
        self.assertEqual(len(result.duplicates), 1)


class SelfReferenceTestCase(TestCase):
    def test_self_reference_surfaces_but_stays_in_typed(self) -> None:
        fm = {"relationships": [
            {"predicate": "influenced", "object": "Aristóteles"},
        ]}
        result = parse_relationships("Aristóteles", fm)
        self.assertEqual(len(result.typed), 1)
        self.assertEqual(len(result.self_references), 1)
        self.assertTrue(result.has_self_references)


class DisambiguatedObjectTestCase(TestCase):
    def test_disambiguated_name_preserved(self) -> None:
        fm = {"relationships": [
            {"predicate": "located_in", "object": "Tebas (Grecia)"},
            {"predicate": "capital_of", "object": "República Romana"},
        ]}
        result = parse_relationships("X", fm)
        self.assertEqual(len(result.typed), 2)
        self.assertEqual(result.typed[0].object, "Tebas (Grecia)")
        self.assertEqual(result.typed[1].object, "República Romana")


class BackwardCompatTestCase(TestCase):
    def test_note_with_only_related_still_works(self) -> None:
        """A note with only `related:` (no `relationships:`) produces empty typed."""
        fm = {"related": ["Sócrates", "Alejandro Magno"]}
        result = parse_relationships("Aristóteles", fm)
        self.assertEqual(result.typed, [])
        self.assertEqual(result.errors, [])

    def test_empty_frontmatter(self) -> None:
        result = parse_relationships("X", {})
        self.assertEqual(result.typed, [])
        self.assertEqual(result.errors, [])


class TypedRelationSerializationTestCase(TestCase):
    def test_to_dict_shape(self) -> None:
        rel = TypedRelation(
            source="Aristóteles",
            predicate="studied_under",
            object="Platón",
            reason="Alumno en la Academia",
            confidence="high",
        )
        data = rel.to_dict()
        self.assertEqual(data["source"], "Aristóteles")
        self.assertEqual(data["predicate"], "studied_under")
        self.assertEqual(data["reason"], "Alumno en la Academia")
        self.assertEqual(data["confidence"], "high")
        self.assertIsNone(data["date"])

    def test_dedup_key_tuple(self) -> None:
        rel = TypedRelation(
            source="Aristóteles", predicate="studied_under", object="Platón",
        )
        self.assertEqual(rel.dedup_key, ("Aristóteles", "studied_under", "Platón"))
