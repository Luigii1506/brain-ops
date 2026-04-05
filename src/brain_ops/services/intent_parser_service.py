from __future__ import annotations

"""Deprecated compatibility wrapper for conversation parsing.

Retained for stable imports while callers migrate to
`brain_ops.interfaces.conversation.parsing_input`.
"""

from brain_ops.interfaces.conversation.parsing_input import parse_intent, parse_intents
from brain_ops.intents import IntentModel, ParseFailure

__all__ = ["parse_intent", "parse_intents", "IntentModel", "ParseFailure"]
