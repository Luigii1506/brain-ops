from __future__ import annotations

from pathlib import Path
from unittest import TestCase

from brain_ops.application.monitoring import (
    EVENT_LOG_ALERT_POLICY_PRESETS,
    EventLogAlertCheck,
    EventLogAlertPolicy,
    EventLogAlerts,
    EventLogFailures,
    EventLogHotspots,
    EventLogReport,
    build_event_log_alert_policy,
    evaluate_event_log_alerts,
    execute_event_log_alert_presets_workflow,
    execute_event_log_alert_check_workflow,
    execute_event_log_alerts_workflow,
    execute_event_log_failures_workflow,
    build_event_log_report_highlights,
    execute_event_log_hotspots_workflow,
    execute_event_log_report_workflow,
)
from brain_ops.application.alerts import AlertMessage, build_event_log_alert_message, execute_event_log_alert_message_workflow
from brain_ops.core.events import EventLogDayActivity, EventLogSummary


class ApplicationMonitoringTestCase(TestCase):
    def test_build_event_log_alert_message_summarizes_check(self) -> None:
        check = EventLogAlertCheck(
            alerts=EventLogAlerts(
                summary=EventLogSummary(
                    path=Path("/tmp/events.jsonl"),
                    total_events=3,
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
                highlights={
                    "latest_day": "2026-04-04",
                    "latest_day_total_events": 2,
                    "latest_day_top_source": "application.notes",
                    "latest_day_top_workflow": "capture",
                    "latest_day_top_outcome": "write_note:failed",
                    "top_path": "Inbox/A.md",
                },
            ),
            policy=EventLogAlertPolicy(max_total_events=1, max_latest_day_events=1),
            triggered_rules=["total_events>1 (3)"],
            ok=False,
        )

        message = build_event_log_alert_message(check)

        self.assertEqual(
            message,
            AlertMessage(
                level="alert",
                title="Event log alert check triggered 1 rule(s)",
                summary="total=3; latest_day=2026-04-04; latest_total=2; source=application.notes; workflow=capture; outcome=write_note:failed; path=Inbox/A.md",
                triggered_rules=["total_events>1 (3)"],
                highlights={
                    "latest_day": "2026-04-04",
                    "latest_day_total_events": 2,
                    "latest_day_top_source": "application.notes",
                    "latest_day_top_workflow": "capture",
                    "latest_day_top_outcome": "write_note:failed",
                    "top_path": "Inbox/A.md",
                    "total_events": 3,
                },
            ),
        )

    def test_build_event_log_report_highlights_uses_latest_day_and_top_path(self) -> None:
        summary = EventLogSummary(
            path=Path("/tmp/events.jsonl"),
            total_events=3,
            first_occurred_at=None,
            last_occurred_at=None,
            names=[],
            sources=[],
            workflows=[],
            outcomes=[],
            actions=[],
            statuses=[],
            paths=[("Inbox/A.md", 2)],
            days=[("2026-04-04", 2), ("2026-04-05", 1)],
        )
        activity = [
            EventLogDayActivity(
                day="2026-04-04",
                total_events=2,
                sources=[("application.notes", 2)],
                workflows=[("capture", 1)],
                outcomes=[("write_note:created", 1)],
            ),
            EventLogDayActivity(
                day="2026-04-05",
                total_events=1,
                sources=[("application.knowledge", 1)],
                workflows=[("weekly-review", 1)],
                outcomes=[("write_report:updated", 1)],
            ),
        ]

        highlights = build_event_log_report_highlights(summary, activity)

        self.assertEqual(highlights["latest_day"], "2026-04-05")
        self.assertEqual(highlights["latest_day_total_events"], 1)
        self.assertEqual(highlights["latest_day_top_source"], "application.knowledge")
        self.assertEqual(highlights["latest_day_top_workflow"], "weekly-review")
        self.assertEqual(highlights["latest_day_top_outcome"], "write_report:updated")
        self.assertEqual(highlights["top_path"], "Inbox/A.md")

    def test_event_log_report_workflow_reuses_resolved_path_and_filters(self) -> None:
        summary = object()
        daily_activity = [object()]
        recent_events = [object(), object()]

        report = execute_event_log_report_workflow(
            event_log_path=Path("~/events.jsonl"),
            top=7,
            limit=4,
            source="application.notes",
            workflow="capture",
            status="created",
            since="2026-04-04",
            until="2026-04-05",
            load_event_log_path=lambda _path: Path("/tmp/events.jsonl"),
            parse_since=lambda value: f"parsed:{value}",
            parse_until=lambda value: f"parsed:{value}",
            summarize_log=lambda path, **kwargs: (summary, path, kwargs),
            summarize_activity=lambda path, **kwargs: [daily_activity, path, kwargs],
            tail_log=lambda path, **kwargs: [recent_events, path, kwargs],
            build_highlights=lambda summary_value, activity_value: {
                "summary": summary_value,
                "activity": activity_value,
            },
        )

        self.assertIsInstance(report, EventLogReport)
        returned_summary, summary_path, summary_kwargs = report.summary
        returned_activity, activity_path, activity_kwargs = report.daily_activity
        returned_events, tail_path, tail_kwargs = report.recent_events
        self.assertIs(returned_summary, summary)
        self.assertIs(returned_activity, daily_activity)
        self.assertIs(returned_events, recent_events)
        self.assertEqual(report.highlights, {"summary": report.summary, "activity": report.daily_activity})
        self.assertEqual(summary_path, Path("/tmp/events.jsonl"))
        self.assertEqual(activity_path, Path("/tmp/events.jsonl"))
        self.assertEqual(tail_path, Path("/tmp/events.jsonl"))
        self.assertEqual(
            summary_kwargs,
            {"top": 7, "source": "application.notes", "workflow": "capture", "status": "created", "since": "parsed:2026-04-04", "until": "parsed:2026-04-05"},
        )
        self.assertEqual(
            activity_kwargs,
            {"days": 7, "top": 7, "source": "application.notes", "workflow": "capture", "status": "created", "since": "parsed:2026-04-04", "until": "parsed:2026-04-05"},
        )
        self.assertEqual(
            tail_kwargs,
            {"limit": 4, "source": "application.notes", "workflow": "capture", "status": "created", "since": "parsed:2026-04-04", "until": "parsed:2026-04-05"},
        )

    def test_event_log_hotspots_workflow_reuses_summary_and_builds_highlights(self) -> None:
        summary = EventLogSummary(
            path=Path("/tmp/events.jsonl"),
            total_events=2,
            first_occurred_at=None,
            last_occurred_at=None,
            names=[],
            sources=[("application.notes", 2)],
            workflows=[("capture", 2)],
            outcomes=[("write_note:created", 2)],
            actions=[("write_note", 2)],
            statuses=[("created", 2)],
            paths=[("Inbox/A.md", 2)],
            days=[("2026-04-04", 2)],
        )

        hotspots = execute_event_log_hotspots_workflow(
            event_log_path=Path("~/events.jsonl"),
            top=5,
            source="application.notes",
            workflow="capture",
            status="created",
            since="2026-04-04",
            until="2026-04-05",
            load_event_log_path=lambda _path: Path("/tmp/events.jsonl"),
            parse_since=lambda value: f"parsed:{value}",
            parse_until=lambda value: f"parsed:{value}",
            summarize_log=lambda path, **kwargs: summary,
        )

        self.assertIsInstance(hotspots, EventLogHotspots)
        self.assertIs(hotspots.summary, summary)
        self.assertEqual(hotspots.highlights["top_path"], "Inbox/A.md")

    def test_event_log_failures_workflow_reuses_resolved_path_and_filters(self) -> None:
        summary = object()
        recent_events = [object()]

        failures = execute_event_log_failures_workflow(
            event_log_path=Path("~/events.jsonl"),
            top=4,
            limit=2,
            source="application.notes",
            workflow="capture",
            since="2026-04-04",
            until="2026-04-05",
            load_event_log_path=lambda _path: Path("/tmp/events.jsonl"),
            parse_since=lambda value: f"parsed:{value}",
            parse_until=lambda value: f"parsed:{value}",
            summarize_log=lambda path, **kwargs: (summary, path, kwargs),
            tail_log=lambda path, **kwargs: [recent_events, path, kwargs],
        )

        self.assertIsInstance(failures, EventLogFailures)
        returned_summary, summary_path, summary_kwargs = failures.summary
        returned_events, tail_path, tail_kwargs = failures.recent_events
        self.assertIs(returned_summary, summary)
        self.assertIs(returned_events, recent_events)
        self.assertEqual(summary_path, Path("/tmp/events.jsonl"))
        self.assertEqual(tail_path, Path("/tmp/events.jsonl"))
        self.assertEqual(
            summary_kwargs,
            {"top": 4, "source": "application.notes", "workflow": "capture", "since": "parsed:2026-04-04", "until": "parsed:2026-04-05"},
        )
        self.assertEqual(
            tail_kwargs,
            {"limit": 2, "source": "application.notes", "workflow": "capture", "since": "parsed:2026-04-04", "until": "parsed:2026-04-05"},
        )

    def test_event_log_alerts_workflow_reuses_summary_activity_and_tail(self) -> None:
        summary = object()
        daily_activity = [object()]
        recent_events = [object()]

        alerts = execute_event_log_alerts_workflow(
            event_log_path=Path("~/events.jsonl"),
            top=4,
            limit=2,
            source="application.notes",
            workflow="capture",
            since="2026-04-04",
            until="2026-04-05",
            load_event_log_path=lambda _path: Path("/tmp/events.jsonl"),
            parse_since=lambda value: f"parsed:{value}",
            parse_until=lambda value: f"parsed:{value}",
            summarize_log=lambda path, **kwargs: (summary, path, kwargs),
            summarize_activity=lambda path, **kwargs: [daily_activity, path, kwargs],
            tail_log=lambda path, **kwargs: [recent_events, path, kwargs],
            build_highlights=lambda summary_value, activity_value: {
                "summary": summary_value,
                "activity": activity_value,
            },
        )

        self.assertIsInstance(alerts, EventLogAlerts)
        returned_summary, summary_path, summary_kwargs = alerts.summary
        returned_activity, activity_path, activity_kwargs = alerts.daily_activity
        returned_events, tail_path, tail_kwargs = alerts.recent_events
        self.assertIs(returned_summary, summary)
        self.assertIs(returned_activity, daily_activity)
        self.assertIs(returned_events, recent_events)
        self.assertEqual(alerts.highlights, {"summary": alerts.summary, "activity": alerts.daily_activity})
        self.assertEqual(summary_path, Path("/tmp/events.jsonl"))
        self.assertEqual(activity_path, Path("/tmp/events.jsonl"))
        self.assertEqual(tail_path, Path("/tmp/events.jsonl"))
        self.assertEqual(
            summary_kwargs,
            {"top": 4, "source": "application.notes", "workflow": "capture", "since": "parsed:2026-04-04", "until": "parsed:2026-04-05"},
        )
        self.assertEqual(
            activity_kwargs,
            {"days": 4, "top": 4, "source": "application.notes", "workflow": "capture", "since": "parsed:2026-04-04", "until": "parsed:2026-04-05"},
        )
        self.assertEqual(
            tail_kwargs,
            {"limit": 2, "source": "application.notes", "workflow": "capture", "since": "parsed:2026-04-04", "until": "parsed:2026-04-05"},
        )

    def test_evaluate_event_log_alerts_marks_triggered_thresholds(self) -> None:
        alerts = EventLogAlerts(
            summary=EventLogSummary(
                path=Path("/tmp/events.jsonl"),
                total_events=3,
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
            highlights={"latest_day_total_events": 2},
        )

        policy = build_event_log_alert_policy(
            max_total_events=1,
            max_latest_day_events=1,
        )
        result = evaluate_event_log_alerts(
            alerts,
            policy=policy,
        )

        self.assertIsInstance(result, EventLogAlertCheck)
        self.assertEqual(result.policy, policy)
        self.assertFalse(result.ok)
        self.assertEqual(
            result.triggered_rules,
            ["total_events>1 (3)", "latest_day_total_events>1 (2)"],
        )

    def test_build_event_log_alert_policy_preserves_thresholds(self) -> None:
        policy = build_event_log_alert_policy(
            max_total_events=5,
            max_latest_day_events=2,
        )

        self.assertEqual(
            policy,
            EventLogAlertPolicy(max_total_events=5, max_latest_day_events=2),
        )
        self.assertEqual(
            policy.to_dict(),
            {"max_total_events": 5, "max_latest_day_events": 2},
        )

    def test_build_event_log_alert_policy_uses_preset_and_allows_overrides(self) -> None:
        policy = build_event_log_alert_policy(
            preset="strict",
            max_total_events=None,
            max_latest_day_events=4,
        )

        self.assertEqual(
            policy,
            EventLogAlertPolicy(max_total_events=1, max_latest_day_events=4),
        )
        self.assertEqual(EVENT_LOG_ALERT_POLICY_PRESETS["default"].max_total_events, 5)

    def test_execute_event_log_alert_presets_workflow_returns_copy_of_presets(self) -> None:
        presets = execute_event_log_alert_presets_workflow()

        self.assertEqual(presets, EVENT_LOG_ALERT_POLICY_PRESETS)
        self.assertIsNot(presets, EVENT_LOG_ALERT_POLICY_PRESETS)

    def test_event_log_alert_check_workflow_reuses_alerts_and_evaluator(self) -> None:
        alerts = object()
        loader = lambda _path: Path("/tmp/events.jsonl")
        policy = object()

        result = execute_event_log_alert_check_workflow(
            event_log_path=Path("~/events.jsonl"),
            top=4,
            limit=2,
            source="application.notes",
            workflow="capture",
            since="2026-04-04",
            until="2026-04-05",
            preset="strict",
            max_total_events=1,
            max_latest_day_events=2,
            load_event_log_path=loader,
            build_policy=lambda **kwargs: (policy, kwargs),
            execute_alerts=lambda **kwargs: (alerts, kwargs),
            evaluate_alerts=lambda alerts_value, **kwargs: (alerts_value, kwargs),
        )

        returned_alerts, evaluation_kwargs = result
        inner_alerts, inner_kwargs = returned_alerts
        self.assertIs(inner_alerts, alerts)
        self.assertEqual(
            inner_kwargs,
            {
                "event_log_path": Path("~/events.jsonl"),
                "top": 4,
                "limit": 2,
                "source": "application.notes",
                "workflow": "capture",
                "since": "2026-04-04",
                "until": "2026-04-05",
                "load_event_log_path": loader,
            },
        )
        self.assertEqual(
            evaluation_kwargs,
            {"policy": (policy, {"preset": "strict", "max_total_events": 1, "max_latest_day_events": 2})},
        )

    def test_event_log_alert_message_workflow_reuses_alert_check_then_builds_message(self) -> None:
        check = object()
        result = execute_event_log_alert_message_workflow(
            event_log_path=Path("~/events.jsonl"),
            top=4,
            limit=2,
            source="application.notes",
            workflow="capture",
            since="2026-04-04",
            until="2026-04-05",
            preset="strict",
            max_total_events=1,
            max_latest_day_events=2,
            load_event_log_path=lambda _path: Path("/tmp/events.jsonl"),
            execute_alert_check=lambda **kwargs: (check, kwargs),
            build_message=lambda value: ("message", value),
        )

        returned_check, kwargs = result[1]
        self.assertEqual(result[0], "message")
        self.assertIs(returned_check, check)
        self.assertEqual(
            kwargs,
            {
                "event_log_path": Path("~/events.jsonl"),
                "top": 4,
                "limit": 2,
                "source": "application.notes",
                "workflow": "capture",
                "since": "2026-04-04",
                "until": "2026-04-05",
                "preset": "strict",
                "max_total_events": 1,
                "max_latest_day_events": 2,
                "load_event_log_path": kwargs["load_event_log_path"],
            },
        )
