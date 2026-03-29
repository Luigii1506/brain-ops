from __future__ import annotations

import sqlite3
from pathlib import Path

from brain_ops.models import OperationRecord, OperationStatus

SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS meals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        logged_at TEXT NOT NULL,
        meal_type TEXT,
        note TEXT,
        source TEXT DEFAULT 'chat'
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS meal_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meal_id INTEGER NOT NULL,
        food_name TEXT NOT NULL,
        grams REAL,
        quantity REAL,
        calories REAL,
        protein_g REAL,
        carbs_g REAL,
        fat_g REAL,
        note TEXT,
        FOREIGN KEY(meal_id) REFERENCES meals(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS workouts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        logged_at TEXT NOT NULL,
        routine_name TEXT,
        duration_minutes INTEGER,
        note TEXT,
        source TEXT DEFAULT 'chat'
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS workout_sets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workout_id INTEGER NOT NULL,
        exercise_name TEXT NOT NULL,
        set_index INTEGER,
        reps INTEGER,
        weight_kg REAL,
        duration_seconds INTEGER,
        distance_m REAL,
        note TEXT,
        FOREIGN KEY(workout_id) REFERENCES workouts(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        logged_at TEXT NOT NULL,
        amount REAL NOT NULL,
        currency TEXT DEFAULT 'MXN',
        category TEXT,
        merchant TEXT,
        note TEXT,
        source TEXT DEFAULT 'chat'
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS body_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        logged_at TEXT NOT NULL,
        weight_kg REAL,
        body_fat_pct REAL,
        waist_cm REAL,
        note TEXT,
        source TEXT DEFAULT 'chat'
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS daily_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        logged_at TEXT NOT NULL,
        domain TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        source TEXT DEFAULT 'chat'
    )
    """,
]


def initialize_database(database_path: Path, dry_run: bool = False) -> list[OperationRecord]:
    target = database_path.expanduser()
    existed_before = target.exists()
    if dry_run:
        return [
            OperationRecord(
                action="init-db",
                path=target,
                detail="would initialize sqlite database and core tables",
                status=OperationStatus.SKIPPED,
            )
        ]

    target.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(target) as connection:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)
        connection.commit()

    return [
        OperationRecord(
            action="init-db",
            path=target,
            detail="initialized sqlite database and core tables",
            status=OperationStatus.UPDATED if existed_before else OperationStatus.CREATED,
        )
    ]
