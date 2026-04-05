from __future__ import annotations

from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock, patch

from brain_ops.interfaces.cli.notes import (
    present_daily_summary_command,
    present_enrich_note_command,
    present_promote_note_command,
    run_capture_command,
    run_link_suggestions_command,
)


class CliNoteAdaptersTestCase(TestCase):
    def test_run_capture_command_loads_vault_and_delegates(self) -> None:
        vault = object()
        result = object()
        sink = object()

        with (
            patch("brain_ops.interfaces.cli.notes.load_validated_vault", return_value=vault) as load_mock,
            patch("brain_ops.interfaces.cli.notes.execute_capture_workflow", return_value=result) as workflow_mock,
            patch("brain_ops.interfaces.cli.notes.load_event_sink", return_value=sink),
        ):
            observed = run_capture_command(
                config_path=Path("/tmp/config.yml"),
                text="idea",
                title="Idea",
                note_type="knowledge_note",
                tags=["x", "y"],
                dry_run=True,
            )

        self.assertIs(observed, result)
        load_mock.assert_called_once_with(Path("/tmp/config.yml"), dry_run=True)
        workflow_mock.assert_called_once_with(
            vault,
            text="idea",
            title="Idea",
            note_type="knowledge_note",
            tags=["x", "y"],
            event_sink=sink,
        )

    def test_run_link_suggestions_command_uses_non_dry_run_vault_loader(self) -> None:
        vault = object()
        result = object()

        with (
            patch("brain_ops.interfaces.cli.notes.load_validated_vault", return_value=vault) as load_mock,
            patch("brain_ops.interfaces.cli.notes.execute_link_suggestions_workflow", return_value=result) as workflow_mock,
            patch("brain_ops.interfaces.cli.notes.load_event_sink", return_value=None),
        ):
            observed = run_link_suggestions_command(
                config_path=Path("/tmp/config.yml"),
                note_path=Path("Knowledge/Test.md"),
                limit=7,
            )

        self.assertIs(observed, result)
        load_mock.assert_called_once_with(Path("/tmp/config.yml"), dry_run=False)
        workflow_mock.assert_called_once_with(
            vault,
            note_path=Path("Knowledge/Test.md"),
            limit=7,
            event_sink=None,
        )

    def test_present_daily_summary_command_routes_json_rendering_with_operations(self) -> None:
        console = Mock()
        result = Mock()
        result.operations = [object()]

        with (
            patch("brain_ops.interfaces.cli.notes.run_daily_summary_command", return_value=result) as run_mock,
            patch("brain_ops.interfaces.cli.notes.render_daily_summary", return_value="rendered summary") as render_mock,
            patch("brain_ops.interfaces.cli.notes.print_json_or_rendered_with_operations") as present_mock,
        ):
            present_daily_summary_command(
                console,
                config_path=Path("/tmp/config.yml"),
                date="2026-04-04",
                dry_run=True,
                as_json=True,
            )

        run_mock.assert_called_once_with(
            config_path=Path("/tmp/config.yml"),
            date="2026-04-04",
            dry_run=True,
            as_json=True,
        )
        render_mock.assert_called_once_with(result)
        present_mock.assert_called_once_with(
            console,
            as_json=True,
            value=result,
            operations=result.operations,
            rendered="rendered summary",
        )

    def test_present_promote_note_command_renders_operations_result(self) -> None:
        console = Mock()
        result = Mock()
        result.operations = [object()]

        with (
            patch("brain_ops.interfaces.cli.notes.run_promote_note_command", return_value=result) as run_mock,
            patch("brain_ops.interfaces.cli.notes.render_promoted_note", return_value="promoted") as render_mock,
            patch("brain_ops.interfaces.cli.notes.print_rendered_with_operations") as present_mock,
        ):
            present_promote_note_command(
                console,
                config_path=Path("/tmp/config.yml"),
                note_path=Path("Inbox/Test.md"),
                target_type="knowledge_note",
                dry_run=False,
            )

        run_mock.assert_called_once_with(
            config_path=Path("/tmp/config.yml"),
            note_path=Path("Inbox/Test.md"),
            target_type="knowledge_note",
            dry_run=False,
        )
        render_mock.assert_called_once_with(result)
        present_mock.assert_called_once_with(console, result.operations, "promoted")

    def test_present_enrich_note_command_renders_composed_result(self) -> None:
        console = Mock()
        result = Mock()
        result.operations = [object(), object()]

        with (
            patch("brain_ops.interfaces.cli.notes.run_enrich_note_command", return_value=result) as run_mock,
            patch("brain_ops.interfaces.cli.notes.render_enriched_note", return_value="enriched") as render_mock,
            patch("brain_ops.interfaces.cli.notes.print_rendered_with_operations") as present_mock,
        ):
            present_enrich_note_command(
                console,
                config_path=Path("/tmp/config.yml"),
                note_path=Path("Knowledge/Test.md"),
                query="protein",
                max_sources=4,
                link_limit=6,
                improve=True,
                research=True,
                apply_links=False,
                dry_run=True,
            )

        run_mock.assert_called_once_with(
            config_path=Path("/tmp/config.yml"),
            note_path=Path("Knowledge/Test.md"),
            query="protein",
            max_sources=4,
            link_limit=6,
            improve=True,
            research=True,
            apply_links=False,
            dry_run=True,
        )
        render_mock.assert_called_once_with(result)
        present_mock.assert_called_once_with(console, result.operations, "enriched")
