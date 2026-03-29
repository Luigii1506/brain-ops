from __future__ import annotations

from pydantic import BaseModel, Field, ValidationError

from brain_ops.ai.ollama_client import generate_json
from brain_ops.config import AIConfig
from brain_ops.errors import AIProviderError
from brain_ops.models import RouteDecisionResult


class LLMRouteSchema(BaseModel):
    domain: str
    command: str
    confidence: float
    reason: str
    extracted_fields: dict[str, object] = Field(default_factory=dict)


def llm_route_input(ai: AIConfig, text: str) -> RouteDecisionResult:
    if ai.provider != "ollama":
        raise AIProviderError(f"Unsupported AI provider for local routing: {ai.provider}")

    prompt = _build_prompt(text)
    payload = generate_json(
        host=ai.ollama_host,
        model=ai.parser_model,
        prompt=prompt,
        timeout_seconds=ai.ollama_timeout_seconds,
    )
    try:
        parsed = LLMRouteSchema.model_validate(payload)
    except ValidationError as exc:
        raise AIProviderError(f"Ollama routing response failed validation: {exc}") from exc

    return RouteDecisionResult(
        input_text=text.strip(),
        domain=parsed.domain.strip(),
        command=parsed.command.strip(),
        confidence=max(0.0, min(1.0, float(parsed.confidence))),
        reason=parsed.reason.strip(),
        routing_source="llm",
        extracted_fields=parsed.extracted_fields,
    )


def _build_prompt(text: str) -> str:
    return f"""
Return JSON only.

Choose one domain:
nutrition, supplements, habits, fitness, expenses, body_metrics, projects, knowledge, daily

Choose one command:
log-meal, log-supplement, habit-checkin, log-workout, log-expense, log-body-metrics,
capture --type project, capture --type knowledge, capture --type source, daily-log

Rules:
- use daily-log for reflection or daily narrative
- use log-workout only for training/routine/set/rep/exercise input
- use log-body-metrics for weight, body fat, waist, or body measurement input
- use capture --type knowledge for learning or durable insight
- use capture --type source for URL or external source input
- keep extracted_fields short

JSON schema:
{{
  "domain": "string",
  "command": "string",
  "confidence": 0.0,
  "reason": "string",
  "extracted_fields": {{}}
}}

Input: {text}
""".strip()
