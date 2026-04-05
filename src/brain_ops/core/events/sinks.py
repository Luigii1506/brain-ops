"""Minimal internal event sinks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from .models import DomainEvent


class EventSink(Protocol):
    def publish(self, event: DomainEvent) -> None: ...


class NoOpEventSink:
    def publish(self, event: DomainEvent) -> None:
        _ = event


class CollectingEventSink:
    def __init__(self) -> None:
        self.events: list[DomainEvent] = []

    def publish(self, event: DomainEvent) -> None:
        self.events.append(event)


class JsonlFileEventSink:
    def __init__(self, path: Path) -> None:
        self.path = path.expanduser()

    def publish(self, event: DomainEvent) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "event_id": event.event_id,
            "name": event.name,
            "source": event.source,
            "occurred_at": event.occurred_at.isoformat(),
            "payload": event.payload,
            "correlation_id": event.correlation_id,
            "causation_id": event.causation_id,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")


def publish_event(event: DomainEvent, sink: EventSink | None = None) -> DomainEvent:
    (sink or NoOpEventSink()).publish(event)
    return event


def publish_events(events: list[DomainEvent], sink: EventSink | None = None) -> list[DomainEvent]:
    event_sink = sink or NoOpEventSink()
    for event in events:
        event_sink.publish(event)
    return events


__all__ = [
    "CollectingEventSink",
    "EventSink",
    "JsonlFileEventSink",
    "NoOpEventSink",
    "publish_event",
    "publish_events",
]
