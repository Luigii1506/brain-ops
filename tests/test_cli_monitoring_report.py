from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock, patch

from brain_ops.application.monitoring import EventLogFailures, EventLogHotspots, EventLogReport
from brain_ops.core.events import EventLogDayActivity, EventLogSummary, new_event
from brain_ops.interfaces.cli.monitoring import (
    present_event_log_failures_command,
    present_event_log_hotspots_command,
    present_event_log_report_command,
)


class CliMonitoringReportTestCase(TestCase):
    def test_present_event_log_failures_command_prints_json(self) -> None:
        console = Mock()
        summary = EventLogSummary(
            path=Path("/tmp/events.jsonl"),
            total_events=1,
            first_occurred_at=None,
            last_occurred_at=None,
            names=[("operation.failed", 1)],
            sources=[("application.notes", 1)],
            workflows=[("capture", 1)],
            outcomes=[("write_note:failed", 1)],
            actions=[("write_note", 1)],
            statuses=[("failed", 1)],
            paths=[("Inbox/A.md", 1)],
            days=[("2026-04-04", 1)],
        )
        failures = EventLogFailures(
            summary=summary,
            recent_events=[
                new_event(
                    "operation.failed",
                    source="application.notes",
                    payload={"workflow": "capture", "status": "failed", "path": "Inbox/A.md"},
                    occurred_at=datetime(2026, 4, 4, 10, 0, tzinfo=UTC),
                )
            ],
        )

        with patch("brain_ops.interfaces.cli.monitoring.execute_event_log_failures_workflow", return_value=failures):
            present_event_log_failures_command(
                console,
                event_log_path=Path("/tmp/events.jsonl"),
                top=3,
                limit=2,
                source="application.notes",
                workflow="capture",
                since="2026-04-04",
                until="2026-04-05",
                as_json=True,
            )

        console.print_json.assert_called_once_with(data=failures.to_dict())

    def test_present_event_log_failures_command_prints_summary_then_tail(self) -> None:
        console = Mock()
        summary = EventLogSummary(
            path=Path("/tmp/events.jsonl"),
            total_events=1,
            first_occurred_at=None,
            last_occurred_at=None,
            names=[("operation.failed", 1)],
            sources=[("application.notes", 1)],
            workflows=[("capture", 1)],
            outcomes=[("write_note:failed", 1)],
            actions=[("write_note", 1)],
            statuses=[("failed", 1)],
            paths=[("Inbox/A.md", 1)],
            days=[("2026-04-04", 1)],
        )
        failures = EventLogFailures(summary=summary, recent_events=[])
        failures_table = object()
        tail_table = object()

        with (
            patch("brain_ops.interfaces.cli.monitoring.execute_event_log_failures_workflow", return_value=failures),
            patch("brain_ops.interfaces.cli.monitoring.build_event_log_failures_table", return_value=failures_table) as failures_mock,
            patch("brain_ops.interfaces.cli.monitoring.build_event_log_tail_table", return_value=tail_table) as tail_mock,
        ):
            present_event_log_failures_command(
                console,
                event_log_path=None,
                top=5,
                limit=10,
                source=None,
                workflow=None,
                since=None,
                until=None,
                as_json=False,
            )

        failures_mock.assert_called_once_with(summary)
        tail_mock.assert_called_once_with([])
        self.assertEqual(console.print.call_args_list[0].args, (failures_table,))
        self.assertEqual(console.print.call_args_list[1].args, (tail_table,))

    def test_present_event_log_hotspots_command_prints_json(self) -> None:
        console = Mock()
        summary = EventLogSummary(
            path=Path("/tmp/events.jsonl"),
            total_events=1,
            first_occurred_at=None,
            last_occurred_at=None,
            names=[("operation.created", 1)],
            sources=[("application.notes", 1)],
            workflows=[("capture", 1)],
            outcomes=[("write_note:created", 1)],
            actions=[("write_note", 1)],
            statuses=[("created", 1)],
            paths=[("Inbox/A.md", 1)],
            days=[("2026-04-04", 1)],
        )
        hotspots = EventLogHotspots(
            summary=summary,
            highlights={
                "latest_day": None,
                "latest_day_total_events": 0,
                "latest_day_top_source": None,
                "latest_day_top_workflow": None,
                "latest_day_top_outcome": None,
                "top_path": "Inbox/A.md",
            },
        )

        with patch("brain_ops.interfaces.cli.monitoring.execute_event_log_hotspots_workflow", return_value=hotspots):
            present_event_log_hotspots_command(
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

        console.print_json.assert_called_once_with(data=hotspots.to_dict())

    def test_present_event_log_hotspots_command_prints_highlights_then_hotspots(self) -> None:
        console = Mock()
        summary = EventLogSummary(
            path=Path("/tmp/events.jsonl"),
            total_events=1,
            first_occurred_at=None,
            last_occurred_at=None,
            names=[("operation.created", 1)],
            sources=[("application.notes", 1)],
            workflows=[("capture", 1)],
            outcomes=[("write_note:created", 1)],
            actions=[("write_note", 1)],
            statuses=[("created", 1)],
            paths=[("Inbox/A.md", 1)],
            days=[("2026-04-04", 1)],
        )
        hotspots = EventLogHotspots(
            summary=summary,
            highlights={
                "latest_day": None,
                "latest_day_total_events": 0,
                "latest_day_top_source": None,
                "latest_day_top_workflow": None,
                "latest_day_top_outcome": None,
                "top_path": "Inbox/A.md",
            },
        )
        highlights_table = object()
        hotspots_table = object()

        with (
            patch("brain_ops.interfaces.cli.monitoring.execute_event_log_hotspots_workflow", return_value=hotspots),
            patch("brain_ops.interfaces.cli.monitoring.build_event_log_highlights_table", return_value=highlights_table) as highlights_mock,
            patch("brain_ops.interfaces.cli.monitoring.build_event_log_hotspots_table", return_value=hotspots_table) as hotspots_mock,
        ):
            present_event_log_hotspots_command(
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

        highlights_mock.assert_called_once_with(hotspots.highlights)
        hotspots_mock.assert_called_once_with(hotspots.to_dict())
        self.assertEqual(console.print.call_args_list[0].args, (highlights_table,))
        self.assertEqual(console.print.call_args_list[1].args, (hotspots_table,))

    def test_present_event_log_report_command_prints_json(self) -> None:
        console = Mock()
        report = EventLogReport(
            summary=EventLogSummary(
                path=Path("/tmp/events.jsonl"),
                total_events=1,
                first_occurred_at=None,
                last_occurred_at=None,
                names=[("operation.created", 1)],
                sources=[("application.notes", 1)],
                workflows=[("capture", 1)],
                outcomes=[("write_note:created", 1)],
                actions=[("write_note", 1)],
                statuses=[("created", 1)],
                paths=[("Inbox/A.md", 1)],
                days=[("2026-04-04", 1)],
            ),
            daily_activity=[
                EventLogDayActivity(
                    day="2026-04-04",
                    total_events=1,
                    sources=[("application.notes", 1)],
                    workflows=[("capture", 1)],
                    outcomes=[("write_note:created", 1)],
                )
            ],
            highlights={
                "latest_day": "2026-04-04",
                "latest_day_total_events": 1,
                "latest_day_top_source": "application.notes",
                "latest_day_top_workflow": "capture",
                "latest_day_top_outcome": "write_note:created",
                "top_path": "Inbox/A.md",
            },
            recent_events=[
                new_event(
                    "operation.created",
                    source="application.notes",
                    payload={"workflow": "capture", "path": "Inbox/A.md"},
                    occurred_at=datetime(2026, 4, 4, 10, 0, tzinfo=UTC),
                )
            ],
        )

        with patch("brain_ops.interfaces.cli.monitoring.execute_event_log_report_workflow", return_value=report) as workflow_mock:
            present_event_log_report_command(
                console,
                event_log_path=Path("/tmp/events.jsonl"),
                top=3,
                limit=2,
                source="application.notes",
                workflow="capture",
                status="created",
                since="2026-04-04",
                until="2026-04-05",
                as_json=True,
            )

        workflow_mock.assert_called_once()
        console.print_json.assert_called_once_with(data=report.to_dict())

    def test_present_event_log_report_command_prints_summary_then_tail(self) -> None:
        console = Mock()
        summary = EventLogSummary(
            path=Path("/tmp/events.jsonl"),
            total_events=1,
            first_occurred_at=None,
            last_occurred_at=None,
            names=[("operation.created", 1)],
            sources=[("application.notes", 1)],
            workflows=[("capture", 1)],
            outcomes=[("write_note:created", 1)],
            actions=[("write_note", 1)],
            statuses=[("created", 1)],
            paths=[("Inbox/A.md", 1)],
            days=[("2026-04-04", 1)],
        )
        events = [
            new_event(
                "operation.created",
                source="application.notes",
                payload={"workflow": "capture", "path": "Inbox/A.md"},
                occurred_at=datetime(2026, 4, 4, 10, 0, tzinfo=UTC),
            )
        ]
        report = EventLogReport(
            summary=summary,
            daily_activity=[
                EventLogDayActivity(
                    day="2026-04-04",
                    total_events=1,
                    sources=[("application.notes", 1)],
                    workflows=[("capture", 1)],
                    outcomes=[("write_note:created", 1)],
                )
            ],
            highlights={
                "latest_day": "2026-04-04",
                "latest_day_total_events": 1,
                "latest_day_top_source": "application.notes",
                "latest_day_top_workflow": "capture",
                "latest_day_top_outcome": "write_note:created",
                "top_path": "Inbox/A.md",
            },
            recent_events=events,
        )
        summary_table = object()
        highlights_table = object()
        activity_table = object()
        tail_table = object()

        with (
            patch("brain_ops.interfaces.cli.monitoring.execute_event_log_report_workflow", return_value=report),
            patch("brain_ops.interfaces.cli.monitoring.build_event_log_summary_table", return_value=summary_table) as summary_mock,
            patch("brain_ops.interfaces.cli.monitoring.build_event_log_highlights_table", return_value=highlights_table) as highlights_mock,
            patch("brain_ops.interfaces.cli.monitoring.build_event_log_daily_activity_table", return_value=activity_table) as activity_mock,
            patch("brain_ops.interfaces.cli.monitoring.build_event_log_tail_table", return_value=tail_table) as tail_mock,
        ):
            present_event_log_report_command(
                console,
                event_log_path=None,
                top=5,
                limit=10,
                source=None,
                workflow=None,
                status=None,
                since=None,
                until=None,
                as_json=False,
            )

        summary_mock.assert_called_once_with(summary)
        highlights_mock.assert_called_once_with(report.highlights)
        activity_mock.assert_called_once_with(report.daily_activity)
        tail_mock.assert_called_once_with(events)
        self.assertEqual(console.print.call_args_list[0].args, (summary_table,))
        self.assertEqual(console.print.call_args_list[1].args, (highlights_table,))
        self.assertEqual(console.print.call_args_list[2].args, (activity_table,))
        self.assertEqual(console.print.call_args_list[3].args, (tail_table,))
