"""Tests for relations_query + `brain query-relations` — Paso 4."""

from __future__ import annotations

import json as _json
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import Mock

import typer
from rich.console import Console
from typer.testing import CliRunner

from brain_ops.domains.knowledge.compile import compile_vault_entities
from brain_ops.domains.knowledge.relations_query import (
    QueriedRelation,
    query_relations,
    summarize_entity_relations,
)
from brain_ops.interfaces.cli.commands_notes import register_note_and_knowledge_commands
from brain_ops.storage.sqlite.entities import write_compiled_entities


# ---------------------------------------------------------------------------
# Helpers: build a small temp SQLite with typed + legacy rows
# ---------------------------------------------------------------------------

def _mk_note(name, **fm):
    base = {
        "name": name,
        "entity": True,
        "type": fm.pop("type", "person"),
        "subtype": fm.pop("subtype", "person"),
        "object_kind": fm.pop("object_kind", "entity"),
    }
    base.update(fm)
    return base


def _build_db(tmp: Path) -> Path:
    """Compile and write a small vault → return path to knowledge.db."""
    notes = [
        ("a.md", _mk_note(
            "Aristóteles",
            relationships=[
                {"predicate": "studied_under", "object": "Platón"},
                {"predicate": "mentor_of", "object": "Alejandro Magno"},
                {"predicate": "author_of", "object": "Ética a Nicómaco",
                 "confidence": "high"},
                {"predicate": "reacted_against", "object": "Platón"},
            ],
            related=["Teofrasto", "Eudoxo de Cnido"],
        )),
        ("b.md", _mk_note(
            "Platón",
            relationships=[
                {"predicate": "mentor_of", "object": "Aristóteles"},
                {"predicate": "studied_under", "object": "Sócrates"},
            ],
        )),
    ]
    result = compile_vault_entities(notes)
    db_path = tmp / "knowledge.db"
    write_compiled_entities(db_path, result)
    return db_path


# ---------------------------------------------------------------------------
# Query-level tests
# ---------------------------------------------------------------------------

class QueryRelationsTestCase(TestCase):
    def test_from_entity_filter_returns_typed_only_by_default(self) -> None:
        with TemporaryDirectory() as td:
            db = _build_db(Path(td))
            rows = query_relations(db, from_entity="Aristóteles")
        # 4 typed relations, no legacy (default include_legacy=False)
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(r.is_typed for r in rows))

    def test_from_entity_with_predicate(self) -> None:
        with TemporaryDirectory() as td:
            db = _build_db(Path(td))
            rows = query_relations(
                db, from_entity="Aristóteles", predicate="mentor_of",
            )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].target_entity, "Alejandro Magno")

    def test_to_entity_reverse_lookup(self) -> None:
        with TemporaryDirectory() as td:
            db = _build_db(Path(td))
            rows = query_relations(db, to_entity="Aristóteles", predicate="mentor_of")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].source_entity, "Platón")

    def test_include_legacy(self) -> None:
        with TemporaryDirectory() as td:
            db = _build_db(Path(td))
            typed_only = query_relations(db, from_entity="Aristóteles")
            with_legacy = query_relations(
                db, from_entity="Aristóteles", include_legacy=True,
            )
        # 4 typed + 2 legacy = 6
        self.assertEqual(len(typed_only), 4)
        self.assertEqual(len(with_legacy), 6)
        legacy = [r for r in with_legacy if not r.is_typed]
        self.assertEqual(len(legacy), 2)
        self.assertEqual({r.target_entity for r in legacy},
                         {"Teofrasto", "Eudoxo de Cnido"})

    def test_limit_respected(self) -> None:
        with TemporaryDirectory() as td:
            db = _build_db(Path(td))
            rows = query_relations(db, from_entity="Aristóteles", limit=2)
        self.assertEqual(len(rows), 2)

    def test_multiple_predicates_same_object_returned_both(self) -> None:
        """Aristóteles has both studied_under AND reacted_against on Platón."""
        with TemporaryDirectory() as td:
            db = _build_db(Path(td))
            rows = query_relations(db, from_entity="Aristóteles", to_entity="Platón")
        self.assertEqual(len(rows), 2)
        self.assertEqual({r.predicate for r in rows},
                         {"studied_under", "reacted_against"})

    def test_nonexistent_entity_empty_not_error(self) -> None:
        with TemporaryDirectory() as td:
            db = _build_db(Path(td))
            rows = query_relations(db, from_entity="NoExiste")
        self.assertEqual(rows, [])

    def test_nonexistent_db_empty_not_error(self) -> None:
        with TemporaryDirectory() as td:
            db = Path(td) / "noent.db"
            rows = query_relations(db, from_entity="X")
        self.assertEqual(rows, [])

    def test_confidence_preserved(self) -> None:
        with TemporaryDirectory() as td:
            db = _build_db(Path(td))
            rows = query_relations(
                db, from_entity="Aristóteles", predicate="author_of",
            )
        self.assertEqual(rows[0].confidence, "high")


