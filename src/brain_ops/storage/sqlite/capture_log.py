from __future__ import annotations

from pathlib import Path

from brain_ops.storage.db import connect_sqlite


def insert_capture_log(
    database_path: Path,
    *,
    input_text: str,
    command: str,
    domain: str,
    confidence: float,
    reason: str,
    routing_source: str = "heuristic",
    executed: bool = True,
    source: str = "cli",
) -> None:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        connection.execute(
            """
            INSERT INTO capture_routing_log
                (input_text, command, domain, confidence, reason, routing_source, executed, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (input_text, command, domain, confidence, reason, routing_source, int(executed), source),
        )


def fetch_recent_capture_logs(database_path: Path, *, limit: int = 20) -> list[dict]:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        cursor = connection.execute(
            """
            SELECT id, logged_at, input_text, command, domain, confidence,
                   reason, routing_source, executed, source
            FROM capture_routing_log
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
