"""API routes for personal life-ops data."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from brain_ops.services.expenses_service import log_expense, spending_summary
from brain_ops.services.goals_service import budget_status, set_budget_target
from brain_ops.services.daily_status_service import daily_status
from brain_ops.services.personal_review_service import (
    daily_review as build_daily_review,
    weekly_review as build_weekly_review,
)
from brain_ops.storage.sqlite.expenses import (
    delete_expense,
    fetch_distinct_expense_categories,
    fetch_distinct_expense_merchants,
)
from brain_ops.storage.sqlite.tasks import (
    complete_task,
    count_tasks_by_status,
    fetch_task_by_id,
    fetch_tasks,
    insert_task,
    update_task,
)

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


def _normalize_task(task: dict | None) -> dict | None:
    if task is None:
        return None
    normalized = dict(task)
    tags_json = normalized.pop("tags_json", None)
    if isinstance(tags_json, str) and tags_json.strip():
        try:
            normalized["tags"] = json.loads(tags_json)
        except json.JSONDecodeError:
            normalized["tags"] = []
    else:
        normalized["tags"] = []
    return normalized


class CreateTaskRequest(BaseModel):
    title: str
    project: str | None = None
    priority: str = "medium"
    due_date: str | None = None
    focus_date: str | None = None
    tags: list[str] = Field(default_factory=list)
    note: str | None = None
    origin_text: str | None = None


class UpdateTaskRequest(BaseModel):
    priority: str | None = None
    status: str | None = None
    due_date: str | None = None
    focus_date: str | None = None
    note: str | None = None
    project: str | None = None


class CreateExpenseRequest(BaseModel):
    amount: float
    category: str | None = None
    merchant: str | None = None
    currency: str = "MXN"
    note: str | None = None
    logged_at: str | None = None


class BudgetTargetRequest(BaseModel):
    amount: float
    period: str = "weekly"
    category: str | None = None
    currency: str = "MXN"


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


@router.get("/expenses/meta")
def get_expenses_meta():
    """Return categories, merchants, currencies and periods for expense forms."""
    db_path = resolve_database_path()
    categories = ["general", "comida", "transporte", "salud", "trabajo"]
    merchants: list[str] = []
    if db_path.exists():
        try:
            categories = sorted(
                {*(categories), *fetch_distinct_expense_categories(db_path)},
                key=str.lower,
            )
            merchants = fetch_distinct_expense_merchants(db_path)
        except sqlite3.OperationalError:
            pass
    return {
        "categories": categories,
        "merchants": merchants,
        "currencies": ["MXN", "USD"],
        "periods": ["daily", "weekly", "monthly"],
    }


@router.post("/expenses")
def create_expense(body: CreateExpenseRequest):
    """Create an expense record."""
    try:
        result = log_expense(
            resolve_database_path(),
            body.amount,
            category=body.category,
            merchant=body.merchant,
            currency=body.currency,
            note=body.note,
            logged_at=datetime.fromisoformat(body.logged_at) if body.logged_at else None,
            dry_run=False,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    rows = _query_db("SELECT * FROM expenses ORDER BY id DESC LIMIT 1")
    latest = rows[0] if rows else None
    return {
        "result": result.model_dump(mode="json"),
        "expense": latest,
    }


@router.delete("/expenses/{expense_id}")
def remove_expense(expense_id: int):
    """Delete an expense."""
    deleted = delete_expense(resolve_database_path(), expense_id=expense_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Expense '{expense_id}' not found.")
    return {"deleted": expense_id}


@router.get("/spending-summary")
def get_spending_summary(date_str: str | None = None, currency: str = "MXN"):
    """Return spending summary for a given date."""
    try:
        summary = spending_summary(resolve_database_path(), date_text=date_str, currency=currency)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return summary.model_dump(mode="json")


@router.get("/budget-status")
def get_budget_status(period: str = "weekly", date_str: str | None = None):
    """Return budget status for a period."""
    try:
        summary = budget_status(resolve_database_path(), period=period, date_text=date_str)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return summary.model_dump(mode="json")


@router.post("/budget-target")
def create_budget_target(body: BudgetTargetRequest):
    """Create or replace a budget target."""
    try:
        result = set_budget_target(
            resolve_database_path(),
            amount=body.amount,
            period=body.period,
            category=body.category,
            currency=body.currency,
            dry_run=False,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump(mode="json")


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
            "SELECT * FROM habits WHERE DATE(checked_at) = ? ORDER BY checked_at DESC LIMIT ?",
            (date_str, limit),
        )
    else:
        rows = _query_db("SELECT * FROM habits ORDER BY checked_at DESC LIMIT ?", (limit,))
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


@router.get("/daily-status")
def get_daily_status(date_str: str | None = None):
    """Return the current daily status summary."""
    result = daily_status(resolve_database_path(), date_text=date_str)
    return result.model_dump(mode="json")


@router.get("/daily-review")
def get_daily_review(date_str: str | None = None):
    """Return the computed daily review."""
    return build_daily_review(resolve_database_path(), date_text=date_str).to_dict()


@router.get("/week-review")
def get_week_review(date_str: str | None = None):
    """Return the aggregated weekly review."""
    return build_weekly_review(resolve_database_path(), date_text=date_str).to_dict()


@router.get("/tasks")
def list_tasks(
    project: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    due_soon_days: int | None = None,
    focus_today: bool = False,
    limit: int = 50,
):
    """List tasks with optional filters."""
    tasks = fetch_tasks(
        resolve_database_path(),
        project=project,
        status=status,
        priority=priority,
        due_soon_days=due_soon_days,
        focus_today=focus_today,
        limit=limit,
    )
    return {
        "items": [_normalize_task(task) for task in tasks],
        "counts": count_tasks_by_status(resolve_database_path(), project=project if project != "personal" else None),
    }


@router.get("/tasks/{task_id}")
def get_task(task_id: int):
    """Get a single task."""
    task = _normalize_task(fetch_task_by_id(resolve_database_path(), task_id))
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return task


@router.post("/tasks")
def create_task(body: CreateTaskRequest):
    """Create a new task."""
    task_id = insert_task(
        resolve_database_path(),
        body.title,
        project=body.project,
        priority=body.priority,
        due_date=body.due_date,
        focus_date=body.focus_date,
        tags=body.tags,
        note=body.note,
        source="api",
        origin_text=body.origin_text,
    )
    task = _normalize_task(fetch_task_by_id(resolve_database_path(), task_id))
    if task is None:
        raise HTTPException(status_code=500, detail="Task created but could not be reloaded.")
    return task


@router.patch("/tasks/{task_id}")
def patch_task(task_id: int, body: UpdateTaskRequest):
    """Update an existing task."""
    updated = update_task(
        resolve_database_path(),
        task_id,
        priority=body.priority,
        status=body.status,
        due_date=body.due_date,
        focus_date=body.focus_date,
        note=body.note,
        project=body.project,
    )
    if not updated:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found or no fields changed.")
    task = _normalize_task(fetch_task_by_id(resolve_database_path(), task_id))
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return task


@router.post("/tasks/{task_id}/done")
def mark_task_done(task_id: int):
    """Mark a task as done."""
    updated = complete_task(resolve_database_path(), task_id)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    task = _normalize_task(fetch_task_by_id(resolve_database_path(), task_id))
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return task
