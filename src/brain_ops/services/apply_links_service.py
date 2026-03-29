from __future__ import annotations

import re
from pathlib import Path

from brain_ops.frontmatter import dump_frontmatter, split_frontmatter
from brain_ops.models import ApplyLinksResult
from brain_ops.services.link_service import suggest_links
from brain_ops.vault import Vault, now_iso

SECTION_PATTERNS = [
    re.compile(r"^## Links\s*$", re.MULTILINE),
    re.compile(r"^## Related notes\s*$", re.MULTILINE),
    re.compile(r"^## Entry points\s*$", re.MULTILINE),
]


def apply_link_suggestions(vault: Vault, note_path: Path, limit: int = 3) -> ApplyLinksResult:
    path = note_path.expanduser()
    if not path.is_absolute():
        path = vault.root / path
    safe_path = vault._safe_path(path)
    relative = vault.relative_path(safe_path)
    text = safe_path.read_text(encoding="utf-8", errors="ignore")
    frontmatter, body = split_frontmatter(text)

    suggestion_result = suggest_links(vault, safe_path, limit=limit)
    applied = [suggestion.path.stem for suggestion in suggestion_result.suggestions]
    updated_body = _insert_links(body, applied)

    if frontmatter.get("created") in (None, ""):
        frontmatter["created"] = now_iso()
    frontmatter["updated"] = now_iso()
    frontmatter.setdefault("tags", [])

    operation = vault.write_text(safe_path, dump_frontmatter(frontmatter, updated_body), overwrite=True)
    return ApplyLinksResult(
        target=relative,
        applied_links=applied,
        operation=operation,
        reason=f"Applied {len(applied)} suggested link(s).",
    )


def _insert_links(body: str, link_titles: list[str]) -> str:
    if not link_titles:
        return body.strip()

    lines = body.splitlines()
    existing = set(re.findall(r"\[\[([^\]|#]+)", body))
    links_to_add = [title for title in link_titles if title not in existing]
    if not links_to_add:
        return body.strip()

    for pattern in SECTION_PATTERNS:
        for index, line in enumerate(lines):
            if pattern.match(line):
                insert_at = index + 1
                while insert_at < len(lines) and lines[insert_at].strip() == "":
                    insert_at += 1
                additions = [f"- [[{title}]]" for title in links_to_add]
                lines[insert_at:insert_at] = [""] + additions
                return "\n".join(lines).strip()

    additions = "\n".join(f"- [[{title}]]" for title in links_to_add)
    suffix = "\n\n## Links\n\n" + additions
    return body.strip() + suffix
