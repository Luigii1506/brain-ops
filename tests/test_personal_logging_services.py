from __future__ import annotations

import unittest
from pathlib import Path

from brain_ops.errors import ConfigError
from brain_ops.services.body_metrics_service import log_body_metrics
from brain_ops.services.daily_log_service import log_daily_event
from brain_ops.services.expenses_service import log_expense
from brain_ops.services.fitness_service import log_workout
from brain_ops.services.life_ops_service import habit_checkin, log_supplement
from brain_ops.services.nutrition_service import log_meal


class PersonalLoggingServicesTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.database_path = Path("/tmp/brain_ops_logging_test.db")

    def test_log_meal_dry_run_preserves_normalized_text_and_items(self) -> None:
        result = log_meal(self.database_path, "  huevos; avena  ", dry_run=True)

        self.assertEqual(len(result.items), 2)
        self.assertIn("2 item(s)", result.operations[0].detail)

    def test_log_supplement_and_habit_checkin_dry_run_normalize_inputs(self) -> None:
        supplement_result = log_supplement(
            self.database_path,
            "  Creatina  ",
            amount=5,
            unit="g",
            dry_run=True,
        )
        habit_result = habit_checkin(
            self.database_path,
            "  leer  ",
            status="Done",
            dry_run=True,
        )

        self.assertEqual(supplement_result.supplement_name, "Creatina")
        self.assertEqual(habit_result.habit_name, "leer")
        self.assertEqual(habit_result.status, "done")

    def test_log_workout_dry_run_uses_normalized_text_for_parsing(self) -> None:
        result = log_workout(
            self.database_path,
            "  Sentadilla 4x8@100kg  ",
            dry_run=True,
        )

        self.assertEqual(len(result.exercises), 1)
        self.assertEqual(result.exercises[0].exercise_name, "Sentadilla")

    def test_log_body_metrics_and_expense_dry_run_preserve_normalized_fields(self) -> None:
        body_metrics_result = log_body_metrics(
            self.database_path,
            weight_kg=78.4,
            body_fat_pct=14.2,
            waist_cm=82.0,
            dry_run=True,
        )
        expense_result = log_expense(
            self.database_path,
            250,
            category="food",
            merchant="Store",
            currency="usd",
            dry_run=True,
        )

        self.assertEqual(body_metrics_result.weight_kg, 78.4)
        self.assertEqual(body_metrics_result.body_fat_pct, 14.2)
        self.assertEqual(body_metrics_result.waist_cm, 82.0)
        self.assertEqual(expense_result.currency, "USD")
        self.assertEqual(expense_result.category, "food")
        self.assertEqual(expense_result.merchant, "Store")

    def test_log_daily_event_dry_run_normalizes_text_and_domain(self) -> None:
        result = log_daily_event(
            self.database_path,
            "  hice backlog  ",
            domain=" Work ",
            dry_run=True,
        )

        self.assertEqual(result.domain, "work")
        self.assertIn("`work`", result.operations[0].detail)

    def test_logging_services_reject_invalid_inputs(self) -> None:
        with self.assertRaises(ConfigError):
            log_workout(self.database_path, "   ", dry_run=True)
        with self.assertRaises(ConfigError):
            log_body_metrics(self.database_path, dry_run=True)
        with self.assertRaises(ConfigError):
            log_expense(self.database_path, 0, dry_run=True)
        with self.assertRaises(ConfigError):
            log_daily_event(self.database_path, "   ", dry_run=True)


if __name__ == "__main__":
    unittest.main()
