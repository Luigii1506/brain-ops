from __future__ import annotations

import unittest
from datetime import datetime
from pathlib import Path

from brain_ops.domains.personal.diet.projections import (
    build_actual_meal_progress,
    build_diet_activation_result,
    build_diet_meal_update_result,
    build_diet_plan_result,
)
from brain_ops.domains.personal.diet.parsing import (
    normalize_diet_meal_update_inputs,
    normalize_diet_plan_name,
    parse_diet_plan_meals,
    parse_diet_update_items,
)
from brain_ops.domains.personal.fitness.workout_parsing import normalize_workout_log_input
from brain_ops.domains.personal.nutrition.meal_parsing import normalize_meal_log_input
from brain_ops.domains.personal.goals import (
    build_date_bounds,
    build_budget_target_result,
    build_period_bounds,
    build_habit_target_result,
    build_macro_targets_result,
    normalize_budget_target_inputs,
    normalize_habit_target_inputs,
    normalize_macro_target_inputs,
    resolve_macro_status_targets,
)
from brain_ops.errors import ConfigError
from brain_ops.domains.personal.tracking import (
    build_body_metrics_log_result,
    build_expense_log_result,
    build_habit_checkin_result,
    build_supplement_log_result,
    build_workout_log_result,
    normalize_body_metrics_inputs,
    normalize_expense_log_inputs,
    normalize_daily_log_inputs,
    normalize_habit_checkin_inputs,
    normalize_supplement_log_inputs,
)
from brain_ops.models import DietPlanMeal, DietPlanMealItem, OperationStatus, WorkoutSetInput


class PersonalDomainResultsTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.database_path = Path("/tmp/brain_ops_test.db")
        self.logged_at = datetime(2026, 4, 4, 12, 30, 0)

    def test_build_macro_targets_result_creates_updated_operation(self) -> None:
        result = build_macro_targets_result(
            database_path=self.database_path,
            calories=2200,
            protein_g=180,
            carbs_g=210,
            fat_g=70,
        )

        self.assertEqual(result.calories, 2200)
        self.assertEqual(result.protein_g, 180)
        self.assertEqual(result.reason, "Stored macro targets in SQLite.")
        self.assertEqual(len(result.operations), 1)
        self.assertEqual(result.operations[0].action, "upsert")
        self.assertEqual(result.operations[0].path, self.database_path)
        self.assertEqual(result.operations[0].status, OperationStatus.UPDATED)

    def test_build_budget_target_result_preserves_category_and_create_semantics(self) -> None:
        result = build_budget_target_result(
            database_path=self.database_path,
            period="month",
            amount=4500,
            currency="MXN",
            category="comida",
        )

        self.assertEqual(result.period, "month")
        self.assertEqual(result.amount, 4500)
        self.assertEqual(result.category, "comida")
        self.assertEqual(result.operations[0].action, "insert")
        self.assertEqual(result.operations[0].status, OperationStatus.CREATED)
        self.assertIn("month budget target", result.operations[0].detail)

    def test_build_diet_plan_result_deep_copies_meals(self) -> None:
        meals = [
            DietPlanMeal(
                meal_type="breakfast",
                label="Desayuno",
                items=[
                    DietPlanMealItem(
                        food_name="Huevos",
                        quantity=3,
                        protein_g=18,
                        fat_g=15,
                        calories=210,
                    )
                ],
                calories_target=210,
                protein_g_target=18,
                carbs_g_target=1,
                fat_g_target=15,
            )
        ]

        result = build_diet_plan_result(
            database_path=self.database_path,
            name="Base",
            status="active",
            meals=meals,
        )

        meals[0].label = "Mutado"
        meals[0].items[0].food_name = "Otro"

        self.assertEqual(result.name, "Base")
        self.assertEqual(result.status, "active")
        self.assertEqual(result.meals[0].label, "Desayuno")
        self.assertEqual(result.meals[0].items[0].food_name, "Huevos")
        self.assertEqual(result.operations[0].action, "create-diet-plan")
        self.assertEqual(result.operations[0].status, OperationStatus.CREATED)

    def test_build_diet_activation_and_meal_update_results_have_expected_operations(self) -> None:
        activation = build_diet_activation_result(
            database_path=self.database_path,
            name="Cut",
        )
        items = [DietPlanMealItem(food_name="Avena", grams=80, carbs_g=54, calories=300)]
        meal_update = build_diet_meal_update_result(
            database_path=self.database_path,
            diet_name="Cut",
            meal_type="breakfast",
            mode="replace",
            items=items,
        )

        items[0].food_name = "Mutado"

        self.assertEqual(activation.status, "active")
        self.assertEqual(activation.operations[0].action, "activate-diet")
        self.assertEqual(activation.operations[0].status, OperationStatus.UPDATED)
        self.assertEqual(meal_update.mode, "replace")
        self.assertEqual(meal_update.items[0].food_name, "Avena")
        self.assertEqual(meal_update.operations[0].action, "update-diet-meal")
        self.assertEqual(meal_update.operations[0].status, OperationStatus.UPDATED)

    def test_build_tracking_results_encode_expected_detail_strings(self) -> None:
        expense = build_expense_log_result(
            database_path=self.database_path,
            logged_at=self.logged_at,
            amount=250,
            currency="MXN",
            category="salud",
            merchant="Farmacia Roma",
        )
        body_metrics = build_body_metrics_log_result(
            database_path=self.database_path,
            logged_at=self.logged_at,
            weight_kg=81.2,
            body_fat_pct=18.5,
            fat_mass_kg=None,
            muscle_mass_kg=None,
            visceral_fat=None,
            bmr_calories=None,
            arm_cm=None,
            waist_cm=86,
            thigh_cm=None,
            calf_cm=None,
        )
        supplement = build_supplement_log_result(
            database_path=self.database_path,
            logged_at=self.logged_at,
            supplement_name="Creatina",
            amount=5,
            unit="g",
        )
        habit = build_habit_checkin_result(
            database_path=self.database_path,
            checked_at=self.logged_at,
            habit_name="leer",
            status="done",
        )

        self.assertIn("250.00 MXN", expense.operations[0].detail)
        self.assertIn("weight=81.2kg", body_metrics.operations[0].detail)
        self.assertIn("waist=86cm", body_metrics.operations[0].detail)
        self.assertIn("Creatina", supplement.operations[0].detail)
        self.assertIn("`leer`", habit.operations[0].detail)
        self.assertEqual(expense.operations[0].status, OperationStatus.CREATED)
        self.assertEqual(body_metrics.operations[0].status, OperationStatus.CREATED)

    def test_build_workout_and_habit_results_preserve_payloads(self) -> None:
        exercises = [
            WorkoutSetInput(
                exercise_name="Bench Press",
                sets=3,
                reps=8,
                weight_kg=80,
            )
        ]
        workout = build_workout_log_result(
            database_path=self.database_path,
            logged_at=self.logged_at,
            routine_name="Push",
            exercises=exercises,
        )
        habit_target = build_habit_target_result(
            database_path=self.database_path,
            habit_name="caminar",
            period="day",
            target_count=1,
        )

        exercises[0].exercise_name = "Mutado"

        self.assertEqual(workout.routine_name, "Push")
        self.assertEqual(workout.exercises[0].exercise_name, "Bench Press")
        self.assertEqual(workout.operations[0].action, "insert")
        self.assertEqual(habit_target.habit_name, "caminar")
        self.assertEqual(habit_target.operations[0].action, "upsert")
        self.assertEqual(habit_target.operations[0].status, OperationStatus.UPDATED)

    def test_build_date_and_period_bounds_cover_daily_weekly_and_monthly(self) -> None:
        self.assertEqual(
            build_date_bounds("2026-04-04"),
            ("2026-04-04T00:00:00", "2026-04-04T23:59:59"),
        )
        self.assertEqual(
            build_period_bounds("2026-04-04", "daily"),
            ("2026-04-04T00:00:00", "2026-04-04T23:59:59"),
        )
        self.assertEqual(
            build_period_bounds("2026-04-04", "weekly"),
            ("2026-03-30T00:00:00", "2026-04-05T23:59:59"),
        )
        self.assertEqual(
            build_period_bounds("2026-04-04", "monthly"),
            ("2026-04-01T00:00:00", "2026-04-30T23:59:59"),
        )

    def test_build_actual_meal_progress_aggregates_per_meal_and_totals(self) -> None:
        by_meal, totals = build_actual_meal_progress(
            [
                ("breakfast", "Eggs", 200, 18, 1, 14),
                ("breakfast", "Toast", 120, 4, 20, 2),
                ("lunch", "Rice", 220, 4, 48, 1),
                (None, "Coffee", 5, 0, 1, 0),
            ]
        )

        self.assertEqual(by_meal["breakfast"]["item_count"], 2)
        self.assertEqual(by_meal["breakfast"]["items"], ["Eggs", "Toast"])
        self.assertEqual(by_meal["breakfast"]["calories"], 320.0)
        self.assertEqual(by_meal["lunch"]["carbs_g"], 48.0)
        self.assertEqual(by_meal["unspecified"]["items"], ["Coffee"])
        self.assertEqual(totals["calories"], 545.0)
        self.assertEqual(totals["protein_g"], 26.0)
        self.assertEqual(totals["carbs_g"], 70.0)
        self.assertEqual(totals["fat_g"], 17.0)

    def test_resolve_macro_status_targets_prefers_active_diet_then_manual_then_empty(self) -> None:
        active_diet = ("Cut", {"calories": 2200.0, "protein_g": 180.0, "carbs_g": 200.0, "fat_g": 70.0})
        self.assertEqual(
            resolve_macro_status_targets(active_diet, (100, 100, 100, 100)),
            {
                "target_source": "active_diet",
                "active_diet_name": "Cut",
                "calories_target": 2200.0,
                "protein_g_target": 180.0,
                "carbs_g_target": 200.0,
                "fat_g_target": 70.0,
            },
        )

        self.assertEqual(
            resolve_macro_status_targets(None, (2200, 180, 210, 70)),
            {
                "target_source": "manual",
                "active_diet_name": None,
                "calories_target": 2200.0,
                "protein_g_target": 180.0,
                "carbs_g_target": 210.0,
                "fat_g_target": 70.0,
            },
        )

        self.assertEqual(
            resolve_macro_status_targets(None, None),
            {
                "target_source": None,
                "active_diet_name": None,
                "calories_target": None,
                "protein_g_target": None,
                "carbs_g_target": None,
                "fat_g_target": None,
            },
        )

    def test_normalize_goal_write_inputs_validate_and_normalize(self) -> None:
        self.assertEqual(
            normalize_macro_target_inputs(
                calories=2200,
                protein_g=None,
                carbs_g=None,
                fat_g=None,
            ),
            {
                "calories": 2200,
                "protein_g": None,
                "carbs_g": None,
                "fat_g": None,
            },
        )
        self.assertEqual(
            normalize_budget_target_inputs(
                amount=4500,
                period="Weekly",
                currency="mxn",
                category="food",
            ),
            {
                "amount": 4500,
                "period": "weekly",
                "currency": "MXN",
                "category": "food",
            },
        )
        self.assertEqual(
            normalize_habit_target_inputs(
                habit_name="  caminar  ",
                target_count=2,
                period="Daily",
            ),
            {
                "habit_name": "caminar",
                "target_count": 2,
                "period": "daily",
            },
        )

        with self.assertRaises(ConfigError):
            normalize_macro_target_inputs(
                calories=None,
                protein_g=None,
                carbs_g=None,
                fat_g=None,
            )
        with self.assertRaises(ConfigError):
            normalize_budget_target_inputs(
                amount=0,
                period="weekly",
                currency="MXN",
                category=None,
            )
        with self.assertRaises(ConfigError):
            normalize_habit_target_inputs(
                habit_name="   ",
                target_count=1,
                period="daily",
            )

    def test_normalize_diet_write_inputs_validate_and_parse(self) -> None:
        self.assertEqual(normalize_diet_plan_name("  Cut  "), "Cut")
        parsed_meals = parse_diet_plan_meals(["breakfast|Eggs 3u"])
        self.assertEqual(len(parsed_meals), 1)
        self.assertEqual(parsed_meals[0].meal_type, "breakfast")

        self.assertEqual(
            normalize_diet_meal_update_inputs(
                meal_type=" Breakfast ",
                items_text="Eggs 3u",
                mode="Append",
            ),
            {
                "meal_type": "breakfast",
                "items_text": "Eggs 3u",
                "mode": "append",
            },
        )
        parsed_items = parse_diet_update_items("Eggs 3u")
        self.assertEqual(len(parsed_items), 1)
        self.assertEqual(parsed_items[0].food_name, "Eggs 3u")

        with self.assertRaises(ConfigError):
            normalize_diet_plan_name("   ")
        with self.assertRaises(ConfigError):
            parse_diet_plan_meals([])
        with self.assertRaises(ConfigError):
            normalize_diet_meal_update_inputs(
                meal_type="breakfast",
                items_text="   ",
                mode="replace",
            )

    def test_normalize_logging_inputs_validate_and_normalize(self) -> None:
        normalized_meal_text, meal_items = normalize_meal_log_input("  huevos; avena  ")
        self.assertEqual(normalized_meal_text, "huevos; avena")
        self.assertEqual(len(meal_items), 2)

        self.assertEqual(
            normalize_supplement_log_inputs(
                supplement_name="  Creatina  ",
                amount=5,
                unit="g",
                note="post",
            ),
            {
                "supplement_name": "Creatina",
                "amount": 5,
                "unit": "g",
                "note": "post",
            },
        )
        self.assertEqual(
            normalize_habit_checkin_inputs(
                habit_name="  leer  ",
                status="Done",
                note="ok",
            ),
            {
                "habit_name": "leer",
                "status": "done",
                "note": "ok",
            },
        )
        self.assertEqual(
            normalize_daily_log_inputs(
                text="  hice backlog  ",
                domain=" Work ",
            ),
            {
                "text": "hice backlog",
                "domain": "work",
            },
        )
        normalized_workout_text, exercises = normalize_workout_log_input("  Sentadilla 4x8@100kg  ")
        self.assertEqual(normalized_workout_text, "Sentadilla 4x8@100kg")
        self.assertEqual(len(exercises), 1)
        self.assertEqual(exercises[0].exercise_name, "Sentadilla")

        self.assertEqual(
            normalize_body_metrics_inputs(
                weight_kg=78.4,
                body_fat_pct=14.2,
                fat_mass_kg=None,
                muscle_mass_kg=None,
                visceral_fat=None,
                bmr_calories=None,
                arm_cm=None,
                waist_cm=82.0,
                thigh_cm=None,
                calf_cm=None,
                note="scan",
            ),
            {
                "weight_kg": 78.4,
                "body_fat_pct": 14.2,
                "fat_mass_kg": None,
                "muscle_mass_kg": None,
                "visceral_fat": None,
                "bmr_calories": None,
                "arm_cm": None,
                "waist_cm": 82.0,
                "thigh_cm": None,
                "calf_cm": None,
                "note": "scan",
            },
        )
        self.assertEqual(
            normalize_expense_log_inputs(
                amount=250,
                category="food",
                merchant="Store",
                currency="usd",
                note="lunch",
            ),
            {
                "amount": 250,
                "category": "food",
                "merchant": "Store",
                "currency": "USD",
                "note": "lunch",
            },
        )

        with self.assertRaises(ConfigError):
            normalize_meal_log_input("   ")
        with self.assertRaises(ConfigError):
            normalize_workout_log_input("   ")
        with self.assertRaises(ConfigError):
            normalize_supplement_log_inputs(
                supplement_name="   ",
                amount=None,
                unit=None,
                note=None,
            )
        with self.assertRaises(ConfigError):
            normalize_habit_checkin_inputs(
                habit_name="leer",
                status="unknown",
                note=None,
            )
        with self.assertRaises(ConfigError):
            normalize_daily_log_inputs(text="   ", domain="general")
        with self.assertRaises(ConfigError):
            normalize_body_metrics_inputs(
                weight_kg=None,
                body_fat_pct=None,
                fat_mass_kg=None,
                muscle_mass_kg=None,
                visceral_fat=None,
                bmr_calories=None,
                arm_cm=None,
                waist_cm=None,
                thigh_cm=None,
                calf_cm=None,
                note=None,
            )
        with self.assertRaises(ConfigError):
            normalize_expense_log_inputs(
                amount=0,
                category=None,
                merchant=None,
                currency="MXN",
                note=None,
            )


if __name__ == "__main__":
    unittest.main()
