from __future__ import annotations

import re
from typing import Any

import yaml

FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    match = FRONTMATTER_PATTERN.match(text)
    if not match:
        return {}, text.strip()

    frontmatter_text, body = match.groups()
    data = yaml.safe_load(frontmatter_text) or {}
    if not isinstance(data, dict):
        raise ValueError("Frontmatter must deserialize to a mapping.")
    return data, body.strip()


def dump_frontmatter(frontmatter: dict[str, Any], body: str) -> str:
    serialized = yaml.safe_dump(frontmatter, sort_keys=False).strip()
    body = body.strip()
    if body:
        return f"---\n{serialized}\n---\n\n{body}\n"
    return f"---\n{serialized}\n---\n"
