"""Planning helpers for direct agent-driven enrichment without API calls."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from brain_ops.domains.knowledge.chunking import (
    ContentChunk,
    chunk_by_headings,
    rank_chunks_for_subtype,
)
from brain_ops.domains.knowledge.coverage_check import should_use_deep_mode
from brain_ops.domains.knowledge.multi_pass import EnrichPass, plan_multi_pass_chunks, render_pass_context


@dataclass(slots=True, frozen=True)
class RankedChunk:
    heading: str
    char_count: int
    priority: str
    position: int

    def to_dict(self) -> dict[str, object]:
        return {
            "heading": self.heading,
            "char_count": self.char_count,
            "priority": self.priority,
            "position": self.position,
        }


@dataclass(slots=True, frozen=True)
class DirectEnrichPassPlan:
    pass_number: int
    focus: str
    total_chars: int
    headings: list[str]
    context: str

    def to_dict(self) -> dict[str, object]:
        return {
            "pass_number": self.pass_number,
            "focus": self.focus,
            "total_chars": self.total_chars,
            "headings": list(self.headings),
            "context": self.context,
        }


@dataclass(slots=True, frozen=True)
class DirectEnrichPlan:
    entity_name: str
    source_url: str
    subtype: str
    mode: str
    source_profile: str
    raw_chars: int
    raw_file: str
    pass_plans: list[DirectEnrichPassPlan]
    ranked_chunks: list[RankedChunk]
    workflow_steps: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "entity_name": self.entity_name,
            "source_url": self.source_url,
            "subtype": self.subtype,
            "mode": self.mode,
            "source_profile": self.source_profile,
            "raw_chars": self.raw_chars,
            "raw_file": self.raw_file,
            "passes": [plan.to_dict() for plan in self.pass_plans],
            "ranked_chunks": [chunk.to_dict() for chunk in self.ranked_chunks],
            "workflow_steps": list(self.workflow_steps),
        }


def build_direct_enrich_plan(
    *,
    entity_name: str,
    source_url: str,
    raw_text: str,
    raw_file: Path,
    subtype: str,
    planning_chunks: list[ContentChunk] | None = None,
    source_profile: str = "generic_html",
) -> DirectEnrichPlan:
    raw_chunks = planning_chunks or chunk_by_headings(raw_text)
    passes = plan_multi_pass_chunks(raw_chunks, fallback_text=raw_text)
    ranked = rank_chunks_for_subtype(raw_chunks, subtype, max_chars=8000)
    mode = "deep" if should_use_deep_mode(subtype, len(raw_text)) else "light"

    pass_plans = [
        DirectEnrichPassPlan(
            pass_number=enrich_pass.pass_number,
            focus=enrich_pass.focus,
            total_chars=enrich_pass.total_chars,
            headings=[chunk.heading for chunk in enrich_pass.chunks],
            context=render_pass_context(enrich_pass),
        )
        for enrich_pass in passes
    ]

    ranked_chunks = [
        RankedChunk(
            heading=chunk.heading,
            char_count=chunk.char_count,
            priority=chunk.priority,
            position=chunk.position,
        )
        for chunk in ranked
    ]

    workflow_steps = [
        "Run this plan before writing directly as the LLM.",
        "Write the entity note pass by pass using the planned contexts in order.",
        "Preserve structured sections and keep frontmatter related links updated.",
        "After writing, run brain post-process with the same source URL.",
        "Then run brain check-coverage and fill any high-priority gaps if needed.",
    ]

    return DirectEnrichPlan(
        entity_name=entity_name,
        source_url=source_url,
        subtype=subtype,
        mode=mode,
        source_profile=source_profile,
        raw_chars=len(raw_text),
        raw_file=str(raw_file),
        pass_plans=pass_plans,
        ranked_chunks=ranked_chunks,
        workflow_steps=workflow_steps,
    )


def save_direct_enrich_plan(plans_dir: Path, plan: DirectEnrichPlan) -> Path:
    plans_dir.mkdir(parents=True, exist_ok=True)
    slug = "".join(c if c.isalnum() or c in "-_ " else "" for c in plan.entity_name)[:60].strip().replace(" ", "-").lower()
    path = plans_dir / f"{slug}.json"
    path.write_text(json.dumps(plan.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


__all__ = [
    "DirectEnrichPassPlan",
    "DirectEnrichPlan",
    "RankedChunk",
    "build_direct_enrich_plan",
    "save_direct_enrich_plan",
]
