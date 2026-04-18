"""Tests for Paso 3 — the 6 typed-relation linter rules.

Rules per RELATIONS_FORMAT.md §10:

    relation_predicate_unknown         error       predicate not in CANONICAL_PREDICATES
    relation_object_missing            warning     object is not a known entity
    relation_object_is_disambig_page   warning     object is a disambiguation_page
    relation_duplicate                 info        (predicate, object) twice in same note
    relation_body_divergent            info        body section ≠ frontmatter
    relation_self                      warning     subject == object
"""

from __future__ import annotations

from unittest import TestCase

from brain_ops.domains.knowledge.schema_validator import (
    validate_body_relations_divergence,
    validate_note,
    validate_vault_notes,
)


def _mk_note(name: str, **fm_extras) -> dict[str, object]:
    base: dict[str, object] = {
        "name": name,
        "entity": True,
        "type": fm_extras.pop("type", "person"),
        "subtype": fm_extras.pop("subtype", "person"),
        "object_kind": fm_extras.pop("object_kind", "entity"),
        "domain": fm_extras.pop("domain", "filosofia"),
    }
    base.update(fm_extras)
    return base


def _rel_violations(violations: list, rule: str) -> list:
    return [v for v in violations if v.field == rule]


# ---------------------------------------------------------------------------
# R1 — relation_predicate_unknown (error)
# ---------------------------------------------------------------------------
class PredicateUnknownRuleTestCase(TestCase):
    def test_unknown_predicate_produces_error(self) -> None:
        fm = _mk_note("Aristóteles", relationships=[
            {"predicate": "makes_burritos_with", "object": "Platón"},
        ])
        vs = validate_note("x.md", "Aristóteles", fm)
        errors = _rel_violations(vs, "relation_unknown_predicate")
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].severity, "error")
        self.assertIn("makes_burritos_with", errors[0].message)

    def test_valid_predicate_produces_no_error(self) -> None:
        fm = _mk_note("Aristóteles", relationships=[
            {"predicate": "studied_under", "object": "Platón"},
        ])
        vs = validate_note("x.md", "Aristóteles", fm)
        self.assertEqual(_rel_violations(vs, "relation_unknown_predicate"), [])

    def test_missing_predicate_field_produces_warning(self) -> None:
        fm = _mk_note("Aristóteles", relationships=[
            {"object": "Platón"},  # no predicate key
        ])
        vs = validate_note("x.md", "Aristóteles", fm)
        errs = _rel_violations(vs, "relation_missing_field")
        self.assertEqual(len(errs), 1)
        self.assertEqual(errs[0].severity, "warning")


# ---------------------------------------------------------------------------
# R2 — relation_duplicate (info)
# ---------------------------------------------------------------------------
class DuplicateRuleTestCase(TestCase):
    def test_exact_duplicate_is_info(self) -> None:
        fm = _mk_note("Aristóteles", relationships=[
            {"predicate": "studied_under", "object": "Platón"},
            {"predicate": "studied_under", "object": "Platón"},
        ])
        vs = validate_note("x.md", "Aristóteles", fm)
        dups = _rel_violations(vs, "relation_duplicate")
        self.assertEqual(len(dups), 1)
        self.assertEqual(dups[0].severity, "info")

    def test_different_predicates_same_object_not_duplicate(self) -> None:
        fm = _mk_note("Augusto", relationships=[
            {"predicate": "allied_with", "object": "Marco Antonio"},
            {"predicate": "opposed", "object": "Marco Antonio"},
        ])
        vs = validate_note("x.md", "Augusto", fm)
        self.assertEqual(_rel_violations(vs, "relation_duplicate"), [])


# ---------------------------------------------------------------------------
# R3 — relation_self (warning)
# ---------------------------------------------------------------------------
class SelfReferenceRuleTestCase(TestCase):
    def test_self_reference_is_warning(self) -> None:
        fm = _mk_note("Aristóteles", relationships=[
            {"predicate": "influenced", "object": "Aristóteles"},
        ])
        vs = validate_note("x.md", "Aristóteles", fm)
        selfs = _rel_violations(vs, "relation_self")
        self.assertEqual(len(selfs), 1)
        self.assertEqual(selfs[0].severity, "warning")
        self.assertIn("influenced", selfs[0].message)

    def test_non_self_no_warning(self) -> None:
        fm = _mk_note("Aristóteles", relationships=[
            {"predicate": "influenced", "object": "Tomás de Aquino"},
        ])
        vs = validate_note("x.md", "Aristóteles", fm)
        self.assertEqual(_rel_violations(vs, "relation_self"), [])


