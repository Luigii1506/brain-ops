from __future__ import annotations

"""Deprecated compatibility wrapper for intent execution dispatch.

Retained for stable imports while callers migrate to
`brain_ops.core.execution.dispatch`.
"""

from brain_ops.config import VaultConfig
from brain_ops.core.execution.dispatch import execute_intent
from brain_ops.core.execution.runtime import IntentExecutionOutcome
from brain_ops.intents import IntentModel

__all__ = ["execute_intent", "IntentExecutionOutcome", "IntentModel", "VaultConfig"]
