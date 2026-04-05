from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from brain_ops.config import AIConfig, VaultConfig
from brain_ops.services.body_metrics_service import log_body_metrics
from brain_ops.services.daily_log_service import log_daily_event
from brain_ops.services.daily_status_service import daily_status
from brain_ops.services.daily_summary_service import write_daily_summary
from brain_ops.services.diet_service import create_diet_plan
from brain_ops.services.expenses_service import log_expense
from brain_ops.services.fitness_service import log_workout
from brain_ops.services.goals_service import set_habit_target, set_macro_targets
from brain_ops.services.life_ops_service import habit_checkin, log_supplement
from brain_ops.services.nutrition_service import log_meal
from brain_ops.storage.db import initialize_database
from brain_ops.vault import Vault


class DailyWorkflowsTestCase(unittest.TestCase):
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
        self.vault = Vault(self.config)
        self.date = "2026-04-04"
        self.logged_at = datetime(2026, 4, 4, 9, 15, 0)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _seed_daily_activity(self) -> None:
        set_macro_targets(
            self.config.database_path,
            calories=2200,
            protein_g=180,
            carbs_g=210,
            fat_g=70,
        )
        set_habit_target(
            self.config.database_path,
            habit_name="leer",
            target_count=1,
            period="daily",
        )
        create_diet_plan(
            self.config.database_path,
            name="Base",
            meals=["breakfast|Desayuno|3 huevos p:18 c:1 f:15 cal:210"],
            activate=True,
        )
        log_meal(
            self.config.database_path,
            "3 huevos p:18 c:1 f:15 cal:210",
            meal_type="breakfast",
            logged_at=self.logged_at,
        )
        log_supplement(
            self.config.database_path,
            "Creatina",
            amount=5,
            unit="g",
            logged_at=self.logged_at,
        )
        habit_checkin(
            self.config.database_path,
            "leer",
            status="done",
            checked_at=self.logged_at,
        )
        log_body_metrics(
            self.config.database_path,
            weight_kg=81.2,
            body_fat_pct=18.5,
            waist_cm=86,
            logged_at=self.logged_at,
        )
        log_expense(
            self.config.database_path,
            250,
            category="salud",
            merchant="Farmacia Roma",
            logged_at=self.logged_at,
        )
        log_workout(
            self.config.database_path,
            "Press banca 3x8@80kg",
            routine_name="Push",
            logged_at=self.logged_at,
        )
        log_daily_event(
            self.config.database_path,
            "Buen día de ejecución.",
            domain="general",
            logged_at=self.logged_at,
        )

    def test_daily_status_aggregates_composed_capabilities(self) -> None:
        self._seed_daily_activity()

        summary = daily_status(self.config.database_path, date_text=self.date)

        self.assertEqual(summary.date, self.date)
        self.assertEqual(summary.active_diet_name, "Base")
        self.assertEqual(summary.calories_actual, 210)
        self.assertEqual(summary.calories_target, 210)
        self.assertEqual(summary.calories_remaining, 0)
        self.assertEqual(summary.workouts_logged, 1)
        self.assertEqual(summary.total_workout_sets, 3)
        self.assertEqual(summary.expenses_total, 250)
        self.assertEqual(summary.expense_currency, "MXN")
        self.assertEqual(summary.supplements_logged, 1)
        self.assertEqual(summary.supplement_names, ["Creatina"])
        self.assertEqual(summary.habits_completed, ["leer"])
        self.assertEqual(summary.habit_pending, [])
        self.assertEqual(summary.body_weight_kg, 81.2)
        self.assertEqual(summary.body_fat_pct, 18.5)
        self.assertEqual(summary.waist_cm, 86)
        self.assertEqual(summary.daily_logs_count, 1)
        self.assertEqual(summary.missing_diet_meals, [])

    def test_write_daily_summary_writes_structured_note_for_logged_day(self) -> None:
        self._seed_daily_activity()

        result = write_daily_summary(self.vault, date_text=self.date)

        self.assertEqual(result.date, self.date)
        self.assertIn("Meals", result.sections_written)
        self.assertIn("Diet Progress", result.sections_written)
        self.assertIn("Daily Logs", result.sections_written)
        self.assertTrue(result.path.exists())

        written = result.path.read_text(encoding="utf-8")
        self.assertIn("brain-ops Daily Summary - 2026-04-04", written)
        self.assertIn("### Meals", written)
        self.assertIn("### Diet Progress", written)
        self.assertIn("### Supplements", written)
        self.assertIn("### Workouts", written)
        self.assertIn("### Expenses", written)
        self.assertIn("### Habits", written)
        self.assertIn("### Body Metrics", written)
        self.assertIn("### Daily Logs", written)
        self.assertIn("Creatina", written)
        self.assertIn("Farmacia Roma", written)
        self.assertIn("Press banca", written)
        self.assertIn("Buen día de ejecución.", written)


if __name__ == "__main__":
    unittest.main()
