from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from brain_ops.config import AIConfig, VaultConfig
from brain_ops.interfaces.conversation.handling import handle_input
from brain_ops.interfaces.conversation.parsing_input import parse_intent, parse_intents
from brain_ops.intents import CreateDietPlanIntent, DailyStatusIntent, LogBodyMetricsIntent, LogExpenseIntent, LogSupplementIntent
from brain_ops.services.diet_service import create_diet_plan
from brain_ops.storage.db import initialize_database


class IntentPipelineTestCase(unittest.TestCase):
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

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_parse_intent_keeps_heuristic_supplement(self) -> None:
        parsed = parse_intent(self.config, "Tomé 5g de creatina")
        self.assertIsInstance(parsed, LogSupplementIntent)
        assert isinstance(parsed, LogSupplementIntent)
        self.assertEqual(parsed.supplement_name, "Creatina")
        self.assertEqual(parsed.amount, 5.0)
        self.assertEqual(parsed.unit, "g")

    def test_parse_intent_keeps_heuristic_expense(self) -> None:
        parsed = parse_intent(self.config, "Gasté 250 en Farmacia Roma")
        self.assertIsInstance(parsed, LogExpenseIntent)
        assert isinstance(parsed, LogExpenseIntent)
        self.assertEqual(parsed.amount, 250.0)
        self.assertEqual(parsed.merchant, "Farmacia Roma")
        self.assertEqual(parsed.category, "salud")

    def test_parse_intent_keeps_heuristic_body_metrics(self) -> None:
        parsed = parse_intent(self.config, "Hoy pesé 81.2kg")
        self.assertIsInstance(parsed, LogBodyMetricsIntent)
        assert isinstance(parsed, LogBodyMetricsIntent)
        self.assertEqual(parsed.weight_kg, 81.2)

    def test_parse_intents_protects_semicolon_diet_input(self) -> None:
        text = (
            "mi dieta ahora será desayuno 3 huevos p:18 c:1 f:15 cal:210; 80g avena p:10 c:54 f:5 cal:300. "
            "comida 200g pechuga de pollo p:62 c:0 f:7 cal:330; 2 tortillas p:4 c:24 f:2 cal:130. "
            "cena 250g yogurt griego p:25 c:10 f:0 cal:150; 1 platano p:1 c:27 f:0 cal:105"
        )
        parsed = parse_intents(self.config, text)
        self.assertIsInstance(parsed, list)
        assert isinstance(parsed, list)
        self.assertEqual(len(parsed), 1)
        self.assertIsInstance(parsed[0], CreateDietPlanIntent)

    def test_handle_input_multi_action_returns_stable_sub_results(self) -> None:
        result = handle_input(
            self.config,
            "Gasté 250 en Farmacia Roma; hoy pesé 81.2kg",
            dry_run=True,
        )
        self.assertTrue(result.executed)
        self.assertEqual(result.intent, "multi_action")
        self.assertEqual(result.intent_version, "1")
        self.assertEqual(result.executed_command, "multi-action")
        self.assertEqual(len(result.sub_results), 2)
        self.assertIn("log_expense", result.normalized_fields["intents"])
        self.assertIn("log_body_metrics", result.normalized_fields["intents"])
        payload = result.model_dump()
        self.assertIn("intent", payload)
        self.assertIn("normalized_fields", payload)
        self.assertEqual(payload["sub_results"][0]["intent_version"], "1")

    def test_daily_status_query_does_not_mutate_state(self) -> None:
        parsed = parse_intent(self.config, "cómo voy hoy")
        self.assertIsInstance(parsed, DailyStatusIntent)
        result = handle_input(self.config, "cómo voy hoy")
        self.assertTrue(result.executed)
        self.assertEqual(result.intent, "daily_status")
        self.assertEqual(result.executed_command, "daily-status")
        self.assertEqual(result.operations, [])
        self.assertFalse(result.needs_follow_up)

    def test_follow_up_state_resolves_affirmation(self) -> None:
        create_diet_plan(
            self.config.database_path,
            name="Dieta Base Real",
            meals=["breakfast|Desayuno|4 huevos; 2 tortillas", "lunch|Comida|200g pollo", "dinner|Cena|210g pollo; 1/2 aguacate"],
            activate=True,
        )
        first = handle_input(self.config, "cuál es mi dieta activa", session_id="telegram-main")
        self.assertTrue(first.executed)
        self.assertTrue(first.needs_follow_up)
        self.assertIn("resumen", first.follow_up_options)

        second = handle_input(self.config, "sí", session_id="telegram-main")
        self.assertTrue(second.executed)
        self.assertEqual(second.intent, "follow_up")
        self.assertEqual(second.executed_command, "active-diet")
        self.assertIn("Resumen de Dieta Base Real", second.assistant_message)


if __name__ == "__main__":
    unittest.main()
