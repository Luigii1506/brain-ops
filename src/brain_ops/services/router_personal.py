from __future__ import annotations

import re

from brain_ops.models import RouteDecisionResult

AMOUNT_PATTERN = re.compile(r"(?P<amount>\d+(?:\.\d+)?)")
COUNT_PATTERN = re.compile(r"(?P<count>\d+)")
PROTEIN_TARGET_PATTERN = re.compile(r"(?P<value>\d+(?:\.\d+)?)\s*g(?:r)?\s+de\s+prote[ií]na", re.IGNORECASE)
CARBS_TARGET_PATTERN = re.compile(r"(?P<value>\d+(?:\.\d+)?)\s*g(?:r)?\s+de\s+(?:carbs?|carbohidratos?)", re.IGNORECASE)
FAT_TARGET_PATTERN = re.compile(r"(?P<value>\d+(?:\.\d+)?)\s*g(?:r)?\s+de\s+(?:grasas?|fat)", re.IGNORECASE)
CALORIES_TARGET_PATTERN = re.compile(r"(?P<value>\d+(?:\.\d+)?)\s*(?:kcal|calor[ií]as?)", re.IGNORECASE)

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


def build_personal_route_decision(text: str) -> RouteDecisionResult | None:
    stripped = text.strip()
    lowered = stripped.lower()
    extracted: dict[str, object] = {}

    if _is_macro_target_input(lowered):
        extracted.update(_extract_macro_target_hints(stripped))
        return RouteDecisionResult(
            input_text=stripped,
            domain="nutrition_goals",
            command="set-macro-targets",
            confidence=0.93,
            reason="Detected macro target-setting language.",
            routing_source="heuristic",
            extracted_fields=extracted,
        )

    if _is_budget_target_input(lowered):
        extracted.update(_extract_budget_target_hints(stripped, lowered))
        return RouteDecisionResult(
            input_text=stripped,
            domain="budget_goals",
            command="set-budget-target",
            confidence=0.93,
            reason="Detected budget target-setting language.",
            routing_source="heuristic",
            extracted_fields=extracted,
        )

    if _is_habit_target_input(lowered):
        extracted.update(_extract_habit_target_hints(stripped, lowered))
        return RouteDecisionResult(
            input_text=stripped,
            domain="habit_goals",
            command="set-habit-target",
            confidence=0.91,
            reason="Detected habit target-setting language.",
            routing_source="heuristic",
            extracted_fields=extracted,
        )

    if _is_macro_status_query(lowered):
        extracted["metric_hint"] = _macro_metric_hint(lowered)
        return RouteDecisionResult(
            input_text=stripped,
            domain="nutrition_status",
            command="macro-status",
            confidence=0.92,
            reason="Detected macro status query.",
            routing_source="heuristic",
            extracted_fields=extracted,
        )

    if _is_budget_status_query(lowered):
        extracted["period_hint"] = _period_hint(lowered)
        extracted["category_hint"] = _expense_category_hint(lowered)
        return RouteDecisionResult(
            input_text=stripped,
            domain="budget_status",
            command="budget-status",
            confidence=0.88,
            reason="Detected budget or spending status query.",
            routing_source="heuristic",
            extracted_fields=extracted,
        )

    if _is_habit_status_query(lowered):
        extracted["period_hint"] = _period_hint(lowered)
        return RouteDecisionResult(
            input_text=stripped,
            domain="habit_status",
            command="habit-status",
            confidence=0.88,
            reason="Detected habit status query.",
            routing_source="heuristic",
            extracted_fields=extracted,
        )

    return None


def _is_macro_target_input(lowered: str) -> bool:
    return (
        any(token in lowered for token in ["meta", "objetivo", "target"])
        and any(
            token in lowered
            for token in ["proteína", "proteina", "carbs", "carbohidratos", "grasa", "grasas", "calorías", "calorias", "kcal"]
        )
    )


