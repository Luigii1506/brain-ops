from __future__ import annotations

import re

from brain_ops.ai import llm_route_input
from brain_ops.config import VaultConfig
from brain_ops.errors import AIProviderError
from brain_ops.models import HandleInputResult, HandleInputSubResult, OperationRecord, RouteDecisionResult
from brain_ops.services.body_metrics_service import log_body_metrics
from brain_ops.services.capture_service import capture_text
from brain_ops.services.daily_log_service import log_daily_event
from brain_ops.services.expenses_service import log_expense
from brain_ops.services.fitness_service import log_workout
from brain_ops.services.life_ops_service import habit_checkin, log_supplement
from brain_ops.services.nutrition_service import log_meal
from brain_ops.services.router_service import route_input
from brain_ops.vault import Vault

AMOUNT_PATTERN = re.compile(r"(?P<amount>\d+(?:\.\d+)?)")
SUPPLEMENT_AMOUNT_PATTERN = re.compile(
    r"(?P<amount>\d+(?:\.\d+)?)\s*(?P<unit>mg|g|caps|c[aá]psulas?|ml|tabletas?)\b",
    re.IGNORECASE,
)
WEIGHT_METRIC_PATTERN = re.compile(r"(?P<value>\d+(?:\.\d+)?)\s*kg\b", re.IGNORECASE)
BODY_FAT_PATTERN = re.compile(r"(?P<value>\d+(?:\.\d+)?)\s*%", re.IGNORECASE)
WAIST_PATTERN = re.compile(r"(?P<value>\d+(?:\.\d+)?)\s*cm\b", re.IGNORECASE)
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
PAYMENT_METHOD_SUFFIX_PATTERN = re.compile(
    r"\b(?:con|usando)\s+(?:tarjeta|efectivo|d[ée]bito|debito|cr[ée]dito|credito|apple pay)\b.*$",
    re.IGNORECASE,
)
EXPENSE_MERCHANT_PATTERN = re.compile(
    r"\b(?:en|de|a|para)\s+([A-Za-zÁÉÍÓÚÑáéíóú0-9][A-Za-zÁÉÍÓÚÑáéíóú0-9& ._-]+)$"
)
COMPOUND_SPLIT_PATTERN = re.compile(r"\s*(?:[.;]\s+|\s+y luego\s+|\s+despu[eé]s\s+|\s+adem[aá]s\s+)\s*", re.IGNORECASE)
ACTION_STARTERS = [
    "pagué",
    "pague",
    "gasté",
    "gaste",
    "compré",
    "compre",
    "tomé",
    "tome",
    "aprendí",
    "aprendi",
    "hice",
    "pesé",
    "pese",
    "medí",
    "medi",
    "desayuné",
    "desayune",
    "comí",
    "comi",
    "cené",
    "cene",
    "almorcé",
    "almorce",
    "leí",
    "lei",
]
ACTION_CONNECTOR_PATTERN = re.compile(
    r"\s+(?:y|tamb[ié]n|adem[aá]s)\s+(?=(?:hoy\s+|me\s+)?(?:"
    + "|".join(re.escape(starter) for starter in ACTION_STARTERS)
    + r")\b)",
    re.IGNORECASE,
)


def handle_input(
    config: VaultConfig,
    input_text: str,
    *,
    dry_run: bool = False,
    use_llm: bool | None = None,
) -> HandleInputResult:
    compound_result = _handle_compound_input(config, input_text, dry_run=dry_run, use_llm=use_llm)
    if compound_result is not None:
        return compound_result

    decision = route_input(input_text)
    db_path = config.database_path
    operations: list[OperationRecord] = []
    vault = Vault(config=config, dry_run=dry_run)
    use_llm = config.ai.enable_llm_routing if use_llm is None else use_llm

    result = _try_execute_from_decision(config, vault, db_path, input_text, decision, dry_run=dry_run)
    if result is not None:
        return result

    if use_llm:
        try:
            llm_decision = llm_route_input(config.ai, input_text)
            llm_result = _try_execute_from_decision(config, vault, db_path, input_text, llm_decision, dry_run=dry_run)
            if llm_result is not None:
                llm_result.reason = f"{llm_result.reason} Used Ollama-assisted routing."
                return llm_result
            decision = llm_decision
        except AIProviderError:
            pass

    return HandleInputResult(
        input_text=input_text,
        decision=decision,
        executed=False,
        operations=operations,
        executed_command=None,
        target_domain=decision.domain,
        routing_source=decision.routing_source,
        extracted_fields=decision.extracted_fields,
        needs_follow_up=True,
        follow_up=f"Suggested next command: {decision.command}",
        assistant_message="Necesito una entrada más estructurada para ejecutar una acción segura.",
        reason="Routed input but did not execute because more explicit structure is needed.",
    )


