from __future__ import annotations

from pathlib import Path

from brain_ops.storage.db import connect_sqlite


def upsert_follow_up(
    database_path: Path,
    *,
    session_id: str,
    followup_type: str,
    payload_json: str,
    updated_at: str,
) -> None:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        _ensure_followup_table(connection)
        connection.execute(
            """
            INSERT INTO conversation_followups (session_id, followup_type, payload_json, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                followup_type = excluded.followup_type,
                payload_json = excluded.payload_json,
                updated_at = excluded.updated_at
            """,
            (session_id, followup_type, payload_json, updated_at),
        )
        connection.commit()


def fetch_follow_up_payload(database_path: Path, *, session_id: str) -> str | None:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        _ensure_followup_table(connection)
        row = connection.execute(
            "SELECT payload_json FROM conversation_followups WHERE session_id = ?",
            (session_id,),
        ).fetchone()
    if not row:
        return None
    return str(row[0])


def delete_follow_up(database_path: Path, *, session_id: str) -> None:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        _ensure_followup_table(connection)
        connection.execute("DELETE FROM conversation_followups WHERE session_id = ?", (session_id,))
        connection.commit()


def _ensure_followup_table(connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS conversation_followups (
            session_id TEXT PRIMARY KEY,
            followup_type TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
