"""API routes for personal life-ops data."""

from __future__ import annotations

import sqlite3
from datetime import date

from fastapi import APIRouter, HTTPException

from .dependencies import resolve_database_path

router = APIRouter()


def _query_db(query: str, params: tuple = ()) -> list[dict]:
    db_path = resolve_database_path()
    if not db_path.exists():
        return []
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()


@router.get("/meals")
def list_meals(date_str: str | None = None, limit: int = 50):
    """List meals, optionally filtered by date."""
    if date_str:
        rows = _query_db(
            "SELECT * FROM meals WHERE DATE(logged_at) = ? ORDER BY logged_at DESC LIMIT ?",
            (date_str, limit),
        )
    else:
        rows = _query_db("SELECT * FROM meals ORDER BY logged_at DESC LIMIT ?", (limit,))
    return rows


@router.get("/meals/{meal_id}/items")
def get_meal_items(meal_id: int):
    """Get items for a specific meal."""
    return _query_db("SELECT * FROM meal_items WHERE meal_id = ?", (meal_id,))


@router.get("/expenses")
def list_expenses(date_str: str | None = None, limit: int = 50):
    """List expenses, optionally filtered by date."""
    if date_str:
        rows = _query_db(
            "SELECT * FROM expenses WHERE DATE(logged_at) = ? ORDER BY logged_at DESC LIMIT ?",
            (date_str, limit),
        )
    else:
        rows = _query_db("SELECT * FROM expenses ORDER BY logged_at DESC LIMIT ?", (limit,))
    return rows


@router.get("/workouts")
def list_workouts(date_str: str | None = None, limit: int = 50):
    """List workouts, optionally filtered by date."""
    if date_str:
        rows = _query_db(
            "SELECT * FROM workouts WHERE DATE(logged_at) = ? ORDER BY logged_at DESC LIMIT ?",
            (date_str, limit),
        )
    else:
        rows = _query_db("SELECT * FROM workouts ORDER BY logged_at DESC LIMIT ?", (limit,))
    return rows


@router.get("/body-metrics")
def list_body_metrics(limit: int = 30):
    """List recent body metrics."""
    return _query_db("SELECT * FROM body_metrics ORDER BY logged_at DESC LIMIT ?", (limit,))


@router.get("/habits")
def list_habits(date_str: str | None = None, limit: int = 50):
    """List habit check-ins, optionally filtered by date."""
    if date_str:
        rows = _query_db(
            "SELECT * FROM habits WHERE DATE(logged_at) = ? ORDER BY logged_at DESC LIMIT ?",
            (date_str, limit),
        )
    else:
        rows = _query_db("SELECT * FROM habits ORDER BY logged_at DESC LIMIT ?", (limit,))
    return rows


@router.get("/supplements")
def list_supplements(date_str: str | None = None, limit: int = 50):
    """List supplement logs, optionally filtered by date."""
    if date_str:
        rows = _query_db(
            "SELECT * FROM supplements WHERE DATE(logged_at) = ? ORDER BY logged_at DESC LIMIT ?",
            (date_str, limit),
        )
    else:
        rows = _query_db("SELECT * FROM supplements ORDER BY logged_at DESC LIMIT ?", (limit,))
    return rows
