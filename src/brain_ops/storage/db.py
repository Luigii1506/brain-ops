from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from brain_ops.errors import ConfigError
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
        fat_mass_kg REAL,
        muscle_mass_kg REAL,
        visceral_fat REAL,
        bmr_calories REAL,
        arm_cm REAL,
        waist_cm REAL,
        thigh_cm REAL,
        calf_cm REAL,
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
    """
    CREATE TABLE IF NOT EXISTS supplements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        logged_at TEXT NOT NULL,
        supplement_name TEXT NOT NULL,
        amount REAL,
        unit TEXT,
        note TEXT,
        source TEXT DEFAULT 'chat'
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS habits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        checked_at TEXT NOT NULL,
        habit_name TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'done',
        note TEXT,
        source TEXT DEFAULT 'chat'
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS macro_targets (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        calories REAL,
        protein_g REAL,
        carbs_g REAL,
        fat_g REAL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS budget_targets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        period TEXT NOT NULL,
        category TEXT,
        amount REAL NOT NULL,
        currency TEXT DEFAULT 'MXN',
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS habit_targets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        habit_name TEXT NOT NULL,
        period TEXT NOT NULL,
        target_count INTEGER NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(habit_name, period)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS diet_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        notes TEXT,
        status TEXT NOT NULL DEFAULT 'inactive',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        activated_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS diet_plan_meals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plan_id INTEGER NOT NULL,
        meal_type TEXT NOT NULL,
        label TEXT NOT NULL,
        sort_order INTEGER NOT NULL DEFAULT 0,
        note TEXT,
        FOREIGN KEY(plan_id) REFERENCES diet_plans(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS diet_plan_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plan_meal_id INTEGER NOT NULL,
        food_name TEXT NOT NULL,
        grams REAL,
        quantity REAL,
        calories REAL,
        protein_g REAL,
        carbs_g REAL,
        fat_g REAL,
        note TEXT,
        FOREIGN KEY(plan_meal_id) REFERENCES diet_plan_meals(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS conversation_followups (
        session_id TEXT PRIMARY KEY,
        followup_type TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS project_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        logged_at TEXT NOT NULL DEFAULT (datetime('now')),
        project_name TEXT NOT NULL,
        entry_type TEXT NOT NULL DEFAULT 'update',
        entry_text TEXT NOT NULL,
        source TEXT NOT NULL DEFAULT 'cli'
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS capture_routing_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        logged_at TEXT NOT NULL DEFAULT (datetime('now')),
        input_text TEXT NOT NULL,
        command TEXT NOT NULL,
        domain TEXT NOT NULL,
        confidence REAL NOT NULL,
        reason TEXT NOT NULL,
        routing_source TEXT NOT NULL DEFAULT 'heuristic',
        executed INTEGER NOT NULL DEFAULT 1,
        source TEXT NOT NULL DEFAULT 'cli'
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
        completed_at TEXT,
        project TEXT,
        title TEXT NOT NULL,
        priority TEXT NOT NULL DEFAULT 'medium',
        status TEXT NOT NULL DEFAULT 'pending',
        due_date TEXT,
        focus_date TEXT,
        tags_json TEXT,
        note TEXT,
        source TEXT NOT NULL DEFAULT 'cli',
        origin_text TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS entity_mastery (
        entity_name TEXT PRIMARY KEY,
        mastery_level INTEGER NOT NULL DEFAULT 0,
        last_reviewed TEXT,
        next_review TEXT,
        times_reviewed INTEGER NOT NULL DEFAULT 0,
        avg_difficulty REAL NOT NULL DEFAULT 3.0,
        notes TEXT
    )
    """,
]


@contextmanager
def connect_sqlite(database_path: Path):
    connection = sqlite3.connect(database_path.expanduser())
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def resolve_database_path(database_path: Path) -> Path:
    return database_path.expanduser()


def ensure_database_parent(database_path: Path) -> Path:
    target = resolve_database_path(database_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def require_database_file(database_path: Path) -> Path:
    target = resolve_database_path(database_path)
    if not target.exists():
        raise ConfigError(f"Database file not found: {target}")
    return target


def initialize_database(database_path: Path, dry_run: bool = False) -> list[OperationRecord]:
    target = resolve_database_path(database_path)
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

    ensure_database_parent(target)
    with connect_sqlite(target) as connection:
        cursor = connection.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            for statement in SCHEMA_STATEMENTS:
                cursor.execute(statement)
            _ensure_body_metrics_columns(connection)
            connection.commit()
        finally:
            cursor.close()

    return [
        OperationRecord(
            action="init-db",
            path=target,
            detail="initialized sqlite database and core tables",
            status=OperationStatus.UPDATED if existed_before else OperationStatus.CREATED,
        )
    ]


def _ensure_body_metrics_columns(connection: sqlite3.Connection) -> None:
    cursor = connection.cursor()
    try:
        cursor.execute("PRAGMA table_info(body_metrics)")
        rows = cursor.fetchall()
        existing = {row[1] for row in rows}
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
                cursor.execute(f"ALTER TABLE body_metrics ADD COLUMN {column} {column_type}")
    finally:
        cursor.close()
