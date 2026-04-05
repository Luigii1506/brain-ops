from __future__ import annotations

from dataclasses import dataclass
import re
from urllib.parse import urlparse

URL_PATTERN = re.compile(r"https?://\S+")


@dataclass(slots=True)
class CapturePlan:
    title: str
    note_type: str
    reason: str
    body: str
    extra_frontmatter: dict[str, object]


def infer_capture_type(text: str, force_type: str | None = None) -> tuple[str, str]:
    if force_type:
        return force_type, f"Forced type `{force_type}`."

    lowered = text.lower()
    has_url = bool(URL_PATTERN.search(text))
    if has_url or any(keyword in lowered for keyword in ["artículo", "article", "video", "youtube", "podcast", "libro", "book", "paper", "wikipedia", "documentación", "docs"]):
        return "source", "Detected external source-like language."
    if any(keyword in lowered for keyword in ["comando", "command", "terminal", "docker", "webhook"]):
        return "command", "Detected command-oriented language."
    if any(keyword in lowered for keyword in ["script", "runbook", "workflow", "deploy"]):
        return "system", "Detected operational or workflow-oriented language."
    if any(keyword in lowered for keyword in ["proyecto", "project", "repo", "feature", "roadmap", "sprint"]):
        return "project", "Detected project-oriented language."
    if any(keyword in lowered for keyword in ["moc", "índice", "indice", "mapa", "hub", "overview"]):
        return "map", "Detected navigation or map-oriented language."
    return "knowledge", "Defaulted to durable knowledge."


def infer_capture_title(text: str, note_type: str) -> str:
    first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
    candidate = re.sub(r"^(aprend[ií]\s+que|nota sobre|quiero una nota de|captura:)\s+", "", first_line, flags=re.IGNORECASE)
    candidate = re.sub(r"https?://\S+", "", candidate).strip(" -:#.")
    if len(candidate) > 90:
        candidate = candidate[:90].rsplit(" ", 1)[0].strip()
    if candidate:
        return candidate[:100]
    return {
        "source": "Captured Source",
        "system": "Captured System Note",
        "project": "Captured Project Note",
        "map": "Captured Map",
    }.get(note_type, "Captured Knowledge")


def build_capture_frontmatter(text: str, note_type: str) -> dict[str, object]:
    extra: dict[str, object] = {}
    if note_type == "source":
        url = _extract_first_url(text)
        if url:
            extra["url"] = [url]
            domain = urlparse(url).netloc.lower()
            if "youtube" in domain or "youtu.be" in domain:
                extra["source_type"] = "youtube"
            elif "wikipedia" in domain:
                extra["source_type"] = "wikipedia"
            else:
                extra["source_type"] = "web"
    if note_type == "knowledge":
        extra["status"] = "draft"
    if note_type == "project":
        extra["status"] = "active"
    if note_type == "map":
        extra["status"] = "seed"
    if note_type == "system":
        extra["status"] = "draft"
    return extra


def build_capture_body(text: str, note_type: str) -> str:
    stripped = text.strip()
    if note_type == "source":
        return "\n".join(
            [
                "## Source",
                "",
                stripped,
                "",
                "## Summary",
                "",
                "## Key ideas",
                "",
                "## Related notes",
            ]
        )
    if note_type == "system":
        return "\n".join(
            [
                "## Objective",
                "",
                stripped,
                "",
                "## Procedure",
                "",
                "## Related notes",
            ]
        )
    if note_type == "project":
        return "\n".join(
            [
                "## Objective",
                "",
                stripped,
                "",
                "## Current status",
                "",
                "## Next action",
                "",
                "## Related notes",
            ]
        )
    if note_type == "map":
        return "\n".join(
            [
                "## Purpose",
                "",
                stripped,
                "",
                "## Entry points",
                "",
                "## Related notes",
            ]
        )
    return "\n".join(
        [
            "## Core idea",
            "",
            stripped,
            "",
            "## Why it matters",
            "",
            "## Links",
        ]
    )


def _extract_first_url(text: str) -> str | None:
    match = URL_PATTERN.search(text)
    return match.group(0) if match else None


def plan_capture_note(
    text: str,
    *,
    title: str | None = None,
    force_type: str | None = None,
) -> CapturePlan:
    raw_text = text.strip()
    if not raw_text:
        raise ValueError("Capture text cannot be empty.")

    note_type, reason = infer_capture_type(raw_text, force_type)
    resolved_title = title or infer_capture_title(raw_text, note_type)
    return CapturePlan(
        title=resolved_title,
        note_type=note_type,
        reason=reason,
        body=build_capture_body(raw_text, note_type),
        extra_frontmatter=build_capture_frontmatter(raw_text, note_type),
    )
