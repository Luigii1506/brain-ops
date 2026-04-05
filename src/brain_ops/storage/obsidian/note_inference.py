from __future__ import annotations

from pathlib import Path


def infer_note_type_from_relative_path(relative: Path) -> str:
    top = relative.parts[0] if relative.parts else ""
    if top == "01 - Sources":
        return "source"
    if top == "02 - Knowledge":
        return "knowledge"
    if top == "03 - Maps":
        return "map"
    if top == "04 - Projects":
        return "project"
    if top == "05 - Systems":
        return "system"
    if top == "06 - Daily":
        return "daily"
    return "knowledge"


def infer_note_title_from_relative_path(relative: Path) -> str:
    return relative.stem
