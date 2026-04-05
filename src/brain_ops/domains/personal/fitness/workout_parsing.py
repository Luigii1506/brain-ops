from __future__ import annotations

import re

from brain_ops.errors import ConfigError
from brain_ops.models import WorkoutSetInput

ENTRY_SPLIT_PATTERN = re.compile(r"\s*;\s*")
SERIES_PATTERN = re.compile(
    r"^(?P<exercise>.+?)\s+(?P<sets>\d+)x(?P<reps>\d+)(?:@(?P<weight>bodyweight|\d+(?:\.\d+)?)\s*(?P<unit>kg)?)?$",
    re.IGNORECASE,
)


def parse_workout_entries(workout_text: str) -> list[WorkoutSetInput]:
    entries = [part.strip() for part in ENTRY_SPLIT_PATTERN.split(workout_text.strip()) if part.strip()]
    return [_parse_entry(entry) for entry in entries]


def normalize_workout_log_input(workout_text: str) -> tuple[str, list[WorkoutSetInput]]:
    normalized_text = workout_text.strip()
    if not normalized_text:
        raise ConfigError("Workout text cannot be empty.")

    exercises = parse_workout_entries(normalized_text)
    if not exercises:
        raise ConfigError("No workout entries could be parsed.")
    return normalized_text, exercises


def _parse_entry(entry: str) -> WorkoutSetInput:
    match = SERIES_PATTERN.match(entry)
    if not match:
        raise ConfigError(
            "Workout entries must look like 'Press banca 4x8@80kg' or 'Dominadas 3x10@bodyweight'."
        )

    exercise_name = match.group("exercise").strip()
    sets = int(match.group("sets"))
    reps = int(match.group("reps"))
    weight_raw = match.group("weight")
    weight_kg = None if not weight_raw or weight_raw.lower() == "bodyweight" else float(weight_raw)
    note = "bodyweight" if weight_raw and weight_raw.lower() == "bodyweight" else None
    return WorkoutSetInput(
        exercise_name=exercise_name,
        sets=sets,
        reps=reps,
        weight_kg=weight_kg,
        note=note,
    )
