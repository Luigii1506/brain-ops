"""Monitoring diffs — change detection between snapshots."""

from __future__ import annotations

import difflib
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
    text_diff: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "source_name": self.source_name,
            "has_changes": self.has_changes,
            "previous_hash": self.previous_hash,
            "current_hash": self.current_hash,
            "previous_length": self.previous_length,
            "current_length": self.current_length,
            "summary": self.summary,
            "text_diff": self.text_diff,
        }


def _build_text_diff(previous_content: str, current_content: str, max_lines: int = 50) -> str:
    prev_lines = previous_content.splitlines(keepends=True)
    curr_lines = current_content.splitlines(keepends=True)
    diff_lines = list(difflib.unified_diff(prev_lines, curr_lines, fromfile="previous", tofile="current", n=2))
    if not diff_lines:
        return ""
    if len(diff_lines) > max_lines:
        diff_lines = diff_lines[:max_lines]
        diff_lines.append(f"... ({len(diff_lines)} more lines truncated)\n")
    return "".join(diff_lines)


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
    text_diff = _build_text_diff(previous.content, current.content)
    return SourceDiff(
        source_name=source_name,
        has_changes=True,
        previous_hash=previous.content_hash,
        current_hash=current.content_hash,
        previous_length=previous.content_length,
        current_length=current.content_length,
        summary=f"Content changed ({direction}, delta: {length_delta:+d} chars).",
        text_diff=text_diff or None,
    )


__all__ = [
    "SourceDiff",
    "compute_diff",
]