# ---------------------------------------------------------------------------
# R4 — relation_object_missing (warning) — requires entity_index
# ---------------------------------------------------------------------------
class ObjectMissingRuleTestCase(TestCase):
    def test_object_not_in_vault_is_warning(self) -> None:
        fm = _mk_note("Aristóteles", relationships=[
            {"predicate": "studied_under", "object": "NoExiste"},
        ])
        vs = validate_note(
            "x.md", "Aristóteles", fm,
            entity_index={"Aristóteles": "person"},  # object not in index
        )
        warns = _rel_violations(vs, "relation_object_missing")
        self.assertEqual(len(warns), 1)
        self.assertEqual(warns[0].severity, "warning")

    def test_object_in_vault_is_clean(self) -> None:
        fm = _mk_note("Aristóteles", relationships=[
            {"predicate": "studied_under", "object": "Platón"},
        ])
        vs = validate_note(
            "x.md", "Aristóteles", fm,
            entity_index={"Aristóteles": "person", "Platón": "person"},
        )
        self.assertEqual(_rel_violations(vs, "relation_object_missing"), [])

    def test_no_entity_index_skips_cross_check(self) -> None:
        """Without entity_index, only local rules run — object_missing skipped."""
        fm = _mk_note("Aristóteles", relationships=[
            {"predicate": "studied_under", "object": "NoExiste"},
        ])
        vs = validate_note("x.md", "Aristóteles", fm)  # no entity_index
        self.assertEqual(_rel_violations(vs, "relation_object_missing"), [])


# ---------------------------------------------------------------------------
# R5 — relation_object_is_disambig_page (warning)
# ---------------------------------------------------------------------------
class ObjectIsDisambigPageRuleTestCase(TestCase):
    def test_pointing_to_disambig_is_warning(self) -> None:
        fm = _mk_note("X", relationships=[
            {"predicate": "located_in", "object": "Tebas"},  # disambig_page
        ])
        vs = validate_note(
            "x.md", "X", fm,
            entity_index={
                "X": "person",
                "Tebas": "disambiguation_page",
                "Tebas (Grecia)": "city",
                "Tebas (Egipto)": "city",
            },
        )
        warns = _rel_violations(vs, "relation_object_is_disambig_page")
        self.assertEqual(len(warns), 1)
        self.assertEqual(warns[0].severity, "warning")
        self.assertIn("Tebas", warns[0].message)
        self.assertIn("variant", warns[0].message)

    def test_pointing_to_specific_variant_is_clean(self) -> None:
        fm = _mk_note("X", relationships=[
            {"predicate": "located_in", "object": "Tebas (Grecia)"},
        ])
        vs = validate_note(
            "x.md", "X", fm,
            entity_index={"X": "person", "Tebas (Grecia)": "city"},
        )
        self.assertEqual(_rel_violations(vs, "relation_object_is_disambig_page"), [])


# ---------------------------------------------------------------------------
# R6 — relation_body_divergent (info) — separate entry point
# ---------------------------------------------------------------------------
class BodyDivergentRuleTestCase(TestCase):
    def test_body_extra_wikilink_is_info(self) -> None:
        fm = _mk_note("Aristóteles", relationships=[
            {"predicate": "studied_under", "object": "Platón"},
        ])
        body = """## Identity

Filósofo griego.

## Relationships

- `studied_under` **[[Platón]]** — Alumno en la Academia.
- `mentor_of` **[[Alejandro Magno]]** — Tutor real.
"""
        vs = validate_body_relations_divergence("x.md", "Aristóteles", fm, body)
        divs = _rel_violations(vs, "relation_body_divergent")
        # Body has Alejandro Magno extra
        self.assertEqual(len(divs), 1)
        self.assertEqual(divs[0].severity, "info")
        self.assertIn("Alejandro Magno", divs[0].message)

    def test_frontmatter_extra_is_info(self) -> None:
        fm = _mk_note("Aristóteles", relationships=[
            {"predicate": "studied_under", "object": "Platón"},
            {"predicate": "author_of", "object": "Ética a Nicómaco"},
        ])
        body = """## Relationships

- `studied_under` **[[Platón]]** — Alumno en la Academia.
"""
        vs = validate_body_relations_divergence("x.md", "Aristóteles", fm, body)
        divs = _rel_violations(vs, "relation_body_divergent")
        # Frontmatter has Ética a Nicómaco, body doesn't
        self.assertEqual(len(divs), 1)
        self.assertIn("Ética a Nicómaco", divs[0].message)

    def test_body_without_section_is_clean(self) -> None:
        """If the body has no `## Relationships` section, no divergence check."""
        fm = _mk_note("Aristóteles", relationships=[
            {"predicate": "studied_under", "object": "Platón"},
        ])
        body = "## Identity\n\nFilósofo.\n"
        vs = validate_body_relations_divergence("x.md", "Aristóteles", fm, body)
        self.assertEqual(vs, [])

    def test_aligned_body_and_frontmatter_clean(self) -> None:
        fm = _mk_note("Aristóteles", relationships=[
            {"predicate": "studied_under", "object": "Platón"},
        ])
        body = """## Relationships

- `studied_under` **[[Platón]]** — Alumno.
"""
        vs = validate_body_relations_divergence("x.md", "Aristóteles", fm, body)
        self.assertEqual(vs, [])


