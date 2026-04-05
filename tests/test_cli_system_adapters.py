from __future__ import annotations

from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock, patch

from brain_ops.interfaces.cli.openclaw import present_openclaw_manifest
from brain_ops.interfaces.cli.system import (
    present_info_command,
    present_init_command,
    present_init_db_command,
)


class CliSystemAdaptersTestCase(TestCase):
    def test_present_info_command_renders_built_info_table(self) -> None:
        console = Mock()
        config = object()
        table = object()

        with (
            patch("brain_ops.interfaces.cli.system.execute_info_workflow", return_value=config) as workflow_mock,
            patch("brain_ops.interfaces.cli.system.build_info_table", return_value=table) as table_mock,
        ):
            present_info_command(
                console,
                version="1.2.3",
                config_path=Path("/tmp/config.yml"),
            )

        workflow_mock.assert_called_once()
        self.assertEqual(
            workflow_mock.call_args.kwargs,
            {
                "config_path": Path("/tmp/config.yml"),
                "load_config": workflow_mock.call_args.kwargs["load_config"],
            },
        )
        table_mock.assert_called_once_with("1.2.3", config)
        console.print.assert_called_once_with(table)

    def test_present_init_command_prints_operations_from_workflow(self) -> None:
        console = Mock()
        operations = [object()]
        print_operations = Mock()
        sink = object()

        with patch("brain_ops.interfaces.cli.system.execute_init_workflow", return_value=operations) as workflow_mock, patch(
            "brain_ops.interfaces.cli.system.load_event_sink",
            return_value=sink,
        ):
            present_init_command(
                console,
                vault_path=Path("/tmp/vault"),
                config_output=Path("/tmp/config.yml"),
                force=True,
                dry_run=False,
                print_operations=print_operations,
            )

        workflow_mock.assert_called_once()
        self.assertEqual(
            workflow_mock.call_args.kwargs,
            {
                "vault_path": Path("/tmp/vault"),
                "config_output": Path("/tmp/config.yml"),
                "force": True,
                "dry_run": False,
                "initialize_config": workflow_mock.call_args.kwargs["initialize_config"],
                "event_sink": sink,
            },
        )
        print_operations.assert_called_once_with(console, operations)

    def test_present_init_db_command_prints_operations_from_workflow(self) -> None:
        console = Mock()
        operations = [object()]
        print_operations = Mock()
        sink = object()

        with patch("brain_ops.interfaces.cli.system.execute_init_db_workflow", return_value=operations) as workflow_mock, patch(
            "brain_ops.interfaces.cli.system.load_event_sink",
            return_value=sink,
        ):
            present_init_db_command(
                console,
                config_path=Path("/tmp/config.yml"),
                dry_run=True,
                print_operations=print_operations,
            )

        workflow_mock.assert_called_once()
        self.assertEqual(
            workflow_mock.call_args.kwargs,
            {
                "config_path": Path("/tmp/config.yml"),
                "dry_run": True,
                "load_config": workflow_mock.call_args.kwargs["load_config"],
                "initialize_database": workflow_mock.call_args.kwargs["initialize_database"],
                "event_sink": sink,
            },
        )
        print_operations.assert_called_once_with(console, operations)

    def test_present_openclaw_manifest_writes_file_and_skips_table_when_not_json(self) -> None:
        console = Mock()

        with patch(
            "brain_ops.interfaces.cli.openclaw.execute_openclaw_manifest_workflow",
            return_value=Path("/tmp/openclaw.json"),
        ) as workflow_mock:
            present_openclaw_manifest(
                console,
                as_json=False,
                output=Path("/tmp/openclaw.json"),
            )

        workflow_mock.assert_called_once()
        console.print.assert_called_once_with("Wrote OpenClaw manifest to /tmp/openclaw.json")
        console.print_json.assert_not_called()

    def test_present_openclaw_manifest_prints_json_when_requested(self) -> None:
        console = Mock()

        with patch(
            "brain_ops.interfaces.cli.openclaw.execute_openclaw_manifest_workflow",
            return_value=None,
        ) as workflow_mock:
            present_openclaw_manifest(console, as_json=True, output=None)

        workflow_mock.assert_called_once()
        console.print_json.assert_called_once()
        console.print.assert_not_called()

    def test_present_openclaw_manifest_prints_table_when_not_json_and_no_output(self) -> None:
        console = Mock()
        table = object()

        with (
            patch(
                "brain_ops.interfaces.cli.openclaw.execute_openclaw_manifest_workflow",
                return_value=None,
            ) as workflow_mock,
            patch("brain_ops.interfaces.cli.openclaw.build_openclaw_manifest_table", return_value=table) as table_mock,
        ):
            present_openclaw_manifest(console, as_json=False, output=None)

        workflow_mock.assert_called_once()
        table_mock.assert_called_once_with()
        console.print.assert_called_once_with(table)
