"""Tests for relations_batch (Campaña 2.1 Paso 4)."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

import yaml

from brain_ops.config import FolderConfig, VaultConfig
from brain_ops.domains.knowledge.relations_batch import (
    BatchBuildError,
    BatchFilter,
    build_batch,
    enumerate_candidate_entities,
)
from brain_ops.vault import Vault


def _mk_vault(root: Path) -> Vault:
    for folder in (
        "00 - Inbox", "01 - Sources", "02 - Knowledge", "03 - Maps",
        "04 - Projects", "05 - Systems", "06 - Daily", "07 - Archive",
        "Templates",
    ):
        (root / folder).mkdir(parents=True, exist_ok=True)
    (root / ".brain-ops").mkdir(exist_ok=True)
    cfg = VaultConfig(
        vault_path=str(root),
        default_timezone="UTC",
        folders=FolderConfig(
            inbox="00 - Inbox", sources="01 - Sources",
            knowledge="02 - Knowledge", maps="03 - Maps",
            projects="04 - Projects", systems="05 - Systems",
            daily="06 - Daily", archive="07 - Archive",
            templates="Templates",
        ),
        database_path=str(root / ".brain-ops" / "brain.db"),
    )
    return Vault(config=cfg)


def _write_note(root: Path, name: str, frontmatter: dict, body: str) -> Path:
    path = root / "02 - Knowledge" / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    fm_yaml = yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True).strip()
    path.write_text(f"---\n{fm_yaml}\n---\n{body}", encoding="utf-8")
    return path


class EnumerateCandidatesTestCase(TestCase):
    def test_filter_by_subtype_and_domain(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td) / "vault"
            vault = _mk_vault(root)
            _write_note(root, "Aristóteles", {
                "name": "Aristóteles", "entity": True,
                "type": "person", "subtype": "person",
                "object_kind": "entity", "domain": "filosofia",
            }, "\n")
            _write_note(root, "Augusto", {
                "name": "Augusto", "entity": True,
                "type": "person", "subtype": "person",
                "object_kind": "entity", "domain": "historia",
            }, "\n")
            _write_note(root, "Platón", {
                "name": "Platón", "entity": True,
                "type": "person", "subtype": "person",
                "object_kind": "entity", "domain": "filosofia",
            }, "\n")
            _write_note(root, "La República", {
                "name": "La República", "entity": True,
                "type": "book", "subtype": "book",
                "object_kind": "entity", "domain": "filosofia",
            }, "\n")

            names = enumerate_candidate_entities(
                vault, BatchFilter(subtype="person", domain="filosofia"),
            )
            self.assertEqual(names, ["Aristóteles", "Platón"])

    def test_disambiguation_pages_excluded(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td) / "vault"
            vault = _mk_vault(root)
            _write_note(root, "Tebas", {
                "name": "Tebas",
                "object_kind": "disambiguation_page",
            }, "\n")
            _write_note(root, "Platón", {
                "name": "Platón", "entity": True,
                "type": "person", "subtype": "person",
                "object_kind": "entity", "domain": "filosofia",
            }, "\n")
            names = enumerate_candidate_entities(
                vault, BatchFilter(subtype="person"),
            )
            self.assertEqual(names, ["Platón"])

    def test_include_restricts_to_explicit_list(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td) / "vault"
            vault = _mk_vault(root)
            for name in ["Aristóteles", "Platón", "Sócrates"]:
                _write_note(root, name, {
                    "name": name, "entity": True,
                    "type": "person", "subtype": "person",
                    "object_kind": "entity", "domain": "filosofia",
                }, "\n")
            names = enumerate_candidate_entities(
                vault,
                BatchFilter(include=("Aristóteles", "Sócrates")),
            )
            self.assertEqual(names, ["Aristóteles", "Sócrates"])

    def test_domain_as_list_matches(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td) / "vault"
            vault = _mk_vault(root)
            _write_note(root, "Marco Aurelio", {
                "name": "Marco Aurelio", "entity": True,
                "type": "person", "subtype": "person",
                "object_kind": "entity",
                "domain": ["historia", "filosofia"],
            }, "\n")
            names = enumerate_candidate_entities(
                vault, BatchFilter(domain="filosofia"),
            )
            self.assertEqual(names, ["Marco Aurelio"])

    def test_limit_caps_output(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td) / "vault"
            vault = _mk_vault(root)
            for name in ["A", "B", "C", "D"]:
                _write_note(root, name, {
                    "name": name, "entity": True,
                    "type": "person", "subtype": "person",
                    "object_kind": "entity", "domain": "filosofia",
                }, "\n")
            names = enumerate_candidate_entities(
                vault, BatchFilter(limit=2),
            )
            self.assertEqual(len(names), 2)


class BuildBatchTestCase(TestCase):
    def test_end_to_end_batch_layout(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td) / "vault"
            vault = _mk_vault(root)
            _write_note(root, "Platón", {
                "name": "Platón", "entity": True,
                "type": "person", "subtype": "person",
                "object_kind": "entity", "domain": "filosofia",
            }, "\n")
            _write_note(root, "Aristóteles", {
                "name": "Aristóteles", "entity": True,
                "type": "person", "subtype": "person",
                "object_kind": "entity", "domain": "filosofia",
            }, "Alumno de [[Platón]] durante 20 años. Fundó el [[Liceo]] en 335 a.C.\n")

            result = build_batch(
                vault, "F1-demo",
                BatchFilter(subtype="person", domain="filosofia",
                            include=("Aristóteles",)),
            )

            batch_dir = result.batch_dir
            self.assertTrue(batch_dir.exists())
            self.assertTrue((batch_dir / "manifest.yaml").exists())
            self.assertTrue((batch_dir / "Aristóteles.yaml").exists())
            self.assertTrue((batch_dir / "missing_entities.md").exists())
            self.assertTrue((batch_dir / "summary.md").exists())

            # Manifest has expected shape
            manifest = yaml.safe_load((batch_dir / "manifest.yaml").read_text())
            self.assertEqual(manifest["batch_name"], "F1-demo")
            self.assertEqual(len(manifest["entities"]), 1)
            self.assertEqual(manifest["entities"][0]["name"], "Aristóteles")

            # Liceo must show up in missing queue
            self.assertIn("Liceo", result.missing_queue)
            self.assertIn("Aristóteles", result.missing_queue["Liceo"])

            # The per-entity YAML has the batch name stamped
            per_entity = yaml.safe_load((batch_dir / "Aristóteles.yaml").read_text())
            self.assertEqual(per_entity["batch"], "F1-demo")
            self.assertGreaterEqual(len(per_entity["proposal"]), 1)

    def test_skip_empty_omits_notes_with_no_proposals(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td) / "vault"
            vault = _mk_vault(root)
            # Note with empty body and no predicate patterns → 0 proposals
            _write_note(root, "Empty", {
                "name": "Empty", "entity": True,
                "type": "person", "subtype": "person",
                "object_kind": "entity", "domain": "filosofia",
            }, "Nothing interesting here.\n")

            result = build_batch(
                vault, "empty-test",
                BatchFilter(subtype="person", domain="filosofia"),
            )

            self.assertEqual(result.entities, [])
            self.assertIn("Empty", result.skipped_empty)
            # No per-entity YAML written
            self.assertFalse((result.batch_dir / "Empty.yaml").exists())

    def test_overwrite_required_to_replace_existing_batch(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td) / "vault"
            vault = _mk_vault(root)
            _write_note(root, "Platón", {
                "name": "Platón", "entity": True,
                "type": "person", "subtype": "person",
                "object_kind": "entity", "domain": "filosofia",
            }, "\n")
            _write_note(root, "Aristóteles", {
                "name": "Aristóteles", "entity": True,
                "type": "person", "subtype": "person",
                "object_kind": "entity", "domain": "filosofia",
            }, "Alumno de [[Platón]].\n")

            build_batch(vault, "F1-ow",
                        BatchFilter(include=("Aristóteles",)))
            with self.assertRaises(BatchBuildError):
                build_batch(vault, "F1-ow",
                            BatchFilter(include=("Aristóteles",)))
            # With overwrite=True it succeeds
            build_batch(vault, "F1-ow",
                        BatchFilter(include=("Aristóteles",)),
                        overwrite=True)

    def test_missing_entities_md_groups_shared_refs(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td) / "vault"
            vault = _mk_vault(root)
            _write_note(root, "Platón", {
                "name": "Platón", "entity": True,
                "type": "person", "subtype": "person",
                "object_kind": "entity", "domain": "filosofia",
            }, "\n")
            # Two notes both mentioning the same missing object
            _write_note(root, "A", {
                "name": "A", "entity": True,
                "type": "person", "subtype": "person",
                "object_kind": "entity", "domain": "filosofia",
            }, "Fundó [[LiceoX]].\n")
            _write_note(root, "B", {
                "name": "B", "entity": True,
                "type": "person", "subtype": "person",
                "object_kind": "entity", "domain": "filosofia",
            }, "Fundó [[LiceoX]].\n")

            result = build_batch(
                vault, "shared-miss",
                BatchFilter(subtype="person", domain="filosofia",
                            include=("A", "B")),
            )

            missing_text = (result.batch_dir / "missing_entities.md").read_text()
            self.assertIn("LiceoX", missing_text)
            self.assertIn("**LiceoX** — 2 refs", missing_text)
            # Both A and B listed as refs
            self.assertIn("A", result.missing_queue["LiceoX"])
            self.assertIn("B", result.missing_queue["LiceoX"])

    def test_summary_md_has_next_steps(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td) / "vault"
            vault = _mk_vault(root)
            _write_note(root, "Platón", {
                "name": "Platón", "entity": True,
                "type": "person", "subtype": "person",
                "object_kind": "entity", "domain": "filosofia",
            }, "\n")
            _write_note(root, "Aristóteles", {
                "name": "Aristóteles", "entity": True,
                "type": "person", "subtype": "person",
                "object_kind": "entity", "domain": "filosofia",
            }, "Alumno de [[Platón]].\n")
            result = build_batch(
                vault, "nextsteps",
                BatchFilter(include=("Aristóteles",)),
            )
            summary = (result.batch_dir / "summary.md").read_text()
            self.assertIn("## Next steps", summary)
            self.assertIn("brain apply-relations-batch nextsteps", summary)
            self.assertIn("--apply", summary)

    def test_no_vault_note_mutations(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td) / "vault"
            vault = _mk_vault(root)
            _write_note(root, "Platón", {
                "name": "Platón", "entity": True,
                "type": "person", "subtype": "person",
                "object_kind": "entity", "domain": "filosofia",
            }, "\n")
            aris_path = _write_note(root, "Aristóteles", {
                "name": "Aristóteles", "entity": True,
                "type": "person", "subtype": "person",
                "object_kind": "entity", "domain": "filosofia",
            }, "Alumno de [[Platón]].\n")
            pre = aris_path.read_bytes()
            build_batch(vault, "readonly",
                        BatchFilter(include=("Aristóteles",)))
            self.assertEqual(aris_path.read_bytes(), pre)
