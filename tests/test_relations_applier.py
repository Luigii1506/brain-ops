"""Tests for relations_applier (Campaña 2.1 Paso 3)."""

from __future__ import annotations

import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

import yaml

from brain_ops.config import FolderConfig, VaultConfig
from brain_ops.domains.knowledge.relations_applier import (
    ApplyReport,
    BatchLoadError,
    apply_batch,
    insert_or_replace_relationships_block,
    load_batch,
    render_relationships_block,
    resolve_batch_dir,
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


def _canonical_entity(root: Path, name: str) -> None:
    _write_note(root, name, {
        "name": name, "entity": True, "type": "person",
        "subtype": "person", "object_kind": "entity",
    }, "\n")


def _write_proposal(batch_dir: Path, entity: str, triples: list[dict]) -> Path:
    batch_dir.mkdir(parents=True, exist_ok=True)
    path = batch_dir / f"{entity}.yaml"
    payload = {
        "batch": batch_dir.name.removeprefix("batch-"),
        "entity": entity,
        "subtype": "person",
        "domain": "filosofia",
        "baseline": {"typed": 0, "legacy_related": 0, "body_chars": 0},
        "proposal": triples,
        "missing_entities_if_approved": [],
        "notes_from_proposer": "",
    }
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
                    encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Block rendering + byte-level insert
# ---------------------------------------------------------------------------


class BlockRenderingTestCase(TestCase):
    def test_render_basic_block(self) -> None:
        text = render_relationships_block([
            {"predicate": "studied_under", "object": "Platón", "confidence": "high"},
            {"predicate": "mentor_of", "object": "Alejandro Magno", "confidence": "high"},
        ])
        expected = (
            "relationships:\n"
            "  - predicate: studied_under\n"
            "    object: Platón\n"
            "    confidence: high\n"
            "  - predicate: mentor_of\n"
            "    object: Alejandro Magno\n"
            "    confidence: high"
        )
        self.assertEqual(text, expected)

    def test_render_omits_medium_default_confidence(self) -> None:
        text = render_relationships_block([
            {"predicate": "influenced_by", "object": "Parménides", "confidence": "medium"},
        ])
        self.assertNotIn("confidence: medium", text)

    def test_render_includes_reason(self) -> None:
        text = render_relationships_block([
            {"predicate": "child_of", "object": "Julio César", "confidence": "high",
             "reason": "adoptive"},
        ])
        self.assertIn("reason: adoptive", text)


class InsertOrReplaceTestCase(TestCase):
    def test_insert_block_when_absent(self) -> None:
        text = "---\nname: X\nentity: true\n---\nBody line one.\nBody line two.\n"
        block = "relationships:\n  - predicate: studied_under\n    object: Y\n    confidence: high"
        new_text = insert_or_replace_relationships_block(text, block)
        self.assertIn("relationships:", new_text)
        self.assertTrue(new_text.endswith("Body line one.\nBody line two.\n"))
        self.assertEqual(new_text.split("---")[2], "\nBody line one.\nBody line two.\n")

    def test_replace_existing_block(self) -> None:
        text = (
            "---\n"
            "name: X\n"
            "entity: true\n"
            "relationships:\n"
            "  - predicate: studied_under\n"
            "    object: Y\n"
            "other_key: z\n"
            "---\n"
            "Body.\n"
        )
        new_block = (
            "relationships:\n"
            "  - predicate: mentor_of\n"
            "    object: W\n"
            "    confidence: high"
        )
        new_text = insert_or_replace_relationships_block(text, new_block)
        self.assertIn("mentor_of", new_text)
        self.assertNotIn("studied_under", new_text)
        self.assertIn("other_key: z", new_text)  # preserved
        self.assertIn("Body.", new_text)  # body preserved


# ---------------------------------------------------------------------------
# load_batch
# ---------------------------------------------------------------------------


class LoadBatchTestCase(TestCase):
    def test_missing_batch_raises(self) -> None:
        with TemporaryDirectory() as td:
            with self.assertRaises(BatchLoadError):
                load_batch(Path(td) / "nope")

    def test_empty_batch_raises(self) -> None:
        with TemporaryDirectory() as td:
            batch = Path(td) / "batch"
            batch.mkdir()
            with self.assertRaises(BatchLoadError):
                load_batch(batch)

    def test_manifest_yaml_is_skipped(self) -> None:
        with TemporaryDirectory() as td:
            batch = Path(td) / "batch-x"
            _write_proposal(batch, "Aristóteles", [])
            (batch / "manifest.yaml").write_text("batch_name: x\n", encoding="utf-8")
            loaded = load_batch(batch)
            self.assertEqual([p.entity for p in loaded], ["Aristóteles"])


# ---------------------------------------------------------------------------
# apply_batch end-to-end
# ---------------------------------------------------------------------------


class ApplyBatchBasicTestCase(TestCase):
    def test_dry_run_does_not_write(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td) / "vault"
            vault = _mk_vault(root)
            _canonical_entity(root, "Platón")
            note_path = _write_note(root, "Aristóteles", {
                "name": "Aristóteles", "entity": True, "type": "person",
                "subtype": "person", "object_kind": "entity",
                "domain": "filosofia",
            }, "Body content here.\n")
            pre = note_path.read_bytes()

            batch_dir = resolve_batch_dir(vault, "t1")
            _write_proposal(batch_dir, "Aristóteles", [
                {"id": "a-01", "predicate": "studied_under", "object": "Platón",
                 "confidence": "high", "status": "approved",
                 "object_status": "canonical_entity_exists"},
            ])

            report = apply_batch("t1", vault, dry_run=True)
            self.assertFalse(report.aborted)
            self.assertEqual(report.total_applied, 1)
            self.assertEqual(note_path.read_bytes(), pre)  # NO write
            self.assertIsNone(report.snapshot_path)

    def test_real_apply_writes_and_preserves_body(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td) / "vault"
            vault = _mk_vault(root)
            _canonical_entity(root, "Platón")
            body = "Body line one.\nBody line two.\n"
            note_path = _write_note(root, "Aristóteles", {
                "name": "Aristóteles", "entity": True, "type": "person",
                "subtype": "person", "object_kind": "entity",
                "domain": "filosofia",
            }, body)

            batch_dir = resolve_batch_dir(vault, "t2")
            _write_proposal(batch_dir, "Aristóteles", [
                {"id": "a-01", "predicate": "studied_under", "object": "Platón",
                 "confidence": "high", "status": "approved",
                 "object_status": "canonical_entity_exists"},
            ])

            report = apply_batch("t2", vault, dry_run=False)
            self.assertFalse(report.aborted)
            self.assertEqual(report.total_applied, 1)
            self.assertIsNotNone(report.snapshot_path)

            post = note_path.read_text(encoding="utf-8")
            self.assertIn("relationships:", post)
            self.assertIn("studied_under", post)
            self.assertTrue(post.endswith(body))


class ApplyBatchMissingEntityTestCase(TestCase):
    def test_missing_entity_blocked_by_default(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td) / "vault"
            vault = _mk_vault(root)
            _write_note(root, "Aristóteles", {
                "name": "Aristóteles", "entity": True, "type": "person",
                "subtype": "person", "object_kind": "entity",
                "domain": "filosofia",
            }, "Body.\n")

            batch_dir = resolve_batch_dir(vault, "t3")
            _write_proposal(batch_dir, "Aristóteles", [
                {"id": "a-01", "predicate": "founded", "object": "Liceo",
                 "confidence": "high", "status": "approved",
                 "object_status": "MISSING_ENTITY"},
            ])

            report = apply_batch("t3", vault, dry_run=False)
            self.assertFalse(report.aborted)
            self.assertEqual(report.total_applied, 0)
            entity = report.entities[0]
            self.assertIn("a-01", entity.skipped.get("missing_entity", []))
            self.assertIn("Liceo", report.missing_entity_queue)

    def test_allow_mentions_bypasses_block(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td) / "vault"
            vault = _mk_vault(root)
            _write_note(root, "Aristóteles", {
                "name": "Aristóteles", "entity": True, "type": "person",
                "subtype": "person", "object_kind": "entity",
                "domain": "filosofia",
            }, "Body.\n")

            batch_dir = resolve_batch_dir(vault, "t4")
            _write_proposal(batch_dir, "Aristóteles", [
                {"id": "a-01", "predicate": "founded", "object": "Liceo",
                 "confidence": "high", "status": "approved",
                 "object_status": "MISSING_ENTITY"},
            ])

            report = apply_batch("t4", vault, dry_run=False, allow_mentions=True)
            self.assertEqual(report.total_applied, 1)


class ApplyBatchIdempotencyTestCase(TestCase):
    def test_second_apply_does_not_duplicate(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td) / "vault"
            vault = _mk_vault(root)
            _canonical_entity(root, "Platón")
            _write_note(root, "Aristóteles", {
                "name": "Aristóteles", "entity": True, "type": "person",
                "subtype": "person", "object_kind": "entity",
                "domain": "filosofia",
            }, "Body.\n")

            batch_dir = resolve_batch_dir(vault, "t5")
            _write_proposal(batch_dir, "Aristóteles", [
                {"id": "a-01", "predicate": "studied_under", "object": "Platón",
                 "confidence": "high", "status": "approved",
                 "object_status": "canonical_entity_exists"},
            ])

            r1 = apply_batch("t5", vault, dry_run=False)
            r2 = apply_batch("t5", vault, dry_run=False)
            self.assertEqual(r1.total_applied, 1)
            self.assertEqual(r2.total_applied, 0)
            entity = r2.entities[0]
            self.assertIn("a-01", entity.skipped.get("already_typed", []))

            # Count relationships in final note — must be exactly 1
            note = (root / "02 - Knowledge" / "Aristóteles.md").read_text(encoding="utf-8")
            self.assertEqual(note.count("predicate: studied_under"), 1)


class ApplyBatchPreExistingTypedTestCase(TestCase):
    def test_proposal_triple_already_in_relationships_is_skipped(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td) / "vault"
            vault = _mk_vault(root)
            _canonical_entity(root, "Platón")
            _canonical_entity(root, "Alejandro Magno")
            _write_note(root, "Aristóteles", {
                "name": "Aristóteles", "entity": True, "type": "person",
                "subtype": "person", "object_kind": "entity",
                "domain": "filosofia",
                "relationships": [
                    {"predicate": "studied_under", "object": "Platón"},
                ],
            }, "Body.\n")

            batch_dir = resolve_batch_dir(vault, "t6")
            _write_proposal(batch_dir, "Aristóteles", [
                {"id": "a-01", "predicate": "studied_under", "object": "Platón",
                 "confidence": "high", "status": "approved",
                 "object_status": "canonical_entity_exists"},
                {"id": "a-02", "predicate": "mentor_of", "object": "Alejandro Magno",
                 "confidence": "high", "status": "approved",
                 "object_status": "canonical_entity_exists"},
            ])

            report = apply_batch("t6", vault, dry_run=False)
            self.assertEqual(report.total_applied, 1)
            entity = report.entities[0]
            self.assertIn("a-01", entity.skipped.get("already_typed", []))

            note = (root / "02 - Knowledge" / "Aristóteles.md").read_text(encoding="utf-8")
            self.assertEqual(note.count("predicate: studied_under"), 1)
            self.assertEqual(note.count("predicate: mentor_of"), 1)


class ApplyBatchApprovalFilteringTestCase(TestCase):
    def test_needs_refinement_not_applied(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td) / "vault"
            vault = _mk_vault(root)
            _canonical_entity(root, "Platón")
            _write_note(root, "Aristóteles", {
                "name": "Aristóteles", "entity": True, "type": "person",
                "subtype": "person", "object_kind": "entity",
                "domain": "filosofia",
            }, "Body.\n")

            batch_dir = resolve_batch_dir(vault, "t7")
            _write_proposal(batch_dir, "Aristóteles", [
                {"id": "a-01", "predicate": "studied_under", "object": "Platón",
                 "confidence": "medium", "status": "needs-refinement",
                 "object_status": "canonical_entity_exists"},
            ])

            report = apply_batch("t7", vault, dry_run=False)
            self.assertEqual(report.total_applied, 0)
            entity = report.entities[0]
            self.assertIn("a-01", entity.skipped.get("not_approved", []))

    def test_unknown_predicate_rejected(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td) / "vault"
            vault = _mk_vault(root)
            _canonical_entity(root, "Platón")
            _write_note(root, "Aristóteles", {
                "name": "Aristóteles", "entity": True, "type": "person",
                "subtype": "person", "object_kind": "entity",
                "domain": "filosofia",
            }, "Body.\n")

            batch_dir = resolve_batch_dir(vault, "t8")
            _write_proposal(batch_dir, "Aristóteles", [
                {"id": "a-01", "predicate": "makes_burritos_with", "object": "Platón",
                 "confidence": "high", "status": "approved",
                 "object_status": "canonical_entity_exists"},
            ])

            report = apply_batch("t8", vault, dry_run=False)
            self.assertEqual(report.total_applied, 0)
            entity = report.entities[0]
            self.assertIn("a-01", entity.skipped.get("unknown_predicate", []))


class ApplyBatchBodySafetyTestCase(TestCase):
    def test_body_bytes_unchanged_after_apply(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td) / "vault"
            vault = _mk_vault(root)
            _canonical_entity(root, "Platón")
            body = "## Identity\n\nAristóteles fue un filósofo griego.\n\n## Timeline\n- 384 a.C. Nacimiento\n"
            note_path = _write_note(root, "Aristóteles", {
                "name": "Aristóteles", "entity": True, "type": "person",
                "subtype": "person", "object_kind": "entity",
                "domain": "filosofia",
            }, body)

            def body_hash(p: Path) -> str:
                t = p.read_text(encoding="utf-8")
                close = -1
                for i, line in enumerate(t.split("\n")[1:], start=1):
                    if line == "---":
                        close = i
                        break
                return hashlib.sha256(
                    "\n".join(t.split("\n")[close+1:]).encode("utf-8")
                ).hexdigest()

            pre = body_hash(note_path)

            batch_dir = resolve_batch_dir(vault, "t9")
            _write_proposal(batch_dir, "Aristóteles", [
                {"id": "a-01", "predicate": "studied_under", "object": "Platón",
                 "confidence": "high", "status": "approved",
                 "object_status": "canonical_entity_exists"},
            ])

            apply_batch("t9", vault, dry_run=False)
            post = body_hash(note_path)
            self.assertEqual(pre, post)


class ApplyBatchNoFilesOutsideBatchTestCase(TestCase):
    def test_other_notes_untouched(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td) / "vault"
            vault = _mk_vault(root)
            _canonical_entity(root, "Platón")
            other_path = _write_note(root, "Sócrates", {
                "name": "Sócrates", "entity": True, "type": "person",
                "subtype": "person", "object_kind": "entity",
                "domain": "filosofia",
            }, "Sócrates body.\n")
            other_pre = other_path.read_bytes()

            _write_note(root, "Aristóteles", {
                "name": "Aristóteles", "entity": True, "type": "person",
                "subtype": "person", "object_kind": "entity",
                "domain": "filosofia",
            }, "Body.\n")

            batch_dir = resolve_batch_dir(vault, "t10")
            _write_proposal(batch_dir, "Aristóteles", [
                {"id": "a-01", "predicate": "studied_under", "object": "Platón",
                 "confidence": "high", "status": "approved",
                 "object_status": "canonical_entity_exists"},
            ])

            apply_batch("t10", vault, dry_run=False)
            self.assertEqual(other_path.read_bytes(), other_pre)


class ApplyBatchAbortGuidanceTestCase(TestCase):
    """When a batch aborts mid-run, the report must provide explicit
    rollback guidance (applied, aborted, not-processed, commands)."""

    def _build_batch_and_sabotage(self, td: Path) -> tuple[Vault, Path]:
        root = td / "vault"
        vault = _mk_vault(root)
        _canonical_entity(root, "Platón")
        _canonical_entity(root, "Sócrates")
        # 3 entities scheduled: E1 (OK), E2 (will abort), E3 (never processed)
        _write_note(root, "E1", {
            "name": "E1", "entity": True, "type": "person",
            "subtype": "person", "object_kind": "entity",
            "domain": "filosofia",
        }, "Body.\n")
        _write_note(root, "E2", {
            "name": "E2", "entity": True, "type": "person",
            "subtype": "person", "object_kind": "entity",
            "domain": "filosofia",
        }, "Body.\n")
        _write_note(root, "E3", {
            "name": "E3", "entity": True, "type": "person",
            "subtype": "person", "object_kind": "entity",
            "domain": "filosofia",
        }, "Body.\n")

        batch_dir = resolve_batch_dir(vault, "abortdemo")
        _write_proposal(batch_dir, "E1", [
            {"id": "e1-01", "predicate": "studied_under", "object": "Platón",
             "confidence": "high", "status": "approved",
             "object_status": "canonical_entity_exists"},
        ])
        _write_proposal(batch_dir, "E2", [
            {"id": "e2-01", "predicate": "studied_under", "object": "Sócrates",
             "confidence": "high", "status": "approved",
             "object_status": "canonical_entity_exists"},
        ])
        _write_proposal(batch_dir, "E3", [
            {"id": "e3-01", "predicate": "mentor_of", "object": "Platón",
             "confidence": "high", "status": "approved",
             "object_status": "canonical_entity_exists"},
        ])
        return vault, batch_dir

    def test_abort_stops_and_reports_applied_vs_not_processed(self) -> None:
        import brain_ops.domains.knowledge.relations_applier as applier_mod

        with TemporaryDirectory() as td:
            vault, _ = self._build_batch_and_sabotage(Path(td))

            # Sabotage the hash check so the SECOND entity's post-hash drifts.
            # We monkeypatch _sha to return a bad value when called with the
            # byte signature of E2's post-body.
            original_sha = applier_mod._sha
            call_counter = {"n": 0}

            def sabotaged_sha(data: bytes) -> str:
                call_counter["n"] += 1
                # The order of _sha() calls per entity is:
                #   1. body_sha_before, 2. fm_outside_sha_before,
                #   3. body_sha_after,  4. fm_outside_sha_after
                # So for entity 2 (calls 5-8), we sabotage call 7 (body_after).
                if call_counter["n"] == 7:
                    return "DRIFT-SENTINEL"
                return original_sha(data)

            applier_mod._sha = sabotaged_sha
            try:
                report = apply_batch("abortdemo", vault, dry_run=False)
            finally:
                applier_mod._sha = original_sha

        self.assertTrue(report.aborted)
        self.assertEqual(report.applied_entities, ["E1"])
        self.assertEqual(report.aborted_entity, "E2")
        self.assertEqual(report.not_processed_entities, ["E3"])
        self.assertIn("E2: body drift", report.abort_reason)

    def test_rollback_instructions_reference_snapshot_and_knowledge_path(self) -> None:
        import brain_ops.domains.knowledge.relations_applier as applier_mod

        with TemporaryDirectory() as td:
            vault, _ = self._build_batch_and_sabotage(Path(td))

            original_sha = applier_mod._sha
            call_counter = {"n": 0}

            def sabotaged_sha(data: bytes) -> str:
                call_counter["n"] += 1
                if call_counter["n"] == 7:
                    return "DRIFT-SENTINEL"
                return original_sha(data)

            applier_mod._sha = sabotaged_sha
            try:
                report = apply_batch("abortdemo", vault, dry_run=False)
            finally:
                applier_mod._sha = original_sha

        instructions = "\n".join(report.rollback_instructions())
        self.assertIn("Entities already applied (1)", instructions)
        self.assertIn("- E1", instructions)
        self.assertIn("Entity that aborted: E2", instructions)
        self.assertIn("- E3", instructions)  # not processed
        self.assertIn("cp -R", instructions)
        self.assertIn("brain compile-knowledge", instructions)
        self.assertIn(str(report.snapshot_path), instructions)

    def test_dry_run_rollback_is_noop_message(self) -> None:
        with TemporaryDirectory() as td:
            root = Path(td) / "vault"
            vault = _mk_vault(root)
            _canonical_entity(root, "Platón")
            _write_note(root, "Aristóteles", {
                "name": "Aristóteles", "entity": True, "type": "person",
                "subtype": "person", "object_kind": "entity",
                "domain": "filosofia",
            }, "Body.\n")
            batch_dir = resolve_batch_dir(vault, "dryrun1")
            _write_proposal(batch_dir, "Aristóteles", [
                {"id": "a-01", "predicate": "studied_under", "object": "Platón",
                 "confidence": "high", "status": "approved",
                 "object_status": "canonical_entity_exists"},
            ])
            report = apply_batch("dryrun1", vault, dry_run=True)
        self.assertIn("Dry-run", report.rollback_instructions()[0])


class ApplyBatchReportShapeTestCase(TestCase):
    def test_report_to_dict_is_serializable(self) -> None:
        import json
        with TemporaryDirectory() as td:
            root = Path(td) / "vault"
            vault = _mk_vault(root)
            _canonical_entity(root, "Platón")
            _write_note(root, "Aristóteles", {
                "name": "Aristóteles", "entity": True, "type": "person",
                "subtype": "person", "object_kind": "entity",
                "domain": "filosofia",
            }, "Body.\n")

            batch_dir = resolve_batch_dir(vault, "t11")
            _write_proposal(batch_dir, "Aristóteles", [
                {"id": "a-01", "predicate": "studied_under", "object": "Platón",
                 "confidence": "high", "status": "approved",
                 "object_status": "canonical_entity_exists"},
                {"id": "a-02", "predicate": "founded", "object": "Liceo",
                 "confidence": "high", "status": "approved",
                 "object_status": "MISSING_ENTITY"},
            ])

            report = apply_batch("t11", vault, dry_run=True)
            payload = report.to_dict()
            # Must be JSON-serializable (no Path, no datetime)
            json.dumps(payload)

            self.assertEqual(payload["total_applied"], 1)
            self.assertEqual(payload["total_skipped"], 1)
            self.assertEqual(payload["dry_run"], True)
            self.assertIn("Liceo", payload["missing_entity_queue"])
