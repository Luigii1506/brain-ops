from __future__ import annotations

import re

from brain_ops.errors import ConfigError
from brain_ops.models import MealItemInput

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


def parse_meal_items(meal_text: str) -> list[MealItemInput]:
    items: list[MealItemInput] = []
    raw_items = [part.strip() for part in ITEM_SPLIT_PATTERN.split(meal_text.strip()) if part.strip()]
    for raw_item in raw_items:
        items.append(_parse_meal_item(raw_item))
    return items


def normalize_meal_log_input(meal_text: str) -> tuple[str, list[MealItemInput]]:
    normalized_text = meal_text.strip()
    if not normalized_text:
        raise ConfigError("Meal text cannot be empty.")
    items = parse_meal_items(normalized_text)
    if not items:
        raise ConfigError("No meal items could be parsed.")
    return normalized_text, items


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
