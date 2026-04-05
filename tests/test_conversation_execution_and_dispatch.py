from __future__ import annotations

import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from brain_ops.config import AIConfig, VaultConfig
from brain_ops.core.execution.runtime import IntentExecutionOutcome
from brain_ops.intents import ActiveDietIntent, CaptureNoteIntent, LogExpenseIntent
from brain_ops.interfaces.conversation.execution import (
    execute_multi_intent_result,
    execute_single_intent_result,
)
from brain_ops.interfaces.conversation.follow_up_state import PendingFollowUp
from brain_ops.models import OperationRecord, OperationStatus
from brain_ops.core.execution.dispatch import execute_intent
from brain_ops.storage.db import initialize_database


class ConversationExecutionAndDispatchTestCase(TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.config = VaultConfig(
            vault_path=root / "vault",
            data_dir=root / "data",
            database_path=root / "data" / "brain_ops.db",
            ai=AIConfig(enable_llm_routing=False),
        )
        self.config.vault_path.mkdir(parents=True, exist_ok=True)
        initialize_database(self.config.database_path)
        self.operation = OperationRecord(
            action="insert",
            path=self.config.database_path,
            detail="ok",
            status=OperationStatus.CREATED,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_execute_single_intent_result_builds_result_and_follow_up_for_active_diet(self) -> None:
        intent = ActiveDietIntent()
        outcome = IntentExecutionOutcome(
            payload=SimpleNamespace(name="Cut"),
            operations=[self.operation],
            normalized_fields={"active_diet_name": "Cut"},
            reason="Executed active diet query.",
        )
        pending = PendingFollowUp(
            followup_type="active_diet_options",
            question="Tu dieta activa es Cut. ¿Quieres resumen?",
            options=["resumen"],
            default_option="resumen",
            context={"diet_name": "Cut"},
        )

        with (
            patch("brain_ops.interfaces.conversation.execution.execute_intent", return_value=outcome) as execute_mock,
            patch("brain_ops.interfaces.conversation.execution.active_diet_pending_follow_up", return_value=pending) as pending_mock,
            patch("brain_ops.interfaces.conversation.execution.save_follow_up") as save_mock,
        ):
            result = execute_single_intent_result(
                self.config,
                "cuál es mi dieta activa",
                intent,
                dry_run=False,
                session_id="telegram-main",
            )

        self.assertTrue(result.executed)
        self.assertTrue(result.needs_follow_up)
        self.assertEqual(result.follow_up, pending.question)
        self.assertEqual(result.follow_up_options, ["resumen"])
        self.assertEqual(result.executed_command, "active-diet")
        execute_mock.assert_called_once_with(self.config, intent, dry_run=False)
        pending_mock.assert_called_once_with("Cut")
        save_mock.assert_called_once_with(self.config.database_path, "telegram-main", pending)

    def test_execute_multi_intent_result_aggregates_sub_results_and_operations(self) -> None:
        expense_intent = LogExpenseIntent(amount=250, category="food", merchant="Cafe")
        capture_intent = CaptureNoteIntent(force_type="knowledge", text="Idea sobre sistemas")
        outcomes = [
            IntentExecutionOutcome(
                payload=SimpleNamespace(),
                operations=[self.operation],
                normalized_fields={"amount": 250},
                reason="Executed expense intent.",
            ),
            IntentExecutionOutcome(
                payload=SimpleNamespace(),
                operations=[],
                normalized_fields={"force_type": "knowledge"},
                reason="Executed capture note intent.",
            ),
        ]

        with patch(
            "brain_ops.interfaces.conversation.execution.execute_intent",
            side_effect=outcomes,
        ) as execute_mock:
            result = execute_multi_intent_result(
                self.config,
                "Gasté 250 en cafe; Idea sobre sistemas",
                [expense_intent, capture_intent],
                dry_run=True,
            )

        self.assertTrue(result.executed)
        self.assertEqual(result.executed_command, "multi-action")
        self.assertEqual(result.normalized_fields["intents"], ["log_expense", "capture_note"])
        self.assertEqual(result.operations, [self.operation])
        self.assertEqual(len(result.sub_results), 2)
        self.assertEqual(result.sub_results[0].input_text, "log-expense")
        self.assertEqual(result.sub_results[1].input_text, "Idea sobre sistemas")
        self.assertIn("multi", result.target_domain)
        self.assertEqual(execute_mock.call_count, 2)

    def test_execute_intent_dispatch_prioritizes_logging_then_personal_then_knowledge(self) -> None:
        intent = LogExpenseIntent(amount=250, category="food", merchant="Cafe")
        logging_outcome = IntentExecutionOutcome(payload=SimpleNamespace(), operations=[self.operation], reason="logging")
        personal_outcome = IntentExecutionOutcome(payload=SimpleNamespace(), operations=[], reason="personal")
        knowledge_outcome = IntentExecutionOutcome(payload=SimpleNamespace(), operations=[], reason="knowledge")

        with (
            patch("brain_ops.core.execution.dispatch.execute_logging_intent", return_value=logging_outcome) as logging_mock,
            patch("brain_ops.core.execution.dispatch.execute_personal_intent", return_value=personal_outcome) as personal_mock,
            patch("brain_ops.core.execution.dispatch.execute_knowledge_intent", return_value=knowledge_outcome) as knowledge_mock,
        ):
            result = execute_intent(self.config, intent, dry_run=True)

        self.assertIs(result, logging_outcome)
        logging_mock.assert_called_once()
        personal_mock.assert_not_called()
        knowledge_mock.assert_not_called()

    def test_execute_intent_dispatch_falls_through_to_knowledge_and_raises_when_unsupported(self) -> None:
        capture_intent = CaptureNoteIntent(force_type="knowledge", text="Idea")
        knowledge_outcome = IntentExecutionOutcome(payload=SimpleNamespace(), operations=[], reason="knowledge")

        with (
            patch("brain_ops.core.execution.dispatch.execute_logging_intent", return_value=None),
            patch("brain_ops.core.execution.dispatch.execute_personal_intent", return_value=None),
            patch("brain_ops.core.execution.dispatch.execute_knowledge_intent", return_value=knowledge_outcome),
        ):
            result = execute_intent(self.config, capture_intent, dry_run=False)

        self.assertIs(result, knowledge_outcome)

        with (
            patch("brain_ops.core.execution.dispatch.execute_logging_intent", return_value=None),
            patch("brain_ops.core.execution.dispatch.execute_personal_intent", return_value=None),
            patch("brain_ops.core.execution.dispatch.execute_knowledge_intent", return_value=None),
        ):
            with self.assertRaises(RuntimeError):
                execute_intent(self.config, capture_intent, dry_run=False)


if __name__ == "__main__":
    import unittest

    unittest.main()
