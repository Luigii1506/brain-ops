from __future__ import annotations

from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock, patch

from datetime import UTC, datetime

from brain_ops.core.events import EventLogSummary, new_event
from brain_ops.interfaces.cli.monitoring import present_event_log_summary_command, present_event_log_tail_command


class CliMonitoringAdaptersTestCase(TestCase):
    def test_present_event_log_summary_command_prints_json(self) -> None:
        console = Mock()
        summary = EventLogSummary(
            path=Path("/tmp/events.jsonl"),
            total_events=2,
            first_occurred_at=None,
            last_occurred_at=None,
            names=[("operation.created", 2)],
            sources=[("application.notes", 2)],
            workflows=[("capture", 2)],
            outcomes=[("write_note:created", 2)],
            actions=[("write_note", 2)],
            statuses=[("created", 2)],
            paths=[("Inbox/A.md", 2)],
            days=[("2026-04-04", 2)],
        )

        with patch(
            "brain_ops.interfaces.cli.monitoring.execute_event_log_summary_workflow",
            return_value=summary,
        ) as workflow_mock:
            present_event_log_summary_command(
                console,
                event_log_path=Path("/tmp/events.jsonl"),
                top=3,
                source="application.notes",
                workflow="capture",
                status="created",
                since="2026-04-04",
                until="2026-04-05",
                as_json=True,
            )

        workflow_mock.assert_called_once()
        self.assertEqual(
            workflow_mock.call_args.kwargs,
            {
                "event_log_path": Path("/tmp/events.jsonl"),
                "top": 3,
                "source": "application.notes",
                "workflow": "capture",
                "status": "created",
                "since": "2026-04-04",
                "until": "2026-04-05",
                "load_event_log_path": workflow_mock.call_args.kwargs["load_event_log_path"],
            },
        )
        console.print_json.assert_called_once_with(data=summary.to_dict())

    def test_present_event_log_summary_command_prints_table(self) -> None:
        console = Mock()
        summary = EventLogSummary(
            path=Path("/tmp/events.jsonl"),
            total_events=2,
            first_occurred_at=None,
            last_occurred_at=None,
            names=[("operation.created", 2)],
            sources=[("application.notes", 2)],
            workflows=[("capture", 2)],
            outcomes=[("write_note:created", 2)],
            actions=[("write_note", 2)],
            statuses=[("created", 2)],
            paths=[("Inbox/A.md", 2)],
            days=[("2026-04-04", 2)],
        )
        table = object()

        with (
            patch(
                "brain_ops.interfaces.cli.monitoring.execute_event_log_summary_workflow",
                return_value=summary,
            ) as workflow_mock,
            patch("brain_ops.interfaces.cli.monitoring.build_event_log_summary_table", return_value=table) as table_mock,
        ):
            present_event_log_summary_command(
                console,
                event_log_path=None,
                top=5,
                source=None,
                workflow=None,
                status=None,
                since=None,
                until=None,
                as_json=False,
            )

        workflow_mock.assert_called_once()
        table_mock.assert_called_once_with(summary)
        console.print.assert_called_once_with(table)

    def test_present_event_log_tail_command_prints_json(self) -> None:
        console = Mock()
        events = [
            new_event(
                "operation.created",
                source="application.notes",
                payload={"path": "Inbox/A.md"},
                occurred_at=datetime(2026, 4, 4, 12, 0, tzinfo=UTC),
            )
        ]

        with patch(
            "brain_ops.interfaces.cli.monitoring.execute_event_log_tail_workflow",
            return_value=events,
        ) as workflow_mock:
            present_event_log_tail_command(
                console,
                event_log_path=Path("/tmp/events.jsonl"),
                limit=2,
                source="application.notes",
                workflow="capture",
                status="created",
                since="2026-04-04T12:00:00+00:00",
                until="2026-04-04T13:00:00+00:00",
                as_json=True,
            )

        workflow_mock.assert_called_once()
        self.assertEqual(
            workflow_mock.call_args.kwargs,
            {
                "event_log_path": Path("/tmp/events.jsonl"),
                "limit": 2,
                "source": "application.notes",
                "workflow": "capture",
                "status": "created",
                "since": "2026-04-04T12:00:00+00:00",
                "until": "2026-04-04T13:00:00+00:00",
                "load_event_log_path": workflow_mock.call_args.kwargs["load_event_log_path"],
            },
        )
        console.print_json.assert_called_once()

    def test_present_event_log_tail_command_prints_table(self) -> None:
        console = Mock()
        events = [
            new_event(
                "operation.created",
                source="application.notes",
                payload={"path": "Inbox/A.md"},
                occurred_at=datetime(2026, 4, 4, 12, 0, tzinfo=UTC),
            )
        ]
        table = object()

        with (
            patch(
                "brain_ops.interfaces.cli.monitoring.execute_event_log_tail_workflow",
                return_value=events,
            ) as workflow_mock,
            patch("brain_ops.interfaces.cli.monitoring.build_event_log_tail_table", return_value=table) as table_mock,
        ):
            present_event_log_tail_command(
                console,
                event_log_path=None,
                limit=5,
                source=None,
                workflow=None,
                status=None,
                since=None,
                until=None,
                as_json=False,
            )

        workflow_mock.assert_called_once()
        table_mock.assert_called_once_with(events)
        console.print.assert_called_once_with(table)
