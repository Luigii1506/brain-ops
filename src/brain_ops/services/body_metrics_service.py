from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from brain_ops.errors import ConfigError
from brain_ops.models import BodyMetricsLogResult, BodyMetricsSummary, OperationRecord, OperationStatus


def log_body_metrics(
    database_path: Path,
    *,
    weight_kg: float | None = None,
    body_fat_pct: float | None = None,
    waist_cm: float | None = None,
    note: str | None = None,
    logged_at: datetime | None = None,
    dry_run: bool = False,
) -> BodyMetricsLogResult:
    if weight_kg is None and body_fat_pct is None and waist_cm is None:
        raise ConfigError("At least one body metric must be provided.")
    if weight_kg is not None and weight_kg <= 0:
        raise ConfigError("Weight must be greater than zero.")
    if body_fat_pct is not None and not 0 <= body_fat_pct <= 100:
        raise ConfigError("Body fat percentage must be between 0 and 100.")
    if waist_cm is not None and waist_cm <= 0:
        raise ConfigError("Waist must be greater than zero.")

    logged_at = logged_at or datetime.now()
    target = database_path.expanduser()
    if not dry_run:
        target.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(target) as connection:
            connection.execute(
                """
                INSERT INTO body_metrics (logged_at, weight_kg, body_fat_pct, waist_cm, note, source)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    logged_at.isoformat(timespec="seconds"),
                    weight_kg,
                    body_fat_pct,
                    waist_cm,
                    note,
                    "chat",
                ),
            )
            connection.commit()

    pieces = []
    if weight_kg is not None:
        pieces.append(f"weight={weight_kg:g}kg")
    if body_fat_pct is not None:
        pieces.append(f"body_fat={body_fat_pct:g}%")
    if waist_cm is not None:
        pieces.append(f"waist={waist_cm:g}cm")
    operation = OperationRecord(
        action="insert",
        path=target,
        detail=f"logged body metrics ({', '.join(pieces)})",
        status=OperationStatus.CREATED,
    )
    return BodyMetricsLogResult(
        logged_at=logged_at,
        weight_kg=weight_kg,
        body_fat_pct=body_fat_pct,
        waist_cm=waist_cm,
        operations=[operation],
        reason="Logged body metrics into SQLite.",
    )


def body_metrics_status(database_path: Path, date_text: str | None = None) -> BodyMetricsSummary:
    target = database_path.expanduser()
    if not target.exists():
        raise ConfigError(f"Database file not found: {target}")

    resolved_date = _resolve_date(date_text)
    start = f"{resolved_date}T00:00:00"
    end = f"{resolved_date}T23:59:59"

    with sqlite3.connect(target) as connection:
        count_row = connection.execute(
            """
            SELECT COUNT(*)
            FROM body_metrics
            WHERE logged_at BETWEEN ? AND ?
            """,
            (start, end),
        ).fetchone()
        latest_row = connection.execute(
            """
            SELECT logged_at, weight_kg, body_fat_pct, waist_cm
            FROM body_metrics
            WHERE logged_at BETWEEN ? AND ?
            ORDER BY logged_at DESC
            LIMIT 1
            """,
            (start, end),
        ).fetchone()

    return BodyMetricsSummary(
        date=resolved_date,
        entries_logged=int((count_row or [0])[0] or 0),
        latest_logged_at=latest_row[0] if latest_row else None,
        latest_weight_kg=float(latest_row[1]) if latest_row and latest_row[1] is not None else None,
        latest_body_fat_pct=float(latest_row[2]) if latest_row and latest_row[2] is not None else None,
        latest_waist_cm=float(latest_row[3]) if latest_row and latest_row[3] is not None else None,
        database_path=target,
    )


def _resolve_date(date_text: str | None) -> str:
    if not date_text:
        return datetime.now().date().isoformat()
    try:
        return datetime.fromisoformat(date_text).date().isoformat()
    except ValueError as exc:
        raise ConfigError("Date must be in YYYY-MM-DD format.") from exc
