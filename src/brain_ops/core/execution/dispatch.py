from __future__ import annotations

from brain_ops.config import VaultConfig
from brain_ops.core.execution.runtime import (
    IntentExecutionOutcome,
    build_execution_runtime,
)
from brain_ops.intents import IntentModel
from brain_ops.services.intent_execution_knowledge import execute_knowledge_intent
from brain_ops.services.intent_execution_logging import execute_logging_intent
from brain_ops.services.intent_execution_personal import execute_personal_intent


def execute_intent(config: VaultConfig, intent: IntentModel, *, dry_run: bool = False) -> IntentExecutionOutcome:
    runtime = build_execution_runtime(config, dry_run=dry_run)
    db_path = runtime.db_path
    vault = runtime.vault
    logging_outcome = execute_logging_intent(db_path, intent, dry_run=dry_run)
    if logging_outcome is not None:
        return logging_outcome
    personal_outcome = execute_personal_intent(db_path, intent, dry_run=dry_run)
    if personal_outcome is not None:
        return personal_outcome
    knowledge_outcome = execute_knowledge_intent(vault, intent)
    if knowledge_outcome is not None:
        return knowledge_outcome

    raise RuntimeError(f"Unsupported intent execution path: {intent.intent}")

