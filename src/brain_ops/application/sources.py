"""Application workflows for monitoring source observation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.request import urlopen, Request

from brain_ops.domains.monitoring import (
    MonitorSource,
    SourceDiff,
    SourceSnapshot,
    build_monitor_source,
    build_snapshot,
    compute_diff,
    load_latest_snapshot,
    load_source_registry,
    save_snapshot,
    save_source_registry,
)
from brain_ops.errors import ConfigError


@dataclass(slots=True, frozen=True)
class SourceCheckResult:
    source: MonitorSource
    snapshot: SourceSnapshot
    diff: SourceDiff
    snapshot_path: Path

    def to_dict(self) -> dict[str, object]:
        return {
            "source": self.source.to_dict(),
            "snapshot": self.snapshot.to_dict(),
            "diff": self.diff.to_dict(),
            "snapshot_path": str(self.snapshot_path),
        }


@dataclass(slots=True, frozen=True)
class SourceRegistryResult:
    source: MonitorSource
    registry_path: Path
    is_new: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "source": self.source.to_dict(),
            "registry_path": str(self.registry_path),
            "is_new": self.is_new,
        }


def _default_fetch_content(url: str) -> str:
    request = Request(url, headers={"User-Agent": "brain-ops/1.0"})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def execute_add_source_workflow(
    *,
    name: str,
    url: str,
    source_type: str,
    selector: str | None,
    check_interval: str,
    description: str | None,
    tags: list[str] | None,
    load_registry_path,
) -> SourceRegistryResult:
    registry_path = load_registry_path()
    sources = load_source_registry(registry_path)
    is_new = name.strip() not in sources
    source = build_monitor_source(
        name,
        url=url,
        source_type=source_type,
        selector=selector,
        check_interval=check_interval,
        description=description,
        tags=tags,
    )
    sources[source.name] = source
    save_source_registry(registry_path, sources)
    return SourceRegistryResult(source=source, registry_path=registry_path, is_new=is_new)


def execute_list_sources_workflow(
    *,
    load_registry_path,
) -> list[MonitorSource]:
    registry_path = load_registry_path()
    sources = load_source_registry(registry_path)
    return sorted(sources.values(), key=lambda s: s.name.lower())


def execute_remove_source_workflow(
    *,
    name: str,
    load_registry_path,
) -> MonitorSource:
    registry_path = load_registry_path()
    sources = load_source_registry(registry_path)
    source = sources.pop(name.strip(), None)
    if source is None:
        available = ", ".join(sorted(sources.keys())) if sources else "none"
        raise ConfigError(f"Source '{name}' not found. Available: {available}.")
    save_source_registry(registry_path, sources)
    return source


def execute_check_source_workflow(
    *,
    name: str,
    load_registry_path,
    load_snapshots_dir,
    fetch_content=_default_fetch_content,
    event_sink=None,
) -> SourceCheckResult:
    registry_path = load_registry_path()
    sources = load_source_registry(registry_path)
    source = sources.get(name.strip())
    if source is None:
        available = ", ".join(sorted(sources.keys())) if sources else "none"
        raise ConfigError(f"Source '{name}' not found. Available: {available}.")

    snapshots_dir = load_snapshots_dir()
    previous = load_latest_snapshot(snapshots_dir, source.name)
    raw_content = fetch_content(source.url)
    current = build_snapshot(source.name, raw_content, selector=source.selector)
    diff = compute_diff(source.name, previous=previous, current=current)
    snapshot_path = save_snapshot(snapshots_dir, current)

    if event_sink is not None and diff.has_changes:
        from brain_ops.core.events import new_event

        event_sink.publish(new_event(
            name="source.changed",
            source="application.sources",
            payload={
                "source_name": source.name,
                "url": source.url,
                "has_changes": True,
                "summary": diff.summary,
                "workflow": "check-source",
            },
        ))

    return SourceCheckResult(
        source=source,
        snapshot=current,
        diff=diff,
        snapshot_path=snapshot_path,
    )


def execute_check_all_sources_workflow(
    *,
    load_registry_path,
    load_snapshots_dir,
    fetch_content=_default_fetch_content,
    event_sink=None,
) -> list[SourceCheckResult]:
    registry_path = load_registry_path()
    sources = load_source_registry(registry_path)
    results: list[SourceCheckResult] = []
    for source in sorted(sources.values(), key=lambda s: s.name.lower()):
        snapshots_dir = load_snapshots_dir()
        previous = load_latest_snapshot(snapshots_dir, source.name)
        try:
            raw_content = fetch_content(source.url)
        except Exception:
            continue
        current = build_snapshot(source.name, raw_content, selector=source.selector)
        diff = compute_diff(source.name, previous=previous, current=current)
        snapshot_path = save_snapshot(snapshots_dir, current)

        if event_sink is not None and diff.has_changes:
            from brain_ops.core.events import new_event

            event_sink.publish(new_event(
                name="source.changed",
                source="application.sources",
                payload={
                    "source_name": source.name,
                    "url": source.url,
                    "has_changes": True,
                    "summary": diff.summary,
                    "workflow": "check-all-sources",
                },
            ))

        results.append(SourceCheckResult(
            source=source,
            snapshot=current,
            diff=diff,
            snapshot_path=snapshot_path,
        ))
    return results


__all__ = [
    "SourceCheckResult",
    "SourceRegistryResult",
    "execute_add_source_workflow",
    "execute_check_all_sources_workflow",
    "execute_check_source_workflow",
    "execute_list_sources_workflow",
    "execute_remove_source_workflow",
]
