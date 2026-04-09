from __future__ import annotations

from brain_ops.core.execution import IntentExecutionOutcome, build_execution_outcome
from brain_ops.intents import (
    DailyLogIntent,
    HabitCheckinIntent,
    IntentModel,
    LogBodyMetricsIntent,
    LogExpenseIntent,
    LogMealIntent,
    LogSupplementIntent,
    LogWorkoutIntent,
    TaskIntent,
)
from brain_ops.services.body_metrics_service import log_body_metrics
from brain_ops.services.daily_log_service import log_daily_event
from brain_ops.services.expenses_service import log_expense
from brain_ops.services.fitness_service import log_workout
from brain_ops.services.life_ops_service import habit_checkin, log_supplement
from brain_ops.services.nutrition_service import log_meal


def execute_logging_intent(
    db_path: object,
    intent: IntentModel,
    *,
    dry_run: bool,
) -> IntentExecutionOutcome | None:
    match intent:
        case LogExpenseIntent():
            result = log_expense(
                db_path,
                amount=intent.amount,
                category=intent.category,
                merchant=intent.merchant,
                currency=intent.currency,
                note=intent.note,
                dry_run=dry_run,
            )
            return build_execution_outcome(
                payload=result,
                operations=result.operations,
                normalized_fields={
                    "amount": intent.amount,
                    "category": intent.category,
                    "merchant": intent.merchant,
                    "currency": intent.currency,
                },
                reason="Executed expense intent.",
            )
        case LogMealIntent():
            result = log_meal(db_path, intent.meal_text, meal_type=intent.meal_type, dry_run=dry_run)
            return build_execution_outcome(
                payload=result,
                operations=result.operations,
                normalized_fields={
                    "meal_text": intent.meal_text,
                    "meal_type": intent.meal_type,
                    "item_count": len(result.items),
                },
                reason="Executed meal intent.",
            )
        case LogSupplementIntent():
            result = log_supplement(
                db_path,
                intent.supplement_name,
                amount=intent.amount,
                unit=intent.unit,
                note=intent.note,
                dry_run=dry_run,
            )
            return build_execution_outcome(
                payload=result,
                operations=result.operations,
                normalized_fields={
                    "supplement_name": intent.supplement_name,
                    "amount": intent.amount,
                    "unit": intent.unit,
                },
                reason="Executed supplement intent.",
            )
        case HabitCheckinIntent():
            result = habit_checkin(
                db_path,
                intent.habit_name,
                status=intent.status,
                note=intent.note,
                dry_run=dry_run,
            )
            return build_execution_outcome(
                payload=result,
                operations=result.operations,
                normalized_fields={
                    "habit_name": intent.habit_name,
                    "status": intent.status,
                },
                reason="Executed habit check-in intent.",
            )
        case LogBodyMetricsIntent():
            result = log_body_metrics(
                db_path,
                weight_kg=intent.weight_kg,
                body_fat_pct=intent.body_fat_pct,
                waist_cm=intent.waist_cm,
                note=intent.note,
                dry_run=dry_run,
            )
            return build_execution_outcome(
                payload=result,
                operations=result.operations,
                normalized_fields={
                    "weight_kg": intent.weight_kg,
                    "body_fat_pct": intent.body_fat_pct,
                    "waist_cm": intent.waist_cm,
                },
                reason="Executed body metrics intent.",
            )
        case LogWorkoutIntent():
            result = log_workout(db_path, intent.workout_text, routine_name=intent.routine_name, dry_run=dry_run)
            return build_execution_outcome(
                payload=result,
                operations=result.operations,
                normalized_fields={
                    "workout_text": intent.workout_text,
                    "routine_name": intent.routine_name,
                    "exercise_count": len(result.exercises),
                },
                reason="Executed workout intent.",
            )
        case DailyLogIntent():
            result = log_daily_event(db_path, intent.text, domain=intent.log_domain, dry_run=dry_run)
            return build_execution_outcome(
                payload=result,
                operations=result.operations,
                normalized_fields={"log_domain": intent.log_domain},
                reason="Executed daily log intent.",
            )
        case TaskIntent():
            if dry_run:
                return build_execution_outcome(
                    payload={"title": intent.title, "project": intent.project},
                    operations=[],
                    normalized_fields={"title": intent.title, "project": intent.project},
                    reason="Would create task (dry run).",
                )
            from brain_ops.storage.sqlite.tasks import insert_task

            task_id = insert_task(
                db_path,
                intent.title,
                project=intent.project,
                source="capture",
            )
            return build_execution_outcome(
                payload={"id": task_id, "title": intent.title, "project": intent.project},
                operations=[],
                normalized_fields={"title": intent.title, "project": intent.project, "task_id": task_id},
                reason=f"Created task #{task_id}.",
            )
    return None
