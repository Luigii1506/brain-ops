from __future__ import annotations
from datetime import datetime
from pathlib import Path

from brain_ops.core.validation import resolve_iso_date
from brain_ops.domains.personal.tracking import (
    build_body_metrics_log_result,
    build_body_metrics_summary,
    normalize_body_metrics_inputs,
)
from brain_ops.models import BodyMetricsLogResult
from brain_ops.storage.db import ensure_database_parent, require_database_file, resolve_database_path
from brain_ops.storage.sqlite import (
    ensure_body_metrics_schema,
    fetch_body_metrics_status_rows,
    insert_body_metrics_log,
)


def log_body_metrics(
    database_path: Path,
    *,
    weight_kg: float | None = None,
    body_fat_pct: float | None = None,
    fat_mass_kg: float | None = None,
    muscle_mass_kg: float | None = None,
    visceral_fat: float | None = None,
    bmr_calories: float | None = None,
    arm_cm: float | None = None,
    waist_cm: float | None = None,
    thigh_cm: float | None = None,
    calf_cm: float | None = None,
    note: str | None = None,
    logged_at: datetime | None = None,
    dry_run: bool = False,
) -> BodyMetricsLogResult:
    normalized = normalize_body_metrics_inputs(
        weight_kg=weight_kg,
        body_fat_pct=body_fat_pct,
        fat_mass_kg=fat_mass_kg,
        muscle_mass_kg=muscle_mass_kg,
        visceral_fat=visceral_fat,
        bmr_calories=bmr_calories,
        arm_cm=arm_cm,
        waist_cm=waist_cm,
        thigh_cm=thigh_cm,
        calf_cm=calf_cm,
        note=note,
    )

    logged_at = logged_at or datetime.now()
    target = resolve_database_path(database_path)
    if not dry_run:
        ensure_database_parent(target)
        insert_body_metrics_log(
            target,
            logged_at=logged_at.isoformat(timespec="seconds"),
            weight_kg=normalized["weight_kg"],
            body_fat_pct=normalized["body_fat_pct"],
            fat_mass_kg=normalized["fat_mass_kg"],
            muscle_mass_kg=normalized["muscle_mass_kg"],
            visceral_fat=normalized["visceral_fat"],
            bmr_calories=normalized["bmr_calories"],
            arm_cm=normalized["arm_cm"],
            waist_cm=normalized["waist_cm"],
            thigh_cm=normalized["thigh_cm"],
            calf_cm=normalized["calf_cm"],
            note=normalized["note"],
        )
    return build_body_metrics_log_result(
        database_path=target,
        logged_at=logged_at,
        weight_kg=normalized["weight_kg"],
        body_fat_pct=normalized["body_fat_pct"],
        fat_mass_kg=normalized["fat_mass_kg"],
        muscle_mass_kg=normalized["muscle_mass_kg"],
        visceral_fat=normalized["visceral_fat"],
        bmr_calories=normalized["bmr_calories"],
        arm_cm=normalized["arm_cm"],
        waist_cm=normalized["waist_cm"],
        thigh_cm=normalized["thigh_cm"],
        calf_cm=normalized["calf_cm"],
    )


def body_metrics_status(database_path: Path, date_text: str | None = None):
    target = require_database_file(database_path)

    resolved_date = resolve_iso_date(date_text)
    start = f"{resolved_date}T00:00:00"
    end = f"{resolved_date}T23:59:59"

    ensure_body_metrics_schema(target)
    count_row, latest_row = fetch_body_metrics_status_rows(target, start=start, end=end)

    return build_body_metrics_summary(
        date=resolved_date,
        database_path=target,
        count_row=count_row,
        latest_row=latest_row,
    )
