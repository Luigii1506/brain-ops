from __future__ import annotations

from unittest import TestCase

from brain_ops.domains.knowledge.schema_validator import (
    SchemaViolation,
    ValidationReport,
    recommended_fields_for,
    required_fields_for,
    typed_relations_for,
    validate_note,
    validate_vault_notes,
)


class RequiredFieldsTestCase(TestCase):
    def test_universal_required_present(self) -> None:
        req = required_fields_for("person")
        for f in ("type", "object_kind", "subtype", "name"):
            self.assertIn(f, req)

    def test_person_specific(self) -> None:
        req = required_fields_for("person")
        for f in ("domain", "era", "born", "died", "occupation", "nationality"):
            self.assertIn(f, req)

    def test_historical_period_required(self) -> None:
        req = required_fields_for("historical_period")
        for f in ("domain", "start_date", "end_date", "region"):
            self.assertIn(f, req)

    def test_esoteric_tradition_required(self) -> None:
        req = required_fields_for("esoteric_tradition")
        for f in ("domain", "origin", "epistemic_mode"):
            self.assertIn(f, req)

    def test_unknown_subtype_has_only_universal(self) -> None:
        req = required_fields_for("bogus_subtype")
        self.assertEqual(req, {"type", "object_kind", "subtype", "name"})

    def test_none_subtype(self) -> None:
        req = required_fields_for(None)
        self.assertEqual(req, {"type", "object_kind", "subtype", "name"})


class RecommendedFieldsTestCase(TestCase):
    def test_person_recommended(self) -> None:
        rec = recommended_fields_for("person")
        self.assertIn("tags", rec)
        self.assertIn("status", rec)

    def test_unknown_is_empty(self) -> None:
        self.assertEqual(recommended_fields_for("bogus"), set())


class TypedRelationsTestCase(TestCase):
    def test_person(self) -> None:
        rels = typed_relations_for("person")
        for r in ("influenced_by", "studied_under", "mentor_of", "contemporary_of"):
            self.assertIn(r, rels)

    def test_historical_period(self) -> None:
        rels = typed_relations_for("historical_period")
        for r in ("preceded_by", "followed", "contains",
                  "emerged_from", "transformed_into"):
            self.assertIn(r, rels)

    def test_deity(self) -> None:
        rels = typed_relations_for("deity")
        for r in ("worshipped_by", "associated_with", "symbolizes", "appears_in"):
            self.assertIn(r, rels)


class ValidateNoteTestCase(TestCase):
    def test_complete_person_has_no_required_violations(self) -> None:
        fm = {
            "type": "person",
            "object_kind": "entity",
            "subtype": "person",
            "name": "Platón",
            "domain": "filosofia",
            "era": "Antigüedad clásica",
            "born": "428 a.C.",
            "died": "347 a.C.",
            "occupation": "Filósofo",
            "nationality": "Griego",
        }
        violations = validate_note("x.md", "Platón", fm)
        errors = [v for v in violations if v.severity == "error"]
        warnings = [v for v in violations if v.severity == "warning"]
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_missing_required_warning_for_existing(self) -> None:
        fm = {
            "type": "person",
            "object_kind": "entity",
            "subtype": "person",
            "name": "X",
        }
        violations = validate_note("x.md", "X", fm, new_note=False)
        severities = {v.severity for v in violations}
        self.assertIn("warning", severities)
        self.assertNotIn("error", severities)

    def test_gated_domain_escalates_to_error_for_new(self) -> None:
        fm = {
            "type": "concept",
            "object_kind": "concept",
            "subtype": "scientific_concept",
            "name": "X",
            "domain": "ciencia",  # gated
            # epistemic_mode intentionally missing
        }
        violations = validate_note(
            "x.md", "X", fm,
            new_note=True,
            gated_domains={"ciencia", "religion", "filosofia", "esoterismo"},
        )
        errors = [v for v in violations if v.severity == "error"]
        # at least one required field ("field" and "epistemic_mode") should be error
        self.assertGreater(len(errors), 0)
        fields = {v.field for v in errors}
        self.assertIn("epistemic_mode", fields)

    def test_ungated_domain_stays_warning_even_for_new(self) -> None:
        fm = {
            "type": "person",
            "object_kind": "entity",
            "subtype": "person",
            "name": "X",
            "domain": "historia",  # not gated
        }
        violations = validate_note(
            "x.md", "X", fm,
            new_note=True,
            gated_domains={"ciencia", "religion", "filosofia", "esoterismo"},
        )
        errors = [v for v in violations if v.severity == "error"]
        self.assertEqual(errors, [])

    def test_recommended_missing_is_info(self) -> None:
        fm = {
            "type": "person",
            "object_kind": "entity",
            "subtype": "person",
            "name": "X",
            "domain": "historia",
            "era": "X",
            "born": "X",
            "died": "X",
            "occupation": "X",
            "nationality": "X",
            # tags/status missing → info
        }
        violations = validate_note("x.md", "X", fm)
        infos = [v for v in violations if v.severity == "info"]
        self.assertGreater(len(infos), 0)

    def test_empty_list_is_missing(self) -> None:
        fm = {
            "type": "war",
            "object_kind": "event",
            "subtype": "war",
            "name": "X",
            "domain": "historia",
            "participants": [],  # empty list counts as missing
        }
        violations = validate_note("x.md", "X", fm)
        fields = {v.field for v in violations}
        self.assertIn("participants", fields)


class ValidateVaultNotesTestCase(TestCase):
    def test_aggregated_report(self) -> None:
        notes = [
            ("a.md", "A", {
                "type": "person", "object_kind": "entity",
                "subtype": "person", "name": "A",
                "domain": "historia", "era": "X",
                "born": "X", "died": "X",
                "occupation": "X", "nationality": "X",
                "tags": ["x"], "status": "canonical", "tradition": "X",
            }),
            ("b.md", "B", {
                "type": "person", "object_kind": "entity",
                "subtype": "person", "name": "B",
                # missing most required fields
            }),
        ]
        report = validate_vault_notes(notes)
        self.assertEqual(report.total_notes, 2)
        self.assertIn("person", report.per_subtype)
        self.assertEqual(report.per_subtype["person"]["total"], 2)
        # Only B has violations (A is fully complete)
        self.assertEqual(report.per_subtype["person"]["violations"], 1)
        self.assertGreater(report.warning_count, 0)

    def test_report_serialization(self) -> None:
        notes = [("a.md", "A", {
            "type": "person", "object_kind": "entity",
            "subtype": "person", "name": "A",
        })]
        report = validate_vault_notes(notes)
        data = report.to_dict()
        self.assertIn("total_notes", data)
        self.assertIn("violations", data)
        self.assertIsInstance(data["violations"], list)
