"""Event-log reading helpers."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path

from brain_ops.errors import ConfigError

from .models import DomainEvent


ATTENTION_STATUSES = frozenset({"failed", "error", "invalid", "rejected", "skipped"})
ATTENTION_NAME_SUFFIXES = (".failed", ".error")


@dataclass(slots=True, frozen=True)
class EventLogSummary:
    path: Path
    total_events: int
    first_occurred_at: datetime | None
    last_occurred_at: datetime | None
    names: list[tuple[str, int]]
    sources: list[tuple[str, int]]
    workflows: list[tuple[str, int]]
    outcomes: list[tuple[str, int]]
    actions: list[tuple[str, int]]
    statuses: list[tuple[str, int]]
    paths: list[tuple[str, int]]
    days: list[tuple[str, int]]

    def to_dict(self) -> dict[str, object]:
        return {
            "path": str(self.path),
            "total_events": self.total_events,
            "first_occurred_at": self.first_occurred_at.isoformat() if self.first_occurred_at else None,
            "last_occurred_at": self.last_occurred_at.isoformat() if self.last_occurred_at else None,
            "names": [{"name": name, "count": count} for name, count in self.names],
            "sources": [{"source": source, "count": count} for source, count in self.sources],
            "workflows": [{"workflow": workflow, "count": count} for workflow, count in self.workflows],
            "outcomes": [{"outcome": outcome, "count": count} for outcome, count in self.outcomes],
            "actions": [{"action": action, "count": count} for action, count in self.actions],
            "statuses": [{"status": status, "count": count} for status, count in self.statuses],
            "paths": [{"path": path, "count": count} for path, count in self.paths],
            "days": [{"day": day, "count": count} for day, count in self.days],
        }


@dataclass(slots=True, frozen=True)
class EventLogDayActivity:
    day: str
    total_events: int
    sources: list[tuple[str, int]]
    workflows: list[tuple[str, int]]
    outcomes: list[tuple[str, int]]

    def to_dict(self) -> dict[str, object]:
        return {
            "day": self.day,
            "total_events": self.total_events,
            "sources": [{"source": source, "count": count} for source, count in self.sources],
            "workflows": [{"workflow": workflow, "count": count} for workflow, count in self.workflows],
            "outcomes": [{"outcome": outcome, "count": count} for outcome, count in self.outcomes],
        }


def event_to_dict(event: DomainEvent) -> dict[str, object]:
    return {
        "event_id": event.event_id,
        "name": event.name,
        "source": event.source,
        "occurred_at": event.occurred_at.isoformat(),
        "payload": dict(event.payload),
        "correlation_id": event.correlation_id,
        "causation_id": event.causation_id,
    }


def is_attention_event(event: DomainEvent) -> bool:
    status = str(event.payload.get("status") or "").strip().lower()
    if status in ATTENTION_STATUSES:
        return True
    return event.name.endswith(ATTENTION_NAME_SUFFIXES)


def read_event_log(path: Path) -> list[DomainEvent]:
    events: list[DomainEvent] = []
    expanded_path = path.expanduser()
    with expanded_path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            payload = json.loads(line)
            events.append(
                DomainEvent(
                    name=payload["name"],
                    source=payload["source"],
                    payload=dict(payload.get("payload") or {}),
                    occurred_at=datetime.fromisoformat(payload["occurred_at"]),
                    event_id=payload["event_id"],
                    correlation_id=payload.get("correlation_id"),
                    causation_id=payload.get("causation_id"),
                )
            )
    return events


def filter_events_by_source(events: list[DomainEvent], *, source: str | None) -> list[DomainEvent]:
    if not source:
        return events
    return [event for event in events if event.source == source]


def filter_events_by_workflow(events: list[DomainEvent], *, workflow: str | None) -> list[DomainEvent]:
    if not workflow:
        return events
    return [event for event in events if event.payload.get("workflow") == workflow]


def filter_events_by_status(events: list[DomainEvent], *, status: str | None) -> list[DomainEvent]:
    if not status:
        return events
    return [event for event in events if event.payload.get("status") == status]


def resolve_since_datetime(since: str | None) -> datetime | None:
    if not since:
        return None
    try:
        parsed = datetime.fromisoformat(since)
    except ValueError as exc:
        raise ConfigError("Since must be in YYYY-MM-DD or ISO datetime format.") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def resolve_until_datetime(until: str | None) -> datetime | None:
    if not until:
        return None
    try:
        parsed = datetime.fromisoformat(until)
    except ValueError as exc:
        raise ConfigError("Until must be in YYYY-MM-DD or ISO datetime format.") from exc
    if parsed.tzinfo is None:
        return (parsed.replace(tzinfo=UTC) + timedelta(days=1)) - timedelta(microseconds=1)
    return parsed


def filter_events_since(events: list[DomainEvent], *, since: datetime | None) -> list[DomainEvent]:
    if since is None:
        return events
    return [event for event in events if event.occurred_at >= since]


def filter_events_until(events: list[DomainEvent], *, until: datetime | None) -> list[DomainEvent]:
    if until is None:
        return events
    return [event for event in events if event.occurred_at <= until]


def filter_events(
    events: list[DomainEvent],
    *,
    source: str | None = None,
    workflow: str | None = None,
    status: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
) -> list[DomainEvent]:
    return filter_events_until(
        filter_events_since(
            filter_events_by_status(
                filter_events_by_workflow(
                    filter_events_by_source(events, source=source),
                    workflow=workflow,
                ),
                status=status,
            ),
            since=since,
        ),
        until=until,
    )


def filter_attention_events(events: list[DomainEvent]) -> list[DomainEvent]:
    return [event for event in events if is_attention_event(event)]


def build_event_log_summary(path: Path, events: list[DomainEvent], *, top: int) -> EventLogSummary:
    expanded_path = path.expanduser()
    occurred_at = [event.occurred_at for event in events]
    names = Counter(event.name for event in events)
    sources = Counter(event.source for event in events)
    workflows = Counter(
        str(workflow)
        for event in events
        for workflow in [event.payload.get("workflow")]
        if workflow
    )
    outcomes = Counter(
        f"{action}:{status}"
        for event in events
        for action, status in [(event.payload.get("action"), event.payload.get("status"))]
        if action and status
    )
    actions = Counter(
        str(action)
        for event in events
        for action in [event.payload.get("action")]
        if action
    )
    statuses = Counter(
        str(status)
        for event in events
        for status in [event.payload.get("status")]
        if status
    )
    paths = Counter(
        str(path_value)
        for event in events
        for path_value in [event.payload.get("path")]
        if path_value
    )
    days = Counter(event.occurred_at.date().isoformat() for event in events)
    return EventLogSummary(
        path=expanded_path,
        total_events=len(events),
        first_occurred_at=min(occurred_at) if occurred_at else None,
        last_occurred_at=max(occurred_at) if occurred_at else None,
        names=names.most_common(top),
        sources=sources.most_common(top),
        workflows=workflows.most_common(top),
        outcomes=outcomes.most_common(top),
        actions=actions.most_common(top),
        statuses=statuses.most_common(top),
        paths=paths.most_common(top),
        days=days.most_common(top),
    )


def tail_event_log(
    path: Path,
    *,
    limit: int = 10,
    source: str | None = None,
    workflow: str | None = None,
    status: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
) -> list[DomainEvent]:
    if limit <= 0:
        return []
    events = filter_events(
        read_event_log(path),
        source=source,
        workflow=workflow,
        status=status,
        since=since,
        until=until,
    )
    return events[-limit:]


def summarize_event_log(
    path: Path,
    *,
    top: int = 5,
    source: str | None = None,
    workflow: str | None = None,
    status: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
) -> EventLogSummary:
    expanded_path = path.expanduser()
    events = filter_events(
        read_event_log(expanded_path),
        source=source,
        workflow=workflow,
        status=status,
        since=since,
        until=until,
    )
    return build_event_log_summary(expanded_path, events, top=top)


def summarize_attention_event_log(
    path: Path,
    *,
    top: int = 5,
    source: str | None = None,
    workflow: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
) -> EventLogSummary:
    expanded_path = path.expanduser()
    events = filter_attention_events(
        filter_events(
            read_event_log(expanded_path),
            source=source,
            workflow=workflow,
            since=since,
            until=until,
        )
    )
    return build_event_log_summary(expanded_path, events, top=top)


def summarize_event_activity_days(
    path: Path,
    *,
    days: int = 5,
    top: int = 3,
    source: str | None = None,
    workflow: str | None = None,
    status: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
) -> list[EventLogDayActivity]:
    if days <= 0:
        return []
    events = filter_events(
        read_event_log(path.expanduser()),
        source=source,
        workflow=workflow,
        status=status,
        since=since,
        until=until,
    )
    grouped: dict[str, list[DomainEvent]] = {}
    for event in events:
        day = event.occurred_at.date().isoformat()
        grouped.setdefault(day, []).append(event)
    recent_days = sorted(grouped.keys(), reverse=True)[:days]
    activity: list[EventLogDayActivity] = []
    for day in sorted(recent_days):
        day_events = grouped[day]
        sources = Counter(event.source for event in day_events)
        workflows = Counter(
            str(item)
            for event in day_events
            for item in [event.payload.get("workflow")]
            if item
        )
        outcomes = Counter(
            f"{action}:{item_status}"
            for event in day_events
            for action, item_status in [(event.payload.get("action"), event.payload.get("status"))]
            if action and item_status
        )
        activity.append(
            EventLogDayActivity(
                day=day,
                total_events=len(day_events),
                sources=sources.most_common(top),
                workflows=workflows.most_common(top),
                outcomes=outcomes.most_common(top),
            )
        )
    return activity


def summarize_attention_event_activity_days(
    path: Path,
    *,
    days: int = 5,
    top: int = 3,
    source: str | None = None,
    workflow: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
) -> list[EventLogDayActivity]:
    if days <= 0:
        return []
    events = filter_attention_events(
        filter_events(
            read_event_log(path.expanduser()),
            source=source,
            workflow=workflow,
            since=since,
            until=until,
        )
    )
    grouped: dict[str, list[DomainEvent]] = {}
    for event in events:
        day = event.occurred_at.date().isoformat()
        grouped.setdefault(day, []).append(event)
    recent_days = sorted(grouped.keys(), reverse=True)[:days]
    activity: list[EventLogDayActivity] = []
    for day in sorted(recent_days):
        day_events = grouped[day]
        sources = Counter(event.source for event in day_events)
        workflows = Counter(
            str(item)
            for event in day_events
            for item in [event.payload.get("workflow")]
            if item
        )
        outcomes = Counter(
            f"{action}:{item_status}"
            for event in day_events
            for action, item_status in [(event.payload.get("action"), event.payload.get("status"))]
            if action and item_status
        )
        activity.append(
            EventLogDayActivity(
                day=day,
                total_events=len(day_events),
                sources=sources.most_common(top),
                workflows=workflows.most_common(top),
                outcomes=outcomes.most_common(top),
            )
        )
    return activity


def tail_attention_event_log(
    path: Path,
    *,
    limit: int = 10,
    source: str | None = None,
    workflow: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
) -> list[DomainEvent]:
    if limit <= 0:
        return []
    events = filter_attention_events(
        filter_events(
            read_event_log(path.expanduser()),
            source=source,
            workflow=workflow,
            since=since,
            until=until,
        )
    )
    return events[-limit:]

__all__ = [
    "ATTENTION_NAME_SUFFIXES",
    "ATTENTION_STATUSES",
    "EventLogDayActivity",
    "EventLogSummary",
    "build_event_log_summary",
    "event_to_dict",
    "filter_attention_events",
    "filter_events",
    "filter_events_by_source",
    "filter_events_by_status",
    "filter_events_by_workflow",
    "filter_events_since",
    "filter_events_until",
    "is_attention_event",
    "read_event_log",
    "resolve_since_datetime",
    "resolve_until_datetime",
    "summarize_attention_event_log",
    "summarize_attention_event_activity_days",
    "summarize_event_activity_days",
    "summarize_event_log",
    "tail_attention_event_log",
    "tail_event_log",
]