def _handle_compound_input(
    config: VaultConfig,
    input_text: str,
    *,
    dry_run: bool,
    use_llm: bool | None,
) -> HandleInputResult | None:
    clauses = _split_compound_input(input_text)
    if len(clauses) < 2:
        return None

    clause_results: list[HandleInputResult] = []
    for clause in clauses:
        result = _handle_single_input(config, clause, dry_run=dry_run, use_llm=use_llm)
        clause_results.append(result)

    executed_results = [result for result in clause_results if result.executed]
    if len(executed_results) < 2:
        return None

    all_operations: list[OperationRecord] = []
    sub_results: list[HandleInputSubResult] = []
    for result in clause_results:
        all_operations.extend(result.operations)
        sub_results.append(
            HandleInputSubResult(
                input_text=result.input_text,
                executed=result.executed,
                executed_command=result.executed_command,
                target_domain=result.target_domain,
                routing_source=result.routing_source,
                extracted_fields=result.extracted_fields,
                assistant_message=result.assistant_message,
                reason=result.reason,
            )
        )

    summary_commands = ", ".join(
        result.executed_command or result.decision.command for result in executed_results
    )
    return HandleInputResult(
        input_text=input_text,
        decision=RouteDecisionResult(
            input_text=input_text,
            domain="multi",
            command="multi-action",
            confidence=0.9,
            reason="Detected multiple actionable clauses in one input.",
            routing_source="heuristic",
            extracted_fields={"clause_count": len(clauses)},
        ),
        executed=True,
        operations=all_operations,
        executed_command="multi-action",
        target_domain="multi",
        routing_source="heuristic",
        extracted_fields={"clause_count": len(clauses), "executed_count": len(executed_results)},
        needs_follow_up=False,
        assistant_message=f"Procesé varias acciones en una sola entrada: {summary_commands}.",
        sub_results=sub_results,
        reason="Executed multiple safe actions from one mixed input.",
    )


def _handle_single_input(
    config: VaultConfig,
    input_text: str,
    *,
    dry_run: bool,
    use_llm: bool | None,
) -> HandleInputResult:
    decision = route_input(input_text)
    db_path = config.database_path
    operations: list[OperationRecord] = []
    vault = Vault(config=config, dry_run=dry_run)
    use_llm = config.ai.enable_llm_routing if use_llm is None else use_llm

    result = _try_execute_from_decision(config, vault, db_path, input_text, decision, dry_run=dry_run)
    if result is not None:
        return result

    if use_llm:
        try:
            llm_decision = llm_route_input(config.ai, input_text)
            llm_result = _try_execute_from_decision(config, vault, db_path, input_text, llm_decision, dry_run=dry_run)
            if llm_result is not None:
                llm_result.reason = f"{llm_result.reason} Used Ollama-assisted routing."
                return llm_result
            decision = llm_decision
        except AIProviderError:
            pass

    return HandleInputResult(
        input_text=input_text,
        decision=decision,
        executed=False,
        operations=operations,
        executed_command=None,
        target_domain=decision.domain,
        routing_source=decision.routing_source,
        extracted_fields=decision.extracted_fields,
        needs_follow_up=True,
        follow_up=f"Suggested next command: {decision.command}",
        assistant_message="Necesito una entrada más estructurada para ejecutar una acción segura.",
        reason="Routed input but did not execute because more explicit structure is needed.",
    )


