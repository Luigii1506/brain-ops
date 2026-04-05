from __future__ import annotations

from datetime import datetime
from typing import Iterable

from brain_ops.errors import ConfigError

DEFAULT_ALLOWED_PERIODS = frozenset({"daily", "weekly", "monthly"})


def resolve_iso_date(date_text: str | None) -> str:
    if not date_text:
        return datetime.now().date().isoformat()
    try:
        return datetime.fromisoformat(date_text).date().isoformat()
    except ValueError as exc:
        raise ConfigError("Date must be in YYYY-MM-DD format.") from exc


def normalize_period(period: str, *, allowed: frozenset[str] = DEFAULT_ALLOWED_PERIODS) -> str:
    normalized = (period or "").strip().lower()
    if normalized not in allowed:
        raise ConfigError(f"Period must be one of: {', '.join(sorted(allowed))}.")
    return normalized


def has_any_non_none(values: Iterable[object]) -> bool:
    return any(value is not None for value in values)
