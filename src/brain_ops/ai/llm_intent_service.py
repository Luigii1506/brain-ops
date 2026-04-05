from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, ValidationError

from brain_ops.ai.ollama_client import generate_json
from brain_ops.config import AIConfig
from brain_ops.errors import AIProviderError
from brain_ops.intents import (
    ActiveDietIntent,
    BudgetStatusIntent,
    CaptureNoteIntent,
    CreateDietPlanIntent,
    DailyLogIntent,
    DailyStatusIntent,
    DietStatusIntent,
    HabitCheckinIntent,
    HabitStatusIntent,
    IntentModel,
    LogBodyMetricsIntent,
    LogExpenseIntent,
    LogMealIntent,
    LogSupplementIntent,
    LogWorkoutIntent,
    MacroStatusIntent,
    SetActiveDietIntent,
    SetBudgetTargetIntent,
    SetHabitTargetIntent,
    SetMacroTargetsIntent,
    UpdateDietMealIntent,
)


INTENT_NAMES = [
    "log_meal",
    "log_supplement",
    "habit_checkin",
    "log_body_metrics",
    "log_workout",
    "log_expense",
    "set_macro_targets",
    "set_budget_target",
    "set_habit_target",
    "create_diet_plan",
    "set_active_diet",
    "update_diet_meal",
    "macro_status",
    "budget_status",
    "habit_status",
    "diet_status",
    "active_diet",
    "daily_status",
    "capture_note",
    "daily_log",
]


class LLMIntentEnvelope(BaseModel):
    intent: Literal[tuple(INTENT_NAMES)]  # type: ignore[arg-type]
    confidence: float
    reason: str
    fields: dict[str, object] = Field(default_factory=dict)


def llm_parse_intent(ai: AIConfig, text: str) -> IntentModel:
    if ai.provider != "ollama":
        raise AIProviderError(f"Unsupported AI provider for local parsing: {ai.provider}")

    payload = generate_json(
        host=ai.ollama_host,
        model=ai.parser_model,
        prompt=_build_prompt(text),
        json_schema=LLMIntentEnvelope.model_json_schema(),
        timeout_seconds=ai.ollama_timeout_seconds,
    )
    try:
        envelope = LLMIntentEnvelope.model_validate(payload)
    except ValidationError as exc:
        raise AIProviderError(f"Ollama intent response failed validation: {exc}") from exc
    return _envelope_to_intent(envelope, text)


