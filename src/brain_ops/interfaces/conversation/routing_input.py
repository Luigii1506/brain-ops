from __future__ import annotations

from brain_ops.models import RouteDecisionResult
from brain_ops.services.router_diet import build_diet_route_decision
from brain_ops.services.router_knowledge import build_knowledge_route_decision
from brain_ops.services.router_logging import build_logging_route_decision
from brain_ops.services.router_personal import build_personal_route_decision


def route_input(text: str) -> RouteDecisionResult:
    stripped = text.strip()
    lowered = stripped.lower()
    extracted: dict[str, object] = {}

    if _is_daily_status_query(lowered):
        return RouteDecisionResult(
            input_text=stripped,
            domain="daily_status",
            command="daily-status",
            confidence=0.92,
            reason="Detected daily overview query.",
            routing_source="heuristic",
            extracted_fields=extracted,
        )

    diet_decision = build_diet_route_decision(stripped)
    if diet_decision is not None:
        return diet_decision

    personal_decision = build_personal_route_decision(stripped)
    if personal_decision is not None:
        return personal_decision

    logging_decision = build_logging_route_decision(stripped)
    if logging_decision is not None:
        return logging_decision

    knowledge_decision = build_knowledge_route_decision(stripped)
    if knowledge_decision is not None:
        return knowledge_decision

    return RouteDecisionResult(
        input_text=stripped,
        domain="daily",
        command="daily-log",
        confidence=0.55,
        reason="No stronger domain signal found; defaulting to generic daily log.",
        routing_source="heuristic",
        extracted_fields=extracted,
    )


def _is_daily_status_query(lowered: str) -> bool:
    return any(
        token in lowered
        for token in [
            "cómo voy hoy",
            "como voy hoy",
            "qué me falta hoy",
            "que me falta hoy",
            "resume mi día",
            "resume mi dia",
            "resumen de mi día",
            "resumen de mi dia",
        ]
    )
