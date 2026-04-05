from __future__ import annotations

from pathlib import Path

from brain_ops.storage.db import connect_sqlite


def fetch_daily_status_supplement_names(
    database_path: Path,
    *,
    start: str,
    end: str,
) -> list[str]:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        rows = connection.execute(
            """
            SELECT supplement_name
            FROM supplements
            WHERE logged_at BETWEEN ? AND ?
            ORDER BY logged_at
            """,
            (start, end),
        ).fetchall()
    return [str(row[0]) for row in rows]


def fetch_daily_status_log_count(
    database_path: Path,
    *,
    start: str,
    end: str,
) -> int:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        row = connection.execute(
            """
            SELECT COUNT(*)
            FROM daily_logs
            WHERE logged_at BETWEEN ? AND ?
            """,
            (start, end),
        ).fetchone()
    return int((row or [0])[0] or 0)


def fetch_daily_status_local_context(
    database_path: Path,
    *,
    start: str,
    end: str,
) -> tuple[list[str], int]:
    supplement_names = fetch_daily_status_supplement_names(database_path, start=start, end=end)
    daily_logs_count = fetch_daily_status_log_count(database_path, start=start, end=end)
    return supplement_names, daily_logs_count
