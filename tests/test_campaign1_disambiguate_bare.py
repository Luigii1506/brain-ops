"""Subfase 1.5 — disambiguate_bare tests.

Verifies plan + apply for converting a bare-name entity into a
disambiguation_page, renaming the original with a discriminator, and
updating incoming wikilinks (body) and related entries (frontmatter).
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from brain_ops.domains.knowledge.consolidation import (
    apply_disambiguate_bare,
    plan_disambiguate_bare,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _bare_tebas(vault: Path) -> None:
    """Write a Tebas (Greek) entity note."""
    _write(vault / "02 - Knowledge" / "Tebas.md", """---
type: city
object_kind: place
subtype: city
name: Tebas
entity: true
status: canonical
domain: historia
subdomain: grecia
related:
- Esparta
- Atenas
- Epaminondas
---

## Identity

**Tebas** fue la principal polis de Beocia.

## Related notes

- [[Esparta]]
""")


def _variant_tebas_egipto(vault: Path) -> None:
    _write(vault / "02 - Knowledge" / "Tebas (Egipto).md", """---
type: city
object_kind: place
subtype: city
name: Tebas (Egipto)
entity: true
status: canonical
domain: historia
subdomain: egipto
---

## Identity

Tebas egipcia, capital del Imperio Nuevo.
""")


def _referencing_note(vault: Path, name: str, body_wikilink_form: str) -> None:
    """Write a note that references Tebas via wikilink and related list."""
    _write(vault / "02 - Knowledge" / f"{name}.md", f"""---
type: person
object_kind: entity
subtype: person
name: {name}
entity: true
status: canonical
domain: historia
related:
- Tebas
- Atenas
---

## Identity

Nota sobre {name} que menciona {body_wikilink_form} en el cuerpo.
""")


class PlanDisambiguateBareTestCase(TestCase):
    def test_plan_finds_bare_and_variants(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _bare_tebas(vault)
            _variant_tebas_egipto(vault)

            report = plan_disambiguate_bare(vault, "Tebas", "Grecia")

            self.assertTrue(report.can_apply)
            self.assertEqual(report.new_canonical_name, "Tebas (Grecia)")
            self.assertIn("Tebas (Grecia)", report.existing_variants)
            self.assertIn("Tebas (Egipto)", report.existing_variants)

    def test_plan_counts_body_wikilinks(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _bare_tebas(vault)
            _referencing_note(vault, "Epaminondas", "[[Tebas]]")

            report = plan_disambiguate_bare(vault, "Tebas", "Grecia")
            self.assertEqual(report.body_wikilink_mentions, 1)
            self.assertEqual(len(report.body_wikilink_files), 1)

    def test_plan_handles_aliased_wikilinks(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _bare_tebas(vault)
            _referencing_note(vault, "Ref", "[[Tebas|la ciudad]]")

            report = plan_disambiguate_bare(vault, "Tebas", "Grecia")
            self.assertEqual(report.body_wikilink_mentions, 1)

    def test_plan_excludes_already_disambiguated(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _bare_tebas(vault)
            _variant_tebas_egipto(vault)
            # A note mentions the Egyptian variant — must NOT be counted
            _write(vault / "02 - Knowledge" / "Ref.md", """---
name: Ref
entity: true
---

Body mentions [[Tebas (Egipto)]] but not bare Tebas.
""")

            report = plan_disambiguate_bare(vault, "Tebas", "Grecia")
            self.assertEqual(report.body_wikilink_mentions, 0)

    def test_plan_detects_related_entries(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _bare_tebas(vault)
            _referencing_note(vault, "Epaminondas", "[[Tebas]]")

            report = plan_disambiguate_bare(vault, "Tebas", "Grecia")
            self.assertEqual(len(report.related_entries), 1)

    def test_plan_rejects_when_bare_missing(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            (vault / "02 - Knowledge").mkdir(parents=True)
            report = plan_disambiguate_bare(vault, "Nonexistent", "X")
            self.assertFalse(report.can_apply)
            self.assertIn("not found", report.error_message)

    def test_plan_rejects_when_already_disambig(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _write(vault / "02 - Knowledge" / "Roma.md", """---
