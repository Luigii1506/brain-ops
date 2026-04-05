"""Application workflows for actionable alerts built on monitoring checks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .monitoring import EventLogAlertCheck, execute_event_log_alert_check_workflow


@dataclass(slots=True, frozen=True)
class AlertMessage:
    level: str
    title: str
    summary: str
    triggered_rules: list[str]
    highlights: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return {
            "level": self.level,
            "title": self.title,
            "summary": self.summary,
            "triggered_rules": list(self.triggered_rules),
            "highlights": dict(self.highlights),
        }


def build_event_log_alert_message(check: EventLogAlertCheck) -> AlertMessage:
    latest_day = check.alerts.highlights.get("latest_day") or "-"
    latest_day_total = int(check.alerts.highlights.get("latest_day_total_events") or 0)
    top_source = check.alerts.highlights.get("latest_day_top_source") or "-"
    top_workflow = check.alerts.highlights.get("latest_day_top_workflow") or "-"
    top_outcome = check.alerts.highlights.get("latest_day_top_outcome") or "-"
    top_path = check.alerts.highlights.get("top_path") or "-"
    level = "ok" if check.ok else "alert"
    title = (
        "Event log alert check passed"
        if check.ok
        else f"Event log alert check triggered {len(check.triggered_rules)} rule(s)"
    )
    summary = (
        f"total={check.alerts.summary.total_events}; latest_day={latest_day}; "
        f"latest_total={latest_day_total}; source={top_source}; "
        f"workflow={top_workflow}; outcome={top_outcome}; path={top_path}"
    )
    return AlertMessage(
        level=level,
        title=title,
        summary=summary,
        triggered_rules=list(check.triggered_rules),
        highlights={
            "latest_day": latest_day,
            "latest_day_total_events": latest_day_total,
            "latest_day_top_source": top_source,
            "latest_day_top_workflow": top_workflow,
            "latest_day_top_outcome": top_outcome,
            "top_path": top_path,
            "total_events": check.alerts.summary.total_events,
        },
    )


def execute_event_log_alert_message_workflow(
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
    execute_alert_check=execute_event_log_alert_check_workflow,
    build_message=build_event_log_alert_message,
) -> AlertMessage:
    check = execute_alert_check(
        event_log_path=event_log_path,
        top=top,
        limit=limit,
        source=source,
        workflow=workflow,
        since=since,
        until=until,
        preset=preset,
        max_total_events=max_total_events,
        max_latest_day_events=max_latest_day_events,
        load_event_log_path=load_event_log_path,
    )
    return build_message(check)


__all__ = [
    "AlertMessage",
    "build_event_log_alert_message",
    "execute_event_log_alert_message_workflow",
]
