from __future__ import annotations

from pathlib import Path

from brain_ops.storage.db import connect_sqlite


def insert_expense(
    database_path: Path,
    *,
    logged_at_iso: str,
    amount: float,
    currency: str,
    category: str | None,
    merchant: str | None,
    note: str | None,
    source: str = "chat",
) -> None:
    target = database_path.expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    with connect_sqlite(target) as connection:
        connection.execute(
            """
            INSERT INTO expenses (logged_at, amount, currency, category, merchant, note, source)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                logged_at_iso,
                amount,
                currency,
                category,
                merchant,
                note,
                source,
            ),
        )


def fetch_expense_category_totals(
    database_path: Path,
    *,
    start: str,
    end: str,
    currency: str,
) -> list[tuple[str, float]]:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        rows = connection.execute(
            """
            SELECT COALESCE(category, 'uncategorized'), COALESCE(SUM(amount), 0)
            FROM expenses
            WHERE logged_at BETWEEN ? AND ? AND currency = ?
            GROUP BY COALESCE(category, 'uncategorized')
            ORDER BY COALESCE(SUM(amount), 0) DESC, COALESCE(category, 'uncategorized')
            """,
            (start, end, currency),
        ).fetchall()
    return [(category, float(total or 0)) for category, total in rows]


def fetch_expense_summary_header(
    database_path: Path,
    *,
    start: str,
    end: str,
    currency: str,
) -> tuple[int, float]:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        row = connection.execute(
            """
            SELECT COUNT(*), COALESCE(SUM(amount), 0)
            FROM expenses
            WHERE logged_at BETWEEN ? AND ? AND currency = ?
            """,
            (start, end, currency),
        ).fetchone()
    return int(row[0] or 0), float(row[1] or 0)
