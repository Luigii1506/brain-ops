from __future__ import annotations

from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock, patch

from brain_ops.interfaces.cli.knowledge import (
    present_audit_vault_command,
    present_process_inbox_command,
    present_weekly_review_command,
    run_normalize_frontmatter_command,
)


class CliKnowledgeAdaptersTestCase(TestCase):
    def test_run_normalize_frontmatter_command_delegates_to_application_workflow(self) -> None:
        result = object()
        sink = object()

        with patch(
            "brain_ops.interfaces.cli.knowledge.execute_normalize_frontmatter_workflow",
            return_value=result,
        ) as workflow_mock, patch(
            "brain_ops.interfaces.cli.knowledge.load_event_sink",
            return_value=sink,
        ):
            observed = run_normalize_frontmatter_command(
                config_path=Path("/tmp/config.yml"),
                dry_run=True,
            )

        self.assertIs(observed, result)
        workflow_mock.assert_called_once_with(
            config_path=Path("/tmp/config.yml"),
            dry_run=True,
            load_vault=workflow_mock.call_args.kwargs["load_vault"],
            event_sink=sink,
        )

    def test_present_process_inbox_command_renders_operations_result(self) -> None:
        console = Mock()
        summary = Mock()
        summary.operations = [object()]

        with (
            patch("brain_ops.interfaces.cli.knowledge.run_process_inbox_command", return_value=summary) as run_mock,
            patch("brain_ops.interfaces.cli.knowledge.render_inbox_report", return_value="inbox report") as render_mock,
            patch("brain_ops.interfaces.cli.knowledge.print_rendered_with_operations") as present_mock,
        ):
            present_process_inbox_command(
                console,
                config_path=Path("/tmp/config.yml"),
                dry_run=True,
                write_report=False,
                improve_structure=True,
            )

        run_mock.assert_called_once_with(
            config_path=Path("/tmp/config.yml"),
            dry_run=True,
            write_report=False,
            improve_structure=True,
        )
        render_mock.assert_called_once_with(summary)
        present_mock.assert_called_once_with(console, summary.operations, "inbox report")

    def test_present_weekly_review_command_renders_operations_result(self) -> None:
        console = Mock()
        summary = Mock()
        summary.operations = [object(), object()]

        with (
            patch("brain_ops.interfaces.cli.knowledge.run_weekly_review_command", return_value=summary) as run_mock,
            patch("brain_ops.interfaces.cli.knowledge.render_weekly_review", return_value="weekly review") as render_mock,
            patch("brain_ops.interfaces.cli.knowledge.print_rendered_with_operations") as present_mock,
        ):
            present_weekly_review_command(
                console,
                config_path=Path("/tmp/config.yml"),
                dry_run=False,
                stale_days=14,
                write_report=True,
            )

        run_mock.assert_called_once_with(
            config_path=Path("/tmp/config.yml"),
            dry_run=False,
            stale_days=14,
            write_report=True,
        )
        render_mock.assert_called_once_with(summary)
        present_mock.assert_called_once_with(console, summary.operations, "weekly review")

    def test_present_audit_vault_command_renders_operations_result(self) -> None:
        console = Mock()
        summary = Mock()
        summary.operations = [object()]

        with (
            patch("brain_ops.interfaces.cli.knowledge.run_audit_vault_command", return_value=summary) as run_mock,
            patch("brain_ops.interfaces.cli.knowledge.render_vault_audit", return_value="audit report") as render_mock,
            patch("brain_ops.interfaces.cli.knowledge.print_rendered_with_operations") as present_mock,
        ):
            present_audit_vault_command(
                console,
                config_path=Path("/tmp/config.yml"),
                write_report=True,
            )

        run_mock.assert_called_once_with(
            config_path=Path("/tmp/config.yml"),
            write_report=True,
        )
        render_mock.assert_called_once_with(summary)
        present_mock.assert_called_once_with(console, summary.operations, "audit report")
