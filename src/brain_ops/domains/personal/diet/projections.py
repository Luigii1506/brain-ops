from __future__ import annotations

from pathlib import Path

from brain_ops.models import (
    DietActivationResult,
    DietMealProgress,
    DietMealUpdateResult,
    DietPlanMeal,
    DietPlanMealItem,
    DietPlanResult,
    DietPlanSummary,
    DietStatusSummary,
    OperationRecord,
    OperationStatus,
)


def remaining(target: float, actual: float) -> float:
    return target - actual


def build_diet_plan_summary(
    *,
    name: str,
    status: str,
    notes: str | None,
    database_path: Path,
    meal_rows: list[tuple[object, str, str]],
    item_rows_by_meal: dict[int, list[tuple[str, float | None, float | None, float | None, float | None, float | None, float | None]]],
) -> DietPlanSummary:
    meals: list[DietPlanMeal] = []
    totals = {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0}
    for meal_id, meal_type, label in meal_rows:
        item_rows = item_rows_by_meal.get(int(meal_id), [])
        items = [
            DietPlanMealItem(
                food_name=food_name,
                grams=grams,
                quantity=quantity,
                calories=calories,
                protein_g=protein_g,
                carbs_g=carbs_g,
                fat_g=fat_g,
            )
            for food_name, grams, quantity, calories, protein_g, carbs_g, fat_g in item_rows
        ]
        meal = DietPlanMeal(
            meal_type=meal_type,
            label=label,
            items=items,
            calories_target=sum(float(item.calories or 0) for item in items),
            protein_g_target=sum(float(item.protein_g or 0) for item in items),
            carbs_g_target=sum(float(item.carbs_g or 0) for item in items),
            fat_g_target=sum(float(item.fat_g or 0) for item in items),
        )
        totals["calories"] += meal.calories_target
        totals["protein_g"] += meal.protein_g_target
        totals["carbs_g"] += meal.carbs_g_target
        totals["fat_g"] += meal.fat_g_target
        meals.append(meal)

    return DietPlanSummary(
        name=name,
        status=status,
        notes=notes,
        meals=meals,
        calories_target=totals["calories"],
        protein_g_target=totals["protein_g"],
        carbs_g_target=totals["carbs_g"],
        fat_g_target=totals["fat_g"],
        database_path=database_path,
    )


def build_diet_status_summary(
    *,
    date: str,
    database_path: Path,
    plan: DietPlanSummary,
    actual_by_meal: dict[str, dict[str, object]],
    actual_totals: dict[str, float],
) -> DietStatusSummary:
    meals: list[DietMealProgress] = []
    for expected_meal in plan.meals:
        actual = actual_by_meal.get(expected_meal.meal_type.lower(), {})
        meals.append(
            DietMealProgress(
                meal_type=expected_meal.meal_type,
                label=expected_meal.label,
                target_items=[item.food_name for item in expected_meal.items],
                actual_items=list(actual.get("items", [])),
                target_count=len(expected_meal.items),
                actual_count=int(actual.get("item_count", 0)),
                logged=bool(actual.get("logged", False)),
                calories_target=expected_meal.calories_target,
                protein_g_target=expected_meal.protein_g_target,
                carbs_g_target=expected_meal.carbs_g_target,
                fat_g_target=expected_meal.fat_g_target,
                calories_actual=float(actual.get("calories", 0)),
                protein_g_actual=float(actual.get("protein_g", 0)),
                carbs_g_actual=float(actual.get("carbs_g", 0)),
                fat_g_actual=float(actual.get("fat_g", 0)),
            )
        )

    return DietStatusSummary(
        date=date,
        active_diet_name=plan.name,
        notes=plan.notes,
        meals=meals,
        calories_target=plan.calories_target,
        protein_g_target=plan.protein_g_target,
        carbs_g_target=plan.carbs_g_target,
        fat_g_target=plan.fat_g_target,
        calories_actual=actual_totals["calories"],
        protein_g_actual=actual_totals["protein_g"],
        carbs_g_actual=actual_totals["carbs_g"],
        fat_g_actual=actual_totals["fat_g"],
        calories_remaining=remaining(plan.calories_target, actual_totals["calories"]),
        protein_g_remaining=remaining(plan.protein_g_target, actual_totals["protein_g"]),
        carbs_g_remaining=remaining(plan.carbs_g_target, actual_totals["carbs_g"]),
        fat_g_remaining=remaining(plan.fat_g_target, actual_totals["fat_g"]),
        database_path=database_path,
    )


def build_diet_plan_result(
    *,
    database_path: Path,
    name: str,
    status: str,
    meals: list[DietPlanMeal],
) -> DietPlanResult:
    operation = OperationRecord(
        action="create-diet-plan",
        path=database_path,
        detail=f"stored diet plan `{name}` with {len(meals)} meal(s)",
        status=OperationStatus.CREATED,
    )
    return DietPlanResult(
        name=name,
        status=status,
        meals=[meal.model_copy(deep=True) for meal in meals],
        operations=[operation],
        reason="Stored diet plan in SQLite.",
    )


def build_diet_activation_result(
    *,
    database_path: Path,
    name: str,
) -> DietActivationResult:
    operation = OperationRecord(
        action="activate-diet",
        path=database_path,
        detail=f"activated diet plan `{name}`",
        status=OperationStatus.UPDATED,
    )
    return DietActivationResult(
        name=name,
        status="active",
        operations=[operation],
        reason="Set diet plan as active in SQLite.",
    )


def build_diet_meal_update_result(
    *,
    database_path: Path,
    diet_name: str,
    meal_type: str,
    mode: str,
    items: list[DietPlanMealItem],
) -> DietMealUpdateResult:
    operation = OperationRecord(
        action="update-diet-meal",
        path=database_path,
        detail=f"{mode} items for `{meal_type}` in active diet `{diet_name}`",
        status=OperationStatus.UPDATED,
    )
    return DietMealUpdateResult(
        diet_name=diet_name,
        meal_type=meal_type,
        mode=mode,
        items=[item.model_copy(deep=True) for item in items],
        operations=[operation],
        reason="Updated meal items in the active diet plan.",
    )


def build_actual_meal_progress(
    rows: list[tuple[object, object, object, object, object, object]],
) -> tuple[dict[str, dict[str, object]], dict[str, float]]:
    by_meal: dict[str, dict[str, object]] = {}
    totals = {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0}
    for meal_type, food_name, calories, protein_g, carbs_g, fat_g in rows:
        key = str(meal_type or "unspecified").lower()
        bucket = by_meal.setdefault(
            key,
            {
                "logged": True,
                "items": [],
                "item_count": 0,
                "calories": 0.0,
                "protein_g": 0.0,
                "carbs_g": 0.0,
                "fat_g": 0.0,
            },
        )
        bucket["items"].append(food_name)
        bucket["item_count"] += 1
        bucket["calories"] += float(calories or 0)
        bucket["protein_g"] += float(protein_g or 0)
        bucket["carbs_g"] += float(carbs_g or 0)
        bucket["fat_g"] += float(fat_g or 0)
        totals["calories"] += float(calories or 0)
        totals["protein_g"] += float(protein_g or 0)
        totals["carbs_g"] += float(carbs_g or 0)
        totals["fat_g"] += float(fat_g or 0)
    return by_meal, totals