# ---------------------------------------------------------------------------
# Aggregate — validate_vault_notes builds the entity_index correctly
# ---------------------------------------------------------------------------
class ValidateVaultIntegrationTestCase(TestCase):
    def test_vault_level_builds_index_and_detects_missing(self) -> None:
        notes = [
            ("a.md", "Aristóteles", _mk_note(
                "Aristóteles",
                relationships=[
                    {"predicate": "studied_under", "object": "Platón"},
                    {"predicate": "mentor_of", "object": "PersonaFantasma"},
                ],
                era="X", born="X", died="X", occupation="X", nationality="X",
                tags=["x"], status="canonical", tradition="X",
            )),
            ("b.md", "Platón", _mk_note(
                "Platón",
                relationships=[
                    {"predicate": "mentor_of", "object": "Aristóteles"},
                ],
                era="X", born="X", died="X", occupation="X", nationality="X",
                tags=["x"], status="canonical", tradition="X",
            )),
        ]
        report = validate_vault_notes(notes)
        vs = _rel_violations(report.violations, "relation_object_missing")
        self.assertEqual(len(vs), 1)
        self.assertIn("PersonaFantasma", vs[0].message)

    def test_vault_disambig_page_detected_cross_note(self) -> None:
        notes = [
            ("a.md", "X", _mk_note(
                "X", relationships=[{"predicate": "located_in", "object": "Tebas"}],
                era="X", born="X", died="X", occupation="X", nationality="X",
                tags=["x"], status="canonical", tradition="X",
            )),
            ("b.md", "Tebas", _mk_note(
                "Tebas", subtype="disambiguation_page", object_kind="disambiguation",
                type="disambiguation",
            )),
            ("c.md", "Tebas (Grecia)", _mk_note(
                "Tebas (Grecia)", type="city", subtype="city",
                object_kind="place", domain="historia",
            )),
        ]
        report = validate_vault_notes(notes)
        vs = _rel_violations(report.violations, "relation_object_is_disambig_page")
        self.assertEqual(len(vs), 1)
        self.assertIn("Tebas", vs[0].message)


# ---------------------------------------------------------------------------
# Silent-on-empty tests — the linter MUST NOT produce false positives on the
# vast majority of the current vault (which has NO `relationships:` anywhere).
# ---------------------------------------------------------------------------
class NoNoiseOnBaselineTestCase(TestCase):
    def test_note_without_relationships_produces_no_rel_violations(self) -> None:
        fm = _mk_note(
            "Cualquiera",
            era="X", born="X", died="X", occupation="X", nationality="X",
            tags=["x"], status="canonical", tradition="X",
            related=["Platón", "Sócrates"],  # legacy
        )
        vs = validate_note("x.md", "Cualquiera", fm, entity_index={"Cualquiera": "person"})
        rel_rules = {"relation_unknown_predicate", "relation_duplicate",
                     "relation_self", "relation_object_missing",
                     "relation_object_is_disambig_page", "relation_missing_field",
                     "relation_invalid_shape"}
        rel_flags = [v for v in vs if v.field in rel_rules]
        self.assertEqual(rel_flags, [])

    def test_empty_relationships_list_produces_no_rel_violations(self) -> None:
        fm = _mk_note(
            "X", relationships=[],
            era="X", born="X", died="X", occupation="X", nationality="X",
            tags=["x"], status="canonical", tradition="X",
        )
        vs = validate_note("x.md", "X", fm, entity_index={"X": "person"})
        rel_rules = {"relation_unknown_predicate", "relation_duplicate",
                     "relation_self", "relation_object_missing",
                     "relation_object_is_disambig_page"}
        rel_flags = [v for v in vs if v.field in rel_rules]
        self.assertEqual(rel_flags, [])
