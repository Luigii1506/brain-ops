"""Test tooling support for list-domain (bridge-figure exception)."""

from __future__ import annotations

from unittest import TestCase

from brain_ops.domains.knowledge.naming_rules import (
    _flag_domain_value,
    check_note_naming,
    check_vault_naming,
)
from brain_ops.domains.knowledge.schema_validator import validate_vault_notes


class ListDomainNamingTestCase(TestCase):
    def test_list_domain_with_canonical_values_is_clean(self) -> None:
        """list-domain with canonicalized Spanish values → no violations."""
        violations = check_note_naming("Séneca", {
            "subtype": "person",
            "domain": ["historia", "filosofia"],
        })
        # May contain capitalization check but no domain violation
        domain_vs = [v for v in violations if v.rule.startswith("domain")]
        self.assertEqual(domain_vs, [])

    def test_list_domain_with_english_values_flagged(self) -> None:
        """list-domain with legacy English values must flag each non-canonical."""
        violations = check_note_naming("Séneca", {
            "subtype": "person",
            "domain": ["history", "philosophy"],
        })
        aliases = [v for v in violations if v.rule == "domain_alias"]
        self.assertEqual(len(aliases), 2)
        # Both messages should mention the list item index
        self.assertTrue(any("list item 0" in v.message for v in aliases))
        self.assertTrue(any("list item 1" in v.message for v in aliases))

    def test_list_domain_mixed_only_non_canonical_flagged(self) -> None:
        violations = check_note_naming("X", {
            "subtype": "person",
            "domain": ["historia", "philosophy"],
        })
        aliases = [v for v in violations if v.rule == "domain_alias"]
        self.assertEqual(len(aliases), 1)
        self.assertIn("philosophy", aliases[0].message)

    def test_list_domain_too_long_flagged(self) -> None:
        violations = check_note_naming("X", {
            "subtype": "person",
            "domain": ["historia", "filosofia", "ciencia"],
        })
        too_long = [v for v in violations if v.rule == "domain_list_too_long"]
        self.assertEqual(len(too_long), 1)

    def test_unknown_domain_in_list_flagged(self) -> None:
        violations = check_note_naming("X", {
            "subtype": "person",
            "domain": ["historia", "frankenstein"],
        })
        unknown = [v for v in violations if v.rule == "domain_unknown"]
        self.assertEqual(len(unknown), 1)


class ListDomainSchemaStatsTestCase(TestCase):
    def test_list_domain_counts_under_each_domain(self) -> None:
        notes = [
            ("a.md", "Solo-hist", {
                "type": "person", "object_kind": "entity", "subtype": "person",
                "name": "Solo-hist", "domain": "historia",
                "era": "X", "born": "X", "died": "X",
                "occupation": "X", "nationality": "X",
                "tags": ["x"], "status": "canonical", "tradition": "X",
            }),
            ("b.md", "Bridge", {
                "type": "person", "object_kind": "entity", "subtype": "person",
                "name": "Bridge", "domain": ["historia", "filosofia"],
                "era": "X", "born": "X", "died": "X",
                "occupation": "X", "nationality": "X",
                "tags": ["x"], "status": "canonical", "tradition": "X",
            }),
        ]
        report = validate_vault_notes(notes)
        # Bridge is counted under BOTH historia and filosofia
        self.assertEqual(report.per_domain["historia"]["total"], 2)
        self.assertEqual(report.per_domain["filosofia"]["total"], 1)
        # No "(none)" bucket needed
        self.assertNotIn("(none)", report.per_domain)

    def test_list_domain_empty_is_none(self) -> None:
        notes = [
            ("a.md", "A", {
                "type": "person", "object_kind": "entity", "subtype": "person",
                "name": "A", "domain": [],
            }),
        ]
        report = validate_vault_notes(notes)
        self.assertIn("(none)", report.per_domain)
