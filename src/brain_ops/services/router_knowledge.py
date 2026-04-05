from __future__ import annotations

import re
from urllib.parse import urlparse

from brain_ops.models import RouteDecisionResult

URL_PATTERN = re.compile(r"https?://\S+")


def build_knowledge_route_decision(text: str) -> RouteDecisionResult | None:
    stripped = text.strip()
    lowered = stripped.lower()
    extracted: dict[str, object] = {}

    if URL_PATTERN.search(stripped):
        url = URL_PATTERN.search(stripped).group(0)
        extracted["url"] = url
        extracted["source_type"] = _source_type_for_url(url)
        return RouteDecisionResult(
            input_text=stripped,
            domain="knowledge",
            command="capture --type source",
            confidence=0.95,
            reason="Detected URL/source-like input.",
            routing_source="heuristic",
            extracted_fields=extracted,
        )

    if any(keyword in lowered for keyword in ["proyecto", "repo", "feature", "bug", "pendiente", "todo"]):
        return RouteDecisionResult(
            input_text=stripped,
            domain="projects",
            command="capture --type project",
            confidence=0.76,
            reason="Detected project-oriented language.",
            routing_source="heuristic",
            extracted_fields=extracted,
        )

    if any(keyword in lowered for keyword in ["aprendí", "aprendi", "idea", "concepto", "nota", "reflexión", "reflexion", "pienso", "siento"]):
        return RouteDecisionResult(
            input_text=stripped,
            domain="knowledge",
            command="capture --type knowledge",
            confidence=0.72,
            reason="Detected knowledge or reflection-oriented language.",
            routing_source="heuristic",
            extracted_fields=extracted,
        )

    return None


def _source_type_for_url(url: str) -> str:
    domain = urlparse(url).netloc.lower()
    if "youtube" in domain or "youtu.be" in domain:
        return "youtube"
    if "wikipedia" in domain:
        return "wikipedia"
    return "web"
