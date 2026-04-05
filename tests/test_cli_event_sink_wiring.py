from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock, patch

from brain_ops.core.events import JsonlFileEventSink
from brain_ops.interfaces.cli.conversation import run_handle_input_command
from brain_ops.interfaces.cli.knowledge import run_normalize_frontmatter_command
from brain_ops.interfaces.cli.notes import run_capture_command
from brain_ops.interfaces.cli.personal_logging import run_log_body_metrics_command
from brain_ops.interfaces.cli.personal_management import run_create_diet_plan_command
from brain_ops.interfaces.cli.system import present_init_command


class CliEventSinkWiringTestCase(TestCase):
    def test_conversation_adapter_builds_jsonl_sink_from_env(self) -> None:
        target = None
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "events.jsonl"
            with patch.dict(os.environ, {"BRAIN_OPS_EVENT_LOG": str(target)}, clear=True):
                with patch(
                    "brain_ops.interfaces.cli.conversation.execute_handle_input_workflow",
                    return_value=object(),
                ) as workflow_mock:
                    run_handle_input_command(
                        config_path=Path("/tmp/config.yml"),
                        text="registra desayuno",
                        dry_run=False,
                        use_llm=None,
                        session_id="session-1",
                    )

        sink = workflow_mock.call_args.kwargs["event_sink"]
        self.assertIsInstance(sink, JsonlFileEventSink)
        self.assertEqual(sink.path, target)

    def test_note_adapter_builds_jsonl_sink_from_env(self) -> None:
        vault = object()
        target = None
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "events.jsonl"
            with patch.dict(os.environ, {"BRAIN_OPS_EVENT_LOG": str(target)}, clear=True):
                with (
                    patch("brain_ops.interfaces.cli.notes.load_validated_vault", return_value=vault),
                    patch(
                        "brain_ops.interfaces.cli.notes.execute_capture_workflow",
                        return_value=object(),
                    ) as workflow_mock,
                ):
                    run_capture_command(
                        config_path=Path("/tmp/config.yml"),
                        text="idea",
                        title="Idea",
                        note_type="knowledge_note",
                        tags=["x"],
                        dry_run=True,
                    )

        sink = workflow_mock.call_args.kwargs["event_sink"]
        self.assertIsInstance(sink, JsonlFileEventSink)
        self.assertEqual(sink.path, target)

    def test_knowledge_adapter_builds_jsonl_sink_from_env(self) -> None:
        target = None
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "events.jsonl"
            with patch.dict(os.environ, {"BRAIN_OPS_EVENT_LOG": str(target)}, clear=True):
                with patch(
                    "brain_ops.interfaces.cli.knowledge.execute_normalize_frontmatter_workflow",
                    return_value=object(),
                ) as workflow_mock:
                    run_normalize_frontmatter_command(
                        config_path=Path("/tmp/config.yml"),
                        dry_run=True,
                    )

        sink = workflow_mock.call_args.kwargs["event_sink"]
        self.assertIsInstance(sink, JsonlFileEventSink)
        self.assertEqual(sink.path, target)

    def test_personal_logging_adapter_builds_jsonl_sink_from_env(self) -> None:
        target = None
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "events.jsonl"
            with patch.dict(os.environ, {"BRAIN_OPS_EVENT_LOG": str(target)}, clear=True):
                with patch(
                    "brain_ops.interfaces.cli.personal_logging.execute_log_body_metrics_workflow",
                    return_value=object(),
                ) as workflow_mock:
                    run_log_body_metrics_command(
                        config_path=Path("/tmp/config.yml"),
                        weight_kg=80.0,
                        body_fat_pct=None,
                        fat_mass_kg=None,
                        muscle_mass_kg=None,
                        visceral_fat=None,
                        bmr_calories=None,
                        arm_cm=None,
                        waist_cm=None,
                        thigh_cm=None,
                        calf_cm=None,
                        logged_at=None,
                        note=None,
                        dry_run=True,
                    )

        sink = workflow_mock.call_args.kwargs["event_sink"]
        self.assertIsInstance(sink, JsonlFileEventSink)
        self.assertEqual(sink.path, target)

    def test_personal_management_adapter_builds_jsonl_sink_from_env(self) -> None:
        target = None
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "events.jsonl"
            with patch.dict(os.environ, {"BRAIN_OPS_EVENT_LOG": str(target)}, clear=True):
                with patch(
                    "brain_ops.interfaces.cli.personal_management.execute_create_diet_plan_workflow",
                    return_value=object(),
                ) as workflow_mock:
                    run_create_diet_plan_command(
                        config_path=Path("/tmp/config.yml"),
                        name="Lean Bulk",
                        meal=["breakfast|eggs"],
                        notes=None,
                        activate=False,
                        dry_run=True,
                    )

        sink = workflow_mock.call_args.kwargs["event_sink"]
        self.assertIsInstance(sink, JsonlFileEventSink)
        self.assertEqual(sink.path, target)

    def test_system_adapter_builds_jsonl_sink_from_env(self) -> None:
        console = Mock()
        print_operations = Mock()
        target = None
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "events.jsonl"
            with patch.dict(os.environ, {"BRAIN_OPS_EVENT_LOG": str(target)}, clear=True):
                with patch(
                    "brain_ops.interfaces.cli.system.execute_init_workflow",
                    return_value=[],
                ) as workflow_mock:
                    present_init_command(
                        console,
                        vault_path=Path("/tmp/vault"),
                        config_output=Path("/tmp/config.yml"),
                        force=True,
                        dry_run=False,
                        print_operations=print_operations,
                    )

        sink = workflow_mock.call_args.kwargs["event_sink"]
        self.assertIsInstance(sink, JsonlFileEventSink)
        self.assertEqual(sink.path, target)


if __name__ == "__main__":
    import unittest

    unittest.main()
