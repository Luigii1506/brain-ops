from __future__ import annotations

from unittest import TestCase
from unittest.mock import patch

from brain_ops.config import VaultConfig
from brain_ops.interfaces.conversation.follow_up_state import (
    PendingFollowUp as ConversationPendingFollowUp,
    clear_follow_up as conversation_clear_follow_up,
    load_follow_up as conversation_load_follow_up,
    save_follow_up as conversation_save_follow_up,
)
from brain_ops.interfaces.conversation.handling import handle_input as conversation_handle_input
from brain_ops.interfaces.conversation.parsing_input import (
    parse_intent as conversation_parse_intent,
    parse_intents as conversation_parse_intents,
)
from brain_ops.services import follow_up_service, handle_input_service, intent_execution_service, intent_parser_service
from brain_ops.services.intent_formatter_service import format_intent_message
from brain_ops.services.router_service import route_input


class ConversationCompatWrappersTestCase(TestCase):
    def test_handle_input_and_parser_services_reexport_conversation_entrypoints(self) -> None:
        self.assertIs(handle_input_service.handle_input, conversation_handle_input)
        self.assertIs(intent_parser_service.parse_intent, conversation_parse_intent)
        self.assertIs(intent_parser_service.parse_intents, conversation_parse_intents)

    def test_follow_up_service_reexports_state_symbols(self) -> None:
        self.assertIs(follow_up_service.PendingFollowUp, ConversationPendingFollowUp)
        self.assertIs(follow_up_service.save_follow_up, conversation_save_follow_up)
        self.assertIs(follow_up_service.load_follow_up, conversation_load_follow_up)
        self.assertIs(follow_up_service.clear_follow_up, conversation_clear_follow_up)

    def test_router_service_delegates_to_conversation_router(self) -> None:
        expected = object()
        with patch("brain_ops.services.router_service.route_conversation_input", return_value=expected) as route_mock:
            observed = route_input("como voy hoy")

        self.assertIs(observed, expected)
        route_mock.assert_called_once_with("como voy hoy")

    def test_intent_formatter_service_delegates_to_conversation_formatter(self) -> None:
        expected = "formatted"
        intent = object()
        payload = {"ok": True}
        with patch(
            "brain_ops.services.intent_formatter_service.format_conversation_intent_message",
            return_value=expected,
        ) as format_mock:
            observed = format_intent_message(intent, payload, "texto")

        self.assertEqual(observed, expected)
        format_mock.assert_called_once_with(intent, payload, "texto")

    def test_follow_up_service_resolve_follow_up_delegates_to_conversation_module(self) -> None:
        config = VaultConfig(vault_path="/tmp/vault")
        expected = object()

        with patch(
            "brain_ops.interfaces.conversation.follow_up_input.resolve_follow_up",
            return_value=expected,
        ) as resolve_mock:
            observed = follow_up_service.resolve_follow_up(config, "session-1", "si")

        self.assertIs(observed, expected)
        resolve_mock.assert_called_once_with(config, "session-1", "si")

    def test_intent_execution_service_reexports_dispatch_entrypoint(self) -> None:
        from brain_ops.core.execution.dispatch import execute_intent as core_execute_intent

        self.assertIs(intent_execution_service.execute_intent, core_execute_intent)


if __name__ == "__main__":
    import unittest

    unittest.main()
