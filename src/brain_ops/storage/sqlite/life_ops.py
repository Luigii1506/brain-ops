from __future__ import annotations

from pathlib import Path

from brain_ops.storage.db import connect_sqlite


def insert_supplement_log(
    database_path: Path,
    *,
    logged_at: str,
    supplement_name: str,
    amount: float | None,
    unit: str | None,
    note: str | None,
    source: str,
) -> None:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        connection.execute(
            """
            INSERT INTO supplements (logged_at, supplement_name, amount, unit, note, source)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (logged_at, supplement_name, amount, unit, note, source),
        )


def insert_habit_checkin(
    database_path: Path,
    *,
    checked_at: str,
    habit_name: str,
    status: str,
    note: str | None,
    source: str,
) -> None:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        connection.execute(
            """
            INSERT INTO habits (checked_at, habit_name, status, note, source)
            VALUES (?, ?, ?, ?, ?)
            """,
            (checked_at, habit_name, status, note, source),
        )


def fetch_daily_habit_rows(
    database_path: Path,
    *,
    start: str,
    end: str,
) -> list[tuple[str, str, int]]:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        return connection.execute(
            """
            SELECT habit_name, status, COUNT(*)
            FROM habits
            WHERE checked_at BETWEEN ? AND ?
            GROUP BY habit_name, status
            ORDER BY habit_name, status
            """,
            (start, end),
        ).fetchall()
