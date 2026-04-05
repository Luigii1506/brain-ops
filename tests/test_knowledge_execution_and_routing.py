from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from brain_ops.intents import CaptureNoteIntent, MacroStatusIntent
from brain_ops.services.intent_execution_knowledge import execute_knowledge_intent
from brain_ops.services.intent_parser_knowledge import build_knowledge_intent_from_decision
from brain_ops.services.router_knowledge import build_knowledge_route_decision


class KnowledgeExecutionAndRoutingTestCase(TestCase):
    def setUp(self) -> None:
        self.vault = object()
        self.operation = SimpleNamespace(path=Path("/tmp/example.md"))

    def test_build_knowledge_route_decision_detects_url_source(self) -> None:
        result = build_knowledge_route_decision("https://en.wikipedia.org/wiki/Systems_thinking")

        self.assertIsNotNone(result)
        self.assertEqual(result.command, "capture --type source")
        self.assertEqual(result.domain, "knowledge")
        self.assertEqual(result.extracted_fields["url"], "https://en.wikipedia.org/wiki/Systems_thinking")
        self.assertEqual(result.extracted_fields["source_type"], "wikipedia")

    def test_build_knowledge_route_decision_detects_project_and_knowledge_text(self) -> None:
        project_result = build_knowledge_route_decision("Pendiente del proyecto: cerrar bug del repo")
        knowledge_result = build_knowledge_route_decision("Hoy aprendí una idea útil sobre systems thinking")

        self.assertIsNotNone(project_result)
        self.assertEqual(project_result.command, "capture --type project")
        self.assertEqual(project_result.domain, "projects")

        self.assertIsNotNone(knowledge_result)
        self.assertEqual(knowledge_result.command, "capture --type knowledge")
        self.assertEqual(knowledge_result.domain, "knowledge")

    def test_build_knowledge_route_decision_returns_none_for_unrelated_text(self) -> None:
        result = build_knowledge_route_decision("Muéstrame mi presupuesto semanal")

        self.assertIsNone(result)

    def test_build_knowledge_intent_from_decision_builds_capture_note_intent(self) -> None:
        decision = build_knowledge_route_decision("https://youtube.com/watch?v=abc123")

        intent = build_knowledge_intent_from_decision(decision.input_text, decision)

        self.assertIsInstance(intent, CaptureNoteIntent)
        self.assertEqual(intent.force_type, "source")
        self.assertEqual(intent.text, "https://youtube.com/watch?v=abc123")
        self.assertEqual(intent.confidence, decision.confidence)
        self.assertEqual(intent.routing_source, decision.routing_source)

    def test_build_knowledge_intent_from_decision_returns_none_for_unknown_command(self) -> None:
        from brain_ops.models import RouteDecisionResult

        decision = RouteDecisionResult(
            input_text="algo",
            domain="knowledge",
            command="weekly-review",
            confidence=0.5,
            reason="manual",
        )

        intent = build_knowledge_intent_from_decision(decision.input_text, decision)

        self.assertIsNone(intent)

    def test_execute_knowledge_intent_handles_capture_note(self) -> None:
        intent = CaptureNoteIntent(force_type="knowledge", text="Idea sobre sistemas")
        result_payload = SimpleNamespace(operation=self.operation)

        with patch(
            "brain_ops.services.intent_execution_knowledge.capture_text",
            return_value=result_payload,
        ) as capture_mock:
            outcome = execute_knowledge_intent(self.vault, intent)

        self.assertIsNotNone(outcome)
        self.assertIs(outcome.payload, result_payload)
        self.assertEqual(outcome.operations, [self.operation])
        self.assertEqual(outcome.normalized_fields["force_type"], "knowledge")
        self.assertIn("capture note intent", outcome.reason.lower())
        capture_mock.assert_called_once_with(
            self.vault,
            text="Idea sobre sistemas",
            force_type="knowledge",
            tags=[],
        )

    def test_execute_knowledge_intent_returns_none_for_non_knowledge_intent(self) -> None:
        outcome = execute_knowledge_intent(self.vault, MacroStatusIntent(metric="protein_g"))

        self.assertIsNone(outcome)


if __name__ == "__main__":
    import unittest

    unittest.main()
