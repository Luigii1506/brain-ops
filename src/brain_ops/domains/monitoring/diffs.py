"""Monitoring diffs — change detection between snapshots."""

from __future__ import annotations

from dataclasses import dataclass

from .snapshots import SourceSnapshot


@dataclass(slots=True, frozen=True)
class SourceDiff:
    source_name: str
    has_changes: bool
    previous_hash: str | None
    current_hash: str
    previous_length: int | None
    current_length: int
    summary: str

    def to_dict(self) -> dict[str, object]:
        return {
            "source_name": self.source_name,
            "has_changes": self.has_changes,
            "previous_hash": self.previous_hash,
            "current_hash": self.current_hash,
            "previous_length": self.previous_length,
            "current_length": self.current_length,
            "summary": self.summary,
        }


def compute_diff(
    source_name: str,
    *,
    previous: SourceSnapshot | None,
    current: SourceSnapshot,
) -> SourceDiff:
    if previous is None:
        return SourceDiff(
            source_name=source_name,
            has_changes=True,
            previous_hash=None,
            current_hash=current.content_hash,
            previous_length=None,
            current_length=current.content_length,
            summary=f"First snapshot captured ({current.content_length} chars).",
        )
    if previous.content_hash == current.content_hash:
        return SourceDiff(
            source_name=source_name,
            has_changes=False,
            previous_hash=previous.content_hash,
            current_hash=current.content_hash,
            previous_length=previous.content_length,
            current_length=current.content_length,
            summary="No changes detected.",
        )
    length_delta = current.content_length - previous.content_length
    direction = "grew" if length_delta > 0 else "shrank" if length_delta < 0 else "same size"
    return SourceDiff(
        source_name=source_name,
        has_changes=True,
        previous_hash=previous.content_hash,
        current_hash=current.content_hash,
        previous_length=previous.content_length,
        current_length=current.content_length,
        summary=f"Content changed ({direction}, delta: {length_delta:+d} chars).",
    )


__all__ = [
    "SourceDiff",
    "compute_diff",
]
