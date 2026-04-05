from __future__ import annotations

from collections.abc import Callable

from brain_ops.intents import DailyLogIntent, IntentModel, ParseFailure

PROTECTED_COMPOUND_COMMANDS = {
    "create-diet-plan",
    "update-diet-meal",
    "set-active-diet",
}


def should_preserve_single_parse(command: str) -> bool:
    return command in PROTECTED_COMPOUND_COMMANDS


def build_compound_parse_result(
    clauses: list[str],
    parse_clause: Callable[[str], IntentModel | ParseFailure],
) -> list[IntentModel]:
    intents: list[IntentModel] = []
    for clause in clauses:
        parsed = parse_clause(clause)
        if isinstance(parsed, ParseFailure):
            intents.append(DailyLogIntent(text=clause, routing_source="fallback", confidence=0.3))
            continue
        intents.append(parsed)
    return intents
