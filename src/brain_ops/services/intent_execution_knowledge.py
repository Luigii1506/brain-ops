from __future__ import annotations

from brain_ops.core.execution import IntentExecutionOutcome, build_execution_outcome
from brain_ops.intents import CaptureNoteIntent, IntentModel
from brain_ops.services.capture_service import capture_text


def execute_knowledge_intent(
    vault: object,
    intent: IntentModel,
) -> IntentExecutionOutcome | None:
    match intent:
        case CaptureNoteIntent():
            result = capture_text(vault, text=intent.text, force_type=intent.force_type, tags=[])
            return build_execution_outcome(
                payload=result,
                operations=[result.operation],
                normalized_fields={"force_type": intent.force_type},
                reason="Executed capture note intent.",
            )
    return None
