from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from brain_ops.errors import ConfigError
from brain_ops.models import ExpenseLogResult, OperationRecord, OperationStatus, SpendingSummary


def log_expense(
    database_path: Path,
    amount: float,
    *,
    category: str | None = None,
    merchant: str | None = None,
    currency: str = "MXN",
    note: str | None = None,
    logged_at: datetime | None = None,
    dry_run: bool = False,
) -> ExpenseLogResult:
    if amount <= 0:
        raise ConfigError("Expense amount must be greater than zero.")

    logged_at = logged_at or datetime.now()
    normalized_currency = (currency or "MXN").upper()
    target = database_path.expanduser()
    if not dry_run:
        target.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(target) as connection:
            connection.execute(
                """
                INSERT INTO expenses (logged_at, amount, currency, category, merchant, note, source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    logged_at.isoformat(timespec="seconds"),
                    amount,
                    normalized_currency,
                    category,
                    merchant,
                    note,
                    "chat",
                ),
            )
            connection.commit()

    operation = OperationRecord(
        action="insert",
        path=target,
        detail=f"logged expense {amount:.2f} {normalized_currency}",
        status=OperationStatus.CREATED,
    )
    return ExpenseLogResult(
        logged_at=logged_at,
        amount=amount,
        currency=normalized_currency,
        category=category,
        merchant=merchant,
        operations=[operation],
        reason="Logged expense into SQLite.",
    )


def spending_summary(
    database_path: Path,
    date_text: str | None = None,
    *,
    currency: str = "MXN",
) -> SpendingSummary:
    target = database_path.expanduser()
    if not target.exists():
        raise ConfigError(f"Database file not found: {target}")

    resolved_date = _resolve_date(date_text)
    start = f"{resolved_date}T00:00:00"
    end = f"{resolved_date}T23:59:59"
    normalized_currency = (currency or "MXN").upper()

    with sqlite3.connect(target) as connection:
        header = connection.execute(
            """
            SELECT COUNT(*), COALESCE(SUM(amount), 0)
            FROM expenses
            WHERE logged_at BETWEEN ? AND ? AND currency = ?
            """,
            (start, end, normalized_currency),
        ).fetchone()
        rows = connection.execute(
            """
            SELECT COALESCE(category, 'uncategorized'), COALESCE(SUM(amount), 0)
            FROM expenses
            WHERE logged_at BETWEEN ? AND ? AND currency = ?
            GROUP BY COALESCE(category, 'uncategorized')
            ORDER BY COALESCE(SUM(amount), 0) DESC, COALESCE(category, 'uncategorized')
            """,
            (start, end, normalized_currency),
        ).fetchall()

    by_category = {category: float(total or 0) for category, total in rows}
    return SpendingSummary(
        date=resolved_date,
        total_amount=float(header[1] or 0),
        transaction_count=int(header[0] or 0),
        by_category=by_category,
        currency=normalized_currency,
        database_path=target,
    )


def _resolve_date(date_text: str | None) -> str:
    if not date_text:
        return datetime.now().date().isoformat()
    try:
        return datetime.fromisoformat(date_text).date().isoformat()
    except ValueError as exc:
        raise ConfigError("Date must be in YYYY-MM-DD format.") from exc
