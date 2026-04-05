from __future__ import annotations

from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock, patch

from brain_ops.interfaces.cli.conversation import (
    present_handle_input_command,
    present_route_input_command,
    run_handle_input_command,
    run_route_input_command,
)


class CliConversationAdaptersTestCase(TestCase):
    def test_run_route_input_command_delegates_to_application_workflow(self) -> None:
        result = object()

        with patch(
            "brain_ops.interfaces.cli.conversation.execute_route_input_workflow",
            return_value=result,
        ) as workflow_mock:
            observed = run_route_input_command(
                config_path=Path("/tmp/config.yml"),
                text="hola",
                use_llm=True,
            )

        self.assertIs(observed, result)
        workflow_mock.assert_called_once_with(
            config_path=Path("/tmp/config.yml"),
            text="hola",
            use_llm=True,
            load_config=workflow_mock.call_args.kwargs["load_config"],
        )

    def test_run_handle_input_command_delegates_to_application_workflow(self) -> None:
        result = object()
        sink = object()

        with patch(
            "brain_ops.interfaces.cli.conversation.execute_handle_input_workflow",
            return_value=result,
        ) as workflow_mock, patch(
            "brain_ops.interfaces.cli.conversation.load_event_sink",
            return_value=sink,
        ):
            observed = run_handle_input_command(
                config_path=Path("/tmp/config.yml"),
                text="registra desayuno",
                dry_run=False,
                use_llm=None,
                session_id="session-1",
            )

        self.assertIs(observed, result)
        workflow_mock.assert_called_once_with(
            config_path=Path("/tmp/config.yml"),
            text="registra desayuno",
            dry_run=False,
            use_llm=None,
            session_id="session-1",
            load_config=workflow_mock.call_args.kwargs["load_config"],
            event_sink=sink,
        )

    def test_present_route_input_command_renders_json_or_text(self) -> None:
        console = Mock()
        result = Mock()

        with (
            patch("brain_ops.interfaces.cli.conversation.run_route_input_command", return_value=result) as run_mock,
            patch("brain_ops.interfaces.cli.conversation.render_route_decision", return_value="route rendered") as render_mock,
            patch("brain_ops.interfaces.cli.conversation.print_json_or_rendered") as present_mock,
        ):
            present_route_input_command(
                console,
                config_path=Path("/tmp/config.yml"),
                text="como voy",
                as_json=True,
                use_llm=False,
            )

        run_mock.assert_called_once_with(
            config_path=Path("/tmp/config.yml"),
            text="como voy",
            use_llm=False,
        )
        render_mock.assert_called_once_with(result)
        present_mock.assert_called_once_with(
            console,
            as_json=True,
            value=result,
            rendered="route rendered",
        )

    def test_present_handle_input_command_renders_operations_result(self) -> None:
        console = Mock()
        result = Mock()
        result.operations = [object()]

        with (
            patch("brain_ops.interfaces.cli.conversation.run_handle_input_command", return_value=result) as run_mock,
            patch("brain_ops.interfaces.cli.conversation.render_handle_input", return_value="handle rendered") as render_mock,
            patch("brain_ops.interfaces.cli.conversation.print_handle_input_result") as present_mock,
        ):
            present_handle_input_command(
                console,
                config_path=Path("/tmp/config.yml"),
                text="log meal eggs",
                dry_run=True,
                as_json=False,
                use_llm=True,
                session_id="session-2",
            )

        run_mock.assert_called_once_with(
            config_path=Path("/tmp/config.yml"),
            text="log meal eggs",
            dry_run=True,
            use_llm=True,
            session_id="session-2",
        )
        render_mock.assert_called_once_with(result)
        present_mock.assert_called_once_with(
            console,
            as_json=False,
            result=result,
            operations=result.operations,
            rendered="handle rendered",
        )
