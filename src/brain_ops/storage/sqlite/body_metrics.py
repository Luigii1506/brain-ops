from __future__ import annotations

import sqlite3
from pathlib import Path

from brain_ops.storage.db import connect_sqlite


def ensure_body_metrics_columns(connection: sqlite3.Connection) -> None:
    existing = {row[1] for row in connection.execute("PRAGMA table_info(body_metrics)").fetchall()}
    wanted = {
        "fat_mass_kg": "REAL",
        "muscle_mass_kg": "REAL",
        "visceral_fat": "REAL",
        "bmr_calories": "REAL",
        "arm_cm": "REAL",
        "thigh_cm": "REAL",
        "calf_cm": "REAL",
    }
    for column, column_type in wanted.items():
        if column not in existing:
            connection.execute(f"ALTER TABLE body_metrics ADD COLUMN {column} {column_type}")


def ensure_body_metrics_schema(database_path: Path) -> None:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        ensure_body_metrics_columns(connection)


def insert_body_metrics_log(
    database_path: Path,
    *,
    logged_at: str,
    weight_kg: float | None,
    body_fat_pct: float | None,
    fat_mass_kg: float | None,
    muscle_mass_kg: float | None,
    visceral_fat: float | None,
    bmr_calories: float | None,
    arm_cm: float | None,
    waist_cm: float | None,
    thigh_cm: float | None,
    calf_cm: float | None,
    note: str | None,
) -> None:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        ensure_body_metrics_columns(connection)
        connection.execute(
            """
            INSERT INTO body_metrics (
                logged_at, weight_kg, body_fat_pct, fat_mass_kg, muscle_mass_kg,
                visceral_fat, bmr_calories, arm_cm, waist_cm, thigh_cm, calf_cm, note, source
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                logged_at,
                weight_kg,
                body_fat_pct,
                fat_mass_kg,
                muscle_mass_kg,
                visceral_fat,
                bmr_calories,
                arm_cm,
                waist_cm,
                thigh_cm,
                calf_cm,
                note,
                "chat",
            ),
        )


def fetch_body_metrics_status_rows(
    database_path: Path,
    *,
    start: str,
    end: str,
) -> tuple[tuple[int] | None, tuple[object, ...] | None]:
    target = database_path.expanduser()
    with connect_sqlite(target) as connection:
        ensure_body_metrics_columns(connection)
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
            SELECT
                logged_at, weight_kg, body_fat_pct, fat_mass_kg, muscle_mass_kg,
                visceral_fat, bmr_calories, arm_cm, waist_cm, thigh_cm, calf_cm
            FROM body_metrics
            WHERE logged_at BETWEEN ? AND ?
            ORDER BY logged_at DESC
            LIMIT 1
            """,
            (start, end),
        ).fetchone()
    return count_row, latest_row
