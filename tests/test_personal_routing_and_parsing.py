from __future__ import annotations

from unittest import TestCase

from brain_ops.intents import (
    HabitCheckinIntent,
    LogBodyMetricsIntent,
    LogExpenseIntent,
    LogMealIntent,
    LogSupplementIntent,
    LogWorkoutIntent,
)
from brain_ops.models import RouteDecisionResult
from brain_ops.services.intent_parser_logging import build_logging_intent_from_decision
from brain_ops.services.router_personal import build_personal_route_decision


class PersonalRoutingAndParsingTestCase(TestCase):
    def test_build_personal_route_decision_detects_macro_targets(self) -> None:
        result = build_personal_route_decision("Mi meta son 2200 kcal y 180 g de proteína")

        self.assertIsNotNone(result)
        self.assertEqual(result.command, "set-macro-targets")
        self.assertEqual(result.extracted_fields["calories_hint"], 2200.0)
        self.assertEqual(result.extracted_fields["protein_g_hint"], 180.0)

    def test_build_personal_route_decision_detects_budget_status(self) -> None:
        result = build_personal_route_decision("Cómo voy de presupuesto esta semana en comida")

        self.assertIsNotNone(result)
        self.assertEqual(result.command, "budget-status")
        self.assertEqual(result.extracted_fields["period_hint"], "weekly")
        self.assertEqual(result.extracted_fields["category_hint"], "comida")

    def test_build_personal_route_decision_detects_habit_target(self) -> None:
        result = build_personal_route_decision("Quiero que mi hábito de leer sea 2 veces por semana")

        self.assertIsNotNone(result)
        self.assertEqual(result.command, "set-habit-target")
        self.assertEqual(result.extracted_fields["target_count_hint"], 2)
        self.assertEqual(result.extracted_fields["period_hint"], "weekly")
        self.assertEqual(result.extracted_fields["habit_name_hint"], "leer")

    def test_build_logging_intent_from_decision_parses_expense(self) -> None:
        decision = RouteDecisionResult(
            input_text="Gasté 250 en farmacia roma con tarjeta",
            domain="expenses",
            command="log-expense",
            confidence=0.9,
            reason="Detected expense",
            extracted_fields={"category_hint": "general"},
        )

        intent = build_logging_intent_from_decision(decision.input_text, decision)

        self.assertIsInstance(intent, LogExpenseIntent)
        self.assertEqual(intent.amount, 250.0)
        self.assertEqual(intent.category, "salud")
        self.assertEqual(intent.merchant, "farmacia roma")
        self.assertEqual(intent.currency, "MXN")

    def test_build_logging_intent_from_decision_parses_supplement_and_habit(self) -> None:
        supplement_decision = RouteDecisionResult(
            input_text="Tomé creatina 5g",
            domain="supplements",
            command="log-supplement",
            confidence=0.9,
            reason="Detected supplement",
        )
        habit_decision = RouteDecisionResult(
            input_text="Hoy medité un poco",
            domain="habits",
            command="habit-checkin",
            confidence=0.9,
            reason="Detected habit",
        )

        supplement_intent = build_logging_intent_from_decision(supplement_decision.input_text, supplement_decision)
        habit_intent = build_logging_intent_from_decision(habit_decision.input_text, habit_decision)

        self.assertIsInstance(supplement_intent, LogSupplementIntent)
        self.assertEqual(supplement_intent.supplement_name, "Creatina")
        self.assertEqual(supplement_intent.amount, 5.0)
        self.assertEqual(supplement_intent.unit, "g")

        self.assertIsInstance(habit_intent, HabitCheckinIntent)
        self.assertEqual(habit_intent.habit_name, "meditar")
        self.assertEqual(habit_intent.status, "partial")

    def test_build_logging_intent_from_decision_parses_body_metrics_and_workout(self) -> None:
        body_decision = RouteDecisionResult(
            input_text="Peso 80 kg y cintura 82 cm",
            domain="body_metrics",
            command="log-body-metrics",
            confidence=0.9,
            reason="Detected body metrics",
        )
        workout_decision = RouteDecisionResult(
            input_text="Hoy hice sentadilla 4x8@100kg",
            domain="fitness",
            command="log-workout",
            confidence=0.9,
            reason="Detected workout",
        )

        body_intent = build_logging_intent_from_decision(body_decision.input_text, body_decision)
        workout_intent = build_logging_intent_from_decision(workout_decision.input_text, workout_decision)

        self.assertIsInstance(body_intent, LogBodyMetricsIntent)
        self.assertEqual(body_intent.weight_kg, 80.0)
        self.assertEqual(body_intent.waist_cm, 82.0)

        self.assertIsInstance(workout_intent, LogWorkoutIntent)
        self.assertEqual(workout_intent.workout_text, "sentadilla 4x8@100kg")

    def test_build_logging_intent_from_decision_normalizes_meal_text(self) -> None:
        decision = RouteDecisionResult(
            input_text="Hoy desayuné huevos y avena",
            domain="nutrition",
            command="log-meal",
            confidence=0.9,
            reason="Detected meal",
            extracted_fields={"meal_type_hint": "breakfast"},
        )

        intent = build_logging_intent_from_decision(decision.input_text, decision)

        self.assertIsInstance(intent, LogMealIntent)
        self.assertEqual(intent.meal_type, "breakfast")
        self.assertEqual(intent.meal_text, "huevos; avena")


if __name__ == "__main__":
    import unittest

    unittest.main()
