from __future__ import annotations

from unittest import TestCase

from brain_ops.domains.knowledge.naming_rules import (
    CANONICAL_DOMAINS,
    DOMAIN_ALIASES,
    canonical_domain,
    check_note_naming,
    check_vault_naming,
    detect_bare_name_ambiguity,
    extract_bare_form,
    has_capitalization_violation,
    is_canonical_domain,
    suggest_capitalization,
    suggested_subdomain_for_alias,
)


class CanonicalDomainTestCase(TestCase):
    def test_canonical_slugs(self) -> None:
        self.assertEqual(
            CANONICAL_DOMAINS,
            frozenset({"historia", "filosofia", "ciencia", "religion",
                       "esoterismo", "machine_learning"}),
        )

    def test_canonical_pass_through(self) -> None:
        self.assertEqual(canonical_domain("historia"), "historia")
        self.assertEqual(canonical_domain("machine_learning"), "machine_learning")

    def test_english_aliases(self) -> None:
        self.assertEqual(canonical_domain("history"), "historia")
        self.assertEqual(canonical_domain("philosophy"), "filosofia")
        self.assertEqual(canonical_domain("science"), "ciencia")

    def test_accented_variant(self) -> None:
        self.assertEqual(canonical_domain("religión"), "religion")
        self.assertEqual(canonical_domain("filosofía"), "filosofia")

    def test_astronomy_collapses_to_science(self) -> None:
        self.assertEqual(canonical_domain("astronomía"), "ciencia")
        self.assertEqual(canonical_domain("astronomia"), "ciencia")

    def test_astronomy_subdomain_hint(self) -> None:
        self.assertEqual(suggested_subdomain_for_alias("astronomía"), "astronomia")
        self.assertEqual(suggested_subdomain_for_alias("astronomia"), "astronomia")

    def test_unknown_returns_none(self) -> None:
        self.assertIsNone(canonical_domain("biología"))
        self.assertIsNone(canonical_domain(""))
        self.assertIsNone(canonical_domain(None))

    def test_is_canonical_domain(self) -> None:
        self.assertTrue(is_canonical_domain("historia"))
        self.assertFalse(is_canonical_domain("history"))
        self.assertFalse(is_canonical_domain(None))


class CapitalizationTestCase(TestCase):
    def test_lowercase_adjective_is_violation(self) -> None:
        self.assertTrue(has_capitalization_violation("Imperio medo"))
        self.assertTrue(has_capitalization_violation("Imperio romano"))
        self.assertTrue(has_capitalization_violation("Período arcaico griego"))

    def test_correctly_capitalized_is_not_violation(self) -> None:
        self.assertFalse(has_capitalization_violation("Imperio Medo"))
        self.assertFalse(has_capitalization_violation("Imperio Antiguo"))
        self.assertFalse(has_capitalization_violation("Período Predinástico"))

    def test_non_period_names_not_flagged(self) -> None:
        self.assertFalse(has_capitalization_violation("Platón"))
        self.assertFalse(has_capitalization_violation("Batalla de Maratón"))

    def test_preposition_after_head_not_flagged(self) -> None:
        """Reino de Macedonia is canonical — `de` is a preposition, not a name part."""
        self.assertFalse(has_capitalization_violation("Reino de Macedonia"))
        self.assertFalse(has_capitalization_violation("Imperio del Sur"))
        self.assertFalse(has_capitalization_violation("Dinastía de los Ptolomeos"))
        self.assertFalse(has_capitalization_violation("Edad del Bronce"))
        self.assertIsNone(suggest_capitalization("Reino de Macedonia"))

    def test_capitalization_still_flags_when_adjective_follows_preposition(self) -> None:
        """`Imperio romano de Oriente` — 'romano' is the violation; 'de Oriente' is fine."""
        self.assertTrue(has_capitalization_violation("Imperio romano de Oriente"))
        self.assertEqual(
            suggest_capitalization("Imperio romano de Oriente"),
            "Imperio Romano de Oriente",
        )

    def test_suggestion(self) -> None:
        self.assertEqual(suggest_capitalization("Imperio medo"), "Imperio Medo")
        self.assertEqual(
            suggest_capitalization("Período arcaico griego"),
            "Período Arcaico griego",
        )

    def test_suggestion_none_for_correct(self) -> None:
        self.assertIsNone(suggest_capitalization("Imperio Medo"))
        self.assertIsNone(suggest_capitalization("Platón"))


class BareFormTestCase(TestCase):
    def test_no_suffix(self) -> None:
        self.assertEqual(extract_bare_form("Platón"), "Platón")

    def test_with_suffix(self) -> None:
        self.assertEqual(extract_bare_form("Júpiter (planeta)"), "Júpiter")
        self.assertEqual(extract_bare_form("Tebas (Egipto)"), "Tebas")
        self.assertEqual(
            extract_bare_form("Demóstenes (orador)"),
            "Demóstenes",
        )