def _try_execute_from_decision(
    config: VaultConfig,
    vault: Vault,
    db_path,
    input_text: str,
    decision: RouteDecisionResult,
    *,
    dry_run: bool,
) -> HandleInputResult | None:
    if decision.command == "log-expense":
        parsed = _parse_expense_input(input_text, decision)
        if parsed is not None:
            result = log_expense(db_path, dry_run=dry_run, **parsed)
            return HandleInputResult(
                input_text=input_text,
                decision=decision,
                executed=True,
                operations=result.operations,
                executed_command=decision.command,
                target_domain=decision.domain,
                routing_source=decision.routing_source,
                extracted_fields=_merge_extracted_fields(
                    decision.extracted_fields,
                    {
                        "amount": parsed["amount"],
                        "category": parsed.get("category"),
                        "merchant": parsed.get("merchant"),
                        "currency": parsed["currency"],
                    },
                ),
                needs_follow_up=False,
                assistant_message=f"Registré un gasto de {parsed['amount']:.2f} {parsed['currency']}.",
                reason="Executed expense logging from routed input.",
            )

    if decision.command == "log-meal":
        normalized = _normalize_meal_input(input_text)
        try:
            result = log_meal(
                db_path,
                normalized,
                meal_type=decision.extracted_fields.get("meal_type_hint") if isinstance(decision.extracted_fields.get("meal_type_hint"), str) else None,
                dry_run=dry_run,
            )
        except Exception:
            result = None
        if result is not None:
            return HandleInputResult(
                input_text=input_text,
                decision=decision,
                executed=True,
                operations=result.operations,
                executed_command=decision.command,
                target_domain=decision.domain,
                routing_source=decision.routing_source,
                extracted_fields=_merge_extracted_fields(
                    decision.extracted_fields,
                    {
                        "meal_type": decision.extracted_fields.get("meal_type_hint"),
                        "item_count": len(result.items),
                        "normalized_meal_text": normalized,
                    },
                ),
                needs_follow_up=False,
                assistant_message=f"Registré una comida con {len(result.items)} item(s).",
                reason="Executed meal logging from routed input.",
            )

    if decision.command == "log-supplement":
        parsed = _parse_supplement_input(input_text)
        if parsed is not None:
            result = log_supplement(db_path, dry_run=dry_run, **parsed)
            return HandleInputResult(
                input_text=input_text,
                decision=decision,
                executed=True,
                operations=result.operations,
                executed_command=decision.command,
                target_domain=decision.domain,
                routing_source=decision.routing_source,
                extracted_fields=_merge_extracted_fields(
                    decision.extracted_fields,
                    {
                        "supplement_name": parsed["supplement_name"],
                        "amount": parsed.get("amount"),
                        "unit": parsed.get("unit"),
                    },
                ),
                needs_follow_up=False,
                assistant_message=f"Registré el suplemento {parsed['supplement_name']}.",
                reason="Executed supplement logging from routed input.",
            )

    if decision.command == "habit-checkin":
        parsed = _parse_habit_input(input_text)
        if parsed is not None:
            result = habit_checkin(db_path, dry_run=dry_run, **parsed)
            return HandleInputResult(
                input_text=input_text,
                decision=decision,
                executed=True,
                operations=result.operations,
                executed_command=decision.command,
                target_domain=decision.domain,
                routing_source=decision.routing_source,
                extracted_fields=_merge_extracted_fields(
                    decision.extracted_fields,
                    {
                        "habit_name": parsed["habit_name"],
                        "status": parsed["status"],
                    },
                ),
                needs_follow_up=False,
                assistant_message=f"Registré el hábito {parsed['habit_name']} como {parsed['status']}.",
                reason="Executed habit check-in from routed input.",
            )

    if decision.command == "log-body-metrics":
        parsed = _parse_body_metrics_input(input_text, decision)
        if parsed is not None:
            result = log_body_metrics(db_path, dry_run=dry_run, **parsed)
            return HandleInputResult(
                input_text=input_text,
                decision=decision,
                executed=True,
                operations=result.operations,
                executed_command=decision.command,
                target_domain=decision.domain,
                routing_source=decision.routing_source,
                extracted_fields=_merge_extracted_fields(
                    decision.extracted_fields,
                    {
                        "weight_kg": parsed.get("weight_kg"),
                        "body_fat_pct": parsed.get("body_fat_pct"),
                        "waist_cm": parsed.get("waist_cm"),
                    },
                ),
                needs_follow_up=False,
                assistant_message="Registré tus métricas corporales.",
                reason="Executed body metrics logging from routed input.",
            )

    if decision.command == "log-workout" and re.search(r"\b\d+x\d+(?:@\d+(?:\.\d+)?kg|@bodyweight)?\b", input_text, re.IGNORECASE):
        normalized = _normalize_workout_input(input_text)
        result = log_workout(db_path, normalized, dry_run=dry_run)
        return HandleInputResult(
            input_text=input_text,
            decision=decision,
            executed=True,
            operations=result.operations,
            executed_command=decision.command,
            target_domain=decision.domain,
            routing_source=decision.routing_source,
            extracted_fields=_merge_extracted_fields(
                decision.extracted_fields,
                {"exercise_count": len(result.exercises), "normalized_workout_text": normalized},
            ),
            needs_follow_up=False,
            assistant_message=f"Registré un workout con {len(result.exercises)} ejercicio(s).",
            reason="Executed workout logging from routed input.",
        )

    if decision.command.startswith("capture --type "):
        note_type = decision.command.split()[-1]
        result = capture_text(vault, text=input_text, force_type=note_type, tags=[])
        return HandleInputResult(
            input_text=input_text,
            decision=decision,
            executed=True,
            operations=[result.operation],
            executed_command=decision.command,
            target_domain=decision.domain,
            routing_source=decision.routing_source,
            extracted_fields=decision.extracted_fields,
            needs_follow_up=False,
            assistant_message=f"Capturé una nota de tipo {note_type}.",
            reason="Executed note capture from routed input.",
        )

    if decision.command == "daily-log":
        result = log_daily_event(db_path, input_text, domain=decision.domain, dry_run=dry_run)
        return HandleInputResult(
            input_text=input_text,
            decision=decision,
            executed=True,
            operations=result.operations,
            executed_command=decision.command,
            target_domain=decision.domain,
            routing_source=decision.routing_source,
            extracted_fields=decision.extracted_fields,
            needs_follow_up=False,
            assistant_message=f"Guardé el evento diario en el dominio {decision.domain}.",
            reason="Executed generic daily log from routed input.",
        )

    return None


