"""Integration test: create-entity workflow applies epistemic defaults."""

from __future__ import annotations

from unittest import TestCase

from brain_ops.domains.knowledge.entities import build_entity_frontmatter


class EpistemicDefaultAppliedTestCase(TestCase):
    def test_deity_gets_mythological_default(self) -> None:
        fm = build_entity_frontmatter("deity", "Ra")
        self.assertEqual(fm.get("epistemic_mode"), "mythological")

    def test_esoteric_tradition_gets_esoteric(self) -> None:
        fm = build_entity_frontmatter("esoteric_tradition", "Hermetismo")
        self.assertEqual(fm.get("epistemic_mode"), "esoteric")

    def test_philosophical_concept_gets_philosophical(self) -> None:
        fm = build_entity_frontmatter("philosophical_concept", "Libertad")
        self.assertEqual(fm.get("epistemic_mode"), "philosophical")

    def test_historical_period_gets_historical(self) -> None:
        fm = build_entity_frontmatter("historical_period", "Edad Media")
        self.assertEqual(fm.get("epistemic_mode"), "historical")

    def test_theorem_gets_scientific(self) -> None:
        fm = build_entity_frontmatter("theorem", "Teorema de Pitágoras")
        self.assertEqual(fm.get("epistemic_mode"), "scientific")

    def test_person_has_no_default(self) -> None:
        fm = build_entity_frontmatter("person", "Platón")
        self.assertNotIn("epistemic_mode", fm)

    def test_city_has_no_default(self) -> None:
        fm = build_entity_frontmatter("city", "Atenas")
        self.assertNotIn("epistemic_mode", fm)

    def test_explicit_epistemic_mode_preserved(self) -> None:
        fm = build_entity_frontmatter(
            "deity", "Ra",
            extra={"epistemic_mode": "religious"},
        )
        self.assertEqual(fm.get("epistemic_mode"), "religious")
