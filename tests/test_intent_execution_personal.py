from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from brain_ops.intents import (
    ActiveDietIntent,
    BudgetStatusIntent,
    DailyStatusIntent,
    LogExpenseIntent,
    MacroStatusIntent,
    SetBudgetTargetIntent,
    SetMacroTargetsIntent,
)
from brain_ops.models import OperationRecord, OperationStatus
from brain_ops.services.intent_execution_personal import execute_personal_intent


class IntentExecutionPersonalTestCase(TestCase):
    def setUp(self) -> None:
        self.db_path = Path("/tmp/brain_ops.sqlite")
        self.operation = OperationRecord(
            action="upsert",
            path=self.db_path,
            detail="updated",
            status=OperationStatus.UPDATED,
        )

    def test_execute_personal_intent_handles_set_macro_targets(self) -> None:
        intent = SetMacroTargetsIntent(calories=2200, protein_g=180, carbs_g=210, fat_g=70)
        result_payload = SimpleNamespace(operations=[self.operation])

        with patch(
            "brain_ops.services.intent_execution_personal.set_macro_targets",
            return_value=result_payload,
        ) as service_mock:
            outcome = execute_personal_intent(self.db_path, intent, dry_run=True)

        self.assertIsNotNone(outcome)
        self.assertIs(outcome.payload, result_payload)
        self.assertEqual(outcome.operations, [self.operation])
        self.assertEqual(outcome.normalized_fields["calories"], 2200)
        self.assertIn("macro target", outcome.reason.lower())
        service_mock.assert_called_once_with(
            self.db_path,
            calories=2200,
            protein_g=180,
            carbs_g=210,
            fat_g=70,
            dry_run=True,
        )

    def test_execute_personal_intent_handles_budget_target_and_budget_status(self) -> None:
        target_intent = SetBudgetTargetIntent(amount=5000, period="monthly", category="food", currency="MXN")
        target_payload = SimpleNamespace(operations=[self.operation])
        status_intent = BudgetStatusIntent(period="weekly", category="food", date="2026-04-04")
        status_payload = SimpleNamespace(items=["a", "b"])

        with (
            patch("brain_ops.services.intent_execution_personal.set_budget_target", return_value=target_payload) as set_mock,
            patch("brain_ops.services.intent_execution_personal.budget_status", return_value=status_payload) as status_mock,
        ):
            target_outcome = execute_personal_intent(self.db_path, target_intent, dry_run=False)
            status_outcome = execute_personal_intent(self.db_path, status_intent, dry_run=False)

        self.assertEqual(target_outcome.normalized_fields["amount"], 5000)
        self.assertEqual(target_outcome.normalized_fields["category"], "food")
        self.assertEqual(status_outcome.normalized_fields["period"], "weekly")
        self.assertEqual(status_outcome.normalized_fields["item_count"], 2)
        set_mock.assert_called_once()
        status_mock.assert_called_once_with(self.db_path, period="weekly", date_text="2026-04-04")

    def test_execute_personal_intent_handles_query_intents(self) -> None:
        macro_intent = MacroStatusIntent(metric="protein_g", date="2026-04-04")
        macro_payload = SimpleNamespace(target_source="active_diet", active_diet_name="Cut")
        active_diet_intent = ActiveDietIntent()
        active_diet_payload = SimpleNamespace(name="Cut")
        daily_status_intent = DailyStatusIntent(date="2026-04-04")
        daily_status_payload = SimpleNamespace(
            active_diet_name="Cut",
            missing_diet_meals=["breakfast"],
            habit_pending=["leer"],
        )

        with (
            patch("brain_ops.services.intent_execution_personal.macro_status", return_value=macro_payload) as macro_mock,
            patch("brain_ops.services.intent_execution_personal.active_diet", return_value=active_diet_payload) as active_mock,
            patch("brain_ops.services.intent_execution_personal.daily_status", return_value=daily_status_payload) as daily_mock,
        ):
            macro_outcome = execute_personal_intent(self.db_path, macro_intent, dry_run=False)
            active_outcome = execute_personal_intent(self.db_path, active_diet_intent, dry_run=False)
            daily_outcome = execute_personal_intent(self.db_path, daily_status_intent, dry_run=False)

        self.assertEqual(macro_outcome.normalized_fields["metric"], "protein_g")
        self.assertEqual(macro_outcome.normalized_fields["active_diet_name"], "Cut")
        self.assertEqual(active_outcome.normalized_fields["active_diet_name"], "Cut")
        self.assertEqual(daily_outcome.normalized_fields["missing_diet_meals"], ["breakfast"])
        self.assertEqual(daily_outcome.normalized_fields["habit_pending"], ["leer"])
        macro_mock.assert_called_once_with(self.db_path, date_text="2026-04-04")
        active_mock.assert_called_once_with(self.db_path)
        daily_mock.assert_called_once_with(self.db_path, date_text="2026-04-04")

    def test_execute_personal_intent_returns_none_for_non_personal_intent(self) -> None:
        intent = LogExpenseIntent(amount=250, category="food", merchant="Store")

        outcome = execute_personal_intent(self.db_path, intent, dry_run=False)

        self.assertIsNone(outcome)


if __name__ == "__main__":
    import unittest

    unittest.main()
