from __future__ import annotations

from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from brain_ops.intents import CreateDietPlanIntent, SetActiveDietIntent, UpdateDietMealIntent
from brain_ops.services.intent_parser_diet import build_diet_intent_from_decision
from brain_ops.services.router_diet import build_diet_route_decision


class DietRoutingAndParsingTestCase(TestCase):
    def setUp(self) -> None:
        self.db_path = Path("/tmp/brain_ops.sqlite")

    def test_build_diet_route_decision_detects_active_and_status_queries(self) -> None:
        active_result = build_diet_route_decision("¿Cuál es mi dieta activa?")
        status_result = build_diet_route_decision("Qué me falta de la dieta en desayuno")

        self.assertIsNotNone(active_result)
        self.assertEqual(active_result.command, "active-diet")

        self.assertIsNotNone(status_result)
        self.assertEqual(status_result.command, "diet-status")
        self.assertEqual(status_result.extracted_fields["meal_focus_hint"], "desayuno")

    def test_build_diet_route_decision_detects_create_update_and_activate(self) -> None:
        create_result = build_diet_route_decision(
            "Mi dieta ahora será desayuno: huevos; comida: pollo con arroz; cena: yogurt"
        )
        update_result = build_diet_route_decision("Agrega plátano a mi desayuno de la dieta")
        activate_result = build_diet_route_decision("Activa la dieta volumen limpio")

        self.assertIsNotNone(create_result)
        self.assertEqual(create_result.command, "create-diet-plan")

        self.assertIsNotNone(update_result)
        self.assertEqual(update_result.command, "update-diet-meal")
        self.assertEqual(update_result.extracted_fields["update_mode_hint"], "append")
        self.assertEqual(update_result.extracted_fields["meal_focus_hint"], "desayuno")

        self.assertIsNotNone(activate_result)
        self.assertEqual(activate_result.command, "set-active-diet")

    def test_build_diet_route_decision_returns_none_for_unrelated_text(self) -> None:
        result = build_diet_route_decision("Muéstrame mis gastos del día")

        self.assertIsNone(result)

    def test_build_diet_intent_from_decision_builds_create_diet_intent(self) -> None:
        text = "Mi dieta ahora será desayuno: huevos; comida: pollo con arroz; cena: yogurt con fruta"
        decision = build_diet_route_decision(text)

        intent = build_diet_intent_from_decision(text, decision, database_path=self.db_path)

        self.assertIsInstance(intent, CreateDietPlanIntent)
        self.assertTrue(intent.activate)
        self.assertEqual(len(intent.meals), 3)
        self.assertIn("breakfast|Desayuno|huevos", intent.meals[0])
        self.assertIn("lunch|Comida|pollo con arroz", intent.meals[1])
        self.assertIn("dinner|Cena|yogurt con fruta", intent.meals[2])

    def test_build_diet_intent_from_decision_builds_set_active_diet_intent(self) -> None:
        text = "Activa la dieta volumen limpio"
        decision = build_diet_route_decision(text)

        with patch(
            "brain_ops.services.intent_parser_diet.fetch_diet_plan_names",
            return_value=["Corte", "Volumen limpio"],
        ) as fetch_mock:
            intent = build_diet_intent_from_decision(text, decision, database_path=self.db_path)

        self.assertIsInstance(intent, SetActiveDietIntent)
        self.assertEqual(intent.name, "Volumen limpio")
        fetch_mock.assert_called_once_with(self.db_path)

    def test_build_diet_intent_from_decision_builds_update_diet_meal_intent(self) -> None:
        text = "Agrega plátano a mi desayuno de la dieta"
        decision = build_diet_route_decision(text)

        intent = build_diet_intent_from_decision(text, decision, database_path=self.db_path)

        self.assertIsInstance(intent, UpdateDietMealIntent)
        self.assertEqual(intent.meal_type, "breakfast")
        self.assertEqual(intent.items_text, "plátano")
        self.assertEqual(intent.mode, "append")

    def test_build_diet_intent_from_decision_returns_none_when_parse_fails(self) -> None:
        text = "Activa la dieta desconocida"
        decision = build_diet_route_decision(text)

        with patch(
            "brain_ops.services.intent_parser_diet.fetch_diet_plan_names",
            return_value=["Corte", "Volumen limpio"],
        ):
            intent = build_diet_intent_from_decision(text, decision, database_path=self.db_path)

        self.assertIsNone(intent)


if __name__ == "__main__":
    import unittest

    unittest.main()
