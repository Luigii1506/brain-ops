from __future__ import annotations

import re

from brain_ops.models import RouteDecisionResult

WORKOUT_PATTERN = re.compile(r"\b\d+x\d+(?:@\d+(?:\.\d+)?kg|@bodyweight)?\b", re.IGNORECASE)
AMOUNT_PATTERN = re.compile(r"(?P<amount>\d+(?:\.\d+)?)")
SUPPLEMENT_AMOUNT_PATTERN = re.compile(
    r"(?P<amount>\d+(?:\.\d+)?)\s*(?P<unit>mg|g|caps|c[aá]psulas?|ml|tabletas?)\b",
    re.IGNORECASE,
)
WEIGHT_METRIC_PATTERN = re.compile(r"(?P<value>\d+(?:\.\d+)?)\s*kg\b", re.IGNORECASE)
BODY_FAT_PATTERN = re.compile(r"(?P<value>\d+(?:\.\d+)?)\s*%", re.IGNORECASE)
WAIST_PATTERN = re.compile(r"(?P<value>\d+(?:\.\d+)?)\s*cm\b", re.IGNORECASE)
WORKOUT_KEYWORD_PATTERN = re.compile(
    r"\b(press|sentadilla|dominadas|peso muerto|remo|curl|extensiones|lagartijas|fondos)\b",
    re.IGNORECASE,
)
WORKOUT_ACTION_PATTERN = re.compile(
    r"\b(entren[eé]|hice|complet[eé]|rutina|series?|reps?)\b",
    re.IGNORECASE,
)
HABIT_HINTS = {
    "tomé agua": "tomar agua",
    "tome agua": "tomar agua",
    "medité": "meditar",
    "medite": "meditar",
    "leí": "leer",
    "lei": "leer",
    "caminé": "caminar",
    "camine": "caminar",
    "dormí": "dormir bien",
    "dormi": "dormir bien",
}
SUPPLEMENT_HINTS = [
    "creatina",
    "whey",
    "proteina",
    "proteína",
    "omega 3",
    "magnesio",
    "vitamina c",
    "vitamina d",
    "colageno",
    "colágeno",
]


def build_logging_route_decision(text: str) -> RouteDecisionResult | None:
    stripped = text.strip()
    lowered = stripped.lower()
    extracted: dict[str, object] = {}

    if any(keyword in lowered for keyword in ["gasté", "gaste", "pagué", "pague", "$", "mxn", "pesos", "compre", "compré"]):
        extracted["category_hint"] = _expense_category_hint(lowered)
        amount_match = AMOUNT_PATTERN.search(stripped)
        if amount_match:
            extracted["amount_hint"] = float(amount_match.group("amount"))
        extracted["currency_hint"] = "MXN" if any(token in lowered for token in ["peso", "pesos", "mxn", "$"]) else "MXN"
        return RouteDecisionResult(
            input_text=stripped,
            domain="expenses",
            command="log-expense",
            confidence=0.9,
            reason="Detected spending language.",
            routing_source="heuristic",
            extracted_fields=extracted,
        )

    if _is_body_metrics_input(lowered):
        extracted.update(_extract_body_metric_hints(stripped, lowered))
        return RouteDecisionResult(
            input_text=stripped,
            domain="body_metrics",
            command="log-body-metrics",
            confidence=0.87,
            reason="Detected body metrics language.",
            routing_source="heuristic",
            extracted_fields=extracted,
        )

    if WORKOUT_PATTERN.search(stripped) or (
        WORKOUT_KEYWORD_PATTERN.search(stripped) and WORKOUT_ACTION_PATTERN.search(stripped)
    ):
        return RouteDecisionResult(
            input_text=stripped,
            domain="fitness",
            command="log-workout",
            confidence=0.92,
            reason="Detected workout-like structure or gym language.",
            routing_source="heuristic",
            extracted_fields=extracted,
        )

    if any(keyword in lowered for keyword in ["creatina", "whey", "vitamina", "omega", "magnesio", "suplemento", "proteína", "proteina"]):
        supplement_name = next((hint for hint in SUPPLEMENT_HINTS if hint in lowered), None)
        if supplement_name:
            extracted["supplement_name_hint"] = supplement_name
        amount_match = SUPPLEMENT_AMOUNT_PATTERN.search(stripped)
        if amount_match:
            extracted["amount_hint"] = float(amount_match.group("amount"))
            extracted["unit_hint"] = amount_match.group("unit")
        return RouteDecisionResult(
            input_text=stripped,
            domain="supplements",
            command="log-supplement",
            confidence=0.88,
            reason="Detected supplement-related language.",
            routing_source="heuristic",
            extracted_fields=extracted,
        )

    if any(keyword in lowered for keyword in ["comí", "comi", "desayuné", "desayune", "cené", "cene", "almorcé", "almorce", "gramos", "calorías", "calorias", "proteína", "proteina"]):
        extracted["meal_type_hint"] = _meal_type_hint(lowered)
        return RouteDecisionResult(
            input_text=stripped,
            domain="nutrition",
            command="log-meal",
            confidence=0.9,
            reason="Detected meal or macro-related language.",
            routing_source="heuristic",
            extracted_fields=extracted,
        )

    if any(keyword in lowered for keyword in ["hábito", "habito", "medité", "medite", "leí", "lei", "tomé agua", "tome agua", "caminé", "camine"]):
        extracted["status_hint"] = _habit_status_hint(lowered)
        habit_name = next((name for phrase, name in HABIT_HINTS.items() if phrase in lowered), None)
        if habit_name:
            extracted["habit_name_hint"] = habit_name
        return RouteDecisionResult(
            input_text=stripped,
            domain="habits",
            command="habit-checkin",
            confidence=0.82,
            reason="Detected habit-style language.",
            routing_source="heuristic",
            extracted_fields=extracted,
        )

    return None


