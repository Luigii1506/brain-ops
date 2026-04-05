from __future__ import annotations

"""Deprecated compatibility wrapper for conversation handling.

Retained for stable imports while callers migrate to
`brain_ops.interfaces.conversation.handling`.
"""

from brain_ops.config import VaultConfig
from brain_ops.interfaces.conversation.handling import handle_input
from brain_ops.models import HandleInputResult

__all__ = ["handle_input", "HandleInputResult", "VaultConfig"]
