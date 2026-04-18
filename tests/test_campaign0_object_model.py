"""Tests for Campaña 0 additions to the object model.

Covers:
- new subtypes in SUBTYPES
- new disambiguation labels
- new section templates
- new canonical predicates and their ES/EN normalizations
- participated_in coexistence with fought_in
"""

from __future__ import annotations

from unittest import TestCase

from brain_ops.domains.knowledge.object_model import (
    CANONICAL_PREDICATES,
    DISAMBIGUATION_LABELS,
    PREDICATE_NORMALIZATION,
    SUBTYPE_SECTIONS,
    SUBTYPES,
    disambiguation_label,
    normalize_predicate,
    resolve_object_kind,
    sections_for_subtype,
)


NEW_SUBTYPES_BY_KIND: dict[str, tuple[str, ...]] = {
    "entity": ("organism", "species", "anatomical_structure", "language", "script"),
    "concept": (
        "biological_process", "cell", "cell_type", "gene",
        "chemical_element", "compound", "molecule",
        "disease", "medical_theory",
        "theorem", "mathematical_object", "constant", "mathematical_function",
        "proof_method", "mathematical_field",
        "symbolic_system", "divination_system", "mystical_concept",
    ),
    "work": ("sacred_text", "esoteric_text"),
    "event": ("historical_period", "dynasty", "historical_process", "ritual"),
    "organization": ("esoteric_tradition", "occult_movement"),
}


class NewSubtypesTestCase(TestCase):
    def test_all_new_subtypes_registered(self) -> None:
        for kind, subtypes in NEW_SUBTYPES_BY_KIND.items():
            for st in subtypes:
                self.assertIn(st, SUBTYPES[kind], f"{st} not in SUBTYPES[{kind}]")

    def test_resolve_object_kind_for_new_subtypes(self) -> None:
        for kind, subtypes in NEW_SUBTYPES_BY_KIND.items():
            for st in subtypes:
                resolved_kind, resolved_st = resolve_object_kind(st)
                self.assertEqual(resolved_kind, kind, f"{st} resolved to {resolved_kind}")
                self.assertEqual(resolved_st, st)

    def test_no_subtype_collisions(self) -> None:
        """A subtype name should belong to exactly one kind."""
        seen: dict[str, str] = {}
        for kind, subtypes in SUBTYPES.items():
            for st in subtypes:
                if st in seen:
                    self.fail(f"subtype '{st}' appears in both {seen[st]} and {kind}")
                seen[st] = kind


class DisambiguationLabelsTestCase(TestCase):
    def test_spanish_labels_for_new_subtypes(self) -> None:
        expected = {
            "organism": "organismo",
            "species": "especie",
            "language": "lengua",
            "script": "escritura",
            "gene": "gen",
            "chemical_element": "elemento químico",
            "molecule": "molécula",
            "theorem": "teorema",
            "constant": "constante",
            "sacred_text": "texto sagrado",
            "esoteric_tradition": "tradición esotérica",
            "historical_period": "período",
            "dynasty": "dinastía",
            "ritual": "ritual",
            "cell": "célula",
            "compound": "compuesto",
        }
        for st, label in expected.items():
            self.assertEqual(
                DISAMBIGUATION_LABELS.get(st), label,
                f"{st} should map to '{label}'",
            )
            self.assertEqual(disambiguation_label(st), label)


class SectionsForNewSubtypesTestCase(TestCase):
    def test_each_new_subtype_has_sections(self) -> None:
        for subtypes in NEW_SUBTYPES_BY_KIND.values():
            for st in subtypes:
                self.assertIn(st, SUBTYPE_SECTIONS, f"No sections for {st}")

    def test_sections_include_relationships_and_related(self) -> None:
        for subtypes in NEW_SUBTYPES_BY_KIND.values():
            for st in subtypes:
                sections = sections_for_subtype(st)
                self.assertIn("Relationships", sections, f"{st} missing Relationships")
                self.assertIn("Related notes", sections, f"{st} missing Related notes")

    def test_preguntas_injected(self) -> None:
        for st in ("theorem", "historical_period", "esoteric_tradition"):
            sections = sections_for_subtype(st)
            self.assertIn("Preguntas de recuperación", sections)


NEW_PREDICATES: tuple[str, ...] = (
    # Intellectual
    "reacted_against", "developed", "extended", "synthesized",
    "refuted", "criticized", "inspired", "derived_from",
    # Historical
    "belongs_to_period", "contemporary_of", "emerged_from",
    "transformed_into", "ruled_by", "centered_on", "continuation_of",
    # Religious / mythological / esoteric
    "worshipped", "worshipped_by", "associated_with", "symbolizes",
    "used_in", "practiced_by", "interpreted_as", "appears_in",
    # Work
    "depicts", "describes", "argues_for", "argues_against",
    "written_in", "based_on",
    # Scientific
    "explains", "measured_by", "studied_in", "part_of_system",
    "precedes_in_process", "depends_on",
    # Generic participative
    "participated_in",
)