def _extract_macro_target_hints(text: str) -> dict[str, object]:
    extracted: dict[str, object] = {}
    protein = PROTEIN_TARGET_PATTERN.search(text)
    carbs = CARBS_TARGET_PATTERN.search(text)
    fat = FAT_TARGET_PATTERN.search(text)
    calories = CALORIES_TARGET_PATTERN.search(text)
    if protein:
        extracted["protein_g_hint"] = float(protein.group("value"))
    if carbs:
        extracted["carbs_g_hint"] = float(carbs.group("value"))
    if fat:
        extracted["fat_g_hint"] = float(fat.group("value"))
    if calories:
        extracted["calories_hint"] = float(calories.group("value"))
    return extracted


def _is_budget_target_input(lowered: str) -> bool:
    return (
        any(token in lowered for token in ["máximo", "maximo", "mi presupuesto", "presupuesto de", "quiero gastar", "gastar máximo", "gastar maximo"])
        and any(token in lowered for token in ["semana", "semanal", "mes", "mensual", "día", "dia", "diario"])
    )


def _extract_budget_target_hints(text: str, lowered: str) -> dict[str, object]:
    extracted: dict[str, object] = {}
    amount = AMOUNT_PATTERN.search(text)
    if amount:
        extracted["amount_hint"] = float(amount.group("amount"))
    extracted["period_hint"] = _period_hint(lowered)
    extracted["category_hint"] = _expense_category_hint(lowered)
    extracted["currency_hint"] = "MXN"
    return extracted


def _is_habit_target_input(lowered: str) -> bool:
    return (
        ("hábito" in lowered or "habito" in lowered or any(name in lowered for name in ["leer", "meditar", "tomar agua", "caminar", "dormir"]))
        and any(token in lowered for token in ["vez", "veces", "al día", "al dia", "por día", "por dia", "por semana", "semanal", "diario"])
        and any(token in lowered for token in ["será", "sera", "meta", "objetivo", "quiero"])
    )


def _extract_habit_target_hints(text: str, lowered: str) -> dict[str, object]:
    extracted: dict[str, object] = {}
    count_match = COUNT_PATTERN.search(text)
    if count_match:
        extracted["target_count_hint"] = int(count_match.group("count"))
    extracted["period_hint"] = _period_hint(lowered)
    habit_name = next((name for phrase, name in HABIT_HINTS.items() if phrase in lowered), None)
    if habit_name is None:
        if "leer" in lowered:
            habit_name = "leer"
        elif "meditar" in lowered or "medite" in lowered or "medité" in lowered:
            habit_name = "meditar"
        elif "tomar agua" in lowered or "agua" in lowered:
            habit_name = "tomar agua"
    if habit_name:
        extracted["habit_name_hint"] = habit_name
    return extracted


def _is_macro_status_query(lowered: str) -> bool:
    return (
        any(token in lowered for token in ["cuánto", "cuanto", "cómo voy", "como voy", "qué me falta", "que me falta", "me falta", "resta"])
        and any(token in lowered for token in ["proteína", "proteina", "carbs", "carbohidratos", "grasas", "grasa", "macros", "calorías", "calorias"])
    )


def _macro_metric_hint(lowered: str) -> str | None:
    if "proteína" in lowered or "proteina" in lowered:
        return "protein_g"
    if "carbs" in lowered or "carbohidratos" in lowered:
        return "carbs_g"
    if "grasas" in lowered or "grasa" in lowered:
        return "fat_g"
    if "calorías" in lowered or "calorias" in lowered:
        return "calories"
    return None


def _is_budget_status_query(lowered: str) -> bool:
    return (
        any(token in lowered for token in ["cuánto gasté", "cuanto gaste", "cómo voy de presupuesto", "como voy de presupuesto", "presupuesto", "gasto"])
        and any(token in lowered for token in ["hoy", "semana", "mes", "semanal", "mensual", "diario"])
    )


def _is_habit_status_query(lowered: str) -> bool:
    return (
        any(token in lowered for token in ["qué hábitos", "que habitos", "qué hábitos me faltan", "que habitos me faltan", "hábitos", "habitos", "me falta"])
        and any(token in lowered for token in ["hoy", "semana", "mes", "diario", "semanal", "mensual"])
    )


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


def _period_hint(lowered: str) -> str:
    if any(token in lowered for token in ["semana", "semanal"]):
        return "weekly"
    if any(token in lowered for token in ["mes", "mensual"]):
        return "monthly"
    return "daily"