def _split_compound_input(text: str) -> list[str]:
    normalized = ACTION_CONNECTOR_PATTERN.sub(" ; ", text.strip())
    clauses = [part.strip(" ,") for part in COMPOUND_SPLIT_PATTERN.split(normalized) if part.strip(" ,")]
    return clauses if len(clauses) > 1 else [text.strip()]


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
    name_hint = None
    name = next((keyword for keyword in SUPPLEMENT_KEYWORDS if keyword in lowered), None)
    if not name:
        return None
    name_hint = name
    amount = None
    unit = None
    match = SUPPLEMENT_AMOUNT_PATTERN.search(lowered)
    if match:
        amount = float(match.group("amount"))
        unit = match.group("unit")
    return {
        "supplement_name": _format_supplement_name(name_hint),
        "amount": amount,
        "unit": unit,
        "note": text.strip(),
    }


def _parse_habit_input(text: str) -> dict[str, object] | None:
    lowered = text.lower()
    for phrase, habit_name in HABIT_MAP.items():
        if phrase in lowered:
            return {"habit_name": habit_name, "status": _infer_habit_status(lowered), "note": text.strip()}
    return None


def _parse_body_metrics_input(text: str, decision: RouteDecisionResult) -> dict[str, object] | None:
    lowered = text.lower()
    weight_kg = decision.extracted_fields.get("weight_kg_hint")
    body_fat_pct = decision.extracted_fields.get("body_fat_pct_hint")
    waist_cm = decision.extracted_fields.get("waist_cm_hint")

    if weight_kg is None and any(token in lowered for token in ["peso", "pese", "pesé"]) and "peso muerto" not in lowered:
        weight_match = WEIGHT_METRIC_PATTERN.search(text)
        if weight_match:
            weight_kg = float(weight_match.group("value"))

    if body_fat_pct is None and any(token in lowered for token in ["grasa corporal", "body fat", "grasa"]):
        body_fat_match = BODY_FAT_PATTERN.search(text)
        if body_fat_match:
            body_fat_pct = float(body_fat_match.group("value"))

    if waist_cm is None and "cintura" in lowered:
        waist_match = WAIST_PATTERN.search(text)
        if waist_match:
            waist_cm = float(waist_match.group("value"))

    if all(value is None for value in [weight_kg, body_fat_pct, waist_cm]):
        return None

    return {
        "weight_kg": float(weight_kg) if isinstance(weight_kg, (int, float)) else None,
        "body_fat_pct": float(body_fat_pct) if isinstance(body_fat_pct, (int, float)) else None,
        "waist_cm": float(waist_cm) if isinstance(waist_cm, (int, float)) else None,
        "note": text.strip(),
    }


def _normalize_workout_input(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"^(hoy\s+)?(hice|entren[eé])\s+", "", cleaned, flags=re.IGNORECASE)
    return cleaned


def _format_supplement_name(name: str) -> str:
    return " ".join(part.capitalize() for part in name.replace("-", " ").split())


def _infer_habit_status(lowered: str) -> str:
    if any(token in lowered for token in ["no ", "no hice", "no pude", "falto", "faltó"]):
        return "skipped"
    if any(token in lowered for token in ["parcial", "medio", "un poco"]):
        return "partial"
    return "done"


def _merge_extracted_fields(base: dict[str, object], extra: dict[str, object]) -> dict[str, object]:
    merged = dict(base)
    for key, value in extra.items():
        if value is not None:
            merged[key] = value
    return merged


def _parse_expense_merchant(text: str) -> str | None:
    cleaned = PAYMENT_METHOD_SUFFIX_PATTERN.sub("", text).strip(" .")
    merchant_match = EXPENSE_MERCHANT_PATTERN.search(cleaned)
    if not merchant_match:
        return None
    merchant = merchant_match.group(1).strip(" .")
    merchant = re.sub(r"\b(?:gasolina|farmacia|comida|caf[eé]|cafe|uber|spotify|netflix)\b\s*$", "", merchant, flags=re.IGNORECASE).strip(" .")
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
