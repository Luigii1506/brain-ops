from __future__ import annotations

import re

SECTION_PATTERN = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


def default_target_type(source_type: str, frontmatter: dict[str, object]) -> str:
    if source_type == "source":
        return "knowledge"
    if source_type == "knowledge" and str(frontmatter.get("status", "")).lower() == "stub":
        return "knowledge"
    return source_type


def normalize_promoted_title(title: str) -> str:
    cleaned = re.sub(r"^SN-", "", title, flags=re.IGNORECASE).strip()
    return cleaned or title


def extract_sections(body: str) -> dict[str, str]:
    matches = list(SECTION_PATTERN.finditer(body))
    if not matches:
        return {}

    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        sections[match.group(1).strip()] = body[start:end].strip()
    return sections


def ensure_related_note_link(body: str, promoted_title: str) -> str:
    target_link = f"[[{promoted_title}]]"
    if target_link in body:
        return body.strip()

    if re.search(r"^## Related notes\s*$", body, flags=re.MULTILINE):
        lines = body.splitlines()
        for index, line in enumerate(lines):
            if line.strip() == "## Related notes":
                insert_at = index + 1
                while insert_at < len(lines) and lines[insert_at].strip() == "":
                    insert_at += 1
                lines[insert_at:insert_at] = ["", f"- {target_link}"]
                return "\n".join(lines).strip()

    suffix = "\n\n## Related notes\n\n- " + target_link
    return body.strip() + suffix


def build_promoted_knowledge_body(
    *,
    promoted_title: str,
    source_title: str,
    summary: str,
    key_ideas: str,
    source_block: str,
    original_body: str,
) -> str:
    promoted_body_parts = [
        f"# {promoted_title}",
        "",
        "## Core idea",
        "",
        summary or f"Derived from [[{source_title}]].",
        "",
        "## Key ideas",
        "",
        key_ideas or "- Extract the durable idea from the source.",
        "",
        "## Why it matters",
        "",
        "",
        "## Sources",
        "",
        f"- [[{source_title}]]",
    ]
    if source_block and source_block != original_body.strip():
        promoted_body_parts.extend(["", "## Source context", "", source_block])
    promoted_body_parts.extend(["", "## Links"])
    return "\n".join(promoted_body_parts)


def materialize_source_promotion(
    frontmatter: dict[str, object],
    body: str,
    promoted_title: str,
    *,
    now: str,
) -> tuple[dict[str, object], str]:
    updated_frontmatter = dict(frontmatter)
    if updated_frontmatter.get("created") in (None, ""):
        updated_frontmatter["created"] = now
    updated_frontmatter["updated"] = now
    updated_frontmatter.setdefault("tags", [])
    updated_frontmatter["promoted_to"] = promoted_title
    return updated_frontmatter, ensure_related_note_link(body, promoted_title)


def materialize_stub_promotion(
    frontmatter: dict[str, object],
    body: str,
    *,
    now: str,
) -> tuple[dict[str, object], str]:
    updated_frontmatter = dict(frontmatter)
    if updated_frontmatter.get("created") in (None, ""):
        updated_frontmatter["created"] = now
    updated_frontmatter["updated"] = now
    updated_frontmatter.setdefault("tags", [])
    updated_frontmatter.setdefault("type", "knowledge")
    updated_frontmatter["status"] = "draft"
    return updated_frontmatter, body
