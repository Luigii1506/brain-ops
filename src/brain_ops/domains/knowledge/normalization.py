from __future__ import annotations

from pathlib import Path

TYPE_ALIASES = {
    "youtube": ("source", {"source_type": "youtube"}),
    "wikipedia": ("source", {"source_type": "wikipedia"}),
    "país": ("knowledge", {"knowledge_kind": "country"}),
    "book-note": ("knowledge", {"knowledge_kind": "book_note"}),
    "quote": ("knowledge", {"knowledge_kind": "quote"}),
}

FOLDER_DEFAULTS = {
    "00 - Inbox": {"type": "inbox", "status": "triage"},
    "01 - Sources": {"type": "source"},
    "02 - Knowledge": {"type": "knowledge"},
    "03 - Maps": {"type": "map"},
    "04 - Projects": {"type": "project"},
    "05 - Systems": {"type": "system"},
    "06 - Daily": {"type": "daily"},
}


def normalize_note_frontmatter(
    frontmatter: dict[str, object],
    relative: Path,
    *,
    systems_folder: str,
    maps_folder: str,
) -> tuple[dict[str, object], bool]:
    changed = False
    top_level = relative.parts[0] if relative.parts else ""

    if not frontmatter:
        frontmatter = {}
        changed = True

    default_values = FOLDER_DEFAULTS.get(top_level, {})
    for key, value in default_values.items():
        if key not in frontmatter or frontmatter[key] in (None, ""):
            frontmatter[key] = value
            changed = True

    note_type = frontmatter.get("type")
    if isinstance(note_type, str):
        normalized_key = note_type.strip().lower()
        alias_target = TYPE_ALIASES.get(normalized_key)
        if alias_target:
            new_type, extra = alias_target
            if frontmatter.get("type") != new_type:
                frontmatter["type"] = new_type
                changed = True
            for key, value in extra.items():
                if key not in frontmatter or frontmatter[key] in (None, ""):
                    frontmatter[key] = value
                    changed = True

    if top_level == systems_folder:
        system_folder = relative.parts[1] if len(relative.parts) > 1 else ""
        if system_folder == "Commands":
            if frontmatter.get("type") in {"system", "command"} and frontmatter.get("type") != "command":
                frontmatter["type"] = "command"
                changed = True
        elif system_folder == "Security":
            if frontmatter.get("type") in {"system", "security_note"} and frontmatter.get("type") != "security_note":
                frontmatter["type"] = "security_note"
                changed = True

    if top_level == maps_folder and relative.name.lower().startswith("moc-"):
        if frontmatter.get("type") != "map":
            frontmatter["type"] = "map"
            changed = True

    if isinstance(frontmatter.get("tags"), str):
        tags = [tag for tag in frontmatter["tags"].split() if tag]
        frontmatter["tags"] = tags
        changed = True

    return frontmatter, changed
