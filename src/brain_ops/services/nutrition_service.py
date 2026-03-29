from __future__ import annotations

import re
import sqlite3
from datetime import datetime
from pathlib import Path

from brain_ops.errors import ConfigError
from brain_ops.models import DailyMacrosSummary, MealItemInput, MealLogResult, OperationRecord, OperationStatus

ITEM_SPLIT_PATTERN = re.compile(r"\s*;\s*")
MACRO_PATTERN = re.compile(r"\b(p|c|f|cal)\s*:\s*(-?\d+(?:\.\d+)?)\b", re.IGNORECASE)
GRAMS_PATTERN = re.compile(r"(?P<value>\d+(?:\.\d+)?)\s*(?:g|gr|gramos?)\b", re.IGNORECASE)
QUANTITY_PATTERN = re.compile(r"^(?P<value>\d+(?:\.\d+)?)\s+(?P<name>.+)$")
LEADING_FILLER_PATTERN = re.compile(
    r"^(?:de|del|la|las|el|los|un|una|unos|unas|algo de|poquito de)\s+",
    re.IGNORECASE,
)
NUMBER_WORDS = {
    "un": 1,
    "una": 1,
    "uno": 1,
    "dos": 2,
    "tres": 3,
    "cuatro": 4,
    "cinco": 5,
    "seis": 6,
    "siete": 7,
    "ocho": 8,
    "nueve": 9,
    "diez": 10,
}


def log_meal(
    database_path: Path,
    meal_text: str,
    *,
    meal_type: str | None = None,
    logged_at: datetime | None = None,
    dry_run: bool = False,
) -> MealLogResult:
    if not meal_text.strip():
        raise ConfigError("Meal text cannot be empty.")

    items = parse_meal_items(meal_text)
    if not items:
        raise ConfigError("No meal items could be parsed.")

    logged_at = logged_at or datetime.now()
    target = database_path.expanduser()
    operations: list[OperationRecord] = []

    if not dry_run:
        target.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(target) as connection:
            connection.execute("PRAGMA foreign_keys=ON")
            cursor = connection.execute(
                "INSERT INTO meals (logged_at, meal_type, note, source) VALUES (?, ?, ?, ?)",
                (logged_at.isoformat(timespec="seconds"), meal_type, meal_text.strip(), "chat"),
            )
            meal_id = int(cursor.lastrowid)
            for item in items:
                connection.execute(
                    """
                    INSERT INTO meal_items (
                        meal_id, food_name, grams, quantity, calories, protein_g, carbs_g, fat_g, note
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        meal_id,
                        item.food_name,
                        item.grams,
                        item.quantity,
                        item.calories,
                        item.protein_g,
                        item.carbs_g,
                        item.fat_g,
                        item.note,
                    ),
                )
            connection.commit()

    operations.append(
        OperationRecord(
            action="insert",
            path=target,
            detail=f"logged meal with {len(items)} item(s)",
            status=OperationStatus.CREATED,
        )
    )
    return MealLogResult(
        logged_at=logged_at,
        meal_type=meal_type,
        items=items,
        operations=operations,
        reason="Logged structured meal data into SQLite.",
    )


def daily_macros(database_path: Path, date_text: str | None = None) -> DailyMacrosSummary:
    target = database_path.expanduser()
    if not target.exists():
        raise ConfigError(f"Database file not found: {target}")

    resolved_date = _resolve_date(date_text)
    date_start = f"{resolved_date}T00:00:00"
    date_end = f"{resolved_date}T23:59:59"

    with sqlite3.connect(target) as connection:
        meals_logged = int(
            connection.execute(
                "SELECT COUNT(*) FROM meals WHERE logged_at BETWEEN ? AND ?",
                (date_start, date_end),
            ).fetchone()[0]
        )
        row = connection.execute(
            """
            SELECT
                COUNT(meal_items.id),
                COALESCE(SUM(meal_items.calories), 0),
                COALESCE(SUM(meal_items.protein_g), 0),
                COALESCE(SUM(meal_items.carbs_g), 0),
                COALESCE(SUM(meal_items.fat_g), 0)
            FROM meals
            LEFT JOIN meal_items ON meal_items.meal_id = meals.id
            WHERE meals.logged_at BETWEEN ? AND ?
            """,
            (date_start, date_end),
        ).fetchone()

    return DailyMacrosSummary(
        date=resolved_date,
        meals_logged=meals_logged,
        items_logged=int(row[0] or 0),
        calories=float(row[1] or 0),
        protein_g=float(row[2] or 0),
        carbs_g=float(row[3] or 0),
        fat_g=float(row[4] or 0),
        database_path=target,
    )


def parse_meal_items(meal_text: str) -> list[MealItemInput]:
    items: list[MealItemInput] = []
    raw_items = [part.strip() for part in ITEM_SPLIT_PATTERN.split(meal_text.strip()) if part.strip()]
    for raw_item in raw_items:
        items.append(_parse_meal_item(raw_item))
    return items


def _parse_meal_item(raw_item: str) -> MealItemInput:
    macros: dict[str, float] = {}
    for metric, value in MACRO_PATTERN.findall(raw_item):
        macros[metric.lower()] = float(value)
    cleaned = MACRO_PATTERN.sub("", raw_item).strip(" ,")

    grams = None
    quantity = None

    grams_match = GRAMS_PATTERN.search(cleaned)
    if grams_match:
        grams = float(grams_match.group("value"))
        cleaned = GRAMS_PATTERN.sub("", cleaned).strip(" ,")

    cleaned, quantity_word = _normalize_quantity_words(cleaned)
    if quantity_word is not None:
        quantity = quantity_word

    quantity_match = QUANTITY_PATTERN.match(cleaned)
    if quantity_match:
        quantity = float(quantity_match.group("value"))
        cleaned = quantity_match.group("name").strip()

    food_name = LEADING_FILLER_PATTERN.sub("", cleaned).strip(" ,")
    if not food_name:
        raise ConfigError(f"Could not parse food name from item: {raw_item}")

    return MealItemInput(
        food_name=food_name,
        grams=grams,
        quantity=quantity,
        calories=macros.get("cal"),
        protein_g=macros.get("p"),
        carbs_g=macros.get("c"),
        fat_g=macros.get("f"),
    )


def _normalize_quantity_words(cleaned: str) -> tuple[str, float | None]:
    parts = cleaned.split(maxsplit=1)
    if not parts:
        return cleaned, None
    first = parts[0].lower()
    if first not in NUMBER_WORDS:
        return cleaned, None
    if len(parts) == 1:
        return cleaned, None
    return f"{NUMBER_WORDS[first]} {parts[1]}", float(NUMBER_WORDS[first])


def _resolve_date(date_text: str | None) -> str:
    if not date_text:
        return datetime.now().date().isoformat()
    try:
        return datetime.fromisoformat(date_text).date().isoformat()
    except ValueError as exc:
        raise ConfigError("Date must be in YYYY-MM-DD format.") from exc
