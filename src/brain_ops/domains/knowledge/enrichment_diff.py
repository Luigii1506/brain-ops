"""Enrichment diffs — track what changed in each enrichment pass."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass(slots=True, frozen=True)
class SectionDiff:
    section: str
    before_length: int
    after_length: int
    was_empty: bool
    is_new_content: bool
    delta_chars: int


@dataclass(slots=True, frozen=True)
class EnrichmentDiff:
    entity_name: str
    source_url: str | None
    timestamp: str
    total_sections_changed: int
    total_chars_added: int
    new_wikilinks: list[str]
    section_diffs: list[SectionDiff]

    def to_dict(self) -> dict[str, object]:
        return {
            "entity_name": self.entity_name,
            "source_url": self.source_url,
            "timestamp": self.timestamp,
            "total_sections_changed": self.total_sections_changed,
            "total_chars_added": self.total_chars_added,
            "new_wikilinks": list(self.new_wikilinks),
            "section_diffs": [
                {
                    "section": sd.section,
                    "before_length": sd.before_length,
                    "after_length": sd.after_length,
                    "was_empty": sd.was_empty,
                    "is_new_content": sd.is_new_content,
                    "delta_chars": sd.delta_chars,
                }
                for sd in self.section_diffs
            ],
        }


def _extract_sections(body: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current_heading = "_preamble"
    current_lines: list[str] = []
    for line in body.splitlines():
        match = re.match(r"^##\s+(.+)", line)
        if match:
            sections[current_heading] = "\n".join(current_lines).strip()
            current_heading = match.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)
    sections[current_heading] = "\n".join(current_lines).strip()
    return sections


def _extract_wikilinks(text: str) -> set[str]:
    return set(re.findall(r"\[\[([^\]]+)\]\]", text))


def compute_enrichment_diff(
    entity_name: str,
    before_body: str,
    after_body: str,
    *,
    source_url: str | None = None,
) -> EnrichmentDiff:
    before_sections = _extract_sections(before_body)
    after_sections = _extract_sections(after_body)
    before_links = _extract_wikilinks(before_body)
    after_links = _extract_wikilinks(after_body)

    section_diffs: list[SectionDiff] = []
    total_chars_added = 0

    all_sections = set(before_sections.keys()) | set(after_sections.keys())
    for section in sorted(all_sections):
        if section == "_preamble":
            continue
        before_text = before_sections.get(section, "")
        after_text = after_sections.get(section, "")
        if before_text == after_text:
            continue
        delta = len(after_text) - len(before_text)
        section_diffs.append(SectionDiff(
            section=section,
            before_length=len(before_text),
            after_length=len(after_text),
            was_empty=len(before_text.strip()) == 0,
            is_new_content=section not in before_sections,
            delta_chars=delta,
        ))
        total_chars_added += max(delta, 0)

    new_wikilinks = sorted(after_links - before_links)

    return EnrichmentDiff(
        entity_name=entity_name,
        source_url=source_url,
        timestamp=datetime.now(timezone.utc).isoformat(),
        total_sections_changed=len(section_diffs),
        total_chars_added=total_chars_added,
        new_wikilinks=new_wikilinks,
        section_diffs=section_diffs,
    )


def save_enrichment_diff(diffs_dir: Path, diff: EnrichmentDiff) -> Path:
    diffs_dir.mkdir(parents=True, exist_ok=True)
    slug = "".join(c if c.isalnum() or c in "-_ " else "" for c in diff.entity_name)[:40].strip().replace(" ", "-").lower()
    ts = diff.timestamp[:19].replace(":", "").replace("-", "")
    filename = f"{ts}-{slug}.json"
    path = diffs_dir / filename
    path.write_text(
        json.dumps(diff.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


__all__ = [
    "EnrichmentDiff",
    "SectionDiff",
    "compute_enrichment_diff",
    "save_enrichment_diff",
]
