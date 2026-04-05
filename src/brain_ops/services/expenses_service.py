from __future__ import annotations

from datetime import datetime
from pathlib import Path

from brain_ops.core.validation import resolve_iso_date
from brain_ops.domains.personal.tracking import (
    build_expense_log_result,
    build_spending_summary,
    normalize_expense_log_inputs,
)
from brain_ops.models import ExpenseLogResult
from brain_ops.storage.db import ensure_database_parent, require_database_file, resolve_database_path
from brain_ops.storage.sqlite import (
    fetch_expense_category_totals,
    fetch_expense_summary_header,
    insert_expense,
)


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
    normalized = normalize_expense_log_inputs(
        amount=amount,
        category=category,
        merchant=merchant,
        currency=currency,
        note=note,
    )

    logged_at = logged_at or datetime.now()
    target = resolve_database_path(database_path)
    if not dry_run:
        ensure_database_parent(target)
        insert_expense(
            target,
            logged_at_iso=logged_at.isoformat(timespec="seconds"),
            amount=normalized["amount"],
            currency=normalized["currency"],
            category=normalized["category"],
            merchant=normalized["merchant"],
            note=normalized["note"],
            source="chat",
        )
    return build_expense_log_result(
        database_path=target,
        logged_at=logged_at,
        amount=normalized["amount"],
        currency=normalized["currency"],
        category=normalized["category"],
        merchant=normalized["merchant"],
    )


def spending_summary(
    database_path: Path,
    date_text: str | None = None,
    *,
    currency: str = "MXN",
):
    target = require_database_file(database_path)

    resolved_date = resolve_iso_date(date_text)
    start = f"{resolved_date}T00:00:00"
    end = f"{resolved_date}T23:59:59"
    normalized_currency = (currency or "MXN").upper()

    transaction_count, total_amount = fetch_expense_summary_header(
        target,
        start=start,
        end=end,
        currency=normalized_currency,
    )
    rows = fetch_expense_category_totals(
        target,
        start=start,
        end=end,
        currency=normalized_currency,
    )
    return build_spending_summary(
        date=resolved_date,
        database_path=target,
        total_amount=total_amount,
        transaction_count=transaction_count,
        category_rows=rows,
        currency=normalized_currency,
    )
