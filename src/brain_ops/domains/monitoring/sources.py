"""Monitoring source definitions and registry."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

SOURCE_TYPES = {"web", "api"}


@dataclass(slots=True)
class MonitorSource:
    name: str
    url: str
    source_type: str
    selector: str | None = None
    check_interval: str = "daily"
    description: str | None = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "url": self.url,
            "source_type": self.source_type,
            "selector": self.selector,
            "check_interval": self.check_interval,
            "description": self.description,
            "tags": list(self.tags),
        }

    @staticmethod
    def from_dict(data: dict[str, object]) -> MonitorSource:
        return MonitorSource(
            name=str(data.get("name", "")),
            url=str(data.get("url", "")),
            source_type=str(data.get("source_type", "web")),
            selector=data.get("selector") if isinstance(data.get("selector"), str) else None,
            check_interval=str(data.get("check_interval", "daily")),
            description=data.get("description") if isinstance(data.get("description"), str) else None,
            tags=list(data.get("tags", [])),
        )


def build_monitor_source(
    name: str,
    *,
    url: str,
    source_type: str = "web",
    selector: str | None = None,
    check_interval: str = "daily",
    description: str | None = None,
    tags: list[str] | None = None,
) -> MonitorSource:
    if not name.strip():
        raise ValueError("Source name cannot be empty.")
    if not url.strip():
        raise ValueError("Source URL cannot be empty.")
    normalized_type = source_type.strip().lower()
    if normalized_type not in SOURCE_TYPES:
        allowed = ", ".join(sorted(SOURCE_TYPES))
        raise ValueError(f"Unknown source type '{source_type}'. Expected one of: {allowed}.")
    return MonitorSource(
        name=name.strip(),
        url=url.strip(),
        source_type=normalized_type,
        selector=selector,
        check_interval=check_interval.strip().lower() if check_interval else "daily",
        description=description,
        tags=tags or [],
    )


def load_source_registry(registry_path: Path) -> dict[str, MonitorSource]:
    if not registry_path.exists():
        return {}
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}
    return {
        name: MonitorSource.from_dict(source_data)
        for name, source_data in data.items()
        if isinstance(source_data, dict)
    }


def save_source_registry(registry_path: Path, sources: dict[str, MonitorSource]) -> Path:
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {name: source.to_dict() for name, source in sources.items()}
    registry_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return registry_path


__all__ = [
    "MonitorSource",
    "SOURCE_TYPES",
    "build_monitor_source",
    "load_source_registry",
    "save_source_registry",
]
