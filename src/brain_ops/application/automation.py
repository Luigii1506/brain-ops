"""Application workflows for simple automation/delivery actions."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from brain_ops.errors import ConfigError

from .alerts import AlertMessage, execute_event_log_alert_message_workflow


@dataclass(slots=True, frozen=True)
class AlertDeliveryPreset:
    output_format: str = "json"
    filename_prefix: str = "event-log-alert"
    write_latest: bool = True
    delivery_mode: str = "both"
    target: str = "file"

    def to_dict(self) -> dict[str, object]:
        return {
            "output_format": self.output_format,
            "filename_prefix": self.filename_prefix,
            "write_latest": self.write_latest,
            "delivery_mode": self.delivery_mode,
            "target": self.target,
        }


ALERT_DELIVERY_PRESETS: dict[str, AlertDeliveryPreset] = {
    "default": AlertDeliveryPreset(),
    "file-text": AlertDeliveryPreset(output_format="text"),
    "stdout-json": AlertDeliveryPreset(target="stdout", delivery_mode="archive"),
    "stdout-text": AlertDeliveryPreset(output_format="text", target="stdout", delivery_mode="archive"),
    "archive-only": AlertDeliveryPreset(delivery_mode="archive"),
}


@dataclass(slots=True, frozen=True)
class AlertDeliveryPolicy:
    output_dir: Path
    output_format: str
    filename_prefix: str = "event-log-alert"
    write_latest: bool = True
    delivery_mode: str = "both"
    target: str = "file"

    def to_dict(self) -> dict[str, object]:
        return {
            "output_dir": str(self.output_dir),
            "output_format": self.output_format,
            "filename_prefix": self.filename_prefix,
            "write_latest": self.write_latest,
            "delivery_mode": self.delivery_mode,
            "target": self.target,
        }


@dataclass(slots=True, frozen=True)
class AlertDelivery:
    message: AlertMessage
    output_path: Path
    output_format: str
    target: str = "file"
    latest_path: Path | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "message": self.message.to_dict(),
            "output_path": str(self.output_path),
            "output_format": self.output_format,
            "target": self.target,
            "latest_path": str(self.latest_path) if self.latest_path is not None else None,
        }


def render_alert_message_text(message: AlertMessage) -> str:
    lines = [
        f"level: {message.level}",
        f"title: {message.title}",
        f"summary: {message.summary}",
        f"triggered_rules: {', '.join(message.triggered_rules) if message.triggered_rules else '-'}",
    ]
    for key, value in message.highlights.items():
        lines.append(f"{key}: {value}")
    return "\n".join(lines) + "\n"


def write_alert_delivery(output_path: Path, payload: str) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(payload, encoding="utf-8")
    return output_path


def build_alert_delivery_policy(
    *,
    output_dir: Path,
    output_format: str | None = None,
    filename_prefix: str | None = None,
    write_latest: bool | None = None,
    delivery_mode: str | None = None,
    target: str | None = None,
    preset: str | None = None,
) -> AlertDeliveryPolicy:
    base = ALERT_DELIVERY_PRESETS["default"]
    if preset is not None:
        base = ALERT_DELIVERY_PRESETS.get(preset)
        if base is None:
            allowed = ", ".join(sorted(ALERT_DELIVERY_PRESETS))
            raise ConfigError(f"Unknown delivery preset '{preset}'. Expected one of: {allowed}.")
    resolved_format = output_format if output_format is not None else base.output_format
    resolved_prefix = filename_prefix if filename_prefix is not None else base.filename_prefix
    resolved_latest = write_latest if write_latest is not None else base.write_latest
    resolved_mode = delivery_mode if delivery_mode is not None else base.delivery_mode
    resolved_target = target if target is not None else base.target
    if resolved_mode not in {"archive", "latest", "both"}:
        raise ValueError(f"Unsupported alert delivery mode: {resolved_mode}")
    if resolved_target not in {"file", "stdout"}:
        raise ValueError(f"Unsupported alert delivery target: {resolved_target}")
    return AlertDeliveryPolicy(
        output_dir=output_dir,
        output_format=resolved_format,
        filename_prefix=resolved_prefix,
        write_latest=resolved_latest,
        delivery_mode=resolved_mode,
        target=resolved_target,
    )


def execute_alert_delivery_presets_workflow() -> dict[str, AlertDeliveryPreset]:
    return dict(ALERT_DELIVERY_PRESETS)


def resolve_alert_delivery_output_path(
    policy: AlertDeliveryPolicy,
    *,
    message: AlertMessage,
    source: str | None,
    workflow: str | None,
) -> Path:
    extension = "json" if policy.output_format == "json" else "txt"

    def _slug(value: str | None) -> str | None:
        if not value:
            return None
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        return slug or None

    parts = [policy.filename_prefix]
    source_slug = _slug(source)
    workflow_slug = _slug(workflow)
    if source_slug:
        parts.append(source_slug)
    if workflow_slug:
        parts.append(workflow_slug)
    parts.append(_slug(message.level) or "alert")
    filename = "-".join(parts) + f".{extension}"
    return policy.output_dir / filename


def resolve_alert_delivery_latest_path(policy: AlertDeliveryPolicy) -> Path | None:
    if not policy.write_latest:
        return None
    extension = "json" if policy.output_format == "json" else "txt"
    return policy.output_dir / f"{policy.filename_prefix}-latest.{extension}"


def resolve_alert_delivery_target_paths(
    policy: AlertDeliveryPolicy,
    *,
    message: AlertMessage,
    source: str | None,
    workflow: str | None,
    explicit_output_path: Path | None,
) -> tuple[Path, Path | None]:
    archive_path = explicit_output_path or resolve_alert_delivery_output_path(
        policy,
        message=message,
        source=source,
        workflow=workflow,
    )
    latest_path = resolve_alert_delivery_latest_path(policy)
    if policy.delivery_mode == "archive":
        return archive_path, None
    if policy.delivery_mode == "latest":
        return explicit_output_path or latest_path or archive_path, None
    return archive_path, latest_path


def deliver_alert_via_target(
    policy: AlertDeliveryPolicy,
    *,
    payload: str,
    output_path: Path,
    latest_path: Path | None,
    write_output=write_alert_delivery,
) -> tuple[Path, Path | None]:
    if policy.target == "stdout":
        return Path("<stdout>"), None
    if policy.target != "file":
        raise ValueError(f"Unsupported alert delivery target: {policy.target}")
    written_path = write_output(output_path, payload)
    if latest_path is not None and latest_path != written_path:
        write_output(latest_path, payload)
    return written_path, latest_path


def execute_event_log_alert_delivery_workflow(
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
    output_path: Path | None,
    output_format: str | None,
    delivery_mode: str | None,
    target: str | None,
    delivery_preset: str | None = None,
    resolve_output_dir,
    load_event_log_path,
    execute_alert_message=execute_event_log_alert_message_workflow,
    build_policy=build_alert_delivery_policy,
    resolve_target_paths=resolve_alert_delivery_target_paths,
    deliver_via_target=deliver_alert_via_target,
    render_text=render_alert_message_text,
) -> AlertDelivery:
    resolved_event_log_path = load_event_log_path(event_log_path)
    message = execute_alert_message(
        event_log_path=resolved_event_log_path,
        top=top,
        limit=limit,
        source=source,
        workflow=workflow,
        since=since,
        until=until,
        preset=preset,
        max_total_events=max_total_events,
        max_latest_day_events=max_latest_day_events,
        load_event_log_path=lambda _path: resolved_event_log_path,
    )
    policy = build_policy(
        output_dir=resolve_output_dir(output_path, event_log_path=resolved_event_log_path),
        output_format=output_format,
        delivery_mode=delivery_mode,
        target=target,
        preset=delivery_preset,
    )
    if policy.output_format == "json":
        payload = json.dumps(message.to_dict(), indent=2, sort_keys=True) + "\n"
    elif policy.output_format == "text":
        payload = render_text(message)
    else:
        raise ValueError(f"Unsupported alert delivery format: {policy.output_format}")
    final_output_path, latest_path = resolve_target_paths(
        policy,
        message=message,
        source=source,
        workflow=workflow,
        explicit_output_path=output_path,
    )
    written_path, delivered_latest_path = deliver_via_target(
        policy,
        payload=payload,
        output_path=final_output_path,
        latest_path=latest_path,
    )
    return AlertDelivery(
        message=message,
        output_path=written_path,
        output_format=policy.output_format,
        target=policy.target,
        latest_path=delivered_latest_path,
    )


__all__ = [
    "ALERT_DELIVERY_PRESETS",
    "AlertDelivery",
    "AlertDeliveryPolicy",
    "AlertDeliveryPreset",
    "build_alert_delivery_policy",
    "deliver_alert_via_target",
    "execute_alert_delivery_presets_workflow",
    "execute_event_log_alert_delivery_workflow",
    "render_alert_message_text",
    "resolve_alert_delivery_latest_path",
    "resolve_alert_delivery_output_path",
    "resolve_alert_delivery_target_paths",
    "write_alert_delivery",
]
