from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field


class OperationStatus(StrEnum):
    CREATED = "created"
    UPDATED = "updated"
    MOVED = "moved"
    SKIPPED = "skipped"
    REPORT = "report"


class OperationRecord(BaseModel):
    action: str
    path: Path
    detail: str
    status: OperationStatus


class CreateNoteRequest(BaseModel):
    title: str
    note_type: str = "permanent_note"
    folder: str | None = None
    template_name: str | None = None
    tags: list[str] = Field(default_factory=list)
    extra_frontmatter: dict[str, object] = Field(default_factory=dict)
    body_override: str | None = None
    overwrite: bool = False


class InboxItemResult(BaseModel):
    source_path: Path
    destination_path: Path | None = None
    note_type: str | None = None
    moved: bool = False
    normalized: bool = False
    reason: str


class InboxProcessSummary(BaseModel):
    scanned: int = 0
    normalized: int = 0
    moved: int = 0
    left_in_inbox: int = 0
    items: list[InboxItemResult] = Field(default_factory=list)
    operations: list[OperationRecord] = Field(default_factory=list)


class WeeklyReviewSummary(BaseModel):
    generated_at: datetime
    inbox_notes: list[Path] = Field(default_factory=list)
    notes_missing_frontmatter: list[Path] = Field(default_factory=list)
    stale_project_notes: list[Path] = Field(default_factory=list)
    possible_orphans: list[Path] = Field(default_factory=list)
    recent_changes: list[Path] = Field(default_factory=list)
    operations: list[OperationRecord] = Field(default_factory=list)


class FolderAuditStats(BaseModel):
    total: int = 0
    with_frontmatter: int = 0
    empty: int = 0
    very_short: int = 0


class AuditFinding(BaseModel):
    path: Path
    reason: str


class VaultAuditSummary(BaseModel):
    generated_at: datetime
    total_notes: int = 0
    with_frontmatter: int = 0
    empty_notes: list[Path] = Field(default_factory=list)
    very_short_notes: list[Path] = Field(default_factory=list)
    notes_missing_frontmatter: list[Path] = Field(default_factory=list)
    invalid_frontmatter: list[AuditFinding] = Field(default_factory=list)
    moc_outside_maps: list[Path] = Field(default_factory=list)
    maps_with_few_links: list[AuditFinding] = Field(default_factory=list)
    system_notes_outside_systems: list[Path] = Field(default_factory=list)
    source_notes_outside_sources: list[Path] = Field(default_factory=list)
    notes_with_unknown_type: list[AuditFinding] = Field(default_factory=list)
    notes_in_root: list[Path] = Field(default_factory=list)
    folder_stats: dict[str, FolderAuditStats] = Field(default_factory=dict)
    operations: list[OperationRecord] = Field(default_factory=list)


class NormalizeFrontmatterSummary(BaseModel):
    scanned: int = 0
    updated: int = 0
    skipped: int = 0
    invalid: list[AuditFinding] = Field(default_factory=list)
    operations: list[OperationRecord] = Field(default_factory=list)


class CaptureResult(BaseModel):
    title: str
    note_type: str
    path: Path
    operation: OperationRecord
    reason: str


class ImproveNoteResult(BaseModel):
    path: Path
    note_type: str
    operation: OperationRecord
    reason: str


class ResearchSource(BaseModel):
    title: str
    url: str
    summary: str


class ResearchNoteResult(BaseModel):
    path: Path
    query: str
    sources: list[ResearchSource] = Field(default_factory=list)
    operation: OperationRecord
    reason: str


class LinkSuggestion(BaseModel):
    path: Path
    score: float
    reason: str


class LinkSuggestionResult(BaseModel):
    target: Path
    suggestions: list[LinkSuggestion] = Field(default_factory=list)
    operation: OperationRecord
    reason: str


class ApplyLinksResult(BaseModel):
    target: Path
    applied_links: list[str] = Field(default_factory=list)
    operation: OperationRecord
    reason: str


class PromoteNoteResult(BaseModel):
    source_path: Path
    promoted_path: Path
    promoted_type: str
    operations: list[OperationRecord] = Field(default_factory=list)
    reason: str


class EnrichNoteResult(BaseModel):
    path: Path
    operations: list[OperationRecord] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
    reason: str


class MealItemInput(BaseModel):
    food_name: str
    grams: float | None = None
    quantity: float | None = None
    calories: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    note: str | None = None


class MealLogResult(BaseModel):
    logged_at: datetime
    meal_type: str | None = None
    items: list[MealItemInput] = Field(default_factory=list)
    operations: list[OperationRecord] = Field(default_factory=list)
    reason: str


class DailyMacrosSummary(BaseModel):
    date: str
    meals_logged: int = 0
    items_logged: int = 0
    calories: float = 0
    protein_g: float = 0
    carbs_g: float = 0
    fat_g: float = 0
    active_diet_name: str | None = None
    database_path: Path


