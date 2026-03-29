from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field


class OperationStatus(StrEnum):
    CREATED = "created"
    UPDATED = "updated"
    MOVED = "moved"
    SKIPPED = "skipped"
    REPORT = "report"


class OperationRecord(BaseModel):
    action: str
    path: Path
    detail: str
    status: OperationStatus


class CreateNoteRequest(BaseModel):
    title: str
    note_type: str = "permanent_note"
    folder: str | None = None
    template_name: str | None = None
    tags: list[str] = Field(default_factory=list)
    extra_frontmatter: dict[str, object] = Field(default_factory=dict)
    body_override: str | None = None
    overwrite: bool = False


class InboxItemResult(BaseModel):
    source_path: Path
    destination_path: Path | None = None
    note_type: str | None = None
    moved: bool = False
    normalized: bool = False
    reason: str


class InboxProcessSummary(BaseModel):
    scanned: int = 0
    normalized: int = 0
    moved: int = 0
    left_in_inbox: int = 0
    items: list[InboxItemResult] = Field(default_factory=list)
    operations: list[OperationRecord] = Field(default_factory=list)


class WeeklyReviewSummary(BaseModel):
    generated_at: datetime
    inbox_notes: list[Path] = Field(default_factory=list)
    notes_missing_frontmatter: list[Path] = Field(default_factory=list)
    stale_project_notes: list[Path] = Field(default_factory=list)
    possible_orphans: list[Path] = Field(default_factory=list)
    recent_changes: list[Path] = Field(default_factory=list)
    operations: list[OperationRecord] = Field(default_factory=list)


class FolderAuditStats(BaseModel):
    total: int = 0
    with_frontmatter: int = 0
    empty: int = 0
    very_short: int = 0


class AuditFinding(BaseModel):
    path: Path
    reason: str


class VaultAuditSummary(BaseModel):
    generated_at: datetime
    total_notes: int = 0
    with_frontmatter: int = 0
    empty_notes: list[Path] = Field(default_factory=list)
    very_short_notes: list[Path] = Field(default_factory=list)
    notes_missing_frontmatter: list[Path] = Field(default_factory=list)
    invalid_frontmatter: list[AuditFinding] = Field(default_factory=list)
    moc_outside_maps: list[Path] = Field(default_factory=list)
    maps_with_few_links: list[AuditFinding] = Field(default_factory=list)
    system_notes_outside_systems: list[Path] = Field(default_factory=list)
    source_notes_outside_sources: list[Path] = Field(default_factory=list)
    notes_with_unknown_type: list[AuditFinding] = Field(default_factory=list)
    notes_in_root: list[Path] = Field(default_factory=list)
    folder_stats: dict[str, FolderAuditStats] = Field(default_factory=dict)
    operations: list[OperationRecord] = Field(default_factory=list)


class NormalizeFrontmatterSummary(BaseModel):
    scanned: int = 0
    updated: int = 0
    skipped: int = 0
    invalid: list[AuditFinding] = Field(default_factory=list)
    operations: list[OperationRecord] = Field(default_factory=list)


class CaptureResult(BaseModel):
    title: str
    note_type: str
    path: Path
    operation: OperationRecord
    reason: str


class ImproveNoteResult(BaseModel):
    path: Path
    note_type: str
    operation: OperationRecord
    reason: str


class ResearchSource(BaseModel):
    title: str
    url: str
    summary: str


class ResearchNoteResult(BaseModel):
    path: Path
    query: str
    sources: list[ResearchSource] = Field(default_factory=list)
    operation: OperationRecord
    reason: str


class LinkSuggestion(BaseModel):
    path: Path
    score: float
    reason: str


class LinkSuggestionResult(BaseModel):
    target: Path
    suggestions: list[LinkSuggestion] = Field(default_factory=list)
    operation: OperationRecord
    reason: str


class ApplyLinksResult(BaseModel):
    target: Path
    applied_links: list[str] = Field(default_factory=list)
    operation: OperationRecord
    reason: str


class PromoteNoteResult(BaseModel):
    source_path: Path
    promoted_path: Path
    promoted_type: str
    operations: list[OperationRecord] = Field(default_factory=list)
    reason: str


class EnrichNoteResult(BaseModel):
    path: Path
    operations: list[OperationRecord] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
    reason: str
