from __future__ import annotations

import re

from brain_ops.core.validation import has_any_non_none
from brain_ops.intents import (
    HabitCheckinIntent,
    IntentModel,
    LogBodyMetricsIntent,
    LogExpenseIntent,
    LogMealIntent,
    LogSupplementIntent,
    LogWorkoutIntent,
)
from brain_ops.models import RouteDecisionResult

AMOUNT_PATTERN = re.compile(r"(?P<amount>\d+(?:\.\d+)?)")
SUPPLEMENT_AMOUNT_PATTERN = re.compile(
    r"(?P<amount>\d+(?:\.\d+)?)\s*(?P<unit>mg|g|caps|c[aá]psulas?|ml|tabletas?)\b",
    re.IGNORECASE,
)
WEIGHT_METRIC_PATTERN = re.compile(r"(?P<value>\d+(?:\.\d+)?)\s*kg\b", re.IGNORECASE)
BODY_FAT_PATTERN = re.compile(r"(?P<value>\d+(?:\.\d+)?)\s*%", re.IGNORECASE)
WAIST_PATTERN = re.compile(r"(?P<value>\d+(?:\.\d+)?)\s*cm\b", re.IGNORECASE)
PAYMENT_METHOD_SUFFIX_PATTERN = re.compile(
    r"\b(?:con|usando)\s+(?:tarjeta|efectivo|d[ée]bito|debito|cr[ée]dito|credito|apple pay)\b.*$",
    re.IGNORECASE,
)
EXPENSE_MERCHANT_PATTERN = re.compile(
    r"\b(?:en|de|a|para)\s+([A-Za-zÁÉÍÓÚÑáéíóú0-9][A-Za-zÁÉÍÓÚÑáéíóú0-9& ._-]+)$"
)

HABIT_MAP = {
    "tomé agua": "tomar agua",
    "tome agua": "tomar agua",
    "medité": "meditar",
    "medite": "meditar",
    "leí": "leer",
    "lei": "leer",
    "caminé": "caminar",
    "camine": "caminar",
    "dormí bien": "dormir bien",
    "dormi bien": "dormir bien",
}
SUPPLEMENT_KEYWORDS = [
    "creatina",
    "whey",
    "proteina",
    "proteína",
    "omega 3",
    "magnesio",
    "vitamina c",
    "vitamina d",
]


def build_logging_intent_from_decision(
    text: str,
    decision: RouteDecisionResult,
) -> IntentModel | None:
    if decision.command == "log-expense":
        parsed = _parse_expense_input(text, decision)
        return (
            LogExpenseIntent(
                confidence=decision.confidence,
                routing_source=decision.routing_source,
                **parsed,
            )
            if parsed
            else None
        )
    if decision.command == "log-meal":
        return LogMealIntent(
            meal_text=_normalize_meal_input(text),
            meal_type=decision.extracted_fields.get("meal_type_hint")
            if isinstance(decision.extracted_fields.get("meal_type_hint"), str)
            else None,
            confidence=decision.confidence,
            routing_source=decision.routing_source,
        )
    if decision.command == "log-supplement":
        parsed = _parse_supplement_input(text)
        return (
            LogSupplementIntent(
                confidence=decision.confidence,
                routing_source=decision.routing_source,
                **parsed,
            )
            if parsed
            else None
        )
    if decision.command == "habit-checkin":
        parsed = _parse_habit_input(text)
        return (
            HabitCheckinIntent(
                confidence=decision.confidence,
                routing_source=decision.routing_source,
                **parsed,
            )
            if parsed
            else None
        )
    if decision.command == "log-body-metrics":
        parsed = _parse_body_metrics_input(text, decision)
        return (
            LogBodyMetricsIntent(
                confidence=decision.confidence,
                routing_source=decision.routing_source,
                **parsed,
            )
            if parsed
            else None
        )
    if decision.command == "log-workout":
        return LogWorkoutIntent(
            workout_text=_normalize_workout_input(text),
            confidence=decision.confidence,
            routing_source=decision.routing_source,
        )
    if decision.command == "task":
        from brain_ops.intents import TaskIntent

        title = decision.extracted_fields.get("title_hint", text)
        project = decision.extracted_fields.get("project_hint")
        return TaskIntent(
            title=str(title),
            project=str(project) if project else None,
            confidence=decision.confidence,
            routing_source=decision.routing_source,
        )
    return None


def _parse_expense_input(text: str, decision: RouteDecisionResult) -> dict[str, object] | None:
    amount_hint = decision.extracted_fields.get("amount_hint")
    amount_match = AMOUNT_PATTERN.search(text) if amount_hint is None else None
    if not amount_match:
        if not isinstance(amount_hint, (int, float)):
            return None
        amount = float(amount_hint)
    else:
        amount = float(amount_match.group("amount"))
    merchant = _parse_expense_merchant(text)
    category = decision.extracted_fields.get("category_hint")
    if not isinstance(category, str) or category == "general":
        category = _infer_expense_category_from_merchant(merchant)
    return {
        "amount": amount,
        "category": category if isinstance(category, str) else None,
        "merchant": merchant,
        "currency": str(decision.extracted_fields.get("currency_hint") or "MXN"),
        "note": text.strip(),
    }


