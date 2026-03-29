from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from brain_ops.errors import ConfigError
from brain_ops.models import DailyLogResult, OperationRecord, OperationStatus


def log_daily_event(
    database_path: Path,
    text: str,
    *,
    domain: str = "general",
    logged_at: datetime | None = None,
    dry_run: bool = False,
) -> DailyLogResult:
    if not text.strip():
        raise ConfigError("Daily log text cannot be empty.")

    logged_at = logged_at or datetime.now()
    target = database_path.expanduser()
    payload = json.dumps({"text": text.strip()}, ensure_ascii=False)

    if not dry_run:
        target.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(target) as connection:
            connection.execute(
                """
                INSERT INTO daily_logs (logged_at, domain, payload_json, source)
                VALUES (?, ?, ?, ?)
                """,
                (logged_at.isoformat(timespec="seconds"), domain.strip().lower(), payload, "chat"),
            )
            connection.commit()

    operation = OperationRecord(
        action="insert",
        path=target,
        detail=f"logged daily event in domain `{domain.strip().lower()}`",
        status=OperationStatus.CREATED,
    )
    return DailyLogResult(
        logged_at=logged_at,
        domain=domain.strip().lower(),
        operations=[operation],
        reason="Logged generic daily event into SQLite.",
    )
