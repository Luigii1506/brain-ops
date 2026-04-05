from __future__ import annotations

from typing import Literal

EnrichmentStep = Literal["improve", "research", "apply_links"]


def plan_enrichment_steps(
    *,
    improve: bool,
    research: bool,
    apply_links: bool,
) -> list[EnrichmentStep]:
    steps: list[EnrichmentStep] = []
    if improve:
        steps.append("improve")
    if research:
        steps.append("research")
    if apply_links:
        steps.append("apply_links")
    return steps


def describe_improve_step(reason: str) -> str:
    return f"improve-note: {reason}"


def describe_research_step(source_count: int) -> str:
    return f"research-note: attached {source_count} source(s)"


def describe_apply_links_step(applied_links_count: int) -> str:
    return f"apply-link-suggestions: inserted {applied_links_count} link(s)"
