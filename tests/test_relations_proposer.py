"""Tests for relations_proposer (Campaña 2.1 Paso 2)."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

import yaml

from brain_ops.config import FolderConfig, VaultConfig
from brain_ops.domains.knowledge.relations_proposer import (
    EVIDENCE_SOURCES,
    ProposalResult,
    propose_relations_for_entity,
)
from brain_ops.vault import Vault


def _write_note(root: Path, name: str, frontmatter: dict, body: str) -> Path:
    path = root / "02 - Knowledge" / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    fm_yaml = yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True).strip()
    path.write_text(f"---\n{fm_yaml}\n---\n{body}", encoding="utf-8")
    return path


def _mk_vault(td: Path) -> Vault:
    root = td / "vault"
    for folder in (
        "00 - Inbox", "01 - Sources", "02 - Knowledge", "03 - Maps",
        "04 - Projects", "05 - Systems", "06 - Daily", "07 - Archive",
        "Templates", ".brain-ops",
    ):
        (root / folder).mkdir(parents=True, exist_ok=True)
    cfg = VaultConfig(
        vault_path=str(root),
        default_timezone="UTC",
        folders=FolderConfig(
            inbox="00 - Inbox",
            sources="01 - Sources",
            knowledge="02 - Knowledge",
            maps="03 - Maps",
            projects="04 - Projects",
            systems="05 - Systems",
            daily="06 - Daily",
            archive="07 - Archive",
            templates="Templates",
        ),
        database_path=str(root / ".brain-ops" / "brain.db"),
    )
    return Vault(config=cfg)


def _canonical_entity(vault_root: Path, name: str, **extras):
    fm = {
        "name": name,
        "entity": True,
        "type": extras.pop("type", "person"),
        "subtype": extras.pop("subtype", "person"),
        "object_kind": extras.pop("object_kind", "entity"),
        **extras,
    }
    _write_note(vault_root, name, fm, extras.pop("body", "\n"))


class BodyExtractionTestCase(TestCase):
    def test_studied_under_pattern_emits_high(self) -> None:
        with TemporaryDirectory() as td:
            vault = _mk_vault(Path(td))
            _canonical_entity(vault.root, "Platón")
            _write_note(vault.root, "Aristóteles", {
                "name": "Aristóteles",
                "entity": True,
                "type": "person",
                "subtype": "person",
                "object_kind": "entity",
                "domain": "filosofia",
            }, "Aristóteles fue alumno de [[Platón]] durante 20 años.")
            result = propose_relations_for_entity("Aristóteles", vault)

        studied = [p for p in result.proposal if p.predicate == "studied_under"]
        self.assertEqual(len(studied), 1)
        self.assertEqual(studied[0].object, "Platón")
        self.assertEqual(studied[0].confidence, "high")
        self.assertEqual(studied[0].status, "approved")
        self.assertIn("body", studied[0].evidence_source)
        self.assertEqual(studied[0].object_status, "canonical_entity_exists")

    def test_hedging_downgrades_to_medium(self) -> None:
        with TemporaryDirectory() as td:
            vault = _mk_vault(Path(td))
            _canonical_entity(vault.root, "Averroes")
            _write_note(vault.root, "Tomás de Aquino", {
                "name": "Tomás de Aquino",
                "entity": True,
                "type": "person",
                "subtype": "person",
                "object_kind": "entity",
                "domain": "filosofia",
            }, "Indirectamente influenciado por [[Averroes]] a través del neoplatonismo.")
            result = propose_relations_for_entity("Tomás de Aquino", vault)

        infs = [p for p in result.proposal if p.predicate == "influenced_by"]
        self.assertEqual(len(infs), 1)
        self.assertEqual(infs[0].confidence, "medium")
        self.assertEqual(infs[0].status, "needs-refinement")

    def test_wikilink_with_pipe_alias_captures_target(self) -> None:
        with TemporaryDirectory() as td:
            vault = _mk_vault(Path(td))
            _canonical_entity(vault.root, "Macedonia (Grecia)")
            _write_note(vault.root, "Alejandro Magno", {
                "name": "Alejandro Magno",
                "entity": True,
                "type": "person",
                "subtype": "person",
                "object_kind": "entity",
                "domain": "historia",
            }, "Rey de [[Macedonia (Grecia)|Macedonia]] desde 336 a.C.")
            result = propose_relations_for_entity("Alejandro Magno", vault)

        ruled = [p for p in result.proposal if p.predicate == "ruled"]
        self.assertEqual(len(ruled), 1)
        self.assertEqual(ruled[0].object, "Macedonia (Grecia)")

    def test_self_reference_is_skipped(self) -> None:
        with TemporaryDirectory() as td:
            vault = _mk_vault(Path(td))
            _write_note(vault.root, "Aristóteles", {
                "name": "Aristóteles",
                "entity": True,
                "type": "person",
                "subtype": "person",
                "object_kind": "entity",
                "domain": "filosofia",
            }, "Aristóteles criticó a [[Aristóteles]] en un pasaje extraño.")
            result = propose_relations_for_entity("Aristóteles", vault)

        self.assertEqual([p for p in result.proposal if p.object == "Aristóteles"], [])

    def test_multiple_predicates_same_target_both_emitted(self) -> None:
        with TemporaryDirectory() as td:
            vault = _mk_vault(Path(td))
            _canonical_entity(vault.root, "Platón")
            _write_note(vault.root, "Aristóteles", {
                "name": "Aristóteles",
                "entity": True, "type": "person", "subtype": "person",
                "object_kind": "entity", "domain": "filosofia",
            }, "Alumno de [[Platón]] durante 20 años. Criticó a [[Platón]] sobre las Formas.")
            result = propose_relations_for_entity("Aristóteles", vault)

        predicates = sorted(p.predicate for p in result.proposal if p.object == "Platón")
        self.assertEqual(predicates, ["reacted_against", "studied_under"])


class MetadataExtractionTestCase(TestCase):
    def test_occupation_king_of_extracts_ruled(self) -> None:
        with TemporaryDirectory() as td:
            vault = _mk_vault(Path(td))
            _canonical_entity(vault.root, "Macedonia (Grecia)")
            _write_note(vault.root, "Alejandro Magno", {
                "name": "Alejandro Magno",
                "entity": True, "type": "person", "subtype": "person",
                "object_kind": "entity", "domain": "historia",
                "occupation": "Rey de Macedonia (Grecia)",
            }, "\n")
            result = propose_relations_for_entity("Alejandro Magno", vault)

        ruled = [p for p in result.proposal if p.predicate == "ruled"]
        self.assertEqual(len(ruled), 1)
        self.assertIn("metadata", ruled[0].evidence_source)
        self.assertEqual(ruled[0].evidence_excerpts[0].location, "metadata.occupation")


class ObjectStatusTestCase(TestCase):
    def test_missing_entity_flagged_and_noted(self) -> None:
        with TemporaryDirectory() as td:
            vault = _mk_vault(Path(td))
            _write_note(vault.root, "Aristóteles", {
                "name": "Aristóteles",
                "entity": True, "type": "person", "subtype": "person",
                "object_kind": "entity", "domain": "filosofia",
            }, "Fundó el [[Liceo]].")
            result = propose_relations_for_entity("Aristóteles", vault)

        liceo = [p for p in result.proposal if p.object == "Liceo"]
        self.assertEqual(len(liceo), 1)
        self.assertEqual(liceo[0].predicate, "founded")
        self.assertEqual(liceo[0].confidence, "high")
        self.assertEqual(liceo[0].object_status, "MISSING_ENTITY")
        self.assertIn("Liceo", result.missing_entities_if_approved)
        self.assertIsNotNone(liceo[0].note)
        self.assertIn("--allow-mentions", liceo[0].note)

    def test_disambiguation_page_flagged(self) -> None:
        with TemporaryDirectory() as td:
            vault = _mk_vault(Path(td))
            _write_note(vault.root, "Tebas", {
                "name": "Tebas",
                "object_kind": "disambiguation_page",
            }, "\n")
            _write_note(vault.root, "Alejandro Magno", {
                "name": "Alejandro Magno",
                "entity": True, "type": "person", "subtype": "person",
                "object_kind": "entity", "domain": "historia",
            }, "Conquistó [[Tebas]] en 335 a.C.")
            result = propose_relations_for_entity("Alejandro Magno", vault)

        tebas = [p for p in result.proposal if p.object == "Tebas"]
        self.assertEqual(len(tebas), 1)
        self.assertEqual(tebas[0].object_status, "DISAMBIGUATION_PAGE")
        self.assertIn("disambiguation_page", tebas[0].note.lower())


class ExistingTypedFilteringTestCase(TestCase):
    def test_existing_typed_excluded_by_default(self) -> None:
        with TemporaryDirectory() as td:
            vault = _mk_vault(Path(td))
            _canonical_entity(vault.root, "Platón")
            _write_note(vault.root, "Aristóteles", {
                "name": "Aristóteles",
                "entity": True, "type": "person", "subtype": "person",
                "object_kind": "entity", "domain": "filosofia",
                "relationships": [
                    {"predicate": "studied_under", "object": "Platón"},
                ],
            }, "Alumno de [[Platón]] durante 20 años.")
            result = propose_relations_for_entity("Aristóteles", vault)

        matches = [p for p in result.proposal
                   if p.predicate == "studied_under" and p.object == "Platón"]
        self.assertEqual(matches, [])
        self.assertEqual(result.baseline.typed, 1)

    def test_include_existing_flag_keeps_them(self) -> None:
        with TemporaryDirectory() as td:
            vault = _mk_vault(Path(td))
            _canonical_entity(vault.root, "Platón")
            _write_note(vault.root, "Aristóteles", {
                "name": "Aristóteles",
                "entity": True, "type": "person", "subtype": "person",
                "object_kind": "entity", "domain": "filosofia",
                "relationships": [
                    {"predicate": "studied_under", "object": "Platón"},
                ],
            }, "Alumno de [[Platón]] durante 20 años.")
            result = propose_relations_for_entity(
                "Aristóteles", vault, include_existing=True,
            )

        matches = [p for p in result.proposal
                   if p.predicate == "studied_under" and p.object == "Platón"]
        self.assertEqual(len(matches), 1)


class RelatedEvidenceTestCase(TestCase):
    def test_related_augments_evidence_source_when_body_also_matches(self) -> None:
        with TemporaryDirectory() as td:
            vault = _mk_vault(Path(td))
            _canonical_entity(vault.root, "Platón")
            _write_note(vault.root, "Aristóteles", {
                "name": "Aristóteles",
                "entity": True, "type": "person", "subtype": "person",
                "object_kind": "entity", "domain": "filosofia",
                "related": ["Platón"],
            }, "Alumno de [[Platón]] durante 20 años.")
            result = propose_relations_for_entity("Aristóteles", vault)

        studied = [p for p in result.proposal if p.predicate == "studied_under"]
        self.assertEqual(len(studied), 1)
        self.assertIn("body", studied[0].evidence_source)
        self.assertIn("related", studied[0].evidence_source)
        locations = [e.location for e in studied[0].evidence_excerpts]
        self.assertIn("related", locations)

    def test_related_alone_does_not_create_proposal(self) -> None:
        with TemporaryDirectory() as td:
            vault = _mk_vault(Path(td))
            _canonical_entity(vault.root, "Teofrasto")
            _write_note(vault.root, "Aristóteles", {
                "name": "Aristóteles",
                "entity": True, "type": "person", "subtype": "person",
                "object_kind": "entity", "domain": "filosofia",
                "related": ["Teofrasto"],
            }, "\n")
            result = propose_relations_for_entity("Aristóteles", vault)

        teof = [p for p in result.proposal if p.object == "Teofrasto"]
        self.assertEqual(teof, [])


class CrossRefEvidenceTestCase(TestCase):
    def test_crossref_adds_source_but_does_not_invert(self) -> None:
        with TemporaryDirectory() as td:
            vault = _mk_vault(Path(td))
            _canonical_entity(vault.root, "Aristóteles")
            _write_note(vault.root, "Platón", {
                "name": "Platón",
                "entity": True, "type": "person", "subtype": "person",
                "object_kind": "entity", "domain": "filosofia",
            }, "Maestro de [[Aristóteles]].")

            # Build a minimal SQLite with a mentor_of edge from Platón.
            db_path = vault.root / ".brain-ops" / "knowledge.db"
            conn = sqlite3.connect(str(db_path))
            conn.execute("""
                CREATE TABLE entity_relations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_entity TEXT NOT NULL,
                    target_entity TEXT NOT NULL,
                    predicate TEXT,
                    confidence TEXT,
                    source_type TEXT
                )
            """)
            # The INVERSE edge on Aristóteles's side is what counts as
            # cross-ref evidence when proposing `Platón -> mentor_of -> Aristóteles`.
            conn.execute(
                "INSERT INTO entity_relations "
                "(source_entity, target_entity, predicate, confidence, source_type) "
                "VALUES (?, ?, ?, ?, ?)",
                ("Aristóteles", "Platón", "studied_under", "high", None),
            )
            conn.commit(); conn.close()

            result = propose_relations_for_entity(
                "Platón", vault, db_path=db_path,
            )

        mentor_props = [p for p in result.proposal
                        if p.predicate == "mentor_of" and p.object == "Aristóteles"]
        self.assertEqual(len(mentor_props), 1)
        # cross-ref should be appended because the inverse edge was already in DB
        self.assertIn("cross-ref", mentor_props[0].evidence_source)


class YAMLContractTestCase(TestCase):
    def test_evidence_source_is_always_from_closed_set(self) -> None:
        with TemporaryDirectory() as td:
            vault = _mk_vault(Path(td))
            _canonical_entity(vault.root, "Platón")
            _write_note(vault.root, "Aristóteles", {
                "name": "Aristóteles",
                "entity": True, "type": "person", "subtype": "person",
                "object_kind": "entity", "domain": "filosofia",
                "related": ["Platón"],
                "occupation": "Filósofo",
            }, "Alumno de [[Platón]] durante 20 años.")
            result = propose_relations_for_entity("Aristóteles", vault)

        for p in result.proposal:
            for src in p.evidence_source:
                self.assertIn(src, EVIDENCE_SOURCES,
                              f"evidence source {src!r} outside closed set")

    def test_to_yaml_dict_round_trip(self) -> None:
        with TemporaryDirectory() as td:
            vault = _mk_vault(Path(td))
            _canonical_entity(vault.root, "Platón")
            _write_note(vault.root, "Aristóteles", {
                "name": "Aristóteles",
                "entity": True, "type": "person", "subtype": "person",
                "object_kind": "entity", "domain": "filosofia",
            }, "Alumno de [[Platón]] durante 20 años.")
            result = propose_relations_for_entity("Aristóteles", vault)
            dumped = yaml.safe_dump(result.to_yaml_dict(), allow_unicode=True)

        # Roundtripping through YAML must preserve structure
        reparsed = yaml.safe_load(dumped)
        self.assertEqual(reparsed["entity"], "Aristóteles")
        self.assertIn("proposal", reparsed)
        self.assertGreaterEqual(len(reparsed["proposal"]), 1)
        for p in reparsed["proposal"]:
            self.assertIn("evidence", p)
            self.assertIn("source", p["evidence"])
            self.assertIsInstance(p["evidence"]["source"], list)

    def test_no_write_to_vault_note(self) -> None:
        with TemporaryDirectory() as td:
            vault = _mk_vault(Path(td))
            _canonical_entity(vault.root, "Platón")
            note_path = _write_note(vault.root, "Aristóteles", {
                "name": "Aristóteles",
                "entity": True, "type": "person", "subtype": "person",
                "object_kind": "entity", "domain": "filosofia",
            }, "Alumno de [[Platón]] durante 20 años.")
            before = note_path.read_bytes()
            propose_relations_for_entity("Aristóteles", vault)
            after = note_path.read_bytes()

        self.assertEqual(before, after, "propose-relations must not mutate the note")
