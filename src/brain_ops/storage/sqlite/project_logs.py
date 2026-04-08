"""SQLite storage adapter for project logs."""

from __future__ import annotations

from pathlib import Path

from brain_ops.storage.db import connect_sqlite


def insert_project_log(
    database_path: Path,
    *,
    project_name: str,
    entry_type: str,
    entry_text: str,
    source: str = "cli",
) -> None:
    target = database_path.expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    with connect_sqlite(target) as connection:
        connection.execute(
            """
            INSERT INTO project_logs (project_name, entry_type, entry_text, source)
            VALUES (?, ?, ?, ?)
            """,
            (project_name, entry_type, entry_text, source),
        )


def fetch_project_logs(
    database_path: Path,
    *,
    project_name: str,
    limit: int = 20,
) -> list[dict]:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        rows = connection.execute(
            """
            SELECT id, logged_at, project_name, entry_type, entry_text, source
            FROM project_logs
            WHERE project_name = ?
            ORDER BY logged_at DESC
            LIMIT ?
            """,
            (project_name, limit),
        ).fetchall()
    return [
        {
            "id": row[0],
            "logged_at": row[1],
            "project_name": row[2],
            "entry_type": row[3],
            "entry_text": row[4],
            "source": row[5],
        }
        for row in rows
    ]


def fetch_recent_project_logs(
    database_path: Path,
    *,
    project_name: str,
    days: int = 7,
) -> list[dict]:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        rows = connection.execute(
            """
            SELECT id, logged_at, project_name, entry_type, entry_text, source
            FROM project_logs
            WHERE project_name = ?
              AND logged_at >= datetime('now', ? || ' days')
            ORDER BY logged_at DESC
            """,
            (project_name, f"-{days}"),
        ).fetchall()
    return [
        {
            "id": row[0],
            "logged_at": row[1],
            "project_name": row[2],
            "entry_type": row[3],
            "entry_text": row[4],
            "source": row[5],
        }
        for row in rows
    ]