name: Roma
subtype: disambiguation_page
entity: false
---

disambig body
""")
            report = plan_disambiguate_bare(vault, "Roma", "Ciudad")
            self.assertFalse(report.can_apply)
            self.assertIn("already a disambiguation_page", report.error_message)

    def test_plan_rejects_when_target_exists(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _bare_tebas(vault)
            # Target name already taken
            _write(vault / "02 - Knowledge" / "Tebas (Grecia).md", """---
name: Tebas (Grecia)
---
""")
            report = plan_disambiguate_bare(vault, "Tebas", "Grecia")
            self.assertFalse(report.can_apply)
            self.assertIn("already exists", report.error_message)

    def test_disambig_page_preview_lists_all_variants(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _bare_tebas(vault)
            _variant_tebas_egipto(vault)

            report = plan_disambiguate_bare(vault, "Tebas", "Grecia")
            preview = report.disambig_page_preview
            self.assertIn("[[Tebas (Grecia)]]", preview)
            self.assertIn("[[Tebas (Egipto)]]", preview)
            self.assertIn("disambiguation_page", preview)


class ApplyDisambiguateBareTestCase(TestCase):
    def test_apply_renames_bare_file(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _bare_tebas(vault)
            _variant_tebas_egipto(vault)

            report = plan_disambiguate_bare(vault, "Tebas", "Grecia")
            result = apply_disambiguate_bare(vault, report)

            self.assertTrue(result["applied"])
            # Renamed file exists
            self.assertTrue((vault / "02 - Knowledge" / "Tebas (Grecia).md").exists())
            # Bare is now the disambig page (different content)
            bare_content = (vault / "02 - Knowledge" / "Tebas.md").read_text()
            self.assertIn("disambiguation_page", bare_content)

    def test_apply_adds_frontmatter_metadata_to_renamed(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _bare_tebas(vault)

            report = plan_disambiguate_bare(vault, "Tebas", "Grecia")
            apply_disambiguate_bare(vault, report)

            renamed = (vault / "02 - Knowledge" / "Tebas (Grecia).md").read_text()
            self.assertIn("name: Tebas (Grecia)", renamed)
            self.assertIn("base_name: Tebas", renamed)
            self.assertIn("- Tebas", renamed)  # in aliases

    def test_apply_updates_body_wikilinks_preserving_display_text(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _bare_tebas(vault)
            _referencing_note(vault, "Epaminondas", "[[Tebas]]")

            report = plan_disambiguate_bare(vault, "Tebas", "Grecia")
            apply_disambiguate_bare(vault, report)

            ref = (vault / "02 - Knowledge" / "Epaminondas.md").read_text()
            # [[Tebas]] must become [[Tebas (Grecia)|Tebas]] so display stays "Tebas"
            self.assertIn("[[Tebas (Grecia)|Tebas]]", ref)
            self.assertNotIn("[[Tebas]] en el cuerpo", ref)

    def test_apply_updates_aliased_wikilinks(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _bare_tebas(vault)
            _referencing_note(vault, "Epaminondas", "[[Tebas|la ciudad]]")

            report = plan_disambiguate_bare(vault, "Tebas", "Grecia")
            apply_disambiguate_bare(vault, report)

            ref = (vault / "02 - Knowledge" / "Epaminondas.md").read_text()
            self.assertIn("[[Tebas (Grecia)|la ciudad]]", ref)
            self.assertNotIn("[[Tebas|la ciudad]]", ref)

    def test_apply_updates_related_entries(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _bare_tebas(vault)
            _referencing_note(vault, "Epaminondas", "nothing in body")

            report = plan_disambiguate_bare(vault, "Tebas", "Grecia")
            apply_disambiguate_bare(vault, report)

            ref = (vault / "02 - Knowledge" / "Epaminondas.md").read_text()
            # The related: - Tebas line should become - Tebas (Grecia)
            self.assertIn("- Tebas (Grecia)", ref)
            # Tebas as a bare list item should no longer match (Atenas stays)
            self.assertIn("- Atenas", ref)

    def test_apply_does_not_touch_variant_mentions(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _bare_tebas(vault)
            _variant_tebas_egipto(vault)
            _write(vault / "02 - Knowledge" / "Ref.md", """---