class MacroTargetsResult(BaseModel):
    calories: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    operations: list[OperationRecord] = Field(default_factory=list)
    reason: str


class MacroStatusSummary(BaseModel):
    date: str
    target_source: str | None = None
    active_diet_name: str | None = None
    calories_target: float | None = None
    protein_g_target: float | None = None
    carbs_g_target: float | None = None
    fat_g_target: float | None = None
    calories_actual: float = 0
    protein_g_actual: float = 0
    carbs_g_actual: float = 0
    fat_g_actual: float = 0
    calories_remaining: float | None = None
    protein_g_remaining: float | None = None
    carbs_g_remaining: float | None = None
    fat_g_remaining: float | None = None
    database_path: Path


class SupplementLogResult(BaseModel):
    logged_at: datetime
    supplement_name: str
    amount: float | None = None
    unit: str | None = None
    operations: list[OperationRecord] = Field(default_factory=list)
    reason: str


class HabitCheckinResult(BaseModel):
    checked_at: datetime
    habit_name: str
    status: str
    operations: list[OperationRecord] = Field(default_factory=list)
    reason: str


class DailyHabitsSummary(BaseModel):
    date: str
    total_checkins: int = 0
    by_status: dict[str, int] = Field(default_factory=dict)
    habits: list[str] = Field(default_factory=list)
    database_path: Path


class HabitTargetResult(BaseModel):
    habit_name: str
    period: str
    target_count: int
    operations: list[OperationRecord] = Field(default_factory=list)
    reason: str


class HabitStatusItem(BaseModel):
    habit_name: str
    period: str
    target_count: int
    completed_count: int
    remaining_count: int


class HabitTargetStatusSummary(BaseModel):
    date: str
    period: str
    items: list[HabitStatusItem] = Field(default_factory=list)
    database_path: Path


class BodyMetricsLogResult(BaseModel):
    logged_at: datetime
    weight_kg: float | None = None
    body_fat_pct: float | None = None
    fat_mass_kg: float | None = None
    muscle_mass_kg: float | None = None
    visceral_fat: float | None = None
    bmr_calories: float | None = None
    arm_cm: float | None = None
    waist_cm: float | None = None
    thigh_cm: float | None = None
    calf_cm: float | None = None
    operations: list[OperationRecord] = Field(default_factory=list)
    reason: str


class BodyMetricsSummary(BaseModel):
    date: str
    entries_logged: int = 0
    latest_logged_at: str | None = None
    latest_weight_kg: float | None = None
    latest_body_fat_pct: float | None = None
    latest_fat_mass_kg: float | None = None
    latest_muscle_mass_kg: float | None = None
    latest_visceral_fat: float | None = None
    latest_bmr_calories: float | None = None
    latest_arm_cm: float | None = None
    latest_waist_cm: float | None = None
    latest_thigh_cm: float | None = None
    latest_calf_cm: float | None = None
    database_path: Path


class WorkoutSetInput(BaseModel):
    exercise_name: str
    sets: int = 1
    reps: int | None = None
    weight_kg: float | None = None
    note: str | None = None


class WorkoutLogResult(BaseModel):
    logged_at: datetime
    routine_name: str | None = None
    exercises: list[WorkoutSetInput] = Field(default_factory=list)
    operations: list[OperationRecord] = Field(default_factory=list)
    reason: str


class WorkoutStatusSummary(BaseModel):
    date: str
    workouts_logged: int = 0
    total_sets: int = 0
    unique_exercises: list[str] = Field(default_factory=list)
    database_path: Path


class ExpenseLogResult(BaseModel):
    logged_at: datetime
    amount: float
    currency: str = "MXN"
    category: str | None = None
    merchant: str | None = None
    operations: list[OperationRecord] = Field(default_factory=list)
    reason: str


class SpendingSummary(BaseModel):
    date: str
    total_amount: float = 0
    transaction_count: int = 0
    by_category: dict[str, float] = Field(default_factory=dict)
    currency: str = "MXN"
    database_path: Path


class BudgetTargetResult(BaseModel):
    period: str
    amount: float
    currency: str = "MXN"
    category: str | None = None
    operations: list[OperationRecord] = Field(default_factory=list)
    reason: str


class BudgetStatusItem(BaseModel):
    period: str
    category: str | None = None
    target_amount: float
    actual_amount: float
    remaining_amount: float
    currency: str = "MXN"


class BudgetStatusSummary(BaseModel):
    date: str
    period: str
    items: list[BudgetStatusItem] = Field(default_factory=list)
    database_path: Path


class DietPlanMealItem(BaseModel):
    food_name: str
    grams: float | None = None
    quantity: float | None = None
    calories: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None


class DietPlanMeal(BaseModel):
    meal_type: str
    label: str
    items: list[DietPlanMealItem] = Field(default_factory=list)
    calories_target: float = 0
    protein_g_target: float = 0
    carbs_g_target: float = 0
    fat_g_target: float = 0


