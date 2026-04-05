from __future__ import annotations

import re
from datetime import datetime

from brain_ops.intents import (
    CreateDietPlanIntent,
    IntentModel,
    SetActiveDietIntent,
    UpdateDietMealIntent,
)
from brain_ops.models import RouteDecisionResult
from brain_ops.storage.sqlite import fetch_diet_plan_names


def build_diet_intent_from_decision(
    text: str,
    decision: RouteDecisionResult,
    *,
    database_path: object,
) -> IntentModel | None:
    if decision.command == "create-diet-plan":
        parsed = _parse_natural_diet_plan(text)
        return (
            CreateDietPlanIntent(
                confidence=decision.confidence,
                routing_source=decision.routing_source,
                **parsed,
            )
            if parsed
            else None
        )
    if decision.command == "set-active-diet":
        name = _parse_active_diet_name(text, database_path)
        return (
            SetActiveDietIntent(
                name=name,
                confidence=decision.confidence,
                routing_source=decision.routing_source,
            )
            if name
            else None
        )
    if decision.command == "update-diet-meal":
        parsed = _parse_diet_meal_update_input(text, decision)
        return (
            UpdateDietMealIntent(
                confidence=decision.confidence,
                routing_source=decision.routing_source,
                **parsed,
            )
            if parsed
            else None
        )
    return None


def _parse_natural_diet_plan(text: str) -> dict[str, object] | None:
    if "dieta" not in text.lower():
        return None
    meals = _extract_diet_meal_specs(text)
    if len(meals) < 2:
        return None
    return {
        "name": f"Dieta {datetime.now().strftime('%Y-%m-%d %H%M%S')}",
        "meals": meals,
        "activate": True,
    }


def _parse_diet_meal_update_input(text: str, decision: RouteDecisionResult) -> dict[str, object] | None:
    meal_focus = decision.extracted_fields.get("meal_focus_hint")
    if not isinstance(meal_focus, str):
        return None
    mode = _as_str(decision.extracted_fields.get("update_mode_hint")) or "replace"
    items_text = _extract_items_for_diet_meal_update(text, meal_focus, mode)
    if not items_text:
        return None
    return {
        "meal_type": _normalize_meal_focus(meal_focus),
        "items_text": items_text,
        "mode": mode,
    }


def _parse_active_diet_name(text: str, database_path: object) -> str | None:
    lowered = text.lower()
    for name in fetch_diet_plan_names(database_path):
        if name.lower() in lowered:
            return name
    return None


def _extract_diet_meal_specs(text: str) -> list[str]:
    matches = list(re.finditer(r"(desayuno|comida|cena)\s*[:\-]?\s*", text, flags=re.IGNORECASE))
    if not matches:
        return []
    specs: list[str] = []
    for index, match in enumerate(matches):
        meal_label = match.group(1)
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        items_text = text[start:end].strip(" .;,-")
        if items_text:
            specs.append(
                f"{_normalize_meal_focus(meal_label)}|{meal_label.capitalize()}|{items_text}"
            )
    return specs


def _extract_items_for_diet_meal_update(text: str, meal_focus: str, mode: str) -> str | None:
    lowered = text.lower()
    marker = meal_focus.lower()
    if mode == "append":
        match = re.search(
            rf"^(?:agrega|añade|anade)\s+(.+?)\s+a\s+(?:mi\s+)?{re.escape(marker)}(?:\s+de\s+la\s+dieta|\s+de\s+mi\s+dieta)?\s*$",
            text,
            flags=re.IGNORECASE,
        )
        return match.group(1).strip(" .") if match else None
    if marker not in lowered:
        return None
    start_index = lowered.index(marker) + len(marker)
    remainder = text[start_index:].strip()
    remainder = re.sub(
        r"^(?:\s*(?:de\s+la\s+dieta|de\s+mi\s+dieta|a|por|con))+\s*",
        "",
        remainder,
        flags=re.IGNORECASE,
    )
    remainder = re.sub(
        r"\s*(?:de\s+la\s+dieta|de\s+mi\s+dieta)\s*$",
        "",
        remainder,
        flags=re.IGNORECASE,
    ).strip(" .")
    return remainder or None


def _normalize_meal_focus(value: str) -> str:
    mapping = {
        "desayuno": "breakfast",
        "breakfast": "breakfast",
        "comida": "lunch",
        "lunch": "lunch",
        "cena": "dinner",
        "dinner": "dinner",
        "all_meals": "all_meals",
        "comidas": "all_meals",
    }
    return mapping.get(value.lower(), value.lower())


def _as_str(value: object) -> str | None:
    return value if isinstance(value, str) else None
