from __future__ import annotations

from unittest import TestCase

from brain_ops.domains.knowledge.epistemology import (
    CERTAINTY_LEVELS,
    DEFAULT_EPISTEMIC_BY_SUBTYPE,
    EPISTEMIC_GATED_DOMAINS,
    EPISTEMIC_MODES,
    apply_epistemic_default,
    default_epistemic_mode,
    is_gated_domain,
    is_valid_certainty_level,
    is_valid_epistemic_mode,
)


class EpistemicModesTestCase(TestCase):
    def test_core_modes_are_present(self) -> None:
        for mode in (
            "historical", "scientific", "religious",
            "mythological", "esoteric", "philosophical", "speculative",
        ):
            self.assertIn(mode, EPISTEMIC_MODES)

    def test_is_valid_epistemic_mode_accepts_known(self) -> None:
        self.assertTrue(is_valid_epistemic_mode("historical"))
        self.assertTrue(is_valid_epistemic_mode("esoteric"))

    def test_is_valid_epistemic_mode_rejects_unknown(self) -> None:
        self.assertFalse(is_valid_epistemic_mode("made_up"))
        self.assertFalse(is_valid_epistemic_mode(None))
        self.assertFalse(is_valid_epistemic_mode(""))


class CertaintyLevelsTestCase(TestCase):
    def test_core_levels_present(self) -> None:
        for level in (
            "well_supported", "tradition_based",
            "symbolic", "contested", "speculative",
        ):
            self.assertIn(level, CERTAINTY_LEVELS)

    def test_is_valid_certainty_level(self) -> None:
        self.assertTrue(is_valid_certainty_level("well_supported"))
        self.assertFalse(is_valid_certainty_level("sort_of"))
        self.assertFalse(is_valid_certainty_level(None))


class GatedDomainsTestCase(TestCase):
    def test_gated_domains_canonical(self) -> None:
        for d in ("religion", "esoterismo", "filosofia", "ciencia"):
            self.assertIn(d, EPISTEMIC_GATED_DOMAINS)

    def test_is_gated_domain(self) -> None:
        self.assertTrue(is_gated_domain("ciencia"))
        self.assertTrue(is_gated_domain("esoterismo"))
        self.assertFalse(is_gated_domain("historia"))
        self.assertFalse(is_gated_domain(None))
        self.assertFalse(is_gated_domain(""))


class DefaultEpistemicBySubtypeTestCase(TestCase):
    def test_mythological_defaults(self) -> None:
        self.assertEqual(default_epistemic_mode("deity"), "mythological")
        self.assertEqual(default_epistemic_mode("myth"), "mythological")
        self.assertEqual(default_epistemic_mode("mythological_place"), "mythological")

    def test_esoteric_defaults(self) -> None:
        self.assertEqual(default_epistemic_mode("esoteric_tradition"), "esoteric")
        self.assertEqual(default_epistemic_mode("ritual"), "esoteric")
        self.assertEqual(default_epistemic_mode("symbolic_system"), "esoteric")
        self.assertEqual(default_epistemic_mode("divination_system"), "esoteric")
        self.assertEqual(default_epistemic_mode("mystical_concept"), "esoteric")
        self.assertEqual(default_epistemic_mode("esoteric_text"), "esoteric")
        self.assertEqual(default_epistemic_mode("occult_movement"), "esoteric")

    def test_philosophical_defaults(self) -> None:
        self.assertEqual(default_epistemic_mode("philosophical_concept"), "philosophical")
        self.assertEqual(default_epistemic_mode("school_of_thought"), "philosophical")

    def test_scientific_defaults(self) -> None:
        for subtype in (
            "scientific_concept", "theorem", "mathematical_object",
            "mathematical_function", "constant", "chemical_element",
            "compound", "molecule", "biological_process", "gene",
            "disease", "cell", "cell_type", "organism", "species",
        ):
            self.assertEqual(default_epistemic_mode(subtype), "scientific", subtype)

    def test_historical_defaults(self) -> None:
        for subtype in (
            "historical_event", "historical_period",
            "historical_process", "dynasty",
        ):
            self.assertEqual(default_epistemic_mode(subtype), "historical", subtype)

    def test_religious_defaults(self) -> None:
        self.assertEqual(default_epistemic_mode("sacred_text"), "religious")

    def test_ambiguous_subtypes_have_no_default(self) -> None:
        self.assertIsNone(default_epistemic_mode("person"))
        self.assertIsNone(default_epistemic_mode("city"))
        self.assertIsNone(default_epistemic_mode("war"))
        self.assertIsNone(default_epistemic_mode(None))

    def test_all_defaults_reference_valid_modes(self) -> None:
        for subtype, mode in DEFAULT_EPISTEMIC_BY_SUBTYPE.items():
            self.assertIn(mode, EPISTEMIC_MODES, f"{subtype} → {mode}")


class ApplyEpistemicDefaultTestCase(TestCase):
    def test_applies_when_absent(self) -> None:
        fm, changed = apply_epistemic_default({"name": "X"}, "deity")
        self.assertTrue(changed)
        self.assertEqual(fm["epistemic_mode"], "mythological")

    def test_does_not_overwrite(self) -> None:
        fm, changed = apply_epistemic_default(
            {"epistemic_mode": "speculative"}, "deity",
        )
        self.assertFalse(changed)
        self.assertEqual(fm["epistemic_mode"], "speculative")

    def test_subtype_without_default_is_noop(self) -> None:
        fm, changed = apply_epistemic_default({"name": "X"}, "person")
        self.assertFalse(changed)
        self.assertNotIn("epistemic_mode", fm)

    def test_none_subtype_is_noop(self) -> None:
        fm, changed = apply_epistemic_default({"name": "X"}, None)
        self.assertFalse(changed)
        self.assertNotIn("epistemic_mode", fm)
