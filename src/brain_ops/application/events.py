"""Shared helpers for application-level event publication."""

from __future__ import annotations

from brain_ops.core.events import EventSink, event_from_operation, publish_events
from brain_ops.models import OperationRecord


def result_operations(result: object) -> list[OperationRecord]:
    if isinstance(result, list) and all(isinstance(item, OperationRecord) for item in result):
        return list(result)

    operation = getattr(result, "operation", None)
    if isinstance(operation, OperationRecord):
        return [operation]

    operations = getattr(result, "operations", None)
    if isinstance(operations, list) and all(isinstance(item, OperationRecord) for item in operations):
        return list(operations)

    return []


def publish_result_events(
    workflow_name: str,
    *,
    source: str,
    result: object,
    event_sink: EventSink | None,
) -> object:
    operations = result_operations(result)
    if not operations:
        return result

    events = [
        event_from_operation(
            operation,
            source=source,
            payload={"workflow": workflow_name},
        )
        for operation in operations
    ]
    publish_events(events, event_sink)
    return result


__all__ = ["publish_result_events", "result_operations"]
