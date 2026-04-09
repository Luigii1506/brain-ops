from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

import typer
from rich.console import Console
from typer.testing import CliRunner

from brain_ops.domains.knowledge.extraction_store import load_extraction_records
from brain_ops.frontmatter import dump_frontmatter
from brain_ops.interfaces.cli.commands_notes import register_note_and_knowledge_commands


class PostProcessCommandTestCase(TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()
        self.console = Console(record=True)
        self.handle_error = Mock()

    def test_post_process_persists_richer_direct_edit_extraction(self) -> None:
        with TemporaryDirectory() as tmpdir:
            vault_path = Path(tmpdir) / "vault"
            (vault_path / "01 - Sources").mkdir(parents=True, exist_ok=True)
            note_path = vault_path / "02 - Knowledge" / "Alejandro Magno.md"
            note_path.parent.mkdir(parents=True, exist_ok=True)

            note_text = dump_frontmatter(
                {
                    "entity": True,
                    "name": "Alejandro Magno",
                    "type": "person",
                    "related": ["Aristóteles", "Imperio Persa"],
                },
                """
## Identity

- Rey de Macedonia y conquistador helenístico.

## Key Facts

- Nació en 356 a.C.
- Fue alumno de Aristóteles.

## Timeline

- **356 a.C.** — Nace en Pella.
- **334 a.C.** — Cruza al Asia Menor.

## Impact

- Transformó el equilibrio político del Mediterráneo oriental.

## Strategic Insights

- Integró conquista militar con fundación de ciudades.
""",
            )

            fake_vault = SimpleNamespace(config=SimpleNamespace(vault_path=vault_path))
            app = typer.Typer()
            register_note_and_knowledge_commands(app, self.console, self.handle_error)

            with (
                patch("brain_ops.interfaces.cli.runtime.load_validated_vault", return_value=fake_vault),
                patch("brain_ops.interfaces.cli.runtime.load_event_sink", return_value=None),
                patch("brain_ops.storage.obsidian.list_vault_markdown_notes", return_value=[note_path]),
                patch(
                    "brain_ops.storage.obsidian.read_note_text",
                    return_value=(note_path, note_path.relative_to(vault_path), note_text),
                ),
                patch(
                    "brain_ops.domains.knowledge.ingest.fetch_url_content",
                    return_value=("full raw source body", "Alejandro Magno"),
                ),
                patch("brain_ops.application.knowledge.execute_compile_knowledge_workflow") as compile_mock,
            ):
                result = self.runner.invoke(
                    app,
                    [
                        "post-process",
                        "Alejandro Magno",
                        "--source-url",
                        "https://es.wikipedia.org/wiki/Alejandro_Magno",
                    ],
                )

            self.assertEqual(result.exit_code, 0)
            compile_mock.assert_called_once()

            records = load_extraction_records(vault_path / ".brain-ops" / "extractions")
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].prompt_version, "direct_agent_v2")
            self.assertEqual(records[0].source_type, "direct_edit")

            extraction = records[0].raw_llm_json
            self.assertEqual(extraction["title"], "Alejandro Magno")
            self.assertEqual(extraction["source_type"], "direct_edit")
            self.assertIn("Rey de Macedonia", extraction["summary"])
            self.assertIn("Nació en 356 a.C.", extraction["core_facts"])
            self.assertIn("Transformó el equilibrio político", extraction["key_insights"][0])
            self.assertEqual(extraction["timeline"][0]["date"], "356 a.C.")
            self.assertEqual(extraction["relationships"][0]["object"], "Aristóteles")
            self.assertIn(
                "Integró conquista militar con fundación de ciudades.",
                extraction["strategic_patterns"],
            )

