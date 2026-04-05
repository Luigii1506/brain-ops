from __future__ import annotations

"""Deprecated compatibility wrapper for conversation follow-up state.

Retained for stable imports while callers migrate to
`brain_ops.interfaces.conversation.follow_up_state` and
`brain_ops.interfaces.conversation.follow_up_input`.
"""

from pathlib import Path

from brain_ops.config import VaultConfig
from brain_ops.interfaces.conversation.follow_up_state import (
    PendingFollowUp,
    active_diet_pending_follow_up,
    clear_follow_up,
    load_follow_up,
    save_follow_up,
)
from brain_ops.models import HandleInputResult


def resolve_follow_up(config: VaultConfig, session_id: str, input_text: str) -> HandleInputResult | None:
    from brain_ops.interfaces.conversation.follow_up_input import resolve_follow_up as resolve_follow_up_input

    return resolve_follow_up_input(config, session_id, input_text)


__all__ = [
    "PendingFollowUp",
    "save_follow_up",
    "load_follow_up",
    "clear_follow_up",
    "resolve_follow_up",
    "active_diet_pending_follow_up",
    "HandleInputResult",
    "VaultConfig",
    "Path",
]
