"""Backlink injection — when a new entity is created, link existing mentions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True, frozen=True)
class BacklinkResult:
    entity_name: str
    notes_scanned: int
    notes_linked: int
    linked_files: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "entity_name": self.entity_name,
            "notes_scanned": self.notes_scanned,
            "notes_linked": self.notes_linked,
            "linked_files": list(self.linked_files),
        }


def inject_backlinks(
    vault_path: Path,
    entity_name: str,
    *,
    excluded_parts: set[str] | None = None,
    dry_run: bool = False,
) -> BacklinkResult:
    """Scan all vault notes and convert plain-text mentions of entity_name to [[wikilinks]].

    Only replaces the first occurrence per note (avoids over-linking).
    Skips the entity's own note.
    Updates the `related` frontmatter field in notes that get linked.
    """
    if excluded_parts is None:
        excluded_parts = {".git", ".obsidian", ".brain-ops", "Templates"}

    from brain_ops.frontmatter import dump_frontmatter, split_frontmatter

    notes_scanned = 0
    linked_files: list[str] = []

    # Build regex: match entity name NOT already inside [[ ]]
    # Negative lookbehind for [[ and negative lookahead for ]]
    escaped = re.escape(entity_name)
    pattern = re.compile(
        rf"(?<!\[\[)(?<!\|)\b({escaped})\b(?!\]\])(?!\|)",
        re.IGNORECASE,
    )

    for md_file in sorted(vault_path.rglob("*.md")):
        # Skip excluded directories
        if any(part in md_file.parts for part in excluded_parts):
            continue

        # Skip the entity's own note
        if md_file.stem.lower() == entity_name.lower():
            continue

        try:
            content = md_file.read_text(encoding="utf-8")
        except Exception:
            continue

        notes_scanned += 1

        # Check if the name appears (not already as wikilink)
        if not pattern.search(content):
            continue

        if dry_run:
            linked_files.append(str(md_file.relative_to(vault_path)))
            continue

        # Split frontmatter and body
        try:
            fm, body = split_frontmatter(content)
        except Exception:
            continue

        # Replace first occurrence in body only
        new_body, count = pattern.subn(f"[[{entity_name}]]", body, count=1)
        if count == 0:
            continue

        # Update related field in frontmatter
        related = fm.get("related")
        if related is None:
            fm["related"] = [entity_name]
        elif isinstance(related, list):
            if entity_name not in related:
                related.append(entity_name)
        elif isinstance(related, str):
            if related.strip() != entity_name:
                fm["related"] = [related.strip(), entity_name]

        # Write back
        new_content = dump_frontmatter(fm, new_body)
        md_file.write_text(new_content, encoding="utf-8")
        linked_files.append(str(md_file.relative_to(vault_path)))

    return BacklinkResult(
        entity_name=entity_name,
        notes_scanned=notes_scanned,
        notes_linked=len(linked_files),
        linked_files=tuple(linked_files),
    )


__all__ = ["BacklinkResult", "inject_backlinks"]
