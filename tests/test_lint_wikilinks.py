"""Tests for the wikilink integrity linter."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest import TestCase

from brain_ops.domains.knowledge.lint_wikilinks import (
    build_vault_index,
    fix_nested_in_text,
    fix_nested_wikilinks,
    lint_text,
    lint_vault,
)


class BuildVaultIndexTestCase(TestCase):
    def _make(self, names: list[str]) -> Path:
        tmp = Path(tempfile.mkdtemp())
        kdir = tmp / "02 - Knowledge"
        kdir.mkdir(parents=True)
        for n in names:
            (kdir / f"{n}.md").write_text("---\nentity: true\n---\n", encoding="utf-8")
        return kdir

    def test_canonical_includes_every_stem(self) -> None:
        kdir = self._make(["Sócrates", "Platón", "Meditaciones (Marco Aurelio)"])
        canonical, _ = build_vault_index(kdir)
        self.assertEqual(canonical, {"Sócrates", "Platón", "Meditaciones (Marco Aurelio)"})

    def test_disambiguated_grouped_by_bare(self) -> None:
        kdir = self._make([
            "Meditaciones (Marco Aurelio)",
            "Meditaciones metafísicas",
            "Ética (Spinoza)",
            "Ética",
        ])
        _, bare = build_vault_index(kdir)
        self.assertIn("Meditaciones", bare)
        self.assertEqual(
            sorted(bare["Meditaciones"]),
            ["Meditaciones (Marco Aurelio)"],
        )
        # "Meditaciones metafísicas" has NO " (X)" suffix → not in disambig map
        self.assertEqual(bare["Ética"], ["Ética (Spinoza)"])


class NestedDetectionTestCase(TestCase):
    def test_nested_with_alias_flagged(self) -> None:
        text = "Las [[Meditaciones ([[Marco Aurelio]])|Meditaciones]] influyeron en Descartes."
        n_links, issues = lint_text(text, "test.md", set(), {})
        self.assertEqual(n_links, 1)
        self.assertEqual(len(issues), 1)
        i = issues[0]
        self.assertEqual(i.rule, "nested")
        self.assertEqual(i.target, "Meditaciones (Marco Aurelio)")
        self.assertEqual(i.suggestion, "[[Meditaciones (Marco Aurelio)|Meditaciones]]")

    def test_nested_without_alias_flagged(self) -> None:
        text = "Ver [[Meditaciones ([[Marco Aurelio]])]] para más."
        _, issues = lint_text(text, "test.md", set(), {})
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].rule, "nested")
        self.assertEqual(issues[0].suggestion, "[[Meditaciones (Marco Aurelio)]]")

    def test_clean_disambiguated_link_not_flagged(self) -> None:
        text = "Las [[Meditaciones (Marco Aurelio)|Meditaciones]] son estoicas."
        canonical = {"Meditaciones (Marco Aurelio)"}
        _, issues = lint_text(text, "t.md", canonical, {})
        self.assertEqual(issues, [])


class BrokenAndAmbiguousBareTestCase(TestCase):
    def test_broken_link_flagged(self) -> None:
        text = "Ver [[Inexistente]] para más."
        _, issues = lint_text(text, "t.md", {"Otra"}, {})
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].rule, "broken")
        self.assertEqual(issues[0].target, "Inexistente")

    def test_ambiguous_bare_flagged(self) -> None:
        # Bare "Meditaciones" doesn't exist as canonical, but two
        # disambiguated forms do → ambiguous
        text = "Ver [[Meditaciones]] para contexto."
        canonical = {"Meditaciones (Marco Aurelio)", "Meditaciones metafísicas"}
        bare = {"Meditaciones": ["Meditaciones (Marco Aurelio)", "Meditaciones metafísicas"]}
        _, issues = lint_text(text, "t.md", canonical, bare)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].rule, "ambiguous_bare")
        self.assertIn("Meditaciones (Marco Aurelio)", issues[0].suggestion)
        self.assertIn("Meditaciones metafísicas", issues[0].suggestion)

    def test_disambiguation_page_not_flagged(self) -> None:
        # If the bare-name disambig page exists, [[Meditaciones]] is fine
        text = "Ver [[Meditaciones]] (página de desambiguación)."
        canonical = {"Meditaciones", "Meditaciones (Marco Aurelio)"}
        bare = {"Meditaciones": ["Meditaciones (Marco Aurelio)"]}
        _, issues = lint_text(text, "t.md", canonical, bare)
        self.assertEqual(issues, [])

    def test_section_anchor_stripped(self) -> None:
        # `[[Foo#Section]]` should resolve against `Foo`, not `Foo#Section`
        text = "Ver [[Sócrates#Muerte]] para más."
        canonical = {"Sócrates"}
        _, issues = lint_text(text, "t.md", canonical, {})
        self.assertEqual(issues, [])


class FixNestedTestCase(TestCase):
    def test_collapse_with_alias(self) -> None:
        text = "Las [[Meditaciones ([[Marco Aurelio]])|Meditaciones]] son estoicas."
        new_text, count = fix_nested_in_text(text)
        self.assertEqual(count, 1)
        self.assertIn("[[Meditaciones (Marco Aurelio)|Meditaciones]]", new_text)
        self.assertNotIn("[[Marco Aurelio]]", new_text)

    def test_collapse_without_alias(self) -> None:
        text = "Ver [[Meditaciones ([[Marco Aurelio]])]] para contexto."
        new_text, count = fix_nested_in_text(text)
        self.assertEqual(count, 1)
        self.assertIn("[[Meditaciones (Marco Aurelio)]]", new_text)

    def test_collapse_preserves_surrounding_text(self) -> None:
        before = "Antes. "
        link = "[[Meditaciones ([[Marco Aurelio]])|Meditaciones]]"
        after = ". Después."
        text = before + link + after
        new_text, _ = fix_nested_in_text(text)
        self.assertTrue(new_text.startswith(before))
        self.assertTrue(new_text.endswith(after))

    def test_no_match_no_change(self) -> None:
        text = "Las [[Meditaciones (Marco Aurelio)|Meditaciones]] ya están bien."
        new_text, count = fix_nested_in_text(text)
        self.assertEqual(count, 0)
        self.assertEqual(new_text, text)

    def test_multiple_in_same_text(self) -> None:
        text = (
            "Una [[Meditaciones ([[Marco Aurelio]])|Meditaciones]] aquí, "
            "otra [[Otro ([[Algo]])]] allá."
        )
        new_text, count = fix_nested_in_text(text)
        self.assertEqual(count, 2)
        self.assertNotIn("[[Marco Aurelio]])", new_text)
        self.assertNotIn("[[Algo]])", new_text)


class FixNestedVaultIntegrationTestCase(TestCase):
    def test_full_vault_fix_writes_files(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        kdir = tmp / "02 - Knowledge"
        kdir.mkdir(parents=True)
        (kdir / "Foo.md").write_text(
            "Body with [[Meditaciones ([[Marco Aurelio]])|Meditaciones]] here.\n",
            encoding="utf-8",
        )
        (kdir / "Bar.md").write_text(
            "Clean body with [[Sócrates]] only.\n",
            encoding="utf-8",
        )
        files_changed, links_fixed = fix_nested_wikilinks(tmp)
        self.assertEqual(files_changed, 1)
        self.assertEqual(links_fixed, 1)
        # Verify Foo was fixed
        foo_text = (kdir / "Foo.md").read_text(encoding="utf-8")
        self.assertIn("[[Meditaciones (Marco Aurelio)|Meditaciones]]", foo_text)
        # Verify Bar was untouched (byte-exact)
        bar_text = (kdir / "Bar.md").read_text(encoding="utf-8")
        self.assertEqual(bar_text, "Clean body with [[Sócrates]] only.\n")


class LintVaultIntegrationTestCase(TestCase):
    def test_end_to_end_finds_three_issue_classes(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        kdir = tmp / "02 - Knowledge"
        kdir.mkdir(parents=True)
        (kdir / "Sócrates.md").write_text("---\nentity: true\n---\n", encoding="utf-8")
        (kdir / "Meditaciones (Marco Aurelio).md").write_text(
            "---\nentity: true\n---\n", encoding="utf-8"
        )
        (kdir / "Meditaciones metafísicas.md").write_text(
            "---\nentity: true\n---\n", encoding="utf-8"
        )
        (kdir / "Buggy.md").write_text(
            "Nested: [[Meditaciones ([[Marco Aurelio]])|Meditaciones]].\n"
            "Broken: [[NoExiste]].\n"
            "Ambiguous: [[Meditaciones]].\n"
            "Good: [[Sócrates]].\n",
            encoding="utf-8",
        )
        report = lint_vault(tmp)
        rules = report.by_rule()
        self.assertEqual(rules.get("nested"), 1)
        self.assertEqual(rules.get("broken"), 1)
        self.assertEqual(rules.get("ambiguous_bare"), 1)
        # files_scanned counts all 4 vault notes
        self.assertEqual(report.files_scanned, 4)

    def test_only_rule_filter(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        kdir = tmp / "02 - Knowledge"
        kdir.mkdir(parents=True)
        (kdir / "Buggy.md").write_text(
            "[[Meditaciones ([[Marco Aurelio]])|M]] and [[NoExiste]].",
            encoding="utf-8",
        )
        report = lint_vault(tmp, only_rule="nested")
        self.assertEqual(len(report.issues), 1)
        self.assertEqual(report.issues[0].rule, "nested")