def _expense_category_hint(lowered: str) -> str:
    if any(word in lowered for word in ["gasolina", "pemex", "uber", "didi", "caseta"]):
        return "transporte"
    if any(word in lowered for word in ["comida", "restaurante", "oxxo", "super", "café", "cafe"]):
        return "comida"
    if any(word in lowered for word in ["farmacia", "medicina", "doctor", "consulta"]):
        return "salud"
    if any(word in lowered for word in ["amazon", "mercado libre", "herramienta", "software", "hosting"]):
        return "trabajo"
    return "general"


def _meal_type_hint(lowered: str) -> str | None:
    if "desayun" in lowered:
        return "breakfast"
    if "almorc" in lowered or "comi" in lowered or "comí" in lowered:
        return "lunch"
    if "cen" in lowered:
        return "dinner"
    return None


def _habit_status_hint(lowered: str) -> str:
    if any(token in lowered for token in ["no ", "no hice", "no pude", "faltó", "falto", "omit"]):
        return "skipped"
    if any(token in lowered for token in ["medio", "parcial", "un poco"]):
        return "partial"
    return "done"


def _is_body_metrics_input(lowered: str) -> bool:
    if "peso muerto" in lowered:
        return False
    metric_keywords = [
        "peso",
        "pese",
        "pesé",
        "grasa corporal",
        "body fat",
        "cintura",
        "medida de cintura",
    ]
    return any(keyword in lowered for keyword in metric_keywords)


def _extract_body_metric_hints(text: str, lowered: str) -> dict[str, object]:
    extracted: dict[str, object] = {}

    weight_match = WEIGHT_METRIC_PATTERN.search(text)
    if weight_match and any(token in lowered for token in ["peso", "pese", "pesé"]):
        extracted["weight_kg_hint"] = float(weight_match.group("value"))

    body_fat_match = BODY_FAT_PATTERN.search(text)
    if body_fat_match and any(token in lowered for token in ["grasa corporal", "body fat", "grasa"]):
        extracted["body_fat_pct_hint"] = float(body_fat_match.group("value"))

    waist_match = WAIST_PATTERN.search(text)
    if waist_match and "cintura" in lowered:
        extracted["waist_cm_hint"] = float(waist_match.group("value"))

    return extracted
