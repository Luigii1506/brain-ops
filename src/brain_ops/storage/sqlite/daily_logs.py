from __future__ import annotations

from pathlib import Path

from brain_ops.storage.db import connect_sqlite


def insert_daily_log(
    database_path: Path,
    *,
    logged_at: str,
    domain: str,
    payload_json: str,
    source: str,
) -> None:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        connection.execute(
            """
            INSERT INTO daily_logs (logged_at, domain, payload_json, source)
            VALUES (?, ?, ?, ?)
            """,
            (logged_at, domain, payload_json, source),
        )