name: Ref
entity: true
---

Body has [[Tebas (Egipto)]] which must NOT be rewritten.
""")
            pre = (vault / "02 - Knowledge" / "Ref.md").read_bytes()
            report = plan_disambiguate_bare(vault, "Tebas", "Grecia")
            apply_disambiguate_bare(vault, report)
            post = (vault / "02 - Knowledge" / "Ref.md").read_bytes()
            self.assertEqual(pre, post, "Variant [[Tebas (Egipto)]] must not be touched")

    def test_apply_creates_disambig_page_with_variants(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _bare_tebas(vault)
            _variant_tebas_egipto(vault)

            report = plan_disambiguate_bare(vault, "Tebas", "Grecia")
            apply_disambiguate_bare(vault, report)

            disambig = (vault / "02 - Knowledge" / "Tebas.md").read_text()
            self.assertIn("subtype: disambiguation_page", disambig)
            self.assertIn("[[Tebas (Grecia)]]", disambig)
            self.assertIn("[[Tebas (Egipto)]]", disambig)

    def test_apply_idempotent_second_run_is_noop(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _bare_tebas(vault)
            _variant_tebas_egipto(vault)

            report = plan_disambiguate_bare(vault, "Tebas", "Grecia")
            apply_disambiguate_bare(vault, report)

            # Second plan should fail — either because bare is now a disambig_page
            # OR because the target file already exists (whichever is checked first).
            second_report = plan_disambiguate_bare(vault, "Tebas", "Grecia")
            self.assertFalse(second_report.can_apply)
            msg = second_report.error_message or ""
            self.assertTrue(
                "already a disambiguation_page" in msg or "already exists" in msg,
                f"Expected idempotency rejection, got: {msg}",
            )

    def test_apply_updates_related_wikilink_string_pattern(self) -> None:
        """Some notes use `- '[[Tebas]]'` (quoted wikilink) in related — must be updated."""
        with TemporaryDirectory() as td:
            vault = Path(td)
            _bare_tebas(vault)
            _write(vault / "02 - Knowledge" / "Batalla.md", """---
name: Batalla
entity: true
related:
- '[[Epaminondas]]'
- '[[Tebas]]'
- "[[Esparta]]"
- '[[Tebas (Egipto)]]'
- Atenas
---

## Identity

Something.
""")
            report = plan_disambiguate_bare(vault, "Tebas", "Grecia")
            # Must detect this file as having a related entry
            self.assertIn("02 - Knowledge/Batalla.md", report.related_entries)

            apply_disambiguate_bare(vault, report)

            ref = (vault / "02 - Knowledge" / "Batalla.md").read_text()
            # Pattern 2 — wikilink-in-string — preserves display "Tebas"
            self.assertIn("- '[[Tebas (Grecia)|Tebas]]'", ref)
            # Not touched: variant in string
            self.assertIn("'[[Tebas (Egipto)]]'", ref)
            # Not touched: unrelated wikilink
            self.assertIn("'[[Epaminondas]]'", ref)
            # Not touched: double-quote variant on other entity
            self.assertIn('"[[Esparta]]"', ref)

    def test_apply_preserves_unrelated_files_byte_exact(self) -> None:
        """Files that don't mention Tebas must remain byte-identical."""
        with TemporaryDirectory() as td:
            vault = Path(td)
            _bare_tebas(vault)
            _variant_tebas_egipto(vault)
            # Unrelated entity
            _write(vault / "02 - Knowledge" / "Sócrates.md", """---
name: Sócrates
entity: true
domain: filosofia
---

## Identity

Filósofo griego. No menciona Tebas.
""")
            pre = (vault / "02 - Knowledge" / "Sócrates.md").read_bytes()
            report = plan_disambiguate_bare(vault, "Tebas", "Grecia")
            apply_disambiguate_bare(vault, report)
            post = (vault / "02 - Knowledge" / "Sócrates.md").read_bytes()
            self.assertEqual(pre, post)
