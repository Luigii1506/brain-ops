from __future__ import annotations

import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from brain_ops.config import AIConfig, VaultConfig
from brain_ops.errors import AIProviderError
from brain_ops.intents import CaptureNoteIntent, DailyLogIntent, DailyStatusIntent, LogExpenseIntent
from brain_ops.interfaces.conversation.parsing_input import parse_intent, parse_intents
from brain_ops.interfaces.conversation.routing_input import route_input
from brain_ops.storage.db import initialize_database


class ConversationRoutingAndParsingInputsTestCase(TestCase):
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

    def test_route_input_prioritizes_daily_status_and_domain_specific_routers(self) -> None:
        daily_result = route_input("cómo voy hoy")
        diet_result = route_input("Activa la dieta volumen limpio")
        personal_result = route_input("Mi meta son 2200 kcal y 180 g de proteína")
        logging_result = route_input("Gasté 250 en farmacia roma")
        knowledge_result = route_input("https://en.wikipedia.org/wiki/Cognitive_science")
        fallback_result = route_input("Necesito pensar mejor este tema más tarde")

        self.assertEqual(daily_result.command, "daily-status")
        self.assertEqual(diet_result.command, "set-active-diet")
        self.assertEqual(personal_result.command, "set-macro-targets")
        self.assertEqual(logging_result.command, "log-expense")
        self.assertEqual(knowledge_result.command, "capture --type source")
        self.assertEqual(fallback_result.command, "daily-log")
        self.assertEqual(fallback_result.domain, "daily")

    def test_parse_intent_builds_heuristic_intents_across_domains(self) -> None:
        expense_intent = parse_intent(self.config, "Gasté 250 en farmacia roma")
        knowledge_intent = parse_intent(self.config, "https://youtube.com/watch?v=abc123")
        daily_fallback_intent = parse_intent(self.config, "Necesito pensar mejor este tema más tarde")

        self.assertIsInstance(expense_intent, LogExpenseIntent)
        self.assertIsInstance(knowledge_intent, CaptureNoteIntent)
        self.assertEqual(knowledge_intent.force_type, "source")
        self.assertIsInstance(daily_fallback_intent, DailyLogIntent)
        self.assertEqual(daily_fallback_intent.log_domain, "daily")

    def test_parse_intent_prefers_heuristic_when_llm_fails(self) -> None:
        config = self.config.model_copy(
            update={"ai": self.config.ai.model_copy(update={"enable_llm_routing": True})}
        )

        with patch(
            "brain_ops.interfaces.conversation.parsing_input.llm_parse_intent",
            side_effect=AIProviderError("provider down"),
        ):
            parsed = parse_intent(config, "Gasté 250 en farmacia roma")

        self.assertIsInstance(parsed, LogExpenseIntent)

    def test_parse_intent_accepts_higher_confidence_llm_override(self) -> None:
        config = self.config.model_copy(
            update={"ai": self.config.ai.model_copy(update={"enable_llm_routing": True})}
        )
        llm_intent = DailyStatusIntent(confidence=0.99, routing_source="llm")
        text = "Hoy aprendí una idea útil sobre systems thinking"

        with patch(
            "brain_ops.interfaces.conversation.parsing_input.llm_parse_intent",
            return_value=llm_intent,
        ):
            parsed = parse_intent(config, text)

        self.assertIsInstance(parsed, DailyStatusIntent)
        self.assertEqual(parsed.routing_source, "hybrid")

    def test_parse_intents_splits_compound_input_when_not_preserved_single_parse(self) -> None:
        parsed = parse_intents(
            self.config,
            "Gasté 250 en farmacia roma; https://en.wikipedia.org/wiki/Cognitive_science",
        )

        self.assertIsInstance(parsed, list)
        self.assertEqual(len(parsed), 2)
        self.assertIsInstance(parsed[0], LogExpenseIntent)
        self.assertIsInstance(parsed[1], CaptureNoteIntent)


if __name__ == "__main__":
    import unittest

    unittest.main()
