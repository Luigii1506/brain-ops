"""Subfase 1.1 / 1.2 — normalize_domain tests.

Verifies plan/apply cycle, subdomain hint behavior, and exclusion logic.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from brain_ops.domains.knowledge.consolidation import (
    apply_normalize_domain,
    plan_normalize_domain,
)


def _write_note(
    vault: Path,
    name: str,
    frontmatter_lines: list[str],
    body: str = "Body here.",
) -> Path:
    note = vault / "02 - Knowledge" / f"{name}.md"
    note.parent.mkdir(parents=True, exist_ok=True)
    fm_text = "\n".join(frontmatter_lines)
    note.write_text(f"---\n{fm_text}\n---\n\n{body}\n", encoding="utf-8")
    return note


class PlanNormalizeDomainTestCase(TestCase):
    def test_reports_canonical_notes_separately(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _write_note(vault, "A", ["name: A", "domain: historia"])
            _write_note(vault, "B", ["name: B", "domain: filosofia"])

            report = plan_normalize_domain(vault)

            self.assertEqual(report.total_notes_scanned, 2)
            self.assertEqual(report.notes_already_canonical, 2)
            self.assertEqual(report.total_changes, 0)

    def test_proposes_english_to_spanish_transitions(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _write_note(vault, "Plato", ["name: Plato", "domain: philosophy"])
            _write_note(vault, "War", ["name: War", "domain: history"])
            _write_note(vault, "Atom", ["name: Atom", "domain: science"])

            report = plan_normalize_domain(vault)

            self.assertEqual(report.total_changes, 3)
            transitions = report.counts_by_transition()
            self.assertEqual(transitions["philosophy → filosofia"], 1)
            self.assertEqual(transitions["history → historia"], 1)
            self.assertEqual(transitions["science → ciencia"], 1)

    def test_astronomia_collapses_with_subdomain_hint(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _write_note(vault, "Jupiter", ["name: Jupiter", "domain: astronomía"])

            report = plan_normalize_domain(vault)

            self.assertEqual(report.total_changes, 1)
            change = report.changes[0]
            self.assertEqual(change.current_domain, "astronomía")
            self.assertEqual(change.new_domain, "ciencia")
            self.assertEqual(change.subdomain_current, None)
            self.assertEqual(change.subdomain_new, "astronomia")

    def test_existing_subdomain_is_preserved(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _write_note(
                vault, "Saturn",
                ["name: Saturn", "domain: astronomía", "subdomain: sistema solar"],
            )

            report = plan_normalize_domain(vault)

            self.assertEqual(report.total_changes, 1)
            change = report.changes[0]
            self.assertEqual(change.subdomain_current, "sistema solar")
            # Existing subdomain is NEVER overwritten
            self.assertEqual(change.subdomain_new, "sistema solar")

    def test_notes_without_domain_reported_separately(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _write_note(vault, "Orphan", ["name: Orphan"])

            report = plan_normalize_domain(vault)

            self.assertEqual(report.notes_without_domain, 1)
            self.assertEqual(report.total_changes, 0)

    def test_unknown_domain_not_touched(self) -> None:
        """A truly unknown label should be left alone — Subfase 1.4 territory."""
        with TemporaryDirectory() as td:
            vault = Path(td)
            _write_note(
                vault, "Weird",
                ["name: Weird", "domain: cryptozoology"],
            )
            report = plan_normalize_domain(vault)
            self.assertEqual(report.total_changes, 0)


class ApplyNormalizeDomainTestCase(TestCase):
    def test_writes_new_domain(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            note = _write_note(vault, "Plato", ["name: Plato", "domain: philosophy"])

            report = plan_normalize_domain(vault)
            result = apply_normalize_domain(vault, report)

            self.assertEqual(result["applied_count"], 1)
            text = note.read_text()
            self.assertIn("domain: filosofia", text)
            self.assertNotIn("domain: philosophy", text)

    def test_adds_subdomain_hint_when_absent(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            note = _write_note(vault, "Jupiter", ["name: Jupiter", "domain: astronomía"])

            report = plan_normalize_domain(vault)
            apply_normalize_domain(vault, report)

            text = note.read_text()
            self.assertIn("domain: ciencia", text)
            self.assertIn("subdomain: astronomia", text)

    def test_preserves_body(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            note = _write_note(
                vault, "Plato",
                ["name: Plato", "domain: philosophy"],
                body="## Identity\n\nGreek philosopher.",
            )

            report = plan_normalize_domain(vault)
            apply_normalize_domain(vault, report)

            text = note.read_text()
            self.assertIn("## Identity", text)
            self.assertIn("Greek philosopher.", text)

    def test_exclude_skips_specific_notes(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            note_a = _write_note(vault, "A", ["name: A", "domain: philosophy"])
            note_b = _write_note(vault, "B", ["name: B", "domain: philosophy"])

            report = plan_normalize_domain(vault)
            # Exclude A by relative path
            rel_a = str(note_a.relative_to(vault))
            result = apply_normalize_domain(vault, report, exclude=[rel_a])

            self.assertEqual(result["applied_count"], 1)
            self.assertIn(rel_a, result["skipped_excluded"])
            # A unchanged, B changed
            self.assertIn("philosophy", note_a.read_text())
            self.assertIn("filosofia", note_b.read_text())

    def test_only_transition_filter(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            note_phi = _write_note(vault, "Plato", ["name: Plato", "domain: philosophy"])
            note_hist = _write_note(vault, "War", ["name: War", "domain: history"])

            report = plan_normalize_domain(vault)
            result = apply_normalize_domain(
                vault, report,
                transitions_filter={"philosophy → filosofia"},
            )

            self.assertEqual(result["applied_count"], 1)
            # Philosophy migrated, history NOT
            self.assertIn("filosofia", note_phi.read_text())
            self.assertIn("history", note_hist.read_text())

    def test_concurrent_edit_protection(self) -> None:
        """If a note's domain changed between plan and apply, skip it."""
        with TemporaryDirectory() as td:
            vault = Path(td)
            note = _write_note(vault, "Plato", ["name: Plato", "domain: philosophy"])

            report = plan_normalize_domain(vault)
            # Simulate concurrent manual edit
            note.write_text(
                "---\nname: Plato\ndomain: filosofia\n---\n\nBody.\n",
                encoding="utf-8",
            )

            result = apply_normalize_domain(vault, report)

            # Note was not re-written (defensive check blocked)
            text = note.read_text()
            self.assertIn("domain: filosofia", text)
            # applied_count does not include this note since it skipped
            self.assertEqual(result["applied_count"], 0)

    def test_idempotency_second_run_is_noop(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _write_note(vault, "Plato", ["name: Plato", "domain: philosophy"])

            # First run: applies
            first_report = plan_normalize_domain(vault)
            first_result = apply_normalize_domain(vault, first_report)
            self.assertEqual(first_result["applied_count"], 1)

            # Second run: plan returns no changes
            second_report = plan_normalize_domain(vault)
            self.assertEqual(second_report.total_changes, 0)


class ReportSerializationTestCase(TestCase):
    def test_to_dict_structure(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _write_note(vault, "A", ["name: A", "domain: philosophy"])

            report = plan_normalize_domain(vault)
            data = report.to_dict()

            self.assertIn("total_notes_scanned", data)
            self.assertIn("transitions", data)
            self.assertIn("changes", data)
            self.assertEqual(data["total_changes"], 1)
            self.assertIn("philosophy → filosofia", data["transitions"])
