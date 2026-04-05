from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from brain_ops.domains.personal.tracking import normalize_daily_log_inputs
from brain_ops.models import DailyLogResult, OperationRecord, OperationStatus
from brain_ops.storage.db import ensure_database_parent, resolve_database_path
from brain_ops.storage.sqlite import insert_daily_log


def log_daily_event(
    database_path: Path,
    text: str,
    *,
    domain: str = "general",
    logged_at: datetime | None = None,
    dry_run: bool = False,
) -> DailyLogResult:
    normalized = normalize_daily_log_inputs(text=text, domain=domain)

    logged_at = logged_at or datetime.now()
    target = resolve_database_path(database_path)
    payload = json.dumps({"text": normalized["text"]}, ensure_ascii=False)

    if not dry_run:
        ensure_database_parent(target)
        insert_daily_log(
            target,
            logged_at=logged_at.isoformat(timespec="seconds"),
            domain=normalized["domain"],
            payload_json=payload,
            source="chat",
        )

    operation = OperationRecord(
        action="insert",
        path=target,
        detail=f"logged daily event in domain `{normalized['domain']}`",
        status=OperationStatus.CREATED,
    )
    return DailyLogResult(
        logged_at=logged_at,
        domain=normalized["domain"],
        operations=[operation],
        reason="Logged generic daily event into SQLite.",
    )
