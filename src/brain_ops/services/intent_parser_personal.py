from __future__ import annotations

import re

from brain_ops.core.validation import has_any_non_none
from brain_ops.intents import (
    ActiveDietIntent,
    BudgetStatusIntent,
    DietStatusIntent,
    HabitStatusIntent,
    IntentModel,
    MacroStatusIntent,
    SetBudgetTargetIntent,
    SetHabitTargetIntent,
    SetMacroTargetsIntent,
    DailyStatusIntent,
)
from brain_ops.models import RouteDecisionResult

PROTEIN_TARGET_PATTERN = re.compile(r"(?P<value>\d+(?:\.\d+)?)\s*g(?:r)?\s+de\s+prote[ií]na", re.IGNORECASE)
CARBS_TARGET_PATTERN = re.compile(r"(?P<value>\d+(?:\.\d+)?)\s*g(?:r)?\s+de\s+(?:carbs?|carbohidratos?)", re.IGNORECASE)
FAT_TARGET_PATTERN = re.compile(r"(?P<value>\d+(?:\.\d+)?)\s*g(?:r)?\s+de\s+(?:grasas?|fat)", re.IGNORECASE)
CALORIES_TARGET_PATTERN = re.compile(r"(?P<value>\d+(?:\.\d+)?)\s*(?:kcal|calor[ií]as?)", re.IGNORECASE)
AMOUNT_PATTERN = re.compile(r"(?P<amount>\d+(?:\.\d+)?)")
COUNT_PATTERN = re.compile(r"(?P<count>\d+)")


def build_personal_intent_from_decision(
    text: str,
    decision: RouteDecisionResult,
) -> IntentModel | None:
    if decision.command == "set-macro-targets":
        parsed = _parse_macro_target_input(text, decision)
        return (
            SetMacroTargetsIntent(
                confidence=decision.confidence,
                routing_source=decision.routing_source,
                **parsed,
            )
            if parsed
            else None
        )
    if decision.command == "set-budget-target":
        parsed = _parse_budget_target_input(text, decision)
        return (
            SetBudgetTargetIntent(
                confidence=decision.confidence,
                routing_source=decision.routing_source,
                **parsed,
            )
            if parsed
            else None
        )
    if decision.command == "set-habit-target":
        parsed = _parse_habit_target_input(text, decision)
        return (
            SetHabitTargetIntent(
                confidence=decision.confidence,
                routing_source=decision.routing_source,
                **parsed,
            )
            if parsed
            else None
        )
    if decision.command == "macro-status":
        return MacroStatusIntent(
            metric=_as_str(decision.extracted_fields.get("metric_hint")),
            confidence=decision.confidence,
            routing_source=decision.routing_source,
        )
    if decision.command == "budget-status":
        return BudgetStatusIntent(
            period=_as_str(decision.extracted_fields.get("period_hint")) or "daily",
            category=_clean_general(decision.extracted_fields.get("category_hint")),
            confidence=decision.confidence,
            routing_source=decision.routing_source,
        )
    if decision.command == "habit-status":
        return HabitStatusIntent(
            period=_as_str(decision.extracted_fields.get("period_hint")) or "daily",
            confidence=decision.confidence,
            routing_source=decision.routing_source,
        )
    if decision.command == "diet-status":
        return DietStatusIntent(
            meal_focus=_as_str(decision.extracted_fields.get("meal_focus_hint")),
            confidence=decision.confidence,
            routing_source=decision.routing_source,
        )
    if decision.command == "active-diet":
        return ActiveDietIntent(
            confidence=decision.confidence,
            routing_source=decision.routing_source,
        )
    if decision.command == "daily-status":
        return DailyStatusIntent(
            confidence=decision.confidence,
            routing_source=decision.routing_source,
        )
    return None


def _parse_macro_target_input(text: str, decision: RouteDecisionResult) -> dict[str, object] | None:
    protein = decision.extracted_fields.get("protein_g_hint")
    carbs = decision.extracted_fields.get("carbs_g_hint")
    fat = decision.extracted_fields.get("fat_g_hint")
    calories = decision.extracted_fields.get("calories_hint")
    if protein is None and (match := PROTEIN_TARGET_PATTERN.search(text)):
        protein = float(match.group("value"))
    if carbs is None and (match := CARBS_TARGET_PATTERN.search(text)):
        carbs = float(match.group("value"))
    if fat is None and (match := FAT_TARGET_PATTERN.search(text)):
        fat = float(match.group("value"))
    if calories is None and (match := CALORIES_TARGET_PATTERN.search(text)):
        calories = float(match.group("value"))
    parsed = {
        "calories": float(calories) if isinstance(calories, (int, float)) else None,
        "protein_g": float(protein) if isinstance(protein, (int, float)) else None,
        "carbs_g": float(carbs) if isinstance(carbs, (int, float)) else None,
        "fat_g": float(fat) if isinstance(fat, (int, float)) else None,
    }
    return None if not has_any_non_none(parsed.values()) else parsed


def _parse_budget_target_input(text: str, decision: RouteDecisionResult) -> dict[str, object] | None:
    amount = decision.extracted_fields.get("amount_hint")
    if amount is None and (amount_match := AMOUNT_PATTERN.search(text)):
        amount = float(amount_match.group("amount"))
    if not isinstance(amount, (int, float)):
        return None
    category = _clean_general(decision.extracted_fields.get("category_hint"))
    return {
        "amount": float(amount),
        "period": _as_str(decision.extracted_fields.get("period_hint")) or "daily",
        "category": category,
        "currency": _as_str(decision.extracted_fields.get("currency_hint")) or "MXN",
    }


def _parse_habit_target_input(text: str, decision: RouteDecisionResult) -> dict[str, object] | None:
    habit_name = decision.extracted_fields.get("habit_name_hint")
    count = decision.extracted_fields.get("target_count_hint")
    if count is None and (count_match := COUNT_PATTERN.search(text)):
        count = int(count_match.group("count"))
    if not isinstance(habit_name, str) or not isinstance(count, int):
        return None
    return {
        "habit_name": habit_name,
        "target_count": count,
        "period": _as_str(decision.extracted_fields.get("period_hint")) or "daily",
    }


def _clean_general(value: object) -> str | None:
    string_value = _as_str(value)
    if string_value == "general":
        return None
    return string_value


def _as_str(value: object) -> str | None:
    return value if isinstance(value, str) else None
