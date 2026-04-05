from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from brain_ops.core.events import (
    JsonlFileEventSink,
    event_to_dict,
    is_attention_event,
    new_event,
    read_event_log,
    resolve_since_datetime,
    resolve_until_datetime,
    summarize_attention_event_log,
    summarize_event_activity_days,
    summarize_event_log,
    tail_attention_event_log,
    tail_event_log,
)


class EventLogSummaryTestCase(TestCase):
    def test_read_event_log_round_trips_jsonl_events(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            sink = JsonlFileEventSink(path)
            occurred_at = datetime(2026, 4, 4, 12, 0, tzinfo=UTC)
            sink.publish(new_event("operation.created", source="application.notes", payload={"path": "Inbox/A.md"}, occurred_at=occurred_at))

            events = read_event_log(path)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].name, "operation.created")
        self.assertEqual(events[0].source, "application.notes")
        self.assertEqual(events[0].payload["path"], "Inbox/A.md")
        self.assertEqual(events[0].occurred_at, occurred_at)

    def test_summarize_event_log_counts_names_sources_and_dates(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            sink = JsonlFileEventSink(path)
            sink.publish(
                new_event(
                    "operation.created",
                    source="application.notes",
                    payload={"workflow": "capture", "action": "write_note", "status": "created", "path": "Inbox/A.md"},
                    occurred_at=datetime(2026, 4, 4, 10, 0, tzinfo=UTC),
                )
            )
            sink.publish(
                new_event(
                    "operation.created",
                    source="application.notes",
                    payload={"workflow": "capture", "action": "write_note", "status": "created", "path": "Inbox/A.md"},
                    occurred_at=datetime(2026, 4, 4, 11, 0, tzinfo=UTC),
                )
            )
            sink.publish(
                new_event(
                    "operation.updated",
                    source="application.knowledge",
                    payload={"workflow": "weekly-review", "action": "write_report", "status": "updated", "path": "Reports/weekly.md"},
                    occurred_at=datetime(2026, 4, 4, 12, 0, tzinfo=UTC),
                )
            )

            summary = summarize_event_log(path, top=2)

        self.assertEqual(summary.path, path)
        self.assertEqual(summary.total_events, 3)
        self.assertEqual(summary.first_occurred_at, datetime(2026, 4, 4, 10, 0, tzinfo=UTC))
        self.assertEqual(summary.last_occurred_at, datetime(2026, 4, 4, 12, 0, tzinfo=UTC))
        self.assertEqual(summary.names, [("operation.created", 2), ("operation.updated", 1)])
        self.assertEqual(summary.sources, [("application.notes", 2), ("application.knowledge", 1)])
        self.assertEqual(summary.workflows, [("capture", 2), ("weekly-review", 1)])
        self.assertEqual(summary.outcomes, [("write_note:created", 2), ("write_report:updated", 1)])
        self.assertEqual(summary.actions, [("write_note", 2), ("write_report", 1)])
        self.assertEqual(summary.statuses, [("created", 2), ("updated", 1)])
        self.assertEqual(summary.paths, [("Inbox/A.md", 2), ("Reports/weekly.md", 1)])
        self.assertEqual(summary.days, [("2026-04-04", 3)])
        self.assertEqual(summary.to_dict()["total_events"], 3)
        self.assertEqual(summary.to_dict()["workflows"][0]["workflow"], "capture")
        self.assertEqual(summary.to_dict()["outcomes"][0]["outcome"], "write_note:created")
        self.assertEqual(summary.to_dict()["actions"][0]["action"], "write_note")
        self.assertEqual(summary.to_dict()["statuses"][0]["status"], "created")
        self.assertEqual(summary.to_dict()["paths"][0]["path"], "Inbox/A.md")
        self.assertEqual(summary.to_dict()["days"][0]["day"], "2026-04-04")

    def test_tail_event_log_returns_most_recent_events(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            sink = JsonlFileEventSink(path)
            sink.publish(new_event("operation.created", source="application.notes", occurred_at=datetime(2026, 4, 4, 10, 0, tzinfo=UTC)))
            sink.publish(new_event("operation.updated", source="application.personal", occurred_at=datetime(2026, 4, 4, 11, 0, tzinfo=UTC)))
            sink.publish(new_event("operation.report", source="application.knowledge", occurred_at=datetime(2026, 4, 4, 12, 0, tzinfo=UTC)))

            events = tail_event_log(path, limit=2)

        self.assertEqual([event.name for event in events], ["operation.updated", "operation.report"])
        self.assertEqual(event_to_dict(events[-1])["source"], "application.knowledge")

    def test_summary_and_tail_can_filter_by_source(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            sink = JsonlFileEventSink(path)
            sink.publish(new_event("operation.created", source="application.notes", payload={"workflow": "capture"}))
            sink.publish(new_event("operation.report", source="application.knowledge", payload={"workflow": "weekly-review"}))
            sink.publish(new_event("operation.updated", source="application.notes", payload={"workflow": "improve-note"}))

            summary = summarize_event_log(path, top=5, source="application.notes")
            events = tail_event_log(path, limit=5, source="application.notes")

        self.assertEqual(summary.total_events, 2)
        self.assertEqual(summary.sources, [("application.notes", 2)])
        self.assertEqual([event.source for event in events], ["application.notes", "application.notes"])

    def test_summary_and_tail_can_filter_by_since(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            sink = JsonlFileEventSink(path)
            sink.publish(new_event("operation.created", source="application.notes", occurred_at=datetime(2026, 4, 4, 10, 0, tzinfo=UTC)))
            sink.publish(new_event("operation.updated", source="application.notes", occurred_at=datetime(2026, 4, 4, 11, 0, tzinfo=UTC)))
            sink.publish(new_event("operation.report", source="application.notes", occurred_at=datetime(2026, 4, 4, 12, 0, tzinfo=UTC)))

            summary = summarize_event_log(path, top=5, since=resolve_since_datetime("2026-04-04T11:00:00+00:00"))
            events = tail_event_log(path, limit=5, since=resolve_since_datetime("2026-04-04T11:00:00+00:00"))

        self.assertEqual(summary.total_events, 2)
        self.assertEqual([event.name for event in events], ["operation.updated", "operation.report"])

    def test_summary_and_tail_can_filter_by_until(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            sink = JsonlFileEventSink(path)
            sink.publish(new_event("operation.created", source="application.notes", occurred_at=datetime(2026, 4, 4, 10, 0, tzinfo=UTC)))
            sink.publish(new_event("operation.updated", source="application.notes", occurred_at=datetime(2026, 4, 4, 11, 0, tzinfo=UTC)))
            sink.publish(new_event("operation.report", source="application.notes", occurred_at=datetime(2026, 4, 4, 12, 0, tzinfo=UTC)))

            summary = summarize_event_log(path, top=5, until=resolve_until_datetime("2026-04-04T11:00:00+00:00"))
            events = tail_event_log(path, limit=5, until=resolve_until_datetime("2026-04-04T11:00:00+00:00"))

        self.assertEqual(summary.total_events, 2)
        self.assertEqual([event.name for event in events], ["operation.created", "operation.updated"])

    def test_summarize_event_activity_days_groups_recent_days(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            sink = JsonlFileEventSink(path)
            sink.publish(
                new_event(
                    "operation.created",
                    source="application.notes",
                    payload={"workflow": "capture", "action": "write_note", "status": "created", "path": "Inbox/A.md"},
                    occurred_at=datetime(2026, 4, 4, 10, 0, tzinfo=UTC),
                )
            )
            sink.publish(
                new_event(
                    "operation.updated",
                    source="application.notes",
                    payload={"workflow": "improve-note", "action": "write_note", "status": "updated", "path": "Inbox/A.md"},
                    occurred_at=datetime(2026, 4, 4, 11, 0, tzinfo=UTC),
                )
            )
            sink.publish(
                new_event(
                    "operation.updated",
                    source="application.knowledge",
                    payload={"workflow": "weekly-review", "action": "write_report", "status": "updated", "path": "Reports/weekly.md"},
                    occurred_at=datetime(2026, 4, 5, 9, 0, tzinfo=UTC),
                )
            )

            activity = summarize_event_activity_days(path, days=2, top=2)

        self.assertEqual(len(activity), 2)
        self.assertEqual(activity[0].day, "2026-04-04")
        self.assertEqual(activity[0].total_events, 2)
        self.assertEqual(activity[0].sources, [("application.notes", 2)])
        self.assertEqual(activity[0].workflows, [("capture", 1), ("improve-note", 1)])
        self.assertEqual(activity[1].day, "2026-04-05")
        self.assertEqual(activity[1].outcomes, [("write_report:updated", 1)])
        self.assertEqual(activity[1].to_dict()["day"], "2026-04-05")

    def test_summary_and_tail_can_filter_by_workflow(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            sink = JsonlFileEventSink(path)
            sink.publish(
                new_event(
                    "operation.created",
                    source="application.notes",
                    payload={"workflow": "capture"},
                    occurred_at=datetime(2026, 4, 4, 10, 0, tzinfo=UTC),
                )
            )
            sink.publish(
                new_event(
                    "operation.report",
                    source="application.knowledge",
                    payload={"workflow": "weekly-review"},
                    occurred_at=datetime(2026, 4, 4, 11, 0, tzinfo=UTC),
                )
            )
            sink.publish(
                new_event(
                    "operation.updated",
                    source="application.notes",
                    payload={"workflow": "capture"},
                    occurred_at=datetime(2026, 4, 4, 12, 0, tzinfo=UTC),
                )
            )

            summary = summarize_event_log(path, top=5, workflow="capture")
            events = tail_event_log(path, limit=5, workflow="capture")

        self.assertEqual(summary.total_events, 2)
        self.assertEqual(summary.workflows, [("capture", 2)])
        self.assertEqual(summary.days, [("2026-04-04", 2)])
        self.assertEqual([event.payload.get("workflow") for event in events], ["capture", "capture"])

    def test_summary_and_tail_can_filter_by_status(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            sink = JsonlFileEventSink(path)
            sink.publish(
                new_event(
                    "operation.created",
                    source="application.notes",
                    payload={"workflow": "capture", "action": "write_note", "status": "created"},
                    occurred_at=datetime(2026, 4, 4, 10, 0, tzinfo=UTC),
                )
            )
            sink.publish(
                new_event(
                    "operation.updated",
                    source="application.notes",
                    payload={"workflow": "improve-note", "action": "write_note", "status": "updated"},
                    occurred_at=datetime(2026, 4, 4, 11, 0, tzinfo=UTC),
                )
            )
            sink.publish(
                new_event(
                    "operation.updated",
                    source="application.knowledge",
                    payload={"workflow": "weekly-review", "action": "write_report", "status": "updated"},
                    occurred_at=datetime(2026, 4, 4, 12, 0, tzinfo=UTC),
                )
            )

            summary = summarize_event_log(path, top=5, status="updated")
            events = tail_event_log(path, limit=5, status="updated")

        self.assertEqual(summary.total_events, 2)
        self.assertEqual(summary.statuses, [("updated", 2)])
        self.assertEqual([event.payload.get("status") for event in events], ["updated", "updated"])

    def test_attention_helpers_focus_on_skipped_and_failed_events(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            sink = JsonlFileEventSink(path)
            created = new_event(
                "operation.created",
                source="application.notes",
                payload={"workflow": "capture", "action": "write_note", "status": "created", "path": "Inbox/A.md"},
                occurred_at=datetime(2026, 4, 4, 10, 0, tzinfo=UTC),
            )
            skipped = new_event(
                "operation.skipped",
                source="application.knowledge",
                payload={"workflow": "normalize-frontmatter", "action": "write_note", "status": "skipped", "path": "Notes/B.md"},
                occurred_at=datetime(2026, 4, 4, 11, 0, tzinfo=UTC),
            )
            failed = new_event(
                "operation.failed",
                source="application.notes",
                payload={"workflow": "capture", "action": "write_note", "status": "failed", "path": "Inbox/C.md"},
                occurred_at=datetime(2026, 4, 4, 12, 0, tzinfo=UTC),
            )
            sink.publish(created)
            sink.publish(skipped)
            sink.publish(failed)

            summary = summarize_attention_event_log(path, top=5)
            events = tail_attention_event_log(path, limit=5)

        self.assertFalse(is_attention_event(created))
        self.assertTrue(is_attention_event(skipped))
        self.assertTrue(is_attention_event(failed))
        self.assertEqual(summary.total_events, 2)
        self.assertEqual(summary.statuses, [("skipped", 1), ("failed", 1)])
        self.assertEqual([event.name for event in events], ["operation.skipped", "operation.failed"])
