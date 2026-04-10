"""SQLite storage layer for tasks."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from brain_ops.storage.db import connect_sqlite, require_database_file


def insert_task(
    db_path: Path,
    title: str,
    *,
    project: str | None = None,
    priority: str = "medium",
    due_date: str | None = None,
    focus_date: str | None = None,
    tags: list[str] | None = None,
    note: str | None = None,
    source: str = "cli",
    origin_text: str | None = None,
) -> int:
    """Insert a task and return its ID."""
    target = require_database_file(db_path)
    tags_json = json.dumps(tags) if tags else None
    with connect_sqlite(target) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO tasks (title, project, priority, due_date, focus_date,
               tags_json, note, source, origin_text)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (title, project, priority, due_date, focus_date, tags_json, note, source, origin_text),
        )
        return cursor.lastrowid or 0


def update_task(
    db_path: Path,
    task_id: int,
    *,
    priority: str | None = None,
    status: str | None = None,
    due_date: str | None = None,
    focus_date: str | None = None,
    note: str | None = None,
    project: str | None = None,
) -> bool:
    """Update task fields. Returns True if a row was updated."""
    target = require_database_file(db_path)
    updates: list[str] = []
    values: list[object] = []

    if priority is not None:
        updates.append("priority = ?")
        values.append(priority)
    if status is not None:
        updates.append("status = ?")
        values.append(status)
        if status == "done":
            updates.append("completed_at = ?")
            values.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    if due_date is not None:
        updates.append("due_date = ?")
        values.append(due_date)
    if focus_date is not None:
        updates.append("focus_date = ?")
        values.append(focus_date)
    if note is not None:
        updates.append("note = ?")
        values.append(note)
    if project is not None:
        updates.append("project = ?")
        values.append(project)

    if not updates:
        return False

    updates.append("updated_at = ?")
    values.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    values.append(task_id)

    with connect_sqlite(target) as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?",
            values,
        )
        return cursor.rowcount > 0


def complete_task(db_path: Path, task_id: int) -> bool:
    """Mark a task as done with completed_at timestamp."""
    return update_task(db_path, task_id, status="done")


def fetch_tasks(
    db_path: Path,
    *,
    project: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    due_soon_days: int | None = None,
    focus_today: bool = False,
    limit: int = 50,
) -> list[dict]:
    """Fetch tasks with optional filters."""
    target = require_database_file(db_path)
    conditions: list[str] = []
    values: list[object] = []

    if project is not None:
        if project == "personal":
            conditions.append("project IS NULL")
        else:
            conditions.append("project = ?")
            values.append(project)
    if status is not None:
        conditions.append("status = ?")
        values.append(status)
    else:
        # Default: exclude done and cancelled
        conditions.append("status IN ('pending', 'active')")
    if priority is not None:
        conditions.append("priority = ?")
        values.append(priority)
    if due_soon_days is not None:
        conditions.append("due_date IS NOT NULL AND due_date <= date('now', 'localtime', ?)")
        values.append(f"+{due_soon_days} days")
    if focus_today:
        conditions.append("focus_date IS NOT NULL AND focus_date <= date('now', 'localtime')")

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    values.append(limit)

    with connect_sqlite(target) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            f"""SELECT id, created_at, updated_at, completed_at, project, title,
                       priority, status, due_date, focus_date, tags_json, note, source
                FROM tasks {where}
                ORDER BY
                    CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
                    due_date ASC NULLS LAST,
                    created_at DESC
                LIMIT ?""",
            values,
        )
        return [dict(row) for row in cursor.fetchall()]


def fetch_task_by_id(db_path: Path, task_id: int) -> dict | None:
    """Fetch a single task by ID."""
    target = require_database_file(db_path)
    with connect_sqlite(target) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def count_tasks_by_status(db_path: Path, project: str | None = None) -> dict[str, int]:
    """Count tasks grouped by status."""
    target = require_database_file(db_path)
    with connect_sqlite(target) as conn:
        cursor = conn.cursor()
        if project:
            if project == "personal":
                cursor.execute(
                    "SELECT status, COUNT(*) FROM tasks WHERE project IS NULL GROUP BY status",
                )
            else:
                cursor.execute(
                    "SELECT status, COUNT(*) FROM tasks WHERE project = ? GROUP BY status",
                    (project,),
                )
        else:
            cursor.execute("SELECT status, COUNT(*) FROM tasks GROUP BY status")
        return {row[0]: row[1] for row in cursor.fetchall()}


__all__ = [
    "complete_task",
    "count_tasks_by_status",
    "fetch_task_by_id",
    "fetch_tasks",
    "insert_task",
    "update_task",
]
