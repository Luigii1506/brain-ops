"""Tests for `brain show-entity-relations` CLI — Paso 5."""

from __future__ import annotations

import json as _json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import Mock

import typer
import yaml
from rich.console import Console
from typer.testing import CliRunner

from brain_ops.domains.knowledge.compile import compile_vault_entities
from brain_ops.interfaces.cli.commands_notes import register_note_and_knowledge_commands
from brain_ops.storage.sqlite.entities import write_compiled_entities


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


class ShowEntityRelationsCliTestCase(TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()
        self.console = Console(record=True)
        self.handle_error = Mock()
        self.app = typer.Typer()
        register_note_and_knowledge_commands(self.app, self.console, self.handle_error)

    def _build_vault(self, tmp: Path) -> Path:
        vault = tmp / "vault"
        for folder in (
            "00 - Inbox", "01 - Sources", "02 - Knowledge",
            "03 - Maps", "04 - Projects", "05 - Systems",
            "06 - Daily", "07 - Archive", "Templates",
        ):
            (vault / folder).mkdir(parents=True, exist_ok=True)

        config_path = tmp / "vault.yaml"
        config_path.write_text(yaml.safe_dump({
            "vault_path": str(vault),
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

        db = vault / ".brain-ops" / "knowledge.db"
        db.parent.mkdir(parents=True, exist_ok=True)
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
                ],
            )),
        ]
        result = compile_vault_entities(notes)
        write_compiled_entities(db, result)
        return config_path

    def test_json_output_has_outgoing_and_incoming(self) -> None:
        with TemporaryDirectory() as td:
            cfg = self._build_vault(Path(td))
            result = self.runner.invoke(
                self.app,
                ["show-entity-relations", "Aristóteles", "--config", str(cfg), "--json"],
            )
        self.assertEqual(result.exit_code, 0, result.output)
        payload = _json.loads(result.stdout)
        self.assertIn("outgoing", payload)
        self.assertIn("incoming", payload)
        self.assertEqual(payload["outgoing"]["typed_count"], 4)
        self.assertEqual(payload["outgoing"]["legacy_count"], 2)
        self.assertEqual(payload["incoming"]["typed_count"], 1)

    def test_json_typed_grouped_by_predicate(self) -> None:
        with TemporaryDirectory() as td:
            cfg = self._build_vault(Path(td))
            result = self.runner.invoke(
                self.app,
                ["show-entity-relations", "Aristóteles", "--config", str(cfg), "--json"],
            )
        payload = _json.loads(result.stdout)
        predicates_out = payload["outgoing"]["typed_by_predicate"]
        self.assertIn("studied_under", predicates_out)
        self.assertIn("reacted_against", predicates_out)
        # Both point to Platón (same target, different predicates)
        self.assertEqual(
            predicates_out["studied_under"][0]["target_entity"], "Platón",
        )
        self.assertEqual(
            predicates_out["reacted_against"][0]["target_entity"], "Platón",
        )

    def test_text_output_contains_expected_headers(self) -> None:
        with TemporaryDirectory() as td:
            cfg = self._build_vault(Path(td))
            result = self.runner.invoke(
                self.app,
                ["show-entity-relations", "Aristóteles", "--config", str(cfg)],
            )
        self.assertEqual(result.exit_code, 0, result.output)
        # Text output should mention outgoing, incoming, predicates
        self.assertIn("Aristóteles", result.stdout)
        self.assertIn("outgoing", result.stdout)
        self.assertIn("incoming", result.stdout)
        self.assertIn("mentor_of", result.stdout)
        self.assertIn("studied_under", result.stdout)

    def test_only_typed_flag_hides_legacy(self) -> None:
        with TemporaryDirectory() as td:
            cfg = self._build_vault(Path(td))
            result = self.runner.invoke(
                self.app,
                ["show-entity-relations", "Aristóteles",
                 "--config", str(cfg), "--only-typed"],
            )
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertNotIn("Teofrasto", result.stdout)
        self.assertNotIn("Eudoxo", result.stdout)

    def test_only_legacy_flag_hides_typed(self) -> None:
        with TemporaryDirectory() as td:
            cfg = self._build_vault(Path(td))
            result = self.runner.invoke(
                self.app,
                ["show-entity-relations", "Aristóteles",
                 "--config", str(cfg), "--only-legacy"],
            )
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Teofrasto", result.stdout)
        # Should NOT show typed predicates in the body
        self.assertNotIn("studied_under", result.stdout)

    def test_nonexistent_entity_clean_empty(self) -> None:
        with TemporaryDirectory() as td:
            cfg = self._build_vault(Path(td))
            result = self.runner.invoke(
                self.app,
                ["show-entity-relations", "NoExiste", "--config", str(cfg), "--json"],
            )
        self.assertEqual(result.exit_code, 0)
        payload = _json.loads(result.stdout)
        self.assertEqual(payload["outgoing"]["typed_count"], 0)
        self.assertEqual(payload["incoming"]["typed_count"], 0)

    def test_confidence_displayed_when_not_medium(self) -> None:
        with TemporaryDirectory() as td:
            cfg = self._build_vault(Path(td))
            result = self.runner.invoke(
                self.app,
                ["show-entity-relations", "Aristóteles", "--config", str(cfg)],
            )
        # author_of Ética a Nicómaco has confidence=high; should appear
        self.assertIn("high", result.stdout)
