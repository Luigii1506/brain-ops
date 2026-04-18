"""Subfase 1.3 — fix_capitalization tests."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase


def _is_case_sensitive_fs(path: Path) -> bool:
    """Return True if the filesystem at `path` is case-sensitive."""
    probe_lower = path / ".__case_probe_lower"
    probe_upper = path / ".__CASE_PROBE_LOWER"
    try:
        probe_lower.write_text("lower", encoding="utf-8")
        # On case-insensitive FS, writing to probe_upper overwrites probe_lower
        probe_upper.write_text("upper", encoding="utf-8")
        lower_content = probe_lower.read_text() if probe_lower.exists() else ""
        result = lower_content == "lower"
    finally:
        for p in (probe_lower, probe_upper):
            if p.exists():
                p.unlink()
    return result


def _list_knowledge_names(vault: Path) -> set[str]:
    """Return actual filenames (case-sensitive, from iterdir) in 02 - Knowledge."""
    d = vault / "02 - Knowledge"
    return {p.name for p in d.iterdir() if p.is_file()}

from brain_ops.domains.knowledge.consolidation import (
    apply_fix_capitalization,
    plan_fix_capitalization,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _entity(vault: Path, name: str, body: str = "## Identity\n\nNota.", related: list[str] | None = None) -> Path:
    fm = ["---"]
    fm.append(f"name: {name}")
    fm.append("type: place")
    fm.append("object_kind: place")
    fm.append("subtype: empire")
    fm.append("entity: true")
    fm.append("status: canonical")
    fm.append("domain: historia")
    if related:
        fm.append("related:")
        for r in related:
            fm.append(f"  - {r}")
    fm.append("---")
    text = "\n".join(fm) + "\n\n" + body + "\n"
    p = vault / "02 - Knowledge" / f"{name}.md"
    _write(p, text)
    return p


class PlanFixCapitalizationTestCase(TestCase):
    def test_detects_imperio_romano(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _entity(vault, "Imperio romano")
            report = plan_fix_capitalization(vault)
            self.assertEqual(len(report.fixes), 1)
            fix = report.fixes[0]
            self.assertEqual(fix.old_name, "Imperio romano")
            self.assertEqual(fix.new_name, "Imperio Romano")
            self.assertTrue(fix.can_apply)

    def test_skips_reino_de_macedonia(self) -> None:
        """The fixed regex must ignore preposition-after-head."""
        with TemporaryDirectory() as td:
            vault = Path(td)
            _entity(vault, "Reino de Macedonia")
            report = plan_fix_capitalization(vault)
            self.assertEqual(len(report.fixes), 0)

    def test_blocks_when_target_exists(self) -> None:
        """Only meaningful on case-sensitive filesystems."""
        with TemporaryDirectory() as td:
            vault = Path(td)
            if not _is_case_sensitive_fs(vault):
                self.skipTest("Case-insensitive filesystem: two case variants cannot coexist.")
            _entity(vault, "Imperio romano")
            _entity(vault, "Imperio Romano")
            report = plan_fix_capitalization(vault)
            self.assertEqual(len(report.fixes), 1)
            self.assertFalse(report.fixes[0].can_apply)
            self.assertIn("already exists", report.fixes[0].error_message)

    def test_counts_incoming_wikilinks(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _entity(vault, "Imperio romano")
            _entity(
                vault, "Augusto",
                body="Fundó el [[Imperio romano]] en el 27 a.C. Líder del [[Imperio romano|imperio]].",
                related=["Imperio romano"],
            )
            report = plan_fix_capitalization(vault)
            self.assertEqual(len(report.fixes), 1)
            fix = report.fixes[0]
            self.assertEqual(fix.body_wikilink_mentions, 2)
            self.assertEqual(len(fix.related_entries), 1)


class ApplyFixCapitalizationTestCase(TestCase):
    def test_renames_file_and_updates_frontmatter(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _entity(vault, "Imperio romano")
            report = plan_fix_capitalization(vault)
            apply_fix_capitalization(vault, report)

            # Case-aware check via iterdir (not Path.exists which is case-insensitive on macOS)
            names = _list_knowledge_names(vault)
            self.assertNotIn("Imperio romano.md", names)
            self.assertIn("Imperio Romano.md", names)

            new = vault / "02 - Knowledge" / "Imperio Romano.md"
            text = new.read_text()
            self.assertIn("name: Imperio Romano", text)

    def test_updates_incoming_wikilinks_directly(self) -> None:
        """For capitalization fix, body wikilinks become [[New]] directly (no alias)."""
        with TemporaryDirectory() as td:
            vault = Path(td)
            _entity(vault, "Imperio romano")
            _entity(
                vault, "Augusto",
                body="Fundó el [[Imperio romano]] en el 27 a.C.",
                related=["Imperio romano"],
            )
            report = plan_fix_capitalization(vault)
            apply_fix_capitalization(vault, report)

            aug = (vault / "02 - Knowledge" / "Augusto.md").read_text()
            self.assertIn("[[Imperio Romano]]", aug)
            self.assertNotIn("[[Imperio romano]]", aug)
            self.assertIn("- Imperio Romano", aug)

    def test_preserves_aliased_display_text(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _entity(vault, "Imperio romano")
            _entity(
                vault, "Augusto",
                body="Líder del [[Imperio romano|imperio]].",
            )
            report = plan_fix_capitalization(vault)
            apply_fix_capitalization(vault, report)

            aug = (vault / "02 - Knowledge" / "Augusto.md").read_text()
            self.assertIn("[[Imperio Romano|imperio]]", aug)

    def test_does_not_touch_plain_text(self) -> None:
        """Plain text 'Imperio romano' in prose must NOT be rewritten."""
        with TemporaryDirectory() as td:
            vault = Path(td)
            _entity(vault, "Imperio romano")
            _entity(
                vault, "Notas",
                body="El Imperio romano (plain) y [[Imperio romano]] (wikilink).",
            )
            report = plan_fix_capitalization(vault)
            apply_fix_capitalization(vault, report)

            notas = (vault / "02 - Knowledge" / "Notas.md").read_text()
            self.assertIn("El Imperio romano (plain)", notas)  # plain preserved
            self.assertIn("[[Imperio Romano]] (wikilink)", notas)

    def test_exclude_skips_specific_entity(self) -> None:
        with TemporaryDirectory() as td:
            vault = Path(td)
            _entity(vault, "Imperio romano")
            _entity(vault, "Imperio medo")
            report = plan_fix_capitalization(vault)
            apply_fix_capitalization(vault, report, exclude=["Imperio romano"])

            names = _list_knowledge_names(vault)
            # Imperio romano NOT renamed (excluded)
            self.assertIn("Imperio romano.md", names)
            self.assertNotIn("Imperio Romano.md", names)
            # Imperio medo renamed
            self.assertNotIn("Imperio medo.md", names)
            self.assertIn("Imperio Medo.md", names)

    def test_handles_related_wikilink_in_string(self) -> None:
        """related: - '[[Imperio romano]]' pattern must also update."""
        with TemporaryDirectory() as td:
            vault = Path(td)
            _entity(vault, "Imperio romano")
            note = vault / "02 - Knowledge" / "Batalla.md"
            _write(note, """---
name: Batalla
entity: true
related:
- '[[Imperio romano]]'
- '[[Esparta]]'
---

## Identity

Something.
""")
            report = plan_fix_capitalization(vault)
            apply_fix_capitalization(vault, report)

            text = note.read_text()
            self.assertIn("'[[Imperio Romano]]'", text)
            self.assertIn("'[[Esparta]]'", text)
