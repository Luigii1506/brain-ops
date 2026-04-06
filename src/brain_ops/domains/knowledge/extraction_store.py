"""Extraction record persistence — save full LLM extraction JSON for replay and debugging."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(slots=True, frozen=True)
class ExtractionRecord:
    source_title: str
    source_url: str | None
    source_type: str
    prompt_version: str
    raw_llm_json: dict[str, object]
    created_at: str

    def to_dict(self) -> dict[str, object]:
        return {
            "source_title": self.source_title,
            "source_url": self.source_url,
            "source_type": self.source_type,
            "prompt_version": self.prompt_version,
            "raw_llm_json": self.raw_llm_json,
            "created_at": self.created_at,
        }


def save_extraction_record(
    extractions_dir: Path,
    *,
    source_title: str,
    source_url: str | None,
    source_type: str,
    raw_llm_json: dict[str, object],
    prompt_version: str = "v2",
) -> Path:
    extractions_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    slug = "".join(c if c.isalnum() or c in "-_ " else "" for c in source_title)[:60].strip().replace(" ", "-").lower()
    filename = f"{now.strftime('%Y%m%d-%H%M%S')}-{slug}.json"
    record = ExtractionRecord(
        source_title=source_title,
        source_url=source_url,
        source_type=source_type,
        prompt_version=prompt_version,
        raw_llm_json=raw_llm_json,
        created_at=now.isoformat(),
    )
    path = extractions_dir / filename
    path.write_text(
        json.dumps(record.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


def load_extraction_records(extractions_dir: Path) -> list[ExtractionRecord]:
    if not extractions_dir.exists():
        return []
    records: list[ExtractionRecord] = []
    for path in sorted(extractions_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        records.append(ExtractionRecord(
            source_title=str(data.get("source_title", "")),
            source_url=data.get("source_url"),
            source_type=str(data.get("source_type", "")),
            prompt_version=str(data.get("prompt_version", "")),
            raw_llm_json=data.get("raw_llm_json", {}),
            created_at=str(data.get("created_at", "")),
        ))
    return records


__all__ = [
    "ExtractionRecord",
    "load_extraction_records",
    "save_extraction_record",
]
