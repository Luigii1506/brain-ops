from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

import typer
from rich.console import Console
from typer.testing import CliRunner

from brain_ops.frontmatter import dump_frontmatter
from brain_ops.interfaces.cli.commands_notes import register_note_and_knowledge_commands


class PlanDirectEnrichCommandTestCase(TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()
        self.console = Console(record=True)
        self.handle_error = Mock()

    def test_plan_direct_enrich_persists_raw_index_and_plan_file(self) -> None:
        with TemporaryDirectory() as tmpdir:
            vault_path = Path(tmpdir) / "vault"
            note_path = vault_path / "02 - Knowledge" / "Albert Einstein.md"
            note_path.parent.mkdir(parents=True, exist_ok=True)
            note_text = dump_frontmatter(
                {
                    "entity": True,
                    "name": "Albert Einstein",
                    "type": "person",
                    "subtype": "person",
                },
                "## Identity\n\nTemplate note.",
            )

            fake_vault = SimpleNamespace(config=SimpleNamespace(vault_path=vault_path))
            app = typer.Typer()
            register_note_and_knowledge_commands(app, self.console, self.handle_error)

            with (
                patch("brain_ops.interfaces.cli.runtime.load_validated_vault", return_value=fake_vault),
                patch(
                    "brain_ops.domains.knowledge.ingest.fetch_url_document",
                    return_value=SimpleNamespace(
                        text="Biography\n[\neditar\n]\nEinstein studied in Zurich.\n\nScientific career\n[\neditar\n]\nHe published relativity and quantum papers.",
                        title="Albert Einstein",
                        html="<html><body><h1>Albert Einstein</h1></body></html>",
                        source_profile="generic_html",
                    ),
                ),
                patch("brain_ops.storage.obsidian.list_vault_markdown_notes", return_value=[note_path]),
                patch(
                    "brain_ops.storage.obsidian.read_note_text",
                    return_value=(note_path, note_path.relative_to(vault_path), note_text),
                ),
            ):
                result = self.runner.invoke(
                    app,
                    [
                        "plan-direct-enrich",
                        "Albert Einstein",
                        "--url",
                        "https://en.wikipedia.org/wiki/Albert_Einstein",
                        "--json",
                    ],
                )

            self.assertEqual(result.exit_code, 0)
            data = json.loads(result.stdout)
            self.assertEqual(data["entity_name"], "Albert Einstein")
            self.assertEqual(data["subtype"], "person")
            self.assertTrue(data["passes"])
            self.assertTrue(Path(data["raw_file"]).exists())
            self.assertTrue(Path(data["plan_file"]).exists())
            index_data = json.loads((vault_path / ".brain-ops" / "raw" / "_index.json").read_text(encoding="utf-8"))
            self.assertIn("Albert Einstein", index_data)
