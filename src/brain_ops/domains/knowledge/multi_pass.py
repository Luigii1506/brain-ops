"""Multi-pass enrichment — process long sources in multiple focused passes."""

from __future__ import annotations

from dataclasses import dataclass

from .chunking import ContentChunk, chunk_by_headings


@dataclass(slots=True, frozen=True)
class EnrichPass:
    pass_number: int
    focus: str
    chunks: list[ContentChunk]
    total_chars: int

    def to_dict(self) -> dict[str, object]:
        return {
            "pass_number": self.pass_number,
            "focus": self.focus,
            "total_chars": self.total_chars,
            "chunk_count": len(self.chunks),
            "headings": [c.heading for c in self.chunks],
        }


def plan_multi_pass(
    text: str,
    *,
    max_chars_per_pass: int = 6000,
) -> list[EnrichPass]:
    """Plan multiple enrichment passes for a long source text."""
    chunks = chunk_by_headings(text)

    if not chunks:
        return [EnrichPass(
            pass_number=1,
            focus="General content",
            chunks=[ContentChunk(heading="Content", text=text[:max_chars_per_pass], char_count=min(len(text), max_chars_per_pass))],
            total_chars=min(len(text), max_chars_per_pass),
        )]

    total_chars = sum(c.char_count for c in chunks)

    # If it fits in one pass, no need for multi-pass
    if total_chars <= max_chars_per_pass:
        return [EnrichPass(
            pass_number=1,
            focus="Full content",
            chunks=chunks,
            total_chars=total_chars,
        )]

    # Group chunks into passes
    passes: list[EnrichPass] = []
    current_chunks: list[ContentChunk] = []
    current_chars = 0
    pass_num = 1

    for chunk in chunks:
        if current_chars + chunk.char_count > max_chars_per_pass and current_chunks:
            focus = _infer_focus(current_chunks)
            passes.append(EnrichPass(
                pass_number=pass_num,
                focus=focus,
                chunks=list(current_chunks),
                total_chars=current_chars,
            ))
            pass_num += 1
            current_chunks = []
            current_chars = 0

        # If a single chunk is too large, truncate it
        if chunk.char_count > max_chars_per_pass:
            truncated = ContentChunk(
                heading=chunk.heading,
                text=chunk.text[:max_chars_per_pass],
                char_count=max_chars_per_pass,
            )
            current_chunks.append(truncated)
            current_chars += max_chars_per_pass
        else:
            current_chunks.append(chunk)
            current_chars += chunk.char_count

    if current_chunks:
        focus = _infer_focus(current_chunks)
        passes.append(EnrichPass(
            pass_number=pass_num,
            focus=focus,
            chunks=list(current_chunks),
            total_chars=current_chars,
        ))

    return passes


def render_pass_context(enrich_pass: EnrichPass) -> str:
    """Render a pass's chunks as context text for the LLM."""
    parts: list[str] = []
    for chunk in enrich_pass.chunks:
        parts.append(f"[{chunk.heading}]\n{chunk.text}")
    return "\n\n".join(parts)


def _infer_focus(chunks: list[ContentChunk]) -> str:
    """Infer a human-readable focus label from chunk headings."""
    headings = [c.heading for c in chunks]
    if len(headings) <= 3:
        return ", ".join(headings)
    return f"{headings[0]} ... {headings[-1]} ({len(headings)} sections)"


__all__ = [
    "EnrichPass",
    "plan_multi_pass",
    "render_pass_context",
]