def _envelope_to_intent(envelope: LLMIntentEnvelope, text: str) -> IntentModel:
    base_fields = {
        "confidence": max(0.0, min(1.0, float(envelope.confidence))),
        "routing_source": "llm",
    }
    fields = dict(envelope.fields)
    try:
        match envelope.intent:
            case "log_meal":
                return LogMealIntent(meal_text=str(fields["meal_text"]), meal_type=fields.get("meal_type"), **base_fields)
            case "log_supplement":
                return LogSupplementIntent(
                    supplement_name=str(fields["supplement_name"]),
                    amount=_as_float(fields.get("amount")),
                    unit=_as_str(fields.get("unit")),
                    note=_as_str(fields.get("note")),
                    **base_fields,
                )
            case "habit_checkin":
                return HabitCheckinIntent(
                    habit_name=str(fields["habit_name"]),
                    status=_as_str(fields.get("status")) or "done",
                    note=_as_str(fields.get("note")),
                    **base_fields,
                )
            case "log_body_metrics":
                return LogBodyMetricsIntent(
                    weight_kg=_as_float(fields.get("weight_kg")),
                    body_fat_pct=_as_float(fields.get("body_fat_pct")),
                    waist_cm=_as_float(fields.get("waist_cm")),
                    note=_as_str(fields.get("note")),
                    **base_fields,
                )
            case "log_workout":
                return LogWorkoutIntent(workout_text=str(fields["workout_text"]), routine_name=_as_str(fields.get("routine_name")), **base_fields)
            case "log_expense":
                return LogExpenseIntent(
                    amount=float(fields["amount"]),
                    currency=_as_str(fields.get("currency")) or "MXN",
                    category=_as_str(fields.get("category")),
                    merchant=_as_str(fields.get("merchant")),
                    note=_as_str(fields.get("note")),
                    **base_fields,
                )
            case "set_macro_targets":
                return SetMacroTargetsIntent(
                    calories=_as_float(fields.get("calories")),
                    protein_g=_as_float(fields.get("protein_g")),
                    carbs_g=_as_float(fields.get("carbs_g")),
                    fat_g=_as_float(fields.get("fat_g")),
                    **base_fields,
                )
            case "set_budget_target":
                return SetBudgetTargetIntent(
                    amount=float(fields["amount"]),
                    period=_as_str(fields.get("period")) or "daily",
                    category=_as_str(fields.get("category")),
                    currency=_as_str(fields.get("currency")) or "MXN",
                    **base_fields,
                )
            case "set_habit_target":
                return SetHabitTargetIntent(
                    habit_name=str(fields["habit_name"]),
                    target_count=int(fields["target_count"]),
                    period=_as_str(fields.get("period")) or "daily",
                    **base_fields,
                )
            case "create_diet_plan":
                return CreateDietPlanIntent(
                    name=_as_str(fields.get("name")) or "Dieta LLM",
                    meals=[str(item) for item in fields.get("meals", []) if isinstance(item, str)],
                    notes=_as_str(fields.get("notes")),
                    activate=bool(fields.get("activate", True)),
                    **base_fields,
                )
            case "set_active_diet":
                return SetActiveDietIntent(name=str(fields["name"]), **base_fields)
            case "update_diet_meal":
                return UpdateDietMealIntent(
                    meal_type=str(fields["meal_type"]),
                    items_text=str(fields["items_text"]),
                    mode=_as_str(fields.get("mode")) or "replace",
                    **base_fields,
                )
            case "macro_status":
                return MacroStatusIntent(metric=_as_str(fields.get("metric")), date=_as_str(fields.get("date")), **base_fields)
            case "budget_status":
                return BudgetStatusIntent(period=_as_str(fields.get("period")) or "daily", category=_as_str(fields.get("category")), date=_as_str(fields.get("date")), **base_fields)
            case "habit_status":
                return HabitStatusIntent(period=_as_str(fields.get("period")) or "daily", date=_as_str(fields.get("date")), **base_fields)
            case "diet_status":
                return DietStatusIntent(meal_focus=_as_str(fields.get("meal_focus")), date=_as_str(fields.get("date")), **base_fields)
            case "active_diet":
                return ActiveDietIntent(date=_as_str(fields.get("date")), **base_fields)
            case "daily_status":
                return DailyStatusIntent(date=_as_str(fields.get("date")), **base_fields)
            case "capture_note":
                return CaptureNoteIntent(force_type=_as_str(fields.get("force_type")) or "knowledge", text=_as_str(fields.get("text")) or text, **base_fields)
            case "daily_log":
                return DailyLogIntent(text=_as_str(fields.get("text")) or text, log_domain=_as_str(fields.get("log_domain")) or "daily", **base_fields)
    except Exception as exc:
        raise AIProviderError(f"Ollama intent payload could not be converted: {exc}") from exc
    raise AIProviderError(f"Unsupported Ollama intent: {envelope.intent}")


def _as_str(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _as_float(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _build_prompt(text: str) -> str:
    intents = ", ".join(INTENT_NAMES)
    return f"""
Return only JSON matching the provided schema.

Choose one intent from:
{intents}

Rules:
- Prefer query intents for status questions.
- Prefer daily_status for broad daily overview questions.
- Prefer diet_status for meal-specific or diet-specific progress questions.
- Prefer capture_note only for durable knowledge/project inputs.
- For ambiguous or unsafe writes, choose daily_log instead of inventing fields.
- Keep fields minimal and only include what is needed.

Input:
{text}
""".strip()