class DietPlanResult(BaseModel):
    name: str
    status: str
    meals: list[DietPlanMeal] = Field(default_factory=list)
    operations: list[OperationRecord] = Field(default_factory=list)
    reason: str


class DietActivationResult(BaseModel):
    name: str
    status: str
    operations: list[OperationRecord] = Field(default_factory=list)
    reason: str


class DietMealUpdateResult(BaseModel):
    diet_name: str
    meal_type: str
    mode: str
    items: list[DietPlanMealItem] = Field(default_factory=list)
    operations: list[OperationRecord] = Field(default_factory=list)
    reason: str


class DietPlanSummary(BaseModel):
    name: str
    status: str
    notes: str | None = None
    meals: list[DietPlanMeal] = Field(default_factory=list)
    calories_target: float = 0
    protein_g_target: float = 0
    carbs_g_target: float = 0
    fat_g_target: float = 0
    database_path: Path


class DietMealProgress(BaseModel):
    meal_type: str
    label: str
    target_items: list[str] = Field(default_factory=list)
    actual_items: list[str] = Field(default_factory=list)
    target_count: int = 0
    actual_count: int = 0
    logged: bool = False
    calories_target: float = 0
    protein_g_target: float = 0
    carbs_g_target: float = 0
    fat_g_target: float = 0
    calories_actual: float = 0
    protein_g_actual: float = 0
    carbs_g_actual: float = 0
    fat_g_actual: float = 0


class DietStatusSummary(BaseModel):
    date: str
    active_diet_name: str | None = None
    notes: str | None = None
    meals: list[DietMealProgress] = Field(default_factory=list)
    calories_target: float = 0
    protein_g_target: float = 0
    carbs_g_target: float = 0
    fat_g_target: float = 0
    calories_actual: float = 0
    protein_g_actual: float = 0
    carbs_g_actual: float = 0
    fat_g_actual: float = 0
    calories_remaining: float | None = None
    protein_g_remaining: float | None = None
    carbs_g_remaining: float | None = None
    fat_g_remaining: float | None = None
    database_path: Path


class DailyLogResult(BaseModel):
    logged_at: datetime
    domain: str
    operations: list[OperationRecord] = Field(default_factory=list)
    reason: str


class RouteDecisionResult(BaseModel):
    input_text: str
    domain: str
    command: str
    confidence: float
    reason: str
    routing_source: str = "heuristic"
    extracted_fields: dict[str, object] = Field(default_factory=dict)


class HandleInputSubResult(BaseModel):
    input_text: str
    intent: str | None = None
    intent_version: str | None = None
    executed: bool = False
    executed_command: str | None = None
    target_domain: str | None = None
    routing_source: str | None = None
    confidence: float | None = None
    extracted_fields: dict[str, object] = Field(default_factory=dict)
    normalized_fields: dict[str, object] = Field(default_factory=dict)
    assistant_message: str | None = None
    reason: str


class HandleInputResult(BaseModel):
    input_text: str
    decision: RouteDecisionResult
    intent: str | None = None
    intent_version: str | None = None
    executed: bool = False
    operations: list[OperationRecord] = Field(default_factory=list)
    executed_command: str | None = None
    target_domain: str | None = None
    routing_source: str | None = None
    confidence: float | None = None
    extracted_fields: dict[str, object] = Field(default_factory=dict)
    normalized_fields: dict[str, object] = Field(default_factory=dict)
    needs_follow_up: bool = False
    follow_up: str | None = None
    follow_up_options: list[str] = Field(default_factory=list)
    assistant_message: str | None = None
    sub_results: list[HandleInputSubResult] = Field(default_factory=list)
    reason: str


class DailySummaryResult(BaseModel):
    date: str
    path: Path
    operations: list[OperationRecord] = Field(default_factory=list)
    sections_written: list[str] = Field(default_factory=list)
    reason: str


class DailyStatusSummary(BaseModel):
    date: str
    active_diet_name: str | None = None
    calories_actual: float = 0
    calories_target: float | None = None
    calories_remaining: float | None = None
    protein_g_actual: float = 0
    protein_g_target: float | None = None
    protein_g_remaining: float | None = None
    carbs_g_actual: float = 0
    carbs_g_target: float | None = None
    carbs_g_remaining: float | None = None
    fat_g_actual: float = 0
    fat_g_target: float | None = None
    fat_g_remaining: float | None = None
    missing_diet_meals: list[str] = Field(default_factory=list)
    workouts_logged: int = 0
    total_workout_sets: int = 0
    expenses_total: float = 0
    expense_currency: str = "MXN"
    supplements_logged: int = 0
    supplement_names: list[str] = Field(default_factory=list)
    habit_pending: list[str] = Field(default_factory=list)
    habits_completed: list[str] = Field(default_factory=list)
    body_weight_kg: float | None = None
    body_fat_pct: float | None = None
    waist_cm: float | None = None
    daily_logs_count: int = 0
    database_path: Path
