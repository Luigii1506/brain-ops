"""Application workflows for monitoring/observability."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from brain_ops.errors import ConfigError
from brain_ops.core.events import (
    DomainEvent,
    EventLogDayActivity,
    EventLogSummary,
    resolve_since_datetime,
    resolve_until_datetime,
    summarize_attention_event_activity_days,
    summarize_attention_event_log,
    summarize_event_activity_days,
    summarize_event_log,
    tail_attention_event_log,
    tail_event_log,
)


@dataclass(slots=True, frozen=True)
class EventLogReport:
    summary: EventLogSummary
    daily_activity: list[EventLogDayActivity]
    recent_events: list[DomainEvent]
    highlights: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return {
            "summary": self.summary.to_dict(),
            "highlights": dict(self.highlights),
            "daily_activity": [activity.to_dict() for activity in self.daily_activity],
            "recent_events": [
                {
                    "event_id": event.event_id,
                    "name": event.name,
                    "source": event.source,
                    "occurred_at": event.occurred_at.isoformat(),
                    "payload": dict(event.payload),
                    "correlation_id": event.correlation_id,
                    "causation_id": event.causation_id,
                }
                for event in self.recent_events
            ],
        }


@dataclass(slots=True, frozen=True)
class EventLogHotspots:
    summary: EventLogSummary
    highlights: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return {
            "highlights": dict(self.highlights),
            "sources": [{"source": source, "count": count} for source, count in self.summary.sources],
            "workflows": [{"workflow": workflow, "count": count} for workflow, count in self.summary.workflows],
            "outcomes": [{"outcome": outcome, "count": count} for outcome, count in self.summary.outcomes],
            "paths": [{"path": path, "count": count} for path, count in self.summary.paths],
        }


@dataclass(slots=True, frozen=True)
class EventLogFailures:
    summary: EventLogSummary
    recent_events: list[DomainEvent]

    def to_dict(self) -> dict[str, object]:
        return {
            "summary": self.summary.to_dict(),
            "recent_events": [
                {
                    "event_id": event.event_id,
                    "name": event.name,
                    "source": event.source,
                    "occurred_at": event.occurred_at.isoformat(),
                    "payload": dict(event.payload),
                    "correlation_id": event.correlation_id,
                    "causation_id": event.causation_id,
                }
                for event in self.recent_events
            ],
        }


@dataclass(slots=True, frozen=True)
class EventLogAlerts:
    summary: EventLogSummary
    daily_activity: list[EventLogDayActivity]
    recent_events: list[DomainEvent]
    highlights: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return {
            "summary": self.summary.to_dict(),
            "highlights": dict(self.highlights),
            "daily_activity": [activity.to_dict() for activity in self.daily_activity],
            "recent_events": [
                {
                    "event_id": event.event_id,
                    "name": event.name,
                    "source": event.source,
                    "occurred_at": event.occurred_at.isoformat(),
                    "payload": dict(event.payload),
                    "correlation_id": event.correlation_id,
                    "causation_id": event.causation_id,
                }
                for event in self.recent_events
            ],
        }


@dataclass(slots=True, frozen=True)
class EventLogAlertCheck:
    alerts: EventLogAlerts
    policy: EventLogAlertPolicy
    triggered_rules: list[str]
    ok: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "policy": self.policy.to_dict(),
            "triggered_rules": list(self.triggered_rules),
            "alerts": self.alerts.to_dict(),
        }


@dataclass(slots=True, frozen=True)
class EventLogAlertPolicy:
    max_total_events: int | None = None
    max_latest_day_events: int | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "max_total_events": self.max_total_events,
            "max_latest_day_events": self.max_latest_day_events,
        }


EVENT_LOG_ALERT_POLICY_PRESETS: dict[str, EventLogAlertPolicy] = {
    "lenient": EventLogAlertPolicy(max_total_events=10, max_latest_day_events=5),
    "default": EventLogAlertPolicy(max_total_events=5, max_latest_day_events=3),
    "strict": EventLogAlertPolicy(max_total_events=1, max_latest_day_events=1),
}


def execute_event_log_alert_presets_workflow() -> dict[str, EventLogAlertPolicy]:
    return dict(EVENT_LOG_ALERT_POLICY_PRESETS)


def build_event_log_report_highlights(
    summary: EventLogSummary,
    daily_activity: list[EventLogDayActivity],
) -> dict[str, object]:
    latest_day = daily_activity[-1] if daily_activity else None
    return {
        "latest_day": latest_day.day if latest_day else None,
        "latest_day_total_events": latest_day.total_events if latest_day else 0,
        "latest_day_top_source": latest_day.sources[0][0] if latest_day and latest_day.sources else None,
        "latest_day_top_workflow": latest_day.workflows[0][0] if latest_day and latest_day.workflows else None,
        "latest_day_top_outcome": latest_day.outcomes[0][0] if latest_day and latest_day.outcomes else None,
        "top_path": summary.paths[0][0] if summary.paths else None,
    }


def build_event_log_alert_policy(
    *,
    preset: str | None = None,
    max_total_events: int | None,
    max_latest_day_events: int | None,
) -> EventLogAlertPolicy:
    base = EVENT_LOG_ALERT_POLICY_PRESETS.get("default")
    if preset is not None:
        base = EVENT_LOG_ALERT_POLICY_PRESETS.get(preset)
        if base is None:
            allowed = ", ".join(sorted(EVENT_LOG_ALERT_POLICY_PRESETS))
            raise ConfigError(f"Unknown alert preset '{preset}'. Expected one of: {allowed}.")
    return EventLogAlertPolicy(
        max_total_events=base.max_total_events if max_total_events is None else max_total_events,
        max_latest_day_events=base.max_latest_day_events if max_latest_day_events is None else max_latest_day_events,
    )


def evaluate_event_log_alerts(
    alerts: EventLogAlerts,
    *,
    policy: EventLogAlertPolicy,
) -> EventLogAlertCheck:
    triggered_rules: list[str] = []
    if policy.max_total_events is not None and alerts.summary.total_events > policy.max_total_events:
        triggered_rules.append(
            f"total_events>{policy.max_total_events} ({alerts.summary.total_events})"
        )
    latest_day_total = int(alerts.highlights.get("latest_day_total_events") or 0)
    if policy.max_latest_day_events is not None and latest_day_total > policy.max_latest_day_events:
        triggered_rules.append(
            f"latest_day_total_events>{policy.max_latest_day_events} ({latest_day_total})"
        )
    return EventLogAlertCheck(
        alerts=alerts,
        policy=policy,
        triggered_rules=triggered_rules,
        ok=not triggered_rules,
    )


def execute_event_log_summary_workflow(
    *,
    event_log_path: Path | None,
    top: int,
    source: str | None,
    workflow: str | None,
    status: str | None,
    since: str | None,
    until: str | None,
    load_event_log_path,
    parse_since=resolve_since_datetime,
    parse_until=resolve_until_datetime,
    summarize_log=summarize_event_log,
) -> EventLogSummary:
    return summarize_log(
        load_event_log_path(event_log_path),
        top=top,
        source=source,
        workflow=workflow,
        status=status,
        since=parse_since(since),
        until=parse_until(until),
    )


def execute_event_log_tail_workflow(
    *,
    event_log_path: Path | None,
    limit: int,
    source: str | None,
    workflow: str | None,
    status: str | None,
    since: str | None,
    until: str | None,
    load_event_log_path,
    parse_since=resolve_since_datetime,
    parse_until=resolve_until_datetime,
    tail_log=tail_event_log,
) -> list[DomainEvent]:
    return tail_log(
        load_event_log_path(event_log_path),
        limit=limit,
        source=source,
        workflow=workflow,
        status=status,
        since=parse_since(since),
        until=parse_until(until),
    )


def execute_event_log_report_workflow(
    *,
    event_log_path: Path | None,
    top: int,
    limit: int,
    source: str | None,
    workflow: str | None,
    status: str | None,
    since: str | None,
    until: str | None,
    load_event_log_path,
    parse_since=resolve_since_datetime,
    parse_until=resolve_until_datetime,
    summarize_activity=summarize_event_activity_days,
    summarize_log=summarize_event_log,
    tail_log=tail_event_log,
    build_highlights=build_event_log_report_highlights,
) -> EventLogReport:
    resolved_path = load_event_log_path(event_log_path)
    parsed_since = parse_since(since)
    parsed_until = parse_until(until)
    summary = summarize_log(
        resolved_path,
        top=top,
        source=source,
        workflow=workflow,
        status=status,
        since=parsed_since,
        until=parsed_until,
    )
    daily_activity = summarize_activity(
        resolved_path,
        days=top,
        top=top,
        source=source,
        workflow=workflow,
        status=status,
        since=parsed_since,
        until=parsed_until,
    )
    recent_events = tail_log(
        resolved_path,
        limit=limit,
        source=source,
        workflow=workflow,
        status=status,
        since=parsed_since,
        until=parsed_until,
    )
    return EventLogReport(
        summary=summary,
        daily_activity=daily_activity,
        recent_events=recent_events,
        highlights=build_highlights(summary, daily_activity),
    )


def execute_event_log_hotspots_workflow(
    *,
    event_log_path: Path | None,
    top: int,
    source: str | None,
    workflow: str | None,
    status: str | None,
    since: str | None,
    until: str | None,
    load_event_log_path,
    parse_since=resolve_since_datetime,
    parse_until=resolve_until_datetime,
    summarize_log=summarize_event_log,
) -> EventLogHotspots:
    summary = summarize_log(
        load_event_log_path(event_log_path),
        top=top,
        source=source,
        workflow=workflow,
        status=status,
        since=parse_since(since),
        until=parse_until(until),
    )
    return EventLogHotspots(summary=summary, highlights=build_event_log_report_highlights(summary, []))


def execute_event_log_failures_workflow(
    *,
    event_log_path: Path | None,
    top: int,
    limit: int,
    source: str | None,
    workflow: str | None,
    since: str | None,
    until: str | None,
    load_event_log_path,
    parse_since=resolve_since_datetime,
    parse_until=resolve_until_datetime,
    summarize_log=summarize_attention_event_log,
    tail_log=tail_attention_event_log,
) -> EventLogFailures:
    resolved_path = load_event_log_path(event_log_path)
    parsed_since = parse_since(since)
    parsed_until = parse_until(until)
    return EventLogFailures(
        summary=summarize_log(
            resolved_path,
            top=top,
            source=source,
            workflow=workflow,
            since=parsed_since,
            until=parsed_until,
        ),
        recent_events=tail_log(
            resolved_path,
            limit=limit,
            source=source,
            workflow=workflow,
            since=parsed_since,
            until=parsed_until,
        ),
    )


def execute_event_log_alerts_workflow(
    *,
    event_log_path: Path | None,
    top: int,
    limit: int,
    source: str | None,
    workflow: str | None,
    since: str | None,
    until: str | None,
    load_event_log_path,
    parse_since=resolve_since_datetime,
    parse_until=resolve_until_datetime,
    summarize_log=summarize_attention_event_log,
    summarize_activity=summarize_attention_event_activity_days,
    tail_log=tail_attention_event_log,
    build_highlights=build_event_log_report_highlights,
) -> EventLogAlerts:
    resolved_path = load_event_log_path(event_log_path)
    parsed_since = parse_since(since)
    parsed_until = parse_until(until)
    summary = summarize_log(
        resolved_path,
        top=top,
        source=source,
        workflow=workflow,
        since=parsed_since,
        until=parsed_until,
    )
    daily_activity = summarize_activity(
        resolved_path,
        days=top,
        top=top,
        source=source,
        workflow=workflow,
        since=parsed_since,
        until=parsed_until,
    )
    recent_events = tail_log(
        resolved_path,
        limit=limit,
        source=source,
        workflow=workflow,
        since=parsed_since,
        until=parsed_until,
    )
    return EventLogAlerts(
        summary=summary,
        daily_activity=daily_activity,
        recent_events=recent_events,
        highlights=build_highlights(summary, daily_activity),
    )


def execute_event_log_alert_check_workflow(
    *,
    event_log_path: Path | None,
    top: int,
    limit: int,
    source: str | None,
    workflow: str | None,
    since: str | None,
    until: str | None,
    preset: str | None,
    max_total_events: int | None,
    max_latest_day_events: int | None,
    load_event_log_path,
    execute_alerts=execute_event_log_alerts_workflow,
    build_policy=build_event_log_alert_policy,
    evaluate_alerts=evaluate_event_log_alerts,
) -> EventLogAlertCheck:
    alerts = execute_alerts(
        event_log_path=event_log_path,
        top=top,
        limit=limit,
        source=source,
        workflow=workflow,
        since=since,
        until=until,
        load_event_log_path=load_event_log_path,
    )
    policy = build_policy(
        preset=preset,
        max_total_events=max_total_events,
        max_latest_day_events=max_latest_day_events,
    )
    return evaluate_alerts(
        alerts,
        policy=policy,
    )

__all__ = [
    "EventLogAlertCheck",
    "EventLogAlertPolicy",
    "EventLogAlerts",
    "EventLogFailures",
    "EventLogHotspots",
    "EventLogReport",
    "EVENT_LOG_ALERT_POLICY_PRESETS",
    "build_event_log_alert_policy",
    "build_event_log_report_highlights",
    "evaluate_event_log_alerts",
    "execute_event_log_alert_presets_workflow",
    "execute_event_log_alert_check_workflow",
    "execute_event_log_alerts_workflow",
    "execute_event_log_failures_workflow",
    "execute_event_log_hotspots_workflow",
    "execute_event_log_report_workflow",
    "execute_event_log_summary_workflow",
    "execute_event_log_tail_workflow",
]
