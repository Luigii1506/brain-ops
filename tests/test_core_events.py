from __future__ import annotations

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from unittest import TestCase

from brain_ops.core.events import (
    CollectingEventSink,
    DomainEvent,
    NoOpEventSink,
    JsonlFileEventSink,
    event_from_operation,
    new_event,
    publish_event,
    publish_events,
)
from brain_ops.models import OperationRecord, OperationStatus


class CoreEventsTestCase(TestCase):
    def test_new_event_builds_stable_domain_event(self) -> None:
        occurred_at = datetime(2026, 4, 4, 12, 0, tzinfo=UTC)

        event = new_event(
            "workflow.completed",
            source="application.notes",
            payload={"path": "Notes/Test.md"},
            occurred_at=occurred_at,
            event_id="event-1",
            correlation_id="corr-1",
            causation_id="cause-1",
        )

        self.assertIsInstance(event, DomainEvent)
        self.assertEqual(event.name, "workflow.completed")
        self.assertEqual(event.source, "application.notes")
        self.assertEqual(event.payload["path"], "Notes/Test.md")
        self.assertEqual(event.occurred_at, occurred_at)
        self.assertEqual(event.event_id, "event-1")
        self.assertEqual(event.correlation_id, "corr-1")
        self.assertEqual(event.causation_id, "cause-1")

    def test_event_from_operation_translates_operation_record(self) -> None:
        operation = OperationRecord(
            action="write report",
            path="Reports/review.md",
            detail="Weekly review report",
            status=OperationStatus.REPORT,
        )

        event = event_from_operation(
            operation,
            source="application.knowledge",
            payload={"kind": "weekly-review"},
            correlation_id="corr-2",
        )

        self.assertEqual(event.name, "operation.report")
        self.assertEqual(event.source, "application.knowledge")
        self.assertEqual(event.payload["action"], "write report")
        self.assertEqual(event.payload["path"], "Reports/review.md")
        self.assertEqual(event.payload["detail"], "Weekly review report")
        self.assertEqual(event.payload["status"], "report")
        self.assertEqual(event.payload["kind"], "weekly-review")
        self.assertEqual(event.correlation_id, "corr-2")

    def test_collecting_sink_and_publish_helpers_collect_events(self) -> None:
        sink = CollectingEventSink()
        first = new_event("a", source="test")
        second = new_event("b", source="test")

        returned = publish_event(first, sink)
        publish_events([second], sink)

        self.assertIs(returned, first)
        self.assertEqual(sink.events, [first, second])

    def test_publish_helpers_accept_noop_sink_or_none(self) -> None:
        event = new_event("noop", source="test")

        returned_single = publish_event(event)
        returned_many = publish_events([event], NoOpEventSink())

        self.assertIs(returned_single, event)
        self.assertEqual(returned_many, [event])

    def test_jsonl_file_event_sink_appends_serialized_events(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            sink = JsonlFileEventSink(Path(temp_dir) / "events" / "brain_ops.jsonl")
            event = new_event(
                "workflow.completed",
                source="application.notes",
                payload={"workflow": "capture"},
                event_id="event-1",
            )

            sink.publish(event)

            written = sink.path.read_text(encoding="utf-8").strip().splitlines()

        self.assertEqual(len(written), 1)
        payload = json.loads(written[0])
        self.assertEqual(payload["event_id"], "event-1")
        self.assertEqual(payload["name"], "workflow.completed")
        self.assertEqual(payload["source"], "application.notes")
        self.assertEqual(payload["payload"]["workflow"], "capture")


if __name__ == "__main__":
    import unittest

    unittest.main()
