"""Monitoring snapshots — captured state of a source at a point in time."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(slots=True, frozen=True)
class SourceSnapshot:
    source_name: str
    captured_at: str
    content_hash: str
    content: str
    content_length: int

    def to_dict(self) -> dict[str, object]:
        return {
            "source_name": self.source_name,
            "captured_at": self.captured_at,
            "content_hash": self.content_hash,
            "content_length": self.content_length,
        }

    def to_full_dict(self) -> dict[str, object]:
        d = self.to_dict()
        d["content"] = self.content
        return d

    @staticmethod
    def from_dict(data: dict[str, object]) -> SourceSnapshot:
        content = str(data.get("content", ""))
        return SourceSnapshot(
            source_name=str(data.get("source_name", "")),
            captured_at=str(data.get("captured_at", "")),
            content_hash=str(data.get("content_hash", "")),
            content=content,
            content_length=int(data.get("content_length", len(content))),
        )


def extract_with_selector(html: str, selector: str | None) -> str:
    if not selector:
        return html
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        elements = soup.select(selector)
        if not elements:
            return html
        return "\n".join(el.get_text(separator="\n", strip=True) for el in elements)
    except Exception:
        return html


def build_snapshot(source_name: str, content: str, *, selector: str | None = None) -> SourceSnapshot:
    extracted = extract_with_selector(content, selector)
    return SourceSnapshot(
        source_name=source_name,
        captured_at=datetime.now(timezone.utc).isoformat(),
        content_hash=hashlib.sha256(extracted.encode("utf-8")).hexdigest(),
        content=extracted,
        content_length=len(extracted),
    )


def load_latest_snapshot(snapshots_dir: Path, source_name: str) -> SourceSnapshot | None:
    snapshot_path = snapshots_dir / f"{source_name}-latest.json"
    if not snapshot_path.exists():
        return None
    data = json.loads(snapshot_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return None
    return SourceSnapshot.from_dict(data)


def save_snapshot(snapshots_dir: Path, snapshot: SourceSnapshot) -> Path:
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = snapshots_dir / f"{snapshot.source_name}-latest.json"
    snapshot_path.write_text(
        json.dumps(snapshot.to_full_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return snapshot_path


__all__ = [
    "SourceSnapshot",
    "build_snapshot",
    "extract_with_selector",
    "load_latest_snapshot",
    "save_snapshot",
]
