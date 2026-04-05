"""Diet domain primitives."""

from brain_ops.domains.personal.diet.parsing import ParsedDietMeal, parse_diet_meal_spec
from brain_ops.domains.personal.diet.projections import (
    build_diet_plan_summary,
    build_diet_status_summary,
    remaining,
)

__all__ = [
    "ParsedDietMeal",
    "build_diet_plan_summary",
    "build_diet_status_summary",
    "parse_diet_meal_spec",
    "remaining",
]
