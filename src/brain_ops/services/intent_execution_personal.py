from __future__ import annotations

from brain_ops.core.execution import IntentExecutionOutcome, build_execution_outcome
from brain_ops.intents import (
    ActiveDietIntent,
    BudgetStatusIntent,
    CreateDietPlanIntent,
    DailyStatusIntent,
    DietStatusIntent,
    HabitStatusIntent,
    IntentModel,
    MacroStatusIntent,
    SetActiveDietIntent,
    SetBudgetTargetIntent,
    SetHabitTargetIntent,
    SetMacroTargetsIntent,
    UpdateDietMealIntent,
)
from brain_ops.services.daily_status_service import daily_status
from brain_ops.services.diet_service import (
    active_diet,
    create_diet_plan,
    diet_status,
    set_active_diet,
    update_active_diet_meal,
)
from brain_ops.services.goals_service import (
    budget_status,
    habit_target_status,
    macro_status,
    set_budget_target,
    set_habit_target,
    set_macro_targets,
)


def execute_personal_intent(
    db_path: object,
    intent: IntentModel,
    *,
    dry_run: bool,
) -> IntentExecutionOutcome | None:
    match intent:
        case SetMacroTargetsIntent():
            result = set_macro_targets(
                db_path,
                calories=intent.calories,
                protein_g=intent.protein_g,
                carbs_g=intent.carbs_g,
                fat_g=intent.fat_g,
                dry_run=dry_run,
            )
            return build_execution_outcome(
                payload=result,
                operations=result.operations,
                normalized_fields={
                    "calories": intent.calories,
                    "protein_g": intent.protein_g,
                    "carbs_g": intent.carbs_g,
                    "fat_g": intent.fat_g,
                },
                reason="Executed macro target intent.",
            )
        case SetBudgetTargetIntent():
            result = set_budget_target(
                db_path,
                amount=intent.amount,
                period=intent.period,
                category=intent.category,
                currency=intent.currency,
                dry_run=dry_run,
            )
            return build_execution_outcome(
                payload=result,
                operations=result.operations,
                normalized_fields={
                    "amount": intent.amount,
                    "period": intent.period,
                    "category": intent.category,
                    "currency": intent.currency,
                },
                reason="Executed budget target intent.",
            )
        case SetHabitTargetIntent():
            result = set_habit_target(
                db_path,
                habit_name=intent.habit_name,
                target_count=intent.target_count,
                period=intent.period,
                dry_run=dry_run,
            )
            return build_execution_outcome(
                payload=result,
                operations=result.operations,
                normalized_fields={
                    "habit_name": intent.habit_name,
                    "target_count": intent.target_count,
                    "period": intent.period,
                },
                reason="Executed habit target intent.",
            )
        case CreateDietPlanIntent():
            result = create_diet_plan(
                db_path,
                name=intent.name,
                meals=intent.meals,
                notes=intent.notes,
                activate=intent.activate,
                dry_run=dry_run,
            )
            return build_execution_outcome(
                payload=result,
                operations=result.operations,
                normalized_fields={
                    "name": intent.name,
                    "meal_count": len(intent.meals),
                    "activate": intent.activate,
                },
                reason="Executed create diet intent.",
            )
        case SetActiveDietIntent():
            result = set_active_diet(db_path, name=intent.name, dry_run=dry_run)
            return build_execution_outcome(
                payload=result,
                operations=result.operations,
                normalized_fields={"name": intent.name},
                reason="Executed set active diet intent.",
            )
        case UpdateDietMealIntent():
            result = update_active_diet_meal(
                db_path,
                meal_type=intent.meal_type,
                items_text=intent.items_text,
                mode=intent.mode,
                dry_run=dry_run,
            )
            return build_execution_outcome(
                payload=result,
                operations=result.operations,
                normalized_fields={
                    "meal_type": intent.meal_type,
                    "items_text": intent.items_text,
                    "mode": intent.mode,
                },
                reason="Executed update diet meal intent.",
            )
        case MacroStatusIntent():
            result = macro_status(db_path, date_text=intent.date)
            return build_execution_outcome(
                payload=result,
                normalized_fields={
                    "metric": intent.metric,
                    "target_source": result.target_source,
                    "active_diet_name": result.active_diet_name,
                },
                reason="Executed macro status query.",
            )
        case BudgetStatusIntent():
            result = budget_status(db_path, period=intent.period, date_text=intent.date)
            return build_execution_outcome(
                payload=result,
                normalized_fields={
                    "period": intent.period,
                    "category": intent.category,
                    "item_count": len(result.items),
                },
                reason="Executed budget status query.",
            )
        case HabitStatusIntent():
            result = habit_target_status(db_path, period=intent.period, date_text=intent.date)
            return build_execution_outcome(
                payload=result,
                normalized_fields={
                    "period": intent.period,
                    "item_count": len(result.items),
                },
                reason="Executed habit status query.",
            )
        case DietStatusIntent():
            result = diet_status(db_path, date_text=intent.date)
            return build_execution_outcome(
                payload=result,
                normalized_fields={
                    "meal_focus": intent.meal_focus,
                    "active_diet_name": result.active_diet_name,
                },
                reason="Executed diet status query.",
            )
        case ActiveDietIntent():
            result = active_diet(db_path)
            return build_execution_outcome(
                payload=result,
                normalized_fields={"active_diet_name": result.name if result else None},
                reason="Executed active diet query.",
            )
        case DailyStatusIntent():
            result = daily_status(db_path, date_text=intent.date)
            return build_execution_outcome(
                payload=result,
                normalized_fields={
                    "active_diet_name": result.active_diet_name,
                    "missing_diet_meals": result.missing_diet_meals,
                    "habit_pending": result.habit_pending,
                },
                reason="Executed daily status query.",
            )
    return None