def _normalize_meal_input(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(
        r"^(?:hoy\s+)?(?:me\s+)?(?:com[ií]|desayun[eé]|cen[eé]|almorc[eé]|merend[eé]|tom[eé])\s+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\b(?:fue|incluy[oó]|consisti[oó] en)\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+(?:junto con|adem[aá]s de|con)\s+", "; ", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.replace(", ", "; ")
    cleaned = cleaned.replace(" y ", "; ")
    cleaned = re.sub(r"\s*;\s*", "; ", cleaned)
    cleaned = re.sub(r"^\s*(?:un poco de|algo de)\s+", "", cleaned, flags=re.IGNORECASE)
    return cleaned


def _parse_supplement_input(text: str) -> dict[str, object] | None:
    lowered = text.lower().strip()
    name = next((keyword for keyword in SUPPLEMENT_KEYWORDS if keyword in lowered), None)
    if not name:
        return None
    amount = None
    unit = None
    match = SUPPLEMENT_AMOUNT_PATTERN.search(lowered)
    if match:
        amount = float(match.group("amount"))
        unit = match.group("unit")
    return {
        "supplement_name": _format_supplement_name(name),
        "amount": amount,
        "unit": unit,
        "note": text.strip(),
    }


def _parse_habit_input(text: str) -> dict[str, object] | None:
    lowered = text.lower()
    for phrase, habit_name in HABIT_MAP.items():
        if phrase in lowered:
            return {
                "habit_name": habit_name,
                "status": _infer_habit_status(lowered),
                "note": text.strip(),
            }
    return None


def _parse_body_metrics_input(text: str, decision: RouteDecisionResult) -> dict[str, object] | None:
    lowered = text.lower()
    weight_kg = decision.extracted_fields.get("weight_kg_hint")
    body_fat_pct = decision.extracted_fields.get("body_fat_pct_hint")
    waist_cm = decision.extracted_fields.get("waist_cm_hint")
    if weight_kg is None and any(token in lowered for token in ["peso", "pese", "pesé"]) and "peso muerto" not in lowered:
        match = WEIGHT_METRIC_PATTERN.search(text)
        if match:
            weight_kg = float(match.group("value"))
    if body_fat_pct is None and any(token in lowered for token in ["grasa corporal", "body fat", "grasa"]):
        match = BODY_FAT_PATTERN.search(text)
        if match:
            body_fat_pct = float(match.group("value"))
    if waist_cm is None and "cintura" in lowered:
        match = WAIST_PATTERN.search(text)
        if match:
            waist_cm = float(match.group("value"))
    if not has_any_non_none([weight_kg, body_fat_pct, waist_cm]):
        return None
    return {
        "weight_kg": float(weight_kg) if isinstance(weight_kg, (int, float)) else None,
        "body_fat_pct": float(body_fat_pct) if isinstance(body_fat_pct, (int, float)) else None,
        "waist_cm": float(waist_cm) if isinstance(waist_cm, (int, float)) else None,
        "note": text.strip(),
    }


def _normalize_workout_input(text: str) -> str:
    return re.sub(r"^(hoy\s+)?(hice|entren[eé])\s+", "", text.strip(), flags=re.IGNORECASE)


def _parse_expense_merchant(text: str) -> str | None:
    cleaned = PAYMENT_METHOD_SUFFIX_PATTERN.sub("", text).strip(" .")
    match = EXPENSE_MERCHANT_PATTERN.search(cleaned)
    if not match:
        return None
    merchant = match.group(1).strip(" .")
    merchant = re.sub(
        r"\b(?:gasolina|farmacia|comida|caf[eé]|cafe|uber|spotify|netflix)\b\s*$",
        "",
        merchant,
        flags=re.IGNORECASE,
    ).strip(" .")
    return merchant or None


def _infer_expense_category_from_merchant(merchant: str | None) -> str | None:
    if not merchant:
        return None
    lowered = merchant.lower()
    if any(name in lowered for name in ["pemex", "uber", "didi"]):
        return "transporte"
    if any(name in lowered for name in ["oxxo", "starbucks", "caffenio", "cafeteria", "cafetería"]):
        return "comida"
    if any(name in lowered for name in ["farmacia", "roma", "guadalajara"]):
        return "salud"
    return None


def _format_supplement_name(name: str) -> str:
    return " ".join(part.capitalize() for part in name.replace("-", " ").split())


def _infer_habit_status(lowered: str) -> str:
    if any(token in lowered for token in ["no ", "no hice", "no pude", "falto", "faltó"]):
        return "skipped"
    if any(token in lowered for token in ["parcial", "medio", "un poco"]):
        return "partial"
    return "done"
