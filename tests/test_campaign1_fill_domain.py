"""Subfase 1.4a — fill_domain tests (high-confidence only)."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from brain_ops.domains.knowledge.consolidation import (
    apply_fill_domain,
    plan_fill_domain,
)


def _write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _note(vault: Path, name: str, fm_extra: dict[str, str]) -> Path:
    lines = ["---"]
    lines.append(f"name: {name}")
    lines.append("entity: true")
    lines.append("status: canonical")
    for k, v in fm_extra.items():
        lines.append(f"{k}: {v}")
    lines.append("---")
    p = vault / "02 - Knowledge" / f"{name}.md"
    _write(p, "\n".join(lines) + "\n\n## Identity\n\nbody\n")
    return p


class PlanFillDomainHardRulesTestCase(TestCase):
    def test_deity_auto_religion(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _note(vault, "Ra", {"type": "entity", "object_kind": "entity", "subtype": "deity"})
            report = plan_fill_domain(vault)
            self.assertEqual(len(report.decisions), 1)
            d = report.decisions[0]
            self.assertEqual(d.rule, "subtype")
            self.assertEqual(d.proposed_domain, "religion")
            self.assertTrue(d.is_auto_applicable)

    def test_battle_auto_historia(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _note(vault, "Batalla X", {"type": "event", "object_kind": "event", "subtype": "battle"})
            report = plan_fill_domain(vault)
            self.assertEqual(report.decisions[0].proposed_domain, "historia")

    def test_algorithm_auto_ml(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _note(vault, "BM25", {"type": "concept", "object_kind": "concept", "subtype": "algorithm"})
            report = plan_fill_domain(vault)
            self.assertEqual(report.decisions[0].proposed_domain, "machine_learning")

    def test_scientific_concept_auto_ciencia(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _note(vault, "Gravedad", {"type": "concept", "object_kind": "concept", "subtype": "scientific_concept"})
            report = plan_fill_domain(vault)
            self.assertEqual(report.decisions[0].proposed_domain, "ciencia")

    def test_philosophical_concept_auto_filosofia(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _note(vault, "Alienación", {
                "type": "concept", "object_kind": "concept", "subtype": "philosophical_concept",
            })
            report = plan_fill_domain(vault)
            self.assertEqual(report.decisions[0].proposed_domain, "filosofia")


class PlanFillDomainSkipsTestCase(TestCase):
    def test_already_has_domain_is_not_touched(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _note(vault, "Ra", {
                "type": "entity", "object_kind": "entity", "subtype": "deity",
                "domain": "religion",
            })
            report = plan_fill_domain(vault)
            self.assertEqual(len(report.decisions), 0)
            self.assertEqual(report.notes_already_have_domain, 1)

    def test_disambiguation_page_is_skipped(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _note(vault, "Roma", {
                "type": "disambiguation", "object_kind": "disambiguation",
                "subtype": "disambiguation_page",
            })
            report = plan_fill_domain(vault)
            self.assertEqual(len(report.decisions), 1)
            self.assertEqual(report.decisions[0].rule, "skip")
            self.assertIsNone(report.decisions[0].proposed_domain)


class PlanFillDomainDeferredTestCase(TestCase):
    def test_abstract_concept_deferred(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _note(vault, "Libertad", {
                "type": "concept", "object_kind": "concept", "subtype": "abstract_concept",
            })
            report = plan_fill_domain(vault)
            self.assertEqual(report.decisions[0].rule, "deferred")
            self.assertIsNone(report.decisions[0].proposed_domain)

    def test_book_deferred_even_with_author(self) -> None:
        """Domain by theme, not by author (per user's explicit instruction)."""
        with TemporaryDirectory() as td:
            vault = Path(td)
            _note(vault, "Book X", {
                "type": "work", "object_kind": "work", "subtype": "book",
                "author": "Platón",
            })
            report = plan_fill_domain(vault)
            self.assertEqual(report.decisions[0].rule, "deferred")

    def test_city_without_era_deferred(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _note(vault, "Siracusa", {
                "type": "place", "object_kind": "place", "subtype": "city",
            })
            report = plan_fill_domain(vault)
            self.assertEqual(report.decisions[0].rule, "deferred")

    def test_discipline_deferred(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _note(vault, "Lógica", {
                "type": "concept", "object_kind": "concept", "subtype": "discipline",
            })
            report = plan_fill_domain(vault)
            self.assertEqual(report.decisions[0].rule, "deferred")


class PlanFillDomainPersonOccupationTestCase(TestCase):
    def test_philosopher_occupation_matches(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _note(vault, "Plato", {
                "type": "entity", "object_kind": "entity", "subtype": "person",
                "occupation": "Filósofo griego",
            })
            report = plan_fill_domain(vault)
            d = report.decisions[0]
            self.assertEqual(d.rule, "person_occupation")
            self.assertEqual(d.proposed_domain, "filosofia")

    def test_emperor_occupation_historia(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _note(vault, "Augusto", {
                "type": "entity", "object_kind": "entity", "subtype": "person",
                "occupation": "Emperador romano",
            })
            report = plan_fill_domain(vault)
            self.assertEqual(report.decisions[0].proposed_domain, "historia")

    def test_physicist_occupation_ciencia(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _note(vault, "Einstein", {
                "type": "entity", "object_kind": "entity", "subtype": "person",
                "occupation": "Físico teórico",
            })
            report = plan_fill_domain(vault)
            self.assertEqual(report.decisions[0].proposed_domain, "ciencia")

    def test_person_without_occupation_deferred(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _note(vault, "Alguien", {
                "type": "entity", "object_kind": "entity", "subtype": "person",
            })
            report = plan_fill_domain(vault)
            self.assertEqual(report.decisions[0].rule, "deferred")

    def test_person_with_ambiguous_occupation_deferred(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _note(vault, "Vago", {
                "type": "entity", "object_kind": "entity", "subtype": "person",
                "occupation": "Persona importante",
            })
            report = plan_fill_domain(vault)
            self.assertEqual(report.decisions[0].rule, "deferred")


class ApplyFillDomainTestCase(TestCase):
    def test_applies_only_auto_decisions(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            auto = _note(vault, "Ra", {
                "type": "entity", "object_kind": "entity", "subtype": "deity",
            })
            deferred = _note(vault, "Libertad", {
                "type": "concept", "object_kind": "concept", "subtype": "abstract_concept",
            })
            report = plan_fill_domain(vault)
            result = apply_fill_domain(vault, report)
            self.assertEqual(result["applied_count"], 1)
            self.assertIn("domain: religion", auto.read_text())
            self.assertNotIn("domain:", deferred.read_text())

    def test_body_untouched(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            p = _note(vault, "Ra", {
                "type": "entity", "object_kind": "entity", "subtype": "deity",
            })
            # Add a body marker
            original = p.read_text()
            p.write_text(original + "\n\nAncient Egyptian sun god.\n", encoding="utf-8")

            report = plan_fill_domain(vault)
            apply_fill_domain(vault, report)

            text = p.read_text()
            self.assertIn("Ancient Egyptian sun god.", text)
            self.assertIn("domain: religion", text)

    def test_exclude_skips_entity(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            ra = _note(vault, "Ra", {"type": "entity", "object_kind": "entity", "subtype": "deity"})
            isis = _note(vault, "Isis", {"type": "entity", "object_kind": "entity", "subtype": "deity"})
            report = plan_fill_domain(vault)
            apply_fill_domain(vault, report, exclude=["Ra"])
            self.assertNotIn("domain: religion", ra.read_text())
            self.assertIn("domain: religion", isis.read_text())

    def test_idempotent(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _note(vault, "Ra", {"type": "entity", "object_kind": "entity", "subtype": "deity"})
            report1 = plan_fill_domain(vault)
            apply_fill_domain(vault, report1)
            report2 = plan_fill_domain(vault)
            self.assertEqual(len(report2.decisions), 0)
            self.assertEqual(report2.notes_already_have_domain, 1)
