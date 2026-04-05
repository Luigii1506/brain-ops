from __future__ import annotations

from brain_ops.domains.personal.nutrition.meal_parsing import parse_meal_items
from brain_ops.errors import ConfigError
from brain_ops.models import DietPlanMeal, DietPlanMealItem


class ParsedDietMeal:
    def __init__(self, *, meal_type: str, label: str, items: list[DietPlanMealItem], note: str | None, sort_order: int):
        self.meal_type = meal_type
        self.label = label
        self.items = items
        self.note = note
        self.sort_order = sort_order

    def to_model(self) -> DietPlanMeal:
        return DietPlanMeal(
            meal_type=self.meal_type,
            label=self.label,
            items=self.items,
            calories_target=sum(float(item.calories or 0) for item in self.items),
            protein_g_target=sum(float(item.protein_g or 0) for item in self.items),
            carbs_g_target=sum(float(item.carbs_g or 0) for item in self.items),
            fat_g_target=sum(float(item.fat_g or 0) for item in self.items),
        )


def normalize_diet_plan_name(name: str) -> str:
    normalized_name = name.strip()
    if not normalized_name:
        raise ConfigError("Diet plan name cannot be empty.")
    return normalized_name


def parse_diet_plan_meals(meals: list[str]) -> list[ParsedDietMeal]:
    parsed_meals = [parse_diet_meal_spec(meal, index) for index, meal in enumerate(meals, start=1)]
    if not parsed_meals:
        raise ConfigError("At least one --meal entry is required.")
    return parsed_meals


def normalize_diet_meal_update_inputs(*, meal_type: str, items_text: str, mode: str) -> dict[str, str]:
    normalized_meal_type = meal_type.strip().lower()
    normalized_mode = mode.strip().lower()
    if normalized_mode not in {"replace", "append"}:
        raise ConfigError("Diet meal update mode must be `replace` or `append`.")
    if not items_text.strip():
        raise ConfigError("Diet meal items cannot be empty.")
    return {
        "meal_type": normalized_meal_type,
        "items_text": items_text,
        "mode": normalized_mode,
    }


def parse_diet_update_items(items_text: str) -> list[DietPlanMealItem]:
    parsed_items = [
        DietPlanMealItem(
            food_name=item.food_name,
            grams=item.grams,
            quantity=item.quantity,
            calories=item.calories,
            protein_g=item.protein_g,
            carbs_g=item.carbs_g,
            fat_g=item.fat_g,
        )
        for item in parse_meal_items(items_text)
    ]
    if not parsed_items:
        raise ConfigError("No meal items could be parsed for the diet update.")
    return parsed_items


def parse_diet_meal_spec(spec: str, sort_order: int) -> ParsedDietMeal:
    raw_parts = [part.strip() for part in spec.split("|")]
    if len(raw_parts) == 2:
        meal_type, items_text = raw_parts
        label = meal_type
    elif len(raw_parts) == 3:
        meal_type, label, items_text = raw_parts
    else:
        raise ConfigError(
            "Diet meal spec must look like 'meal_type|items' or 'meal_type|label|items'."
        )
    if not meal_type or not items_text:
        raise ConfigError("Diet meal spec is missing meal_type or items.")
    items = [
        DietPlanMealItem(
            food_name=item.food_name,
            grams=item.grams,
            quantity=item.quantity,
            calories=item.calories,
            protein_g=item.protein_g,
            carbs_g=item.carbs_g,
            fat_g=item.fat_g,
        )
        for item in parse_meal_items(items_text)
    ]
    return ParsedDietMeal(
        meal_type=meal_type.strip(),
        label=label.strip() or meal_type.strip(),
        items=items,
        note=None,
        sort_order=sort_order,
    )
