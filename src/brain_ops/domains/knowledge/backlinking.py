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

    Disambiguation policy (Campaña 0.7):
    Entities with a disambiguation suffix (e.g. "Política (Aristóteles)")
    are SKIPPED entirely — the suffix itself is explicit acknowledgement
    that the base name has multiple referents, so auto-wikifying plain
    mentions of the base name ("política") would be semantically wrong.
    For disambiguated entities, the writer must link explicitly via
    ``[[Política (Aristóteles)]]`` or ``[[Política (Aristóteles)|Política]]``.
    """
    if excluded_parts is None:
        excluded_parts = {".git", ".obsidian", ".brain-ops", "Templates"}

    from brain_ops.frontmatter import dump_frontmatter, split_frontmatter
    from brain_ops.domains.knowledge.registry import extract_base_name

    notes_scanned = 0
    linked_files: list[str] = []

    # Determine search term and wikilink format for disambiguated entities
    base_name = extract_base_name(entity_name)
    is_disambiguated = base_name != entity_name

    # Campaña 0.7: disambiguated entities (e.g. "Política (Aristóteles)")
    # have ambiguous base names BY DESIGN — the disambiguation suffix is
    # explicit testimony that the base name has multiple referents.
    # Auto-injecting backlinks for the base name would wikify plain
    # mentions (e.g. "política" as common noun, "economía política", etc.)
    # to the specific disambig target — semantically wrong.
    #
    # For disambiguated entities, require EXPLICIT linking: the writer
    # must type `[[Política (Aristóteles)]]` or `[[Política (Aristóteles)|Política]]`
    # themselves. Returning early keeps the wikify pass conservative.
    if is_disambiguated:
        return BacklinkResult(
            entity_name=entity_name,
            notes_scanned=0,
            notes_linked=0,
            linked_files=(),
        )

    search_term = entity_name
    wikilink = f"[[{entity_name}]]"

    # Build regex: match search term NOT already inside [[ ]]
    escaped = re.escape(search_term)
    pattern = re.compile(
        rf"(?<!\[\[)(?<!\|)\b({escaped})\b(?!\]\])(?!\|)",
        re.IGNORECASE,
    )

    # Skip stems: both the entity's own note and the disambiguation page
    skip_stems = {entity_name.lower(), base_name.lower()}

    for md_file in sorted(vault_path.rglob("*.md")):
        # Skip excluded directories
        if any(part in md_file.parts for part in excluded_parts):
            continue

        # Skip the entity's own note and disambiguation page
        if md_file.stem.lower() in skip_stems:
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
        new_body, count = pattern.subn(wikilink, body, count=1)
        if count == 0:
            continue

        # Update related field in frontmatter (use canonical name)
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
