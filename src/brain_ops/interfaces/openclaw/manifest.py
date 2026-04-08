"""Static OpenClaw manifest for brain-ops."""

from __future__ import annotations

import json
from pathlib import Path

from rich.table import Table

OPENCLAW_MANIFEST = {
    "name": "brain-ops",
    "entrypoint": "brain",
    "preferred_natural_input_command": "handle-input",
    "preferred_natural_input_args": ["<text>", "--json"],
    "notes": [
        "Use brain-ops as the deterministic execution layer.",
        "Prefer handle-input for natural language.",
        "Prefer route-input for plan-only classification.",
    ],
    "natural_input_contract_version": "1",
    "capabilities": {
        "write_tools": [
            "handle_input",
            "daily_summary",
            "capture",
            "improve_note",
            "research_note",
            "update_diet_meal",
        ],
        "query_tools": [
            "route_input",
            "daily_status",
            "daily_macros",
            "macro_status",
            "diet_status",
            "daily_habits",
            "habit_status",
            "workout_status",
            "spending_summary",
            "budget_status",
            "body_metrics_status",
        ],
        "confirm_before_write": [
            "handle_input",
            "capture",
            "improve_note",
            "research_note",
            "update_diet_meal",
        ],
    },
    "tools": [
        {
            "name": "handle_input",
            "command": 'brain handle-input "<text>" --json',
            "purpose": "Route and execute safe actions from natural language.",
        },
        {
            "name": "route_input",
            "command": 'brain route-input "<text>" --json',
            "purpose": "Classify natural language without side effects.",
        },
        {
            "name": "daily_summary",
            "command": "brain daily-summary --date <yyyy-mm-dd>",
            "purpose": "Write structured day summaries into the Obsidian vault.",
        },
        {
            "name": "daily_status",
            "command": "brain daily-status --date <yyyy-mm-dd> --json",
            "purpose": "Read a compact daily state snapshot across diet, macros, habits, spending, supplements, and workouts.",
        },
        {
            "name": "daily_macros",
            "command": "brain daily-macros --date <yyyy-mm-dd>",
            "purpose": "Read nutrition totals from SQLite.",
        },
        {
            "name": "macro_status",
            "command": "brain macro-status --date <yyyy-mm-dd> --json",
            "purpose": "Compare actual macros against stored macro targets or the active diet.",
        },
        {
            "name": "diet_status",
            "command": "brain diet-status --date <yyyy-mm-dd> --json",
            "purpose": "Compare actual intake against the active diet plan.",
        },
        {
            "name": "update_diet_meal",
            "command": "brain update-diet-meal --meal-type <breakfast|lunch|dinner> --items \"<items>\" --mode <replace|append>",
            "purpose": "Change one meal inside the active diet plan.",
        },
        {
            "name": "daily_habits",
            "command": "brain daily-habits --date <yyyy-mm-dd>",
            "purpose": "Read habit status summaries from SQLite.",
        },
        {
            "name": "habit_status",
            "command": "brain habit-status --period <daily|weekly|monthly> --date <yyyy-mm-dd> --json",
            "purpose": "Compare habit completion against stored habit targets.",
        },
        {
            "name": "workout_status",
            "command": "brain workout-status --date <yyyy-mm-dd>",
            "purpose": "Read workout summaries from SQLite.",
        },
        {
            "name": "spending_summary",
            "command": "brain spending-summary --date <yyyy-mm-dd>",
            "purpose": "Read expense summaries from SQLite.",
        },
        {
            "name": "budget_status",
            "command": "brain budget-status --period <daily|weekly|monthly> --date <yyyy-mm-dd> --json",
            "purpose": "Compare actual spending against stored budget targets.",
        },
        {
            "name": "body_metrics_status",
            "command": "brain body-metrics-status --date <yyyy-mm-dd>",
            "purpose": "Read body metrics summaries from SQLite.",
        },
        {
            "name": "capture",
            "command": 'brain capture "<text>"',
            "purpose": "Capture personal data (meals, workouts, expenses, habits, journal) from natural language.",
        },
        {
            "name": "improve_note",
            "command": "brain improve-note <note_path>",
            "purpose": "Improve structure of an existing note.",
        },
        {
            "name": "research_note",
            "command": "brain research-note <note_path> --query <query>",
            "purpose": "Enrich a note with grounded research.",
        },
    ],
}


def serialize_openclaw_manifest() -> str:
    return json.dumps(OPENCLAW_MANIFEST, indent=2) + "\n"


def write_openclaw_manifest(output_path: Path) -> Path:
    target = output_path.expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(serialize_openclaw_manifest(), encoding="utf-8")
    return target


def build_openclaw_manifest_table() -> Table:
    table = Table(title="OpenClaw Manifest")
    table.add_column("Tool")
    table.add_column("Command")
    table.add_column("Purpose")
    for tool in OPENCLAW_MANIFEST["tools"]:
        table.add_row(tool["name"], tool["command"], tool["purpose"])
    return table


__all__ = [
    "OPENCLAW_MANIFEST",
    "build_openclaw_manifest_table",
    "serialize_openclaw_manifest",
    "write_openclaw_manifest",
]
