from __future__ import annotations

from brain_ops.ai import llm_parse_intent
from brain_ops.config import VaultConfig
from brain_ops.errors import AIProviderError
from brain_ops.interfaces.conversation.parsing import (
    build_compound_parse_result,
    should_preserve_single_parse,
)
from brain_ops.interfaces.conversation.routing import intent_to_route_decision
from brain_ops.interfaces.conversation.routing_input import route_input as route_input_heuristic
from brain_ops.interfaces.conversation.splitting import split_compound_input
from brain_ops.intents import (
    DailyLogIntent,
    IntentModel,
    ParseFailure,
)
from brain_ops.models import RouteDecisionResult
from brain_ops.services.intent_parser_diet import build_diet_intent_from_decision
from brain_ops.services.intent_parser_knowledge import build_knowledge_intent_from_decision
from brain_ops.services.intent_parser_logging import build_logging_intent_from_decision
from brain_ops.services.intent_parser_personal import build_personal_intent_from_decision


def parse_intent(
    config: VaultConfig,
    text: str,
    *,
    use_llm: bool | None = None,
) -> IntentModel | ParseFailure:
    heuristic_decision = route_input_heuristic(text)
    heuristic_intent = _build_intent_from_decision(text, heuristic_decision, config)
    allow_llm = config.ai.enable_llm_routing if use_llm is None else use_llm

    if _should_accept_heuristic(heuristic_decision, heuristic_intent):
        return heuristic_intent

    if allow_llm:
        try:
            llm_intent = llm_parse_intent(config.ai, text)
            if heuristic_intent is None:
                return llm_intent
            if llm_intent.command == heuristic_intent.command:
                llm_intent.routing_source = "hybrid"
                return llm_intent
            if llm_intent.confidence >= heuristic_intent.confidence + 0.15:
                llm_intent.routing_source = "hybrid"
                return llm_intent
            heuristic_intent.routing_source = "hybrid"
            return heuristic_intent
        except AIProviderError:
            pass

    if heuristic_intent is not None:
        return heuristic_intent
    return ParseFailure(
        input_text=text,
        reason="Could not parse a valid intent from the input.",
        follow_up=f"Suggested next command: {heuristic_decision.command}",
    )


def parse_intents(
    config: VaultConfig,
    text: str,
    *,
    use_llm: bool | None = None,
) -> list[IntentModel] | ParseFailure:
    initial = route_input_heuristic(text)
    if should_preserve_single_parse(initial.command):
        parsed = parse_intent(config, text, use_llm=use_llm)
        return parsed if isinstance(parsed, ParseFailure) else [parsed]

    clauses = split_compound_input(text)
    if len(clauses) <= 1:
        parsed = parse_intent(config, text, use_llm=use_llm)
        return parsed if isinstance(parsed, ParseFailure) else [parsed]

    return build_compound_parse_result(
        clauses,
        lambda clause: parse_intent(config, clause, use_llm=use_llm),
    )


def _should_accept_heuristic(decision: RouteDecisionResult, intent: IntentModel | None) -> bool:
    if intent is None:
        return False
    if should_preserve_single_parse(decision.command):
        return True
    return decision.confidence >= 0.86


def _build_intent_from_decision(
    text: str,
    decision: RouteDecisionResult,
    config: VaultConfig,
) -> IntentModel | None:
    logging_intent = build_logging_intent_from_decision(text, decision)
    if logging_intent is not None:
        return logging_intent
    personal_intent = build_personal_intent_from_decision(text, decision)
    if personal_intent is not None:
        return personal_intent
    diet_intent = build_diet_intent_from_decision(
        text,
        decision,
        database_path=config.database_path,
    )
    if diet_intent is not None:
        return diet_intent
    knowledge_intent = build_knowledge_intent_from_decision(text, decision)
    if knowledge_intent is not None:
        return knowledge_intent
    if decision.command == "daily-log":
        return DailyLogIntent(
            text=text,
            log_domain=decision.domain,
            confidence=decision.confidence,
            routing_source=decision.routing_source,
        )
    return None

