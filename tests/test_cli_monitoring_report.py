from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock, patch

from click.exceptions import Exit

from brain_ops.application.alerts import AlertMessage
from brain_ops.application.monitoring import EventLogAlertCheck, EventLogAlertPolicy, EventLogAlerts, EventLogFailures, EventLogHotspots, EventLogReport
from brain_ops.core.events import EventLogDayActivity, EventLogSummary, new_event
from brain_ops.interfaces.cli.monitoring import (
    present_event_log_alert_check_command,
    present_event_log_alert_delivery_command,
    present_event_log_alert_message_command,
    present_event_log_alert_presets_command,
    present_event_log_alerts_command,
    present_event_log_failures_command,
    present_event_log_hotspots_command,
    present_event_log_report_command,
)


class CliMonitoringReportTestCase(TestCase):
    def test_present_event_log_alert_delivery_command_prints_json(self) -> None:
        console = Mock()
        message = AlertMessage(
            level="alert",
            title="Event log alert check triggered 1 rule(s)",
            summary="summary text",
            triggered_rules=["total_events>1 (3)"],
            highlights={"latest_day": "2026-04-04"},
        )
        delivery = {
            "message": message.to_dict(),
            "output_path": "/tmp/alert.json",
            "output_format": "json",
        }

        with patch(
            "brain_ops.interfaces.cli.automation.execute_event_log_alert_delivery_workflow",
            return_value=type("Delivery", (), {"to_dict": lambda self: delivery, "output_path": Path('/tmp/alert.json'), "output_format": "json"})(),
        ):
            present_event_log_alert_delivery_command(
                console,
                event_log_path=Path("/tmp/events.jsonl"),
                top=3,
                limit=2,
                source="application.notes",
                workflow="capture",
                since="2026-04-04",
                until="2026-04-05",
                preset="strict",
                max_total_events=0,
                max_latest_day_events=0,
                output_path=Path("/tmp/alert.json"),
                output_format="json",
                delivery_mode="both",
                target="file",
                as_json=True,
            )

        console.print_json.assert_called_once_with(data=delivery)

    def test_present_event_log_alert_delivery_command_prints_payload_for_stdout_target(self) -> None:
        console = Mock()
        delivery = type(
            "Delivery",
            (),
            {
                "message": AlertMessage(
                    level="alert",
                    title="title",
                    summary="summary",
                    triggered_rules=["r1"],
                    highlights={"latest_day": "2026-04-04"},
                ),
                "to_dict": lambda self: {"target": "stdout"},
                "output_path": Path("<stdout>"),
                "output_format": "json",
                "target": "stdout",
                "latest_path": None,
            },
        )()

        with patch(
            "brain_ops.interfaces.cli.automation.execute_event_log_alert_delivery_workflow",
            return_value=delivery,
        ):
            present_event_log_alert_delivery_command(
                console,
                event_log_path=Path("/tmp/events.jsonl"),
                top=3,
                limit=2,
                source="application.notes",
                workflow="capture",
                since="2026-04-04",
                until="2026-04-05",
                preset="strict",
                max_total_events=0,
                max_latest_day_events=0,
                output_path=None,
                output_format="json",
                delivery_mode="both",
                target="stdout",
                as_json=False,
            )

        console.print_json.assert_called_once_with(data=delivery.message.to_dict())

    def test_present_event_log_alert_delivery_command_prints_written_and_latest_paths(self) -> None:
        console = Mock()
        delivery = type(
            "Delivery",
            (),
            {
                "to_dict": lambda self: {
                    "output_path": "/tmp/alerts/derived.json",
                    "output_format": "json",
                    "latest_path": "/tmp/alerts/event-log-alert-latest.json",
                },
                "output_path": Path("/tmp/alerts/derived.json"),
                "output_format": "json",
                "target": "file",
                "latest_path": Path("/tmp/alerts/event-log-alert-latest.json"),
            },
        )()

        with patch(
            "brain_ops.interfaces.cli.automation.execute_event_log_alert_delivery_workflow",
            return_value=delivery,
        ):
            present_event_log_alert_delivery_command(
                console,
                event_log_path=Path("/tmp/events.jsonl"),
                top=3,
                limit=2,
                source="application.notes",
                workflow="capture",
                since="2026-04-04",
                until="2026-04-05",
                preset="strict",
                max_total_events=0,
                max_latest_day_events=0,
                output_path=None,
                output_format="json",
                delivery_mode="both",
                target="file",
                as_json=False,
            )

        self.assertEqual(console.print.call_count, 2)

    def test_present_event_log_alert_message_command_prints_json(self) -> None:
        console = Mock()
        message = AlertMessage(
            level="alert",
            title="Event log alert check triggered 1 rule(s)",
            summary="total=3; latest_day=2026-04-04; latest_total=2; source=application.notes; workflow=capture; outcome=write_note:failed; path=Inbox/A.md",
            triggered_rules=["total_events>1 (3)"],
            highlights={"latest_day": "2026-04-04", "total_events": 3},
        )

        with patch("brain_ops.interfaces.cli.monitoring.execute_event_log_alert_message_workflow", return_value=message):
            present_event_log_alert_message_command(
                console,
                event_log_path=Path("/tmp/events.jsonl"),
                top=3,
                limit=2,
                source="application.notes",
                workflow="capture",
                since="2026-04-04",
                until="2026-04-05",
                preset="strict",
                max_total_events=0,
                max_latest_day_events=0,
                as_json=True,
            )

        console.print_json.assert_called_once_with(data=message.to_dict())

    def test_present_event_log_alert_presets_command_prints_json(self) -> None:
        console = Mock()
        presets = {
            "default": EventLogAlertPolicy(max_total_events=5, max_latest_day_events=3),
            "strict": EventLogAlertPolicy(max_total_events=1, max_latest_day_events=1),
        }

        with patch("brain_ops.interfaces.cli.monitoring.execute_event_log_alert_presets_workflow", return_value=presets):
            present_event_log_alert_presets_command(
                console,
                as_json=True,
            )

        console.print_json.assert_called_once_with(
            data={
                "default": {"max_total_events": 5, "max_latest_day_events": 3},
                "strict": {"max_total_events": 1, "max_latest_day_events": 1},
            }
        )

    def test_present_event_log_alert_check_command_prints_json(self) -> None:
        console = Mock()
        result = EventLogAlertCheck(
            alerts=EventLogAlerts(
                summary=EventLogSummary(
                    path=Path("/tmp/events.jsonl"),
                    total_events=1,
                    first_occurred_at=None,
                    last_occurred_at=None,
                    names=[],
                    sources=[],
                    workflows=[],
                    outcomes=[],
                    actions=[],
                    statuses=[],
                    paths=[],
                    days=[],
                ),
                daily_activity=[],
                recent_events=[],
                highlights={"latest_day_total_events": 1},
            ),
            policy=EventLogAlertPolicy(max_total_events=0, max_latest_day_events=0),
            triggered_rules=["total_events>0 (1)"],
            ok=False,
        )

        with patch("brain_ops.interfaces.cli.monitoring.execute_event_log_alert_check_workflow", return_value=result):
            present_event_log_alert_check_command(
                console,
                event_log_path=Path("/tmp/events.jsonl"),
                top=3,
                limit=2,
                source="application.notes",
                workflow="capture",
                since="2026-04-04",
                until="2026-04-05",
                preset="strict",
                max_total_events=0,
                max_latest_day_events=0,
                fail_on_alerts=False,
                as_json=True,
            )

        console.print_json.assert_called_once_with(data=result.to_dict())

    def test_present_event_log_alert_check_command_exits_when_fail_on_alerts(self) -> None:
        console = Mock()
        result = EventLogAlertCheck(
            alerts=EventLogAlerts(
                summary=EventLogSummary(
                    path=Path("/tmp/events.jsonl"),
                    total_events=1,
                    first_occurred_at=None,
                    last_occurred_at=None,
                    names=[],
                    sources=[],
                    workflows=[],
                    outcomes=[],
                    actions=[],
                    statuses=[],
                    paths=[],
                    days=[],
                ),
                daily_activity=[],
                recent_events=[],
                highlights={"latest_day_total_events": 1},
            ),
            policy=EventLogAlertPolicy(max_total_events=0, max_latest_day_events=None),
            triggered_rules=["total_events>0 (1)"],
            ok=False,
        )

        with patch("brain_ops.interfaces.cli.monitoring.execute_event_log_alert_check_workflow", return_value=result):
            with self.assertRaises(Exit) as raised:
                present_event_log_alert_check_command(
                    console,
                    event_log_path=None,
                    top=5,
                    limit=10,
                    source=None,
                    workflow=None,
                    since=None,
                    until=None,
                    preset=None,
                    max_total_events=0,
                    max_latest_day_events=None,
                    fail_on_alerts=True,
                    as_json=False,
                )

        self.assertEqual(raised.exception.exit_code, 2)

    def test_present_event_log_alerts_command_prints_json(self) -> None:
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
        alerts = EventLogAlerts(
            summary=summary,
            daily_activity=[
                EventLogDayActivity(
                    day="2026-04-04",
                    total_events=1,
                    sources=[("application.notes", 1)],
                    workflows=[("capture", 1)],
                    outcomes=[("write_note:failed", 1)],
                )
            ],
            highlights={
                "latest_day": "2026-04-04",
                "latest_day_total_events": 1,
                "latest_day_top_source": "application.notes",
                "latest_day_top_workflow": "capture",
                "latest_day_top_outcome": "write_note:failed",
                "top_path": "Inbox/A.md",
            },
            recent_events=[],
        )

        with patch("brain_ops.interfaces.cli.monitoring.execute_event_log_alerts_workflow", return_value=alerts):
            present_event_log_alerts_command(
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

        console.print_json.assert_called_once_with(data=alerts.to_dict())

    def test_present_event_log_alerts_command_prints_summary_highlights_activity_then_tail(self) -> None:
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
        alerts = EventLogAlerts(
            summary=summary,
            daily_activity=[],
            highlights={
                "latest_day": "2026-04-04",
                "latest_day_total_events": 1,
                "latest_day_top_source": "application.notes",
                "latest_day_top_workflow": "capture",
                "latest_day_top_outcome": "write_note:failed",
                "top_path": "Inbox/A.md",
            },
            recent_events=[],
        )
        failures_table = object()
        highlights_table = object()
        activity_table = object()
        tail_table = object()

        with (
            patch("brain_ops.interfaces.cli.monitoring.execute_event_log_alerts_workflow", return_value=alerts),
            patch("brain_ops.interfaces.cli.monitoring.build_event_log_failures_table", return_value=failures_table) as failures_mock,
            patch("brain_ops.interfaces.cli.monitoring.build_event_log_highlights_table", return_value=highlights_table) as highlights_mock,
            patch("brain_ops.interfaces.cli.monitoring.build_event_log_daily_activity_table", return_value=activity_table) as activity_mock,
            patch("brain_ops.interfaces.cli.monitoring.build_event_log_tail_table", return_value=tail_table) as tail_mock,
        ):
            present_event_log_alerts_command(
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
        highlights_mock.assert_called_once_with(alerts.highlights)
        activity_mock.assert_called_once_with(alerts.daily_activity)
        tail_mock.assert_called_once_with([])
        self.assertEqual(console.print.call_args_list[0].args, (failures_table,))
        self.assertEqual(console.print.call_args_list[1].args, (highlights_table,))
        self.assertEqual(console.print.call_args_list[2].args, (activity_table,))
        self.assertEqual(console.print.call_args_list[3].args, (tail_table,))

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
