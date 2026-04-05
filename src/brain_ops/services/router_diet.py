from __future__ import annotations

from brain_ops.models import RouteDecisionResult


def build_diet_route_decision(text: str) -> RouteDecisionResult | None:
    stripped = text.strip()
    lowered = stripped.lower()
    extracted: dict[str, object] = {}

    if _is_active_diet_query(lowered):
        return RouteDecisionResult(
            input_text=stripped,
            domain="diet",
            command="active-diet",
            confidence=0.94,
            reason="Detected active diet query.",
            routing_source="heuristic",
            extracted_fields=extracted,
        )

    if _is_create_diet_input(lowered):
        return RouteDecisionResult(
            input_text=stripped,
            domain="diet",
            command="create-diet-plan",
            confidence=0.89,
            reason="Detected natural-language diet creation request.",
            routing_source="heuristic",
            extracted_fields=extracted,
        )

    if _is_update_diet_meal_input(lowered):
        extracted["update_mode_hint"] = _diet_update_mode_hint(lowered)
        extracted["meal_focus_hint"] = _diet_meal_focus_hint(lowered)
        return RouteDecisionResult(
            input_text=stripped,
            domain="diet",
            command="update-diet-meal",
            confidence=0.88,
            reason="Detected active diet meal update request.",
            routing_source="heuristic",
            extracted_fields=extracted,
        )

    if _is_set_active_diet_input(lowered):
        return RouteDecisionResult(
            input_text=stripped,
            domain="diet",
            command="set-active-diet",
            confidence=0.9,
            reason="Detected active diet change request.",
            routing_source="heuristic",
            extracted_fields=extracted,
        )

    if _is_diet_status_query(lowered):
        extracted["meal_focus_hint"] = _diet_meal_focus_hint(lowered)
        return RouteDecisionResult(
            input_text=stripped,
            domain="diet",
            command="diet-status",
            confidence=0.94,
            reason="Detected active diet progress query.",
            routing_source="heuristic",
            extracted_fields=extracted,
        )

    return None


def _is_diet_status_query(lowered: str) -> bool:
    meal_terms = ["desayuno", "comida", "cena", "breakfast", "lunch", "dinner"]
    progress_terms = [
        "falta",
        "progreso",
        "cómo voy",
        "como voy",
        "qué me falta",
        "que me falta",
        "cumplí",
        "cumpli",
        "ya cumplí",
        "ya cumpli",
    ]
    if "dieta" in lowered and any(token in lowered for token in progress_terms + ["comida me falta"]):
        return True
    return any(term in lowered for term in meal_terms) and any(term in lowered for term in progress_terms)


def _is_active_diet_query(lowered: str) -> bool:
    return "dieta" in lowered and any(
        token in lowered
        for token in ["dieta activa", "qué dieta", "que dieta", "cuál es mi dieta", "cual es mi dieta"]
    )


def _is_set_active_diet_input(lowered: str) -> bool:
    return "dieta" in lowered and any(
        token in lowered
        for token in ["activa", "activar", "cambia", "cambiar", "usa la dieta", "usar la dieta", "pon la dieta"]
    )


def _is_create_diet_input(lowered: str) -> bool:
    return "dieta" in lowered and any(
        token in lowered for token in ["mi dieta ahora será", "mi dieta ahora sera", "mi dieta será", "mi dieta sera"]
    ) and any(token in lowered for token in ["desayuno", "comida", "cena"])


def _is_update_diet_meal_input(lowered: str) -> bool:
    return (
        "dieta" in lowered
        and any(token in lowered for token in ["desayuno", "comida", "cena"])
        and any(token in lowered for token in ["cambia", "cambiar", "agrega", "añade", "anade"])
    )


def _diet_meal_focus_hint(lowered: str) -> str | None:
    if "comidas" in lowered:
        return "all_meals"
    for token in ["desayuno", "breakfast", "comida", "lunch", "cena", "dinner"]:
        if token in lowered:
            return token
    if "meal" in lowered:
        return "all_meals"
    return None


def _diet_update_mode_hint(lowered: str) -> str:
    if any(token in lowered for token in ["agrega", "añade", "anade"]):
        return "append"
    return "replace"
