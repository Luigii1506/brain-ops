from __future__ import annotations


def apply_note_frontmatter_defaults(
    frontmatter: dict[str, object],
    *,
    now: str,
    note_type: str | None = None,
    tags: list[str] | None = None,
) -> dict[str, object]:
    updated_frontmatter = dict(frontmatter)
    if note_type is not None:
        updated_frontmatter.setdefault("type", note_type)
    if updated_frontmatter.get("created") in (None, ""):
        updated_frontmatter["created"] = now
    updated_frontmatter["updated"] = now
    if tags is not None:
        updated_frontmatter["tags"] = tags
    else:
        updated_frontmatter.setdefault("tags", [])
    return updated_frontmatter


def apply_note_frontmatter_defaults_with_change(
    frontmatter: dict[str, object],
    *,
    now: str,
    note_type: str | None = None,
    tags: list[str] | None = None,
) -> tuple[dict[str, object], bool]:
    updated_frontmatter = apply_note_frontmatter_defaults(
        frontmatter,
        now=now,
        note_type=note_type,
        tags=tags,
    )
    return updated_frontmatter, updated_frontmatter != frontmatter
