from __future__ import annotations

from pathlib import Path

from brain_ops.frontmatter import dump_frontmatter, split_frontmatter
from brain_ops.models import AuditFinding, NormalizeFrontmatterSummary
from brain_ops.vault import Vault, now_iso


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


def normalize_frontmatter(vault: Vault) -> NormalizeFrontmatterSummary:
    summary = NormalizeFrontmatterSummary()
    for path in sorted(vault.root.rglob("*.md")):
        if not path.is_file() or ".obsidian" in path.parts or ".git" in path.parts:
            continue
        if "07 - Archive" in path.parts:
            continue

        summary.scanned += 1
        relative = vault.relative_path(path)
        text = path.read_text(encoding="utf-8", errors="ignore")
        try:
            frontmatter, body = split_frontmatter(text)
        except Exception as exc:
            summary.invalid.append(AuditFinding(path=relative, reason=str(exc)))
            summary.skipped += 1
            continue

        original = text
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

        if top_level == vault.config.folders.systems:
            system_folder = relative.parts[1] if len(relative.parts) > 1 else ""
            if system_folder == "Commands":
                if frontmatter.get("type") in {"system", "command"}:
                    if frontmatter.get("type") != "command":
                        frontmatter["type"] = "command"
                        changed = True
            elif system_folder == "Security":
                if frontmatter.get("type") in {"system", "security_note"}:
                    if frontmatter.get("type") != "security_note":
                        frontmatter["type"] = "security_note"
                        changed = True

        if top_level == vault.config.folders.maps and relative.name.lower().startswith("moc-"):
            if frontmatter.get("type") != "map":
                frontmatter["type"] = "map"
                changed = True

        if "created" not in frontmatter or frontmatter["created"] in (None, ""):
            frontmatter["created"] = now_iso()
            changed = True
        frontmatter["updated"] = now_iso()
        if "tags" not in frontmatter or frontmatter["tags"] in (None, ""):
            frontmatter["tags"] = []
            changed = True
        elif isinstance(frontmatter["tags"], str):
            tags = [tag for tag in frontmatter["tags"].split() if tag]
            frontmatter["tags"] = tags
            changed = True

        rendered = dump_frontmatter(frontmatter, body)
        if changed and rendered != original:
            summary.operations.append(vault.write_text(path, rendered, overwrite=True))
            summary.updated += 1
        else:
            summary.skipped += 1
    return summary
