from __future__ import annotations

import re
import unicodedata

from brain_ops.models import RouteDecisionResult
from brain_ops.services.router_diet import build_diet_route_decision
from brain_ops.services.router_knowledge import build_knowledge_route_decision
from brain_ops.services.router_logging import build_logging_route_decision
from brain_ops.services.router_personal import build_personal_route_decision


# ---------------------------------------------------------------------------
# Text normalization
# ---------------------------------------------------------------------------

def _strip_accents(text: str) -> str:
    """Remove diacritical marks (á→a, é→e, etc.) for matching purposes."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))


def normalize_capture_text(text: str) -> tuple[str, str, str]:
    """Normalize input text for capture routing.

    Returns (original_stripped, lowered, accent_stripped_lowered).
    - original_stripped: whitespace-trimmed, duplicate spaces removed, original case.
    - lowered: lowercased version for primary matching.
    - accent_stripped_lowered: lowercased + accent-stripped for secondary matching.
    """
    stripped = text.strip()
    stripped = re.sub(r"\s+", " ", stripped)
    lowered = stripped.lower()
    accent_stripped = _strip_accents(lowered)
    return stripped, lowered, accent_stripped


# ---------------------------------------------------------------------------
# Multi-intent splitting
# ---------------------------------------------------------------------------

_SPLIT_CONNECTORS = re.compile(
    r"\s+(?:y|después|despues|luego|también|tambien|además|ademas)\s+",
    re.IGNORECASE,
)

# Known keywords that signal a valid intent segment
_INTENT_KEYWORDS = [
    "comí", "comi", "desayuné", "desayune", "almorcé", "almorce", "cené", "cene",
    "entrené", "entrene", "hice", "gasté", "gaste", "pagué", "pague",
    "tomé", "tome", "suplemento", "creatina", "proteína", "proteina",
    "hábito", "habito", "peso", "medí", "medi",
    "corrí", "corri", "caminé", "camine", "cardio",
    "compré", "compre", "uber", "taxi",
    "me sentí", "me senti", "reflexión", "reflexion",
    "anoté", "anote", "registré", "registre",
]


def _looks_like_intent(segment: str) -> bool:
    """Return True if *segment* looks like a standalone intent."""
    words = segment.strip().split()
    if len(words) >= 3:
        return True
    lowered = segment.lower()
    return any(kw in lowered for kw in _INTENT_KEYWORDS)


def split_multi_intent(text: str) -> list[str]:
    """Split text on Spanish connectors and semicolons into intent segments.

    Only splits if both parts look like separate intents (>=3 words or
    contains a known keyword).  Returns a list of segments (1 segment if
    no split needed).
    """
    # First split on semicolons
    parts: list[str] = []
    for chunk in text.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        # Then split on Spanish connectors
        sub_parts = _SPLIT_CONNECTORS.split(chunk)
        parts.extend(p.strip() for p in sub_parts if p.strip())

    if len(parts) <= 1:
        return [text.strip()]

    # Validate that all parts look like intents
    if all(_looks_like_intent(p) for p in parts):
        return parts

    # If any part doesn't look like an intent, don't split
    return [text.strip()]


# ---------------------------------------------------------------------------
# Reflective / journal keywords
# ---------------------------------------------------------------------------

REFLECTIVE_KEYWORDS = [
    "me sentí", "me senti", "fue un día", "fue un dia", "estoy",
    "pienso", "creo que", "aprendí", "aprendi", "reflexión",
    "me di cuenta", "necesito", "quiero",
]


def _is_reflective(lowered: str) -> bool:
    return any(kw in lowered for kw in REFLECTIVE_KEYWORDS)


# ---------------------------------------------------------------------------
# Core routing
# ---------------------------------------------------------------------------

def route_input(text: str) -> RouteDecisionResult:
    original, lowered, _accent_stripped = normalize_capture_text(text)
    extracted: dict[str, object] = {}

    if _is_daily_status_query(lowered):
        return RouteDecisionResult(
            input_text=original,
            domain="daily_status",
            command="daily-status",
            confidence=0.92,
            reason="Detected daily overview query.",
            routing_source="heuristic",
            extracted_fields=extracted,
        )

    diet_decision = build_diet_route_decision(original)
    if diet_decision is not None:
        return diet_decision

    personal_decision = build_personal_route_decision(original)
    if personal_decision is not None:
        return personal_decision

    logging_decision = build_logging_route_decision(original)
    if logging_decision is not None:
        return logging_decision

    knowledge_decision = build_knowledge_route_decision(original)
    if knowledge_decision is not None:
        return knowledge_decision

    # Reflective / journal detection — higher confidence than generic fallback
    if _is_reflective(lowered):
        return RouteDecisionResult(
            input_text=original,
            domain="daily",
            command="daily-log",
            confidence=0.70,
            reason="Detected reflective/journal language.",
            routing_source="heuristic",
            extracted_fields=extracted,
        )

    # TODO: LLM fallback here when confidence < 0.75 and use_llm=True

    return RouteDecisionResult(
        input_text=original,
        domain="daily",
        command="daily-log",
        confidence=0.55,
        reason="No stronger domain signal found; defaulting to generic daily log.",
        routing_source="heuristic",
        extracted_fields=extracted,
    )


def route_input_multi(text: str) -> list[RouteDecisionResult]:
    """Split *text* into intent segments and route each one independently."""
    segments = split_multi_intent(text)
    return [route_input(seg) for seg in segments]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
