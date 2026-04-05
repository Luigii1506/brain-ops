"""Minimal internal event models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from brain_ops.models import OperationRecord


@dataclass(slots=True, frozen=True)
class DomainEvent:
    name: str
    source: str
    payload: dict[str, object] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    event_id: str = field(default_factory=lambda: str(uuid4()))
    correlation_id: str | None = None
    causation_id: str | None = None


def new_event(
    name: str,
    *,
    source: str,
    payload: dict[str, object] | None = None,
    occurred_at: datetime | None = None,
    event_id: str | None = None,
    correlation_id: str | None = None,
    causation_id: str | None = None,
) -> DomainEvent:
    return DomainEvent(
        name=name,
        source=source,
        payload=dict(payload or {}),
        occurred_at=occurred_at or datetime.now(UTC),
        event_id=event_id or str(uuid4()),
        correlation_id=correlation_id,
        causation_id=causation_id,
    )


def event_from_operation(
    operation: OperationRecord,
    *,
    source: str,
    payload: dict[str, object] | None = None,
    correlation_id: str | None = None,
    causation_id: str | None = None,
) -> DomainEvent:
    event_payload = {
        "action": operation.action,
        "path": str(operation.path),
        "detail": operation.detail,
        "status": operation.status.value,
    }
    event_payload.update(payload or {})
    return new_event(
        f"operation.{operation.status.value}",
        source=source,
        payload=event_payload,
        correlation_id=correlation_id,
        causation_id=causation_id,
    )


__all__ = ["DomainEvent", "event_from_operation", "new_event"]
