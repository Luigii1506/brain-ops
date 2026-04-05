from __future__ import annotations

"""Deprecated compatibility wrapper for conversation routing.

Retained for stable imports while callers migrate to
`brain_ops.interfaces.conversation.routing_input`.
"""

from brain_ops.interfaces.conversation.routing_input import route_input as route_conversation_input
from brain_ops.models import RouteDecisionResult


def route_input(text: str) -> RouteDecisionResult:
    return route_conversation_input(text)


__all__ = ["route_input", "RouteDecisionResult"]
