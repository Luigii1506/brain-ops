"""Message builders for CLI output."""

from __future__ import annotations

from brain_ops.services.capture_service import CaptureResult
from brain_ops.services.improve_service import ImproveNoteResult
from brain_ops.services.research_service import ResearchNoteResult


def capture_result_lines(result: CaptureResult) -> list[str]:
    return [
        f"Captured as `{result.note_type}`: {result.title}",
        f"Reason: {result.reason}",
    ]


def improve_result_lines(result: ImproveNoteResult) -> list[str]:
    return [
        f"Improved `{result.note_type}` note: {result.path}",
        f"Reason: {result.reason}",
    ]


def research_result_lines(result: ResearchNoteResult) -> list[str]:
    return [
        f"Researched note: {result.path}",
        f"Query: {result.query}",
        f"Sources attached: {len(result.sources)}",
        f"Reason: {result.reason}",
    ]


__all__ = [
    "capture_result_lines",
    "improve_result_lines",
    "research_result_lines",
]
