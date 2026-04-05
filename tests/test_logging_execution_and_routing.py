from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from brain_ops.intents import (
    DailyLogIntent,
    LogBodyMetricsIntent,
    LogExpenseIntent,
    LogMealIntent,
    LogSupplementIntent,
    LogWorkoutIntent,
    MacroStatusIntent,
)
from brain_ops.models import OperationRecord, OperationStatus
from brain_ops.services.intent_execution_logging import execute_logging_intent
from brain_ops.services.router_logging import build_logging_route_decision


class LoggingExecutionAndRoutingTestCase(TestCase):
    def setUp(self) -> None:
        self.db_path = Path("/tmp/brain_ops.sqlite")
        self.operation = OperationRecord(
            action="insert",
            path=self.db_path,
            detail="logged",
            status=OperationStatus.CREATED,
        )

    def test_execute_logging_intent_handles_expense_and_meal(self) -> None:
        expense_intent = LogExpenseIntent(amount=250, category="food", merchant="Cafe", currency="MXN")
        expense_payload = SimpleNamespace(operations=[self.operation])
        meal_intent = LogMealIntent(meal_text="eggs; oats", meal_type="breakfast")
        meal_payload = SimpleNamespace(operations=[self.operation], items=["eggs", "oats"])

        with (
            patch("brain_ops.services.intent_execution_logging.log_expense", return_value=expense_payload) as expense_mock,
            patch("brain_ops.services.intent_execution_logging.log_meal", return_value=meal_payload) as meal_mock,
        ):
            expense_outcome = execute_logging_intent(self.db_path, expense_intent, dry_run=True)
            meal_outcome = execute_logging_intent(self.db_path, meal_intent, dry_run=False)

        self.assertEqual(expense_outcome.normalized_fields["amount"], 250)
        self.assertEqual(expense_outcome.normalized_fields["merchant"], "Cafe")
        self.assertIn("expense intent", expense_outcome.reason.lower())
        expense_mock.assert_called_once_with(
            self.db_path,
            amount=250,
            category="food",
            merchant="Cafe",
            currency="MXN",
            note=None,
            dry_run=True,
        )

        self.assertEqual(meal_outcome.normalized_fields["meal_text"], "eggs; oats")
        self.assertEqual(meal_outcome.normalized_fields["meal_type"], "breakfast")
        self.assertEqual(meal_outcome.normalized_fields["item_count"], 2)
        meal_mock.assert_called_once_with(
            self.db_path,
            "eggs; oats",
            meal_type="breakfast",
            dry_run=False,
        )

    def test_execute_logging_intent_handles_other_logging_intents(self) -> None:
        supplement_intent = LogSupplementIntent(supplement_name="Creatina", amount=5, unit="g", note="post")
        supplement_payload = SimpleNamespace(operations=[self.operation])
        body_intent = LogBodyMetricsIntent(weight_kg=80, body_fat_pct=15, waist_cm=82, note="morning")
        body_payload = SimpleNamespace(operations=[self.operation])
        workout_intent = LogWorkoutIntent(workout_text="sentadilla 4x8@100kg", routine_name="Lower")
        workout_payload = SimpleNamespace(operations=[self.operation], exercises=["sq"])
        daily_log_intent = DailyLogIntent(text="Cierre del dia", log_domain="work")
        daily_log_payload = SimpleNamespace(operations=[self.operation])

        with (
            patch("brain_ops.services.intent_execution_logging.log_supplement", return_value=supplement_payload) as supplement_mock,
            patch("brain_ops.services.intent_execution_logging.log_body_metrics", return_value=body_payload) as body_mock,
            patch("brain_ops.services.intent_execution_logging.log_workout", return_value=workout_payload) as workout_mock,
            patch("brain_ops.services.intent_execution_logging.log_daily_event", return_value=daily_log_payload) as daily_log_mock,
        ):
            supplement_outcome = execute_logging_intent(self.db_path, supplement_intent, dry_run=False)
            body_outcome = execute_logging_intent(self.db_path, body_intent, dry_run=False)
            workout_outcome = execute_logging_intent(self.db_path, workout_intent, dry_run=True)
            daily_log_outcome = execute_logging_intent(self.db_path, daily_log_intent, dry_run=True)

        self.assertEqual(supplement_outcome.normalized_fields["supplement_name"], "Creatina")
        self.assertEqual(supplement_outcome.normalized_fields["amount"], 5)
        self.assertEqual(body_outcome.normalized_fields["weight_kg"], 80)
        self.assertEqual(body_outcome.normalized_fields["waist_cm"], 82)
        self.assertEqual(workout_outcome.normalized_fields["routine_name"], "Lower")
        self.assertEqual(workout_outcome.normalized_fields["exercise_count"], 1)
        self.assertEqual(daily_log_outcome.normalized_fields["log_domain"], "work")

        supplement_mock.assert_called_once_with(
            self.db_path,
            "Creatina",
            amount=5,
            unit="g",
            note="post",
            dry_run=False,
        )
        body_mock.assert_called_once_with(
            self.db_path,
            weight_kg=80,
            body_fat_pct=15,
            waist_cm=82,
            note="morning",
            dry_run=False,
        )
        workout_mock.assert_called_once_with(
            self.db_path,
            "sentadilla 4x8@100kg",
            routine_name="Lower",
            dry_run=True,
        )
        daily_log_mock.assert_called_once_with(
            self.db_path,
            "Cierre del dia",
            domain="work",
            dry_run=True,
        )

    def test_execute_logging_intent_returns_none_for_non_logging_intent(self) -> None:
        outcome = execute_logging_intent(self.db_path, MacroStatusIntent(metric="protein_g"), dry_run=False)

        self.assertIsNone(outcome)

    def test_build_logging_route_decision_detects_expense_and_body_metrics(self) -> None:
        expense_result = build_logging_route_decision("Gasté 315 pesos en farmacia roma")
        body_result = build_logging_route_decision("Peso 80 kg y cintura 82 cm")

        self.assertIsNotNone(expense_result)
        self.assertEqual(expense_result.command, "log-expense")
        self.assertEqual(expense_result.extracted_fields["category_hint"], "salud")
        self.assertEqual(expense_result.extracted_fields["amount_hint"], 315.0)
        self.assertEqual(expense_result.extracted_fields["currency_hint"], "MXN")

        self.assertIsNotNone(body_result)
        self.assertEqual(body_result.command, "log-body-metrics")
        self.assertEqual(body_result.extracted_fields["weight_kg_hint"], 80.0)
        self.assertEqual(body_result.extracted_fields["waist_cm_hint"], 82.0)

    def test_build_logging_route_decision_detects_workout_supplement_meal_and_habit(self) -> None:
        workout_result = build_logging_route_decision("Hoy hice sentadilla 4x8@100kg")
        supplement_result = build_logging_route_decision("Tomé creatina 5g")
        meal_result = build_logging_route_decision("Hoy desayuné huevos y avena")
        habit_result = build_logging_route_decision("Hoy medité un poco")

        self.assertIsNotNone(workout_result)
        self.assertEqual(workout_result.command, "log-workout")

        self.assertIsNotNone(supplement_result)
        self.assertEqual(supplement_result.command, "log-supplement")
        self.assertEqual(supplement_result.extracted_fields["supplement_name_hint"], "creatina")
        self.assertEqual(supplement_result.extracted_fields["amount_hint"], 5.0)
        self.assertEqual(supplement_result.extracted_fields["unit_hint"], "g")

        self.assertIsNotNone(meal_result)
        self.assertEqual(meal_result.command, "log-meal")
        self.assertEqual(meal_result.extracted_fields["meal_type_hint"], "breakfast")

        self.assertIsNotNone(habit_result)
        self.assertEqual(habit_result.command, "habit-checkin")
        self.assertEqual(habit_result.extracted_fields["habit_name_hint"], "meditar")
        self.assertEqual(habit_result.extracted_fields["status_hint"], "partial")

    def test_build_logging_route_decision_returns_none_for_unrelated_text(self) -> None:
        result = build_logging_route_decision("Necesito reorganizar la carpeta de proyectos")

        self.assertIsNone(result)


if __name__ == "__main__":
    import unittest

    unittest.main()
