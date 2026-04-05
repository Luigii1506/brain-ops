"""Monitoring domain — source observation, snapshots, and change detection."""

from .sources import (
    MonitorSource,
    SOURCE_TYPES,
    build_monitor_source,
    load_source_registry,
    save_source_registry,
)
from .snapshots import (
    SourceSnapshot,
    build_snapshot,
    load_latest_snapshot,
    save_snapshot,
)
from .diffs import (
    SourceDiff,
    compute_diff,
)

__all__ = [
    "MonitorSource",
    "SOURCE_TYPES",
    "SourceDiff",
    "SourceSnapshot",
    "build_monitor_source",
    "build_snapshot",
    "compute_diff",
    "load_latest_snapshot",
    "load_source_registry",
    "save_snapshot",
    "save_source_registry",
]
