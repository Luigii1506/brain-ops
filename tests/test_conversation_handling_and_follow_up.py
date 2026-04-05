from __future__ import annotations

import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from brain_ops.config import AIConfig, VaultConfig
from brain_ops.core.execution.runtime import IntentExecutionOutcome
from brain_ops.interfaces.conversation.follow_up_state import PendingFollowUp
from brain_ops.interfaces.conversation.handling import handle_input
from brain_ops.interfaces.conversation.intake import resolve_conversation_input
from brain_ops.intents import DailyLogIntent, LogExpenseIntent, ParseFailure
from brain_ops.models import HandleInputResult, OperationRecord, OperationStatus, RouteDecisionResult
from brain_ops.storage.db import initialize_database


class ConversationHandlingAndFollowUpTestCase(TestCase):
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

    def test_resolve_conversation_input_prefers_pending_follow_up_over_parsing(self) -> None:
        expected_result = SimpleNamespace(kind="follow_up")

        with (
            patch("brain_ops.interfaces.conversation.intake.resolve_follow_up", return_value=expected_result) as follow_up_mock,
            patch("brain_ops.interfaces.conversation.intake.parse_intents") as parse_mock,
        ):
            result = resolve_conversation_input(
                self.config,
                "sí",
                use_llm=None,
                session_id="telegram-main",
            )

        self.assertIs(result, expected_result)
        follow_up_mock.assert_called_once_with(self.config, "telegram-main", "sí")
        parse_mock.assert_not_called()

    def test_resolve_conversation_input_falls_back_to_parse_intents(self) -> None:
        parsed = [LogExpenseIntent(amount=250, category="food", merchant="Cafe")]

        with (
            patch("brain_ops.interfaces.conversation.intake.resolve_follow_up", return_value=None) as follow_up_mock,
            patch("brain_ops.interfaces.conversation.intake.parse_intents", return_value=parsed) as parse_mock,
        ):
            result = resolve_conversation_input(
                self.config,
                "Gasté 250 en cafe",
                use_llm=False,
                session_id="telegram-main",
            )

        self.assertIs(result, parsed)
        follow_up_mock.assert_called_once()
        parse_mock.assert_called_once_with(self.config, "Gasté 250 en cafe", use_llm=False)

    def test_handle_input_returns_existing_follow_up_result_without_dispatch(self) -> None:
        pending_result = HandleInputResult(
            input_text="sí",
            decision=RouteDecisionResult(
                input_text="sí",
                domain="follow_up",
                command="resolve-follow-up",
                confidence=1.0,
                reason="Resolved pending follow-up.",
                routing_source="follow_up",
            ),
            executed=True,
            executed_command="resolve-follow-up",
            target_domain="follow_up",
            routing_source="follow_up",
            confidence=1.0,
            extracted_fields={},
            normalized_fields={},
            needs_follow_up=False,
            assistant_message="ok",
            reason="Resolved pending follow-up.",
        )

        with (
            patch("brain_ops.interfaces.conversation.handling.resolve_conversation_input", return_value=pending_result) as intake_mock,
            patch("brain_ops.interfaces.conversation.handling.dispatch_parsed_input") as dispatch_mock,
        ):
            result = handle_input(
                self.config,
                "sí",
                dry_run=False,
                use_llm=None,
                session_id="telegram-main",
            )

        self.assertIs(result, pending_result)
        intake_mock.assert_called_once()
        dispatch_mock.assert_not_called()

    def test_handle_input_dispatches_parsed_input_and_builds_failure_result(self) -> None:
        failure = ParseFailure(input_text="??", reason="bad input", follow_up="try again")

        with patch(
            "brain_ops.interfaces.conversation.handling.resolve_conversation_input",
            return_value=failure,
        ):
            result = handle_input(self.config, "??", dry_run=True)

        self.assertFalse(result.executed)
        self.assertTrue(result.needs_follow_up)
        self.assertEqual(result.follow_up, "try again")

    def test_follow_up_resolution_handles_default_cancel_and_unresolved_paths(self) -> None:
        pending = PendingFollowUp(
            followup_type="active_diet_options",
            question="Tu dieta activa es Cut. ¿Quieres resumen, objetivos o recomendaciones?",
            options=["resumen", "objetivos", "recomendaciones"],
            default_option="resumen",
            context={"diet_name": "Cut"},
        )

        with (
            patch("brain_ops.interfaces.conversation.follow_up_input.load_follow_up", return_value=pending),
            patch("brain_ops.interfaces.conversation.follow_up_input.clear_follow_up") as clear_mock,
            patch(
                "brain_ops.interfaces.conversation.follow_up_input.execute_intent",
                return_value=IntentExecutionOutcome(
                    payload=SimpleNamespace(name="Cut", meals=[]),
                    operations=[self.operation],
                    normalized_fields={},
                    reason="Executed active diet query.",
                ),
            ),
        ):
            resolved = handle_input(self.config, "sí", session_id="telegram-main")

        self.assertTrue(resolved.executed)
        self.assertEqual(resolved.executed_command, "active-diet")
        self.assertEqual(resolved.normalized_fields["selected_option"], "resumen")
        clear_mock.assert_called_once_with(self.config.database_path, "telegram-main")

        with (
            patch("brain_ops.interfaces.conversation.follow_up_input.load_follow_up", return_value=pending),
            patch("brain_ops.interfaces.conversation.follow_up_input.clear_follow_up") as clear_mock,
        ):
            canceled = handle_input(self.config, "cancelar", session_id="telegram-main")

        self.assertFalse(canceled.executed)
        self.assertEqual(canceled.normalized_fields["selected_option"], "cancel")
        clear_mock.assert_called_once_with(self.config.database_path, "telegram-main")

        with (
            patch("brain_ops.interfaces.conversation.follow_up_input.load_follow_up", return_value=pending),
            patch("brain_ops.interfaces.conversation.follow_up_input.clear_follow_up") as clear_mock,
        ):
            unresolved = handle_input(self.config, "tal vez", session_id="telegram-main")

        self.assertFalse(unresolved.executed)
        self.assertTrue(unresolved.needs_follow_up)
        self.assertIn("resumen", unresolved.follow_up_options)
        clear_mock.assert_not_called()

    def test_follow_up_resolution_supports_objectives_and_recommendations_branches(self) -> None:
        pending = PendingFollowUp(
            followup_type="active_diet_options",
            question="Tu dieta activa es Cut. ¿Quieres resumen, objetivos o recomendaciones?",
            options=["resumen", "objetivos", "recomendaciones"],
            default_option="resumen",
            context={"diet_name": "Cut"},
        )

        macro_payload = SimpleNamespace(
            target_source="active_diet",
            calories_target=2200,
            protein_g_target=180,
            carbs_g_target=210,
            fat_g_target=70,
        )
        daily_payload = SimpleNamespace(
            missing_diet_meals=["breakfast"],
            habit_pending=["leer"],
            protein_g_remaining=35,
        )

        with (
            patch("brain_ops.interfaces.conversation.follow_up_input.load_follow_up", return_value=pending),
            patch("brain_ops.interfaces.conversation.follow_up_input.clear_follow_up"),
            patch(
                "brain_ops.interfaces.conversation.follow_up_input.execute_intent",
                side_effect=[
                    IntentExecutionOutcome(
                        payload=macro_payload,
                        operations=[],
                        normalized_fields={},
                        reason="Executed macro status query.",
                    ),
                    IntentExecutionOutcome(
                        payload=daily_payload,
                        operations=[],
                        normalized_fields={},
                        reason="Executed daily status query.",
                    ),
                ],
            ),
        ):
            objectives = handle_input(self.config, "objetivos", session_id="telegram-main")
            recommendations = handle_input(self.config, "recomendaciones", session_id="telegram-main")

        self.assertTrue(objectives.executed)
        self.assertEqual(objectives.executed_command, "macro-status")
        self.assertEqual(objectives.normalized_fields["selected_option"], "objetivos")
        self.assertIn("2200", objectives.assistant_message)

        self.assertTrue(recommendations.executed)
        self.assertEqual(recommendations.executed_command, "daily-status")
        self.assertEqual(recommendations.normalized_fields["selected_option"], "recomendaciones")
        self.assertIn("Cut", recommendations.assistant_message)

    def test_handle_input_dispatches_normal_single_intent_flow(self) -> None:
        parsed = [DailyLogIntent(text="Necesito pensar esto luego", log_domain="daily")]
        result_obj = SimpleNamespace(kind="executed")

        with (
            patch("brain_ops.interfaces.conversation.handling.resolve_conversation_input", return_value=parsed),
            patch("brain_ops.interfaces.conversation.handling.dispatch_parsed_input", return_value=result_obj) as dispatch_mock,
        ):
            result = handle_input(self.config, "Necesito pensar esto luego", dry_run=True)

        self.assertIs(result, result_obj)
        dispatch_mock.assert_called_once_with(
            self.config,
            "Necesito pensar esto luego",
            parsed,
            dry_run=True,
            session_id=None,
        )


if __name__ == "__main__":
    import unittest

    unittest.main()