class NewPredicatesTestCase(TestCase):
    def test_all_new_predicates_canonical(self) -> None:
        for p in NEW_PREDICATES:
            self.assertIn(p, CANONICAL_PREDICATES, f"{p} missing from CANONICAL_PREDICATES")

    def test_no_duplicates_in_canonical(self) -> None:
        keys = list(CANONICAL_PREDICATES.keys())
        self.assertEqual(len(keys), len(set(keys)))

    def test_canonical_predicate_passes_through(self) -> None:
        for p in NEW_PREDICATES:
            self.assertEqual(normalize_predicate(p), p)


class PredicateNormalizationTestCase(TestCase):
    def test_spanish_intellectual(self) -> None:
        self.assertEqual(normalize_predicate("reaccionó contra"), "reacted_against")
        self.assertEqual(normalize_predicate("desarrolló"), "developed")
        self.assertEqual(normalize_predicate("sintetizó"), "synthesized")
        self.assertEqual(normalize_predicate("refutó"), "refuted")
        self.assertEqual(normalize_predicate("criticó"), "criticized")
        self.assertEqual(normalize_predicate("inspiró"), "inspired")
        self.assertEqual(normalize_predicate("derivado de"), "derived_from")

    def test_english_intellectual(self) -> None:
        self.assertEqual(normalize_predicate("reacted against"), "reacted_against")
        self.assertEqual(normalize_predicate("synthesized"), "synthesized")

    def test_historical(self) -> None:
        self.assertEqual(normalize_predicate("contemporáneo de"), "contemporary_of")
        self.assertEqual(normalize_predicate("emergió de"), "emerged_from")
        self.assertEqual(normalize_predicate("se transformó en"), "transformed_into")
        self.assertEqual(normalize_predicate("gobernado por"), "ruled_by")
        self.assertEqual(normalize_predicate("centrado en"), "centered_on")
        self.assertEqual(normalize_predicate("continuación de"), "continuation_of")

    def test_religious_esoteric(self) -> None:
        self.assertEqual(normalize_predicate("adorado por"), "worshipped_by")
        self.assertEqual(normalize_predicate("adorada por"), "worshipped_by")
        self.assertEqual(normalize_predicate("simboliza"), "symbolizes")
        self.assertEqual(normalize_predicate("usado en"), "used_in")
        self.assertEqual(normalize_predicate("practicado por"), "practiced_by")
        self.assertEqual(normalize_predicate("aparece en"), "appears_in")

    def test_work(self) -> None:
        self.assertEqual(normalize_predicate("describe"), "describes")
        self.assertEqual(normalize_predicate("representa"), "depicts")
        self.assertEqual(normalize_predicate("argumenta a favor de"), "argues_for")
        self.assertEqual(normalize_predicate("argumenta contra"), "argues_against")
        self.assertEqual(normalize_predicate("escrito en"), "written_in")
        self.assertEqual(normalize_predicate("basado en"), "based_on")

    def test_scientific(self) -> None:
        self.assertEqual(normalize_predicate("explica"), "explains")
        self.assertEqual(normalize_predicate("medido por"), "measured_by")
        self.assertEqual(normalize_predicate("depende de"), "depends_on")


class ParticipatedInCoexistsWithFoughtInTestCase(TestCase):
    def test_participated_in_is_canonical(self) -> None:
        self.assertIn("participated_in", CANONICAL_PREDICATES)
        self.assertIn("fought_in", CANONICAL_PREDICATES)
        self.assertNotEqual(
            CANONICAL_PREDICATES["participated_in"],
            CANONICAL_PREDICATES["fought_in"],
        )

    def test_participo_en_maps_to_participated_in(self) -> None:
        # After Campaña 0 — generic participation, NOT military.
        self.assertEqual(normalize_predicate("participó en"), "participated_in")
        self.assertEqual(normalize_predicate("participated in"), "participated_in")

    def test_luchó_en_maps_to_fought_in(self) -> None:
        self.assertEqual(normalize_predicate("luchó en"), "fought_in")
        self.assertEqual(normalize_predicate("fought in"), "fought_in")
        self.assertEqual(normalize_predicate("combatió en"), "fought_in")


class RegressionCoreBehaviorTestCase(TestCase):
    """Make sure Campaña 0 did not break pre-existing normalizations."""

    def test_old_predicates_still_work(self) -> None:
        self.assertEqual(normalize_predicate("padre de"), "parent_of")
        self.assertEqual(normalize_predicate("alumno de"), "studied_under")
        self.assertEqual(normalize_predicate("conquistó"), "conquered")
        self.assertEqual(normalize_predicate("nació en"), "born_in")
        self.assertEqual(normalize_predicate("murió en"), "died_in")
        self.assertEqual(normalize_predicate("wrote"), "wrote")

    def test_unknown_still_falls_back(self) -> None:
        self.assertEqual(normalize_predicate("completely unrelated phrase"), "related_to")