class SummarizeEntityRelationsTestCase(TestCase):
    def test_summary_groups_typed_by_predicate(self) -> None:
        with TemporaryDirectory() as td:
            db = _build_db(Path(td))
            s = summarize_entity_relations(db, "Aristóteles")
        # Outgoing typed: studied_under(1) + mentor_of(1) + author_of(1) + reacted_against(1)
        self.assertEqual(s.typed_count, 4)
        self.assertEqual(s.legacy_count, 2)
        self.assertIn("studied_under", s.typed_by_predicate)
        self.assertEqual(s.typed_by_predicate["studied_under"][0].target_entity,
                         "Platón")

    def test_summary_includes_incoming(self) -> None:
        with TemporaryDirectory() as td:
            db = _build_db(Path(td))
            s = summarize_entity_relations(db, "Aristóteles")
        # Platón declares mentor_of → Aristóteles
        self.assertIn("mentor_of", s.incoming_typed_by_predicate)
        self.assertEqual(
            s.incoming_typed_by_predicate["mentor_of"][0].source_entity,
            "Platón",
        )

    def test_summary_serializes_to_dict(self) -> None:
        with TemporaryDirectory() as td:
            db = _build_db(Path(td))
            s = summarize_entity_relations(db, "Aristóteles")
        d = s.to_dict()
        self.assertIn("outgoing", d)
        self.assertIn("incoming", d)
        self.assertIn("typed_by_predicate", d["outgoing"])


# ---------------------------------------------------------------------------
# CLI-level tests (brain query-relations)
# ---------------------------------------------------------------------------

class QueryRelationsCliTestCase(TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()
        self.console = Console(record=True)
        self.handle_error = Mock()
        self.app = typer.Typer()
        register_note_and_knowledge_commands(self.app, self.console, self.handle_error)

    def _build_vault_with_db(self, tmp: Path) -> Path:
        """Build a temp vault whose knowledge.db has the test data."""
        from brain_ops.config import load_config
        import yaml

        vault_path = tmp / "vault"
        for folder in (
            "00 - Inbox", "01 - Sources", "02 - Knowledge",
            "03 - Maps", "04 - Projects", "05 - Systems",
            "06 - Daily", "07 - Archive", "Templates",
        ):
            (vault_path / folder).mkdir(parents=True, exist_ok=True)

        config_path = tmp / "vault.yaml"
        config_path.write_text(yaml.safe_dump({
            "vault_path": str(vault_path),
            "default_timezone": "UTC",
            "inbox_folder": "00 - Inbox",
            "sources_folder": "01 - Sources",
            "knowledge_folder": "02 - Knowledge",
            "maps_folder": "03 - Maps",
            "projects_folder": "04 - Projects",
            "systems_folder": "05 - Systems",
            "daily_folder": "06 - Daily",
            "archive_folder": "07 - Archive",
            "templates_folder": "Templates",
            "database_path": str(tmp / "db.sqlite"),
        }))

        # Build the knowledge.db at the expected location
        db_location = vault_path / ".brain-ops" / "knowledge.db"
        db_location.parent.mkdir(parents=True, exist_ok=True)
        notes = [
            ("a.md", _mk_note(
                "Aristóteles",
                relationships=[
                    {"predicate": "studied_under", "object": "Platón"},
                    {"predicate": "mentor_of", "object": "Alejandro Magno"},
                ],
                related=["Teofrasto"],
            )),
        ]
        result = compile_vault_entities(notes)
        write_compiled_entities(db_location, result)

        return config_path

    def test_cli_requires_at_least_one_filter(self) -> None:
        with TemporaryDirectory() as td:
            cfg = self._build_vault_with_db(Path(td))
            result = self.runner.invoke(
                self.app, ["query-relations", "--config", str(cfg)],
            )
        self.assertEqual(result.exit_code, 2)
        self.assertIn("at least one", result.output)

    def test_cli_from_entity_json(self) -> None:
        with TemporaryDirectory() as td:
            cfg = self._build_vault_with_db(Path(td))
            result = self.runner.invoke(
                self.app,
                ["query-relations", "--config", str(cfg),
                 "--from", "Aristóteles", "--json"],
            )
        self.assertEqual(result.exit_code, 0, result.output)
        payload = _json.loads(result.stdout)
        self.assertEqual(len(payload), 2)  # only typed by default
        self.assertTrue(all(row["is_typed"] for row in payload))

    def test_cli_include_legacy(self) -> None:
        with TemporaryDirectory() as td:
            cfg = self._build_vault_with_db(Path(td))
            result = self.runner.invoke(
                self.app,
                ["query-relations", "--config", str(cfg),
                 "--from", "Aristóteles", "--include-legacy", "--json"],
            )
        self.assertEqual(result.exit_code, 0, result.output)
        payload = _json.loads(result.stdout)
        self.assertEqual(len(payload), 3)  # 2 typed + 1 legacy

    def test_cli_predicate_filter(self) -> None:
        with TemporaryDirectory() as td:
            cfg = self._build_vault_with_db(Path(td))
            result = self.runner.invoke(
                self.app,
                ["query-relations", "--config", str(cfg),
                 "--from", "Aristóteles", "--predicate", "mentor_of", "--json"],
            )
        self.assertEqual(result.exit_code, 0, result.output)
        payload = _json.loads(result.stdout)
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["target_entity"], "Alejandro Magno")