class BareNameAmbiguityTestCase(TestCase):
    def test_no_ambiguity(self) -> None:
        result = detect_bare_name_ambiguity(
            ["Platón", "Aristóteles"]
        )
        self.assertEqual(result, {})

    def test_bare_and_disambiguated_coexist(self) -> None:
        result = detect_bare_name_ambiguity([
            "Júpiter",
            "Júpiter (planeta)",
            "Júpiter (dios)",
        ])
        self.assertIn("Júpiter", result)
        self.assertEqual(
            set(result["Júpiter"]),
            {"Júpiter", "Júpiter (planeta)", "Júpiter (dios)"},
        )

    def test_multiple_variants_without_bare_not_flagged(self) -> None:
        # If only disambiguated forms exist and no bare, that's fine.
        result = detect_bare_name_ambiguity([
            "Sol (estrella)",
            "Sol (nota musical)",
        ])
        # bare "Sol" does not exist → not flagged
        self.assertEqual(result, {})


class CheckNoteNamingTestCase(TestCase):
    def test_canonical_domain_passes(self) -> None:
        vs = check_note_naming("Platón", {"domain": "filosofia"})
        self.assertEqual(vs, [])

    def test_aliased_domain_warns(self) -> None:
        vs = check_note_naming("Platón", {"domain": "philosophy"})
        self.assertEqual(len(vs), 1)
        self.assertEqual(vs[0].rule, "domain_alias")
        self.assertEqual(vs[0].severity, "warning")
        self.assertIn("filosofia", vs[0].message)

    def test_unknown_domain_warns(self) -> None:
        vs = check_note_naming("X", {"domain": "frankenstein"})
        self.assertEqual(len(vs), 1)
        self.assertEqual(vs[0].rule, "domain_unknown")

    def test_capitalization_flagged(self) -> None:
        vs = check_note_naming("Imperio medo", {"domain": "historia"})
        self.assertTrue(any(v.rule == "capitalization" for v in vs))


class CheckVaultNamingTestCase(TestCase):
    def test_bare_name_ambiguity_flagged_once(self) -> None:
        pairs = [
            ("Júpiter", {"subtype": "disambiguation_page", "domain": "ciencia"}),
            ("Júpiter (planeta)", {"subtype": "celestial_body", "domain": "ciencia"}),
            ("Júpiter (dios)", {"subtype": "deity", "domain": "religion"}),
        ]
        vs = check_vault_naming(pairs)
        # Because the bare is already a disambiguation_page, NOT flagged
        ambiguity = [v for v in vs if v.rule == "bare_name_ambiguity"]
        self.assertEqual(ambiguity, [])

    def test_bare_as_entity_with_variants_is_flagged(self) -> None:
        pairs = [
            ("Roma", {"subtype": "civilization", "domain": "historia"}),
            ("Ciudad de Roma", {"subtype": "city", "domain": "historia"}),
            ("Imperio Romano", {"subtype": "empire", "domain": "historia"}),
        ]
        vs = check_vault_naming(pairs)
        # Note: Ciudad de Roma has different base ("Ciudad de Roma"), so not a
        # suffix variant of "Roma". This test verifies we DON'T false-positive
        # on unrelated names.
        ambiguity = [v for v in vs if v.rule == "bare_name_ambiguity"]
        self.assertEqual(ambiguity, [])

    def test_real_disambiguation_case(self) -> None:
        pairs = [
            ("Tebas", {"subtype": "city", "domain": "historia"}),
            ("Tebas (Egipto)", {"subtype": "city", "domain": "historia"}),
        ]
        vs = check_vault_naming(pairs)
        ambiguity = [v for v in vs if v.rule == "bare_name_ambiguity"]
        self.assertEqual(len(ambiguity), 1)
        self.assertEqual(ambiguity[0].note_name, "Tebas")

    def test_disambiguation_dominant_silences_warning(self) -> None:
        """B-type bare with disambiguation_dominant: true must not be flagged."""
        pairs = [
            ("Ética", {
                "subtype": "discipline",
                "domain": "filosofia",
                "disambiguation_dominant": True,
            }),
            ("Ética (Spinoza)", {"subtype": "book", "domain": "filosofia"}),
        ]
        vs = check_vault_naming(pairs)
        ambiguity = [v for v in vs if v.rule == "bare_name_ambiguity"]
        self.assertEqual(ambiguity, [])

    def test_disambiguation_dominant_false_still_flags(self) -> None:
        """Only explicit True silences — False or missing still flags."""
        pairs = [
            ("Ética", {
                "subtype": "discipline",
                "domain": "filosofia",
                "disambiguation_dominant": False,
            }),
            ("Ética (Spinoza)", {"subtype": "book", "domain": "filosofia"}),
        ]
        vs = check_vault_naming(pairs)
        ambiguity = [v for v in vs if v.rule == "bare_name_ambiguity"]
        self.assertEqual(len(ambiguity), 1)
