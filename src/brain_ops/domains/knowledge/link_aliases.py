"""Link alias resolution — redirect ambiguous wikilinks to canonical entities."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


# Map: ambiguous name → canonical entity name
# These are cases where a short name almost always refers to a specific entity
LINK_ALIASES: dict[str, str] = {
    "Persia": "Imperio Persa",
    "Egipto": "Alejandría",  # NO — Egipto is a place, not Alejandría. Remove this.
}

# These are contextual: they MIGHT need redirect depending on meaning.
# The fix-links command will use display aliases: [[canonical|display]]
CONTEXTUAL_ALIASES: dict[str, str] = {
    "Persia": "Imperio Persa",
    # "Macedonia" is both a kingdom entity AND a region — keep as-is, it's correct
    # "Grecia" is both a civilization AND a place — we have the entity, it's correct
}


@dataclass(slots=True, frozen=True)
class LinkFixResult:
    notes_scanned: int
    notes_fixed: int
    fixes: tuple[tuple[str, str, str], ...]  # (file, old_link, new_link)

    def to_dict(self) -> dict[str, object]:
        return {
            "notes_scanned": self.notes_scanned,
            "notes_fixed": self.notes_fixed,
            "fixes": [{"file": f, "old": o, "new": n} for f, o, n in self.fixes],
        }


def fix_ambiguous_links(
    vault_path: Path,
    aliases: dict[str, str] | None = None,
    *,
    dry_run: bool = False,
    excluded_parts: set[str] | None = None,
) -> LinkFixResult:
    """Scan vault notes and replace [[alias]] with [[canonical|alias]].

    Example: [[Persia]] → [[Imperio Persa|Persia]]
    This preserves the display text while linking to the correct entity.
    """
    if aliases is None:
        aliases = CONTEXTUAL_ALIASES
    if excluded_parts is None:
        excluded_parts = {".git", ".obsidian", ".brain-ops", "Templates"}

    notes_scanned = 0
    fixes: list[tuple[str, str, str]] = []

    for md_file in sorted(vault_path.rglob("*.md")):
        if any(part in md_file.parts for part in excluded_parts):
            continue

        try:
            content = md_file.read_text(encoding="utf-8")
        except Exception:
            continue

        notes_scanned += 1
        new_content = content
        file_fixed = False

        for alias, canonical in aliases.items():
            # Skip the canonical entity's own note
            if md_file.stem == canonical:
                continue

            # Match [[alias]] but NOT [[canonical|alias]] (already fixed)
            pattern = re.compile(
                rf"\[\[{re.escape(alias)}\]\]",
            )

            # Don't replace if it's already [[canonical|alias]]
            already_fixed = f"[[{canonical}|{alias}]]"
            if already_fixed in new_content:
                continue

            replacement = f"[[{canonical}|{alias}]]"
            matches = pattern.findall(new_content)
            if matches:
                new_content = pattern.sub(replacement, new_content)
                rel_path = str(md_file.relative_to(vault_path))
                for _ in matches:
                    fixes.append((rel_path, f"[[{alias}]]", replacement))
                file_fixed = True

        if file_fixed and not dry_run:
            md_file.write_text(new_content, encoding="utf-8")

    notes_fixed = len({f for f, _, _ in fixes})
    return LinkFixResult(
        notes_scanned=notes_scanned,
        notes_fixed=notes_fixed,
        fixes=tuple(fixes),
    )


def add_alias_to_frontmatter(
    note_path: Path,
    aliases: list[str],
) -> bool:
    """Add aliases to a note's frontmatter for Obsidian search."""
    from brain_ops.frontmatter import dump_frontmatter, split_frontmatter

    try:
        content = note_path.read_text(encoding="utf-8")
        fm, body = split_frontmatter(content)

        existing = fm.get("aliases", [])
        if not isinstance(existing, list):
            existing = [existing] if existing else []

        added = False
        for alias in aliases:
            if alias not in existing:
                existing.append(alias)
                added = True

        if added:
            fm["aliases"] = existing
            note_path.write_text(dump_frontmatter(fm, body), encoding="utf-8")
            return True
    except Exception:
        pass
    return False


__all__ = [
    "CONTEXTUAL_ALIASES",
    "LINK_ALIASES",
    "LinkFixResult",
    "add_alias_to_frontmatter",
    "fix_ambiguous_links",
]
