"""Tests for compile-knowledge with typed relations — Step 2 of Campaña 2.0.

Covers:
- Legacy-only (`related:`) compilation produces rows with predicate=None.
- Typed-only (`relationships:`) produces rows with predicate and confidence.
- Mixed typed + legacy: typed wins, legacy dedupes by target object.
- Multiple typed predicates to same object coexist.
- Dedup key is (source, predicate, object).
- SQLite roundtrip preserves predicate/confidence correctly.
- Backward compatibility: notes without `relationships:` behave as before.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from brain_ops.domains.knowledge.compile import (
    CompileResult,
    CompiledEntity,
    CompiledRelation,
    compile_relations_from_frontmatter,
    compile_vault_entities,
)
from brain_ops.storage.sqlite.entities import write_compiled_entities


def _make_fm(**extra) -> dict[str, object]:
    """Build a minimal entity frontmatter with some defaults."""
    fm: dict[str, object] = {
        "name": extra.pop("name", "Aristóteles"),
        "entity": True,
        "type": extra.pop("type", "person"),
    }
    fm.update(extra)
    return fm


class CompiledRelationShapeTestCase(TestCase):
    def test_typed_relation_flag(self) -> None:
        r = CompiledRelation(
            source_entity="A", target_entity="B",
            source_type="person", predicate="studied_under",
            confidence="high",
        )
        self.assertTrue(r.is_typed)
        self.assertEqual(r.predicate, "studied_under")

    def test_legacy_relation_flag(self) -> None:
        r = CompiledRelation(
            source_entity="A", target_entity="B",
            source_type="person", predicate=None,
        )
        self.assertFalse(r.is_typed)
        self.assertIsNone(r.predicate)

    def test_to_dict_contains_predicate_and_confidence(self) -> None:
        r = CompiledRelation(
            source_entity="A", target_entity="B",
            source_type="person", predicate="mentor_of", confidence="high",
        )
        d = r.to_dict()
        self.assertEqual(d["predicate"], "mentor_of")
        self.assertEqual(d["confidence"], "high")


class LegacyOnlyCompilationTestCase(TestCase):
    """Notes with only `related:` produce legacy (untyped) rows."""

    def test_produces_untyped_rows(self) -> None:
        fm = _make_fm(related=["Platón", "Sócrates"])
        rels = compile_relations_from_frontmatter(fm)
        self.assertEqual(len(rels), 2)
        for r in rels:
            self.assertFalse(r.is_typed)
            self.assertIsNone(r.predicate)

    def test_preserves_order(self) -> None:
        fm = _make_fm(related=["A", "B", "C"])
        rels = compile_relations_from_frontmatter(fm)
        self.assertEqual([r.target_entity for r in rels], ["A", "B", "C"])


class TypedOnlyCompilationTestCase(TestCase):
    def test_produces_typed_rows(self) -> None:
        fm = _make_fm(relationships=[
            {"predicate": "studied_under", "object": "Platón"},
            {"predicate": "mentor_of", "object": "Alejandro Magno"},
        ])
        rels = compile_relations_from_frontmatter(fm)
        self.assertEqual(len(rels), 2)
        self.assertTrue(all(r.is_typed for r in rels))
        self.assertEqual(rels[0].predicate, "studied_under")
        self.assertEqual(rels[0].target_entity, "Platón")
        self.assertEqual(rels[1].predicate, "mentor_of")

    def test_confidence_default_medium(self) -> None:
        fm = _make_fm(relationships=[
            {"predicate": "studied_under", "object": "Platón"},
        ])
        rels = compile_relations_from_frontmatter(fm)
        self.assertEqual(rels[0].confidence, "medium")

    def test_confidence_explicit(self) -> None:
        fm = _make_fm(relationships=[
            {"predicate": "studied_under", "object": "Platón", "confidence": "high"},
        ])
        rels = compile_relations_from_frontmatter(fm)
        self.assertEqual(rels[0].confidence, "high")

    def test_invalid_predicate_skipped(self) -> None:
        fm = _make_fm(relationships=[
            {"predicate": "studied_under", "object": "Platón"},
            {"predicate": "bogus_predicate", "object": "Random"},
            {"predicate": "mentor_of", "object": "Alejandro Magno"},
        ])
        rels = compile_relations_from_frontmatter(fm)
        self.assertEqual(len(rels), 2)
        predicates = {r.predicate for r in rels}
        self.assertEqual(predicates, {"studied_under", "mentor_of"})


class MixedTypedLegacyCompilationTestCase(TestCase):
    """Core of the Paso 2 contract: typed wins; legacy dedupes by object."""

    def test_typed_wins_over_legacy_same_object(self) -> None:
        fm = _make_fm(
            relationships=[
                {"predicate": "studied_under", "object": "Platón"},
            ],
            related=["Platón", "Sócrates"],
        )
        rels = compile_relations_from_frontmatter(fm)
        # Expected: 1 typed (Platón, studied_under) + 1 legacy (Sócrates, NULL)
        self.assertEqual(len(rels), 2)
        # Typed comes first
        self.assertTrue(rels[0].is_typed)
        self.assertEqual(rels[0].target_entity, "Platón")
        # Legacy-only objects remain as legacy rows
        self.assertFalse(rels[1].is_typed)
        self.assertEqual(rels[1].target_entity, "Sócrates")
        # Platón does NOT appear as a legacy row
        legacy_targets = [r.target_entity for r in rels if not r.is_typed]
        self.assertNotIn("Platón", legacy_targets)

    def test_multiple_typed_predicates_same_object_coexist(self) -> None:
        """User-approved design: dedup key is (source, predicate, object)."""
        fm = _make_fm(
            name="Augusto",
            relationships=[
                {"predicate": "allied_with", "object": "Marco Antonio"},
                {"predicate": "opposed", "object": "Marco Antonio"},
            ],
            related=["Marco Antonio"],  # Should be dedup'd — already typed
        )
        rels = compile_relations_from_frontmatter(fm)
        self.assertEqual(len(rels), 2)
        self.assertEqual({r.predicate for r in rels}, {"allied_with", "opposed"})
        # All typed; no legacy row for Marco Antonio
        self.assertFalse(any(not r.is_typed and r.target_entity == "Marco Antonio"
                             for r in rels))

    def test_legacy_duplicate_within_related_is_dedup(self) -> None:
        fm = _make_fm(related=["Platón", "Platón", "Sócrates"])
        rels = compile_relations_from_frontmatter(fm)
        self.assertEqual(len(rels), 2)
        self.assertEqual([r.target_entity for r in rels], ["Platón", "Sócrates"])

    def test_typed_duplicate_exact_triple_is_dedup(self) -> None:
        """Duplicate (source, predicate, object) is dropped by the parser."""
        fm = _make_fm(relationships=[
            {"predicate": "studied_under", "object": "Platón"},
            {"predicate": "studied_under", "object": "Platón"},
        ])
        rels = compile_relations_from_frontmatter(fm)
        self.assertEqual(len(rels), 1)

    def test_mixed_full_example(self) -> None:
        """End-to-end: typed + legacy with overlaps + multi-predicate."""
        fm = _make_fm(
            name="Aristóteles",
            relationships=[
                {"predicate": "studied_under", "object": "Platón"},
                {"predicate": "reacted_against", "object": "Platón"},
                {"predicate": "mentor_of", "object": "Alejandro Magno"},
            ],
            related=[
                "Platón",           # both predicates already typed → dedup
                "Alejandro Magno",  # typed → dedup
                "Teofrasto",        # legacy only
                "Eudoxo de Cnido",  # legacy only
            ],
        )
        rels = compile_relations_from_frontmatter(fm)
        # 3 typed + 2 legacy = 5
        self.assertEqual(len(rels), 5)

        typed = [r for r in rels if r.is_typed]
        legacy = [r for r in rels if not r.is_typed]
        self.assertEqual(len(typed), 3)
        self.assertEqual(len(legacy), 2)

        # Platón and Alejandro Magno MUST NOT appear in legacy
        legacy_targets = {r.target_entity for r in legacy}
        self.assertEqual(legacy_targets, {"Teofrasto", "Eudoxo de Cnido"})

        # Platón appears twice in typed (studied_under and reacted_against)
        platon_rels = [r for r in typed if r.target_entity == "Platón"]
        self.assertEqual(len(platon_rels), 2)
        self.assertEqual({r.predicate for r in platon_rels},
                         {"studied_under", "reacted_against"})


class NonEntityNoteTestCase(TestCase):
    def test_non_entity_produces_no_relations(self) -> None:
        fm = {"name": "Random", "entity": False, "type": "person"}
        rels = compile_relations_from_frontmatter(fm)
        self.assertEqual(rels, [])

    def test_missing_name_produces_no_relations(self) -> None:
        fm = {"entity": True, "type": "person",
              "relationships": [{"predicate": "studied_under", "object": "X"}]}
        rels = compile_relations_from_frontmatter(fm)
        self.assertEqual(rels, [])


class CompileVaultEntitiesTestCase(TestCase):
    def test_multi_note_compile(self) -> None:
        notes = [
            ("a.md", _make_fm(
                name="Aristóteles",
                relationships=[{"predicate": "studied_under", "object": "Platón"}],
                related=["Teofrasto"],
            )),
            ("b.md", _make_fm(
                name="Platón",
                relationships=[{"predicate": "mentor_of", "object": "Aristóteles"}],
            )),
        ]
        result = compile_vault_entities(notes)
        self.assertEqual(len(result.relations), 3)
        typed_count = sum(1 for r in result.relations if r.is_typed)
        legacy_count = sum(1 for r in result.relations if not r.is_typed)
        self.assertEqual(typed_count, 2)
        self.assertEqual(legacy_count, 1)

    def test_result_metrics(self) -> None:
        notes = [
            ("a.md", _make_fm(
                relationships=[{"predicate": "studied_under", "object": "Platón"}],
                related=["Teofrasto"],
            )),
        ]
        result = compile_vault_entities(notes)
        data = result.to_dict()
        self.assertEqual(data["total_typed_relations"], 1)
        self.assertEqual(data["total_legacy_relations"], 1)


class SqliteRoundtripTestCase(TestCase):
    """End-to-end: compile → SQLite → verify predicate/confidence columns."""

    def test_typed_row_persists_predicate_and_confidence(self) -> None:
        notes = [
            ("a.md", _make_fm(
                name="Aristóteles",
                relationships=[
                    {"predicate": "studied_under", "object": "Platón", "confidence": "high"},
                    {"predicate": "mentor_of", "object": "Alejandro Magno"},
                ],
                related=["Teofrasto"],
            )),
        ]
        result = compile_vault_entities(notes)

        with TemporaryDirectory() as td:
            db = Path(td) / "knowledge.db"
            write_compiled_entities(db, result)

            conn = sqlite3.connect(str(db))
            try:
                rows = conn.execute(
                    "SELECT source_entity, target_entity, predicate, confidence "
                    "FROM entity_relations ORDER BY id"
                ).fetchall()
            finally:
                conn.close()

        # 3 rows total: 2 typed + 1 legacy
        self.assertEqual(len(rows), 3)

        # Typed Platón: predicate='studied_under', confidence='high'
        typed_platon = [r for r in rows if r[1] == "Platón"][0]
        self.assertEqual(typed_platon[2], "studied_under")
        self.assertEqual(typed_platon[3], "high")

        # Typed Alejandro Magno: predicate set, confidence=default 'medium'
        typed_alejandro = [r for r in rows if r[1] == "Alejandro Magno"][0]
        self.assertEqual(typed_alejandro[2], "mentor_of")
        self.assertEqual(typed_alejandro[3], "medium")

        # Legacy Teofrasto: predicate NULL, confidence NULL
        legacy_teofrasto = [r for r in rows if r[1] == "Teofrasto"][0]
        self.assertIsNone(legacy_teofrasto[2])
        self.assertIsNone(legacy_teofrasto[3])

    def test_legacy_only_note_persists_nulls(self) -> None:
        notes = [
            ("a.md", _make_fm(name="X", related=["A", "B"])),
        ]
        result = compile_vault_entities(notes)
        with TemporaryDirectory() as td:
            db = Path(td) / "knowledge.db"
            write_compiled_entities(db, result)
            conn = sqlite3.connect(str(db))
            try:
                rows = conn.execute(
                    "SELECT target_entity, predicate, confidence FROM entity_relations"
                ).fetchall()
            finally:
                conn.close()
        self.assertEqual(len(rows), 2)
        for _target, predicate, confidence in rows:
            self.assertIsNone(predicate)
            self.assertIsNone(confidence)

    def test_sqlite_query_by_predicate(self) -> None:
        """Verify SQL predicate filtering works as expected."""
        notes = [
            ("a.md", _make_fm(
                name="Aristóteles",
                relationships=[
                    {"predicate": "mentor_of", "object": "Alejandro Magno"},
                    {"predicate": "studied_under", "object": "Platón"},
                ],
            )),
            ("b.md", _make_fm(
                name="Platón",
                relationships=[
                    {"predicate": "mentor_of", "object": "Aristóteles"},
                ],
            )),
        ]
        result = compile_vault_entities(notes)
        with TemporaryDirectory() as td:
            db = Path(td) / "knowledge.db"
            write_compiled_entities(db, result)
            conn = sqlite3.connect(str(db))
            try:
                # Query: "Whom did Aristóteles mentor?"
                mentees = conn.execute(
                    "SELECT target_entity FROM entity_relations "
                    "WHERE source_entity=? AND predicate=?",
                    ("Aristóteles", "mentor_of"),
                ).fetchall()
            finally:
                conn.close()
        self.assertEqual(mentees, [("Alejandro Magno",)])


class BackwardCompatTestCase(TestCase):
    """Notes without `relationships:` MUST behave exactly like pre-Campaña-2.0."""

    def test_only_related_works_identically(self) -> None:
        fm = _make_fm(related=["A", "B", "C"])
        rels = compile_relations_from_frontmatter(fm)
        self.assertEqual(len(rels), 3)
        self.assertEqual([r.target_entity for r in rels], ["A", "B", "C"])
        # All untyped
        self.assertTrue(all(r.predicate is None for r in rels))

    def test_entity_compile_excludes_relationships_from_metadata(self) -> None:
        from brain_ops.domains.knowledge.compile import compile_entity_from_frontmatter
        fm = _make_fm(
            relationships=[{"predicate": "studied_under", "object": "Platón"}],
            related=["Teofrasto"],
            domain="filosofia",
        )
        e = compile_entity_from_frontmatter(fm, "Aristóteles.md")
        self.assertIsNotNone(e)
        # Neither related nor relationships appears in metadata
        self.assertNotIn("relationships", e.metadata)
        self.assertNotIn("related", e.metadata)
        # Other fields preserved
        self.assertEqual(e.metadata.get("domain"), "filosofia")
