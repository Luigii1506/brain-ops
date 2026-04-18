"""Typed-relation parsing for Campaña 2.0.

Parses the `relationships:` field from a note's frontmatter (structural
source of truth per `docs/operations/RELATIONS_FORMAT.md`) and produces a
list of `TypedRelation` objects suitable for downstream compilation into
SQLite.

Accepted input shapes for each list entry:

    1. Compact inline dict:
       - {predicate: studied_under, object: Platón}

    2. Multi-line block dict:
       - predicate: reacted_against
         object: Platón
         reason: Crítica a la teoría de las Formas
         confidence: high

Unknown optional keys are preserved in `TypedRelation.extra` for future
extensions without schema changes.

Validation is tolerant: malformed entries do NOT raise — they surface in
`RelationsParseResult.errors` so the caller can decide what to do (the
linter surfaces them; the compiler skips them).

Uniqueness for typed relations is by the key `(source, predicate, object)`.
Multiple predicates between the same subject-object pair are legitimate
(e.g., `allied_with` AND `opposed` on Marco Antonio across time).

See also:
    - `CANONICAL_PREDICATES` in `object_model.py`
    - `docs/operations/RELATIONS_FORMAT.md`
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .object_model import CANONICAL_PREDICATES


# Optional keys recognized per entry. Unknown keys go into `extra`.
_KNOWN_KEYS: frozenset[str] = frozenset({
    "predicate", "object", "reason", "date", "confidence", "source_id",
})

_VALID_CONFIDENCE: frozenset[str] = frozenset({"high", "medium", "low"})

_DEFAULT_CONFIDENCE = "medium"


@dataclass(slots=True, frozen=True)
class TypedRelation:
    """A single typed relation emitted from frontmatter `relationships:`.

    The `source` is set by the caller (the note owner). Parser returns
    relations with `source` pre-filled from the note name.
    """

    source: str
    predicate: str
    object: str
    reason: str | None = None
    date: str | None = None
    confidence: str = _DEFAULT_CONFIDENCE
    source_id: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def dedup_key(self) -> tuple[str, str, str]:
        """Uniqueness key per user-approved design (Campaña 2.0)."""
        return (self.source, self.predicate, self.object)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "predicate": self.predicate,
            "object": self.object,
            "reason": self.reason,
            "date": self.date,
            "confidence": self.confidence,
            "source_id": self.source_id,
            "extra": dict(self.extra) if self.extra else {},
        }


@dataclass(slots=True)
class ParseError:
    """A recoverable issue in a single `relationships:` entry."""

    index: int                 # Position in the list
    kind: str                  # "invalid_shape", "unknown_predicate", "missing_field", etc.
    message: str
    raw: Any = None            # The offending entry, for debugging


@dataclass(slots=True)
class RelationsParseResult:
    """Outcome of parsing a note's `relationships:` field."""

    source: str
    typed: list[TypedRelation] = field(default_factory=list)
    errors: list[ParseError] = field(default_factory=list)
    duplicates: list[TypedRelation] = field(default_factory=list)
    self_references: list[TypedRelation] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)

    @property
    def has_duplicates(self) -> bool:
        return bool(self.duplicates)

    @property
    def has_self_references(self) -> bool:
        return bool(self.self_references)


def parse_relationships(
    source: str,
    frontmatter: dict[str, Any],
) -> RelationsParseResult:
    """Parse `frontmatter['relationships']` into typed relations for `source`.

    Parameters
    ----------
    source
        The note's canonical `name`. Used as the subject for every relation.
    frontmatter
        Already-parsed YAML dict from `split_frontmatter`.

    Returns
    -------
    RelationsParseResult
        - `typed`: valid relations, deduplicated by (source, predicate, object).
        - `errors`: list of ParseError for malformed entries.
        - `duplicates`: TypedRelations dropped because an identical
          (source, predicate, object) tuple was seen earlier.
        - `self_references`: TypedRelations whose object equals source;
          kept in `typed` too but surfaced separately for linter warnings.

    This function never raises on input shape — everything goes to errors.
    """
    result = RelationsParseResult(source=source)

    raw = frontmatter.get("relationships")
    if raw is None:
        return result
    if not isinstance(raw, list):
        result.errors.append(ParseError(
            index=-1,
            kind="invalid_shape",
            message=f"`relationships:` must be a list, got {type(raw).__name__}",
            raw=raw,
        ))
        return result

    seen: set[tuple[str, str, str]] = set()

    for idx, entry in enumerate(raw):
        if not isinstance(entry, dict):
            result.errors.append(ParseError(
                index=idx,
                kind="invalid_shape",
                message=f"entry must be a dict, got {type(entry).__name__}",
                raw=entry,
            ))
            continue

        predicate = entry.get("predicate")
        obj = entry.get("object")

        if not isinstance(predicate, str) or not predicate.strip():
            result.errors.append(ParseError(
                index=idx,
                kind="missing_field",
                message="entry missing `predicate`",
                raw=entry,
            ))
            continue
        if not isinstance(obj, str) or not obj.strip():
            result.errors.append(ParseError(
                index=idx,
                kind="missing_field",
                message="entry missing `object`",
                raw=entry,
            ))
            continue

        predicate = predicate.strip()
        obj = obj.strip()

        if predicate not in CANONICAL_PREDICATES:
            result.errors.append(ParseError(
                index=idx,
                kind="unknown_predicate",
                message=(
                    f"predicate '{predicate}' is not in CANONICAL_PREDICATES — "
                    f"see object_model.py for the canonical vocabulary"
                ),
                raw=entry,
            ))
            continue

        # Optional keys
        reason = entry.get("reason")
        if reason is not None and not isinstance(reason, str):
            reason = str(reason)

        date = entry.get("date")
        if date is not None and not isinstance(date, str):
            date = str(date)

        confidence = entry.get("confidence", _DEFAULT_CONFIDENCE)
        if not isinstance(confidence, str):
            confidence = _DEFAULT_CONFIDENCE
        if confidence not in _VALID_CONFIDENCE:
            result.errors.append(ParseError(
                index=idx,
                kind="invalid_confidence",
                message=(
                    f"confidence '{confidence}' not in "
                    f"{sorted(_VALID_CONFIDENCE)}; defaulting to '{_DEFAULT_CONFIDENCE}'"
                ),
                raw=entry,
            ))
            confidence = _DEFAULT_CONFIDENCE

        source_id = entry.get("source_id")
        if source_id is not None and not isinstance(source_id, str):
            source_id = str(source_id)

        # Any other keys preserved in `extra`
        extra = {k: v for k, v in entry.items() if k not in _KNOWN_KEYS}

        rel = TypedRelation(
            source=source,
            predicate=predicate,
            object=obj,
            reason=reason,
            date=date,
            confidence=confidence,
            source_id=source_id,
            extra=extra,
        )

        # Dedup by (source, predicate, object) — user-approved key
        if rel.dedup_key in seen:
            result.duplicates.append(rel)
            continue
        seen.add(rel.dedup_key)

        # Self-reference check (surfaced for linter, but kept)
        if rel.object == rel.source:
            result.self_references.append(rel)

        result.typed.append(rel)

    return result


__all__ = [
    "ParseError",
    "RelationsParseResult",
    "TypedRelation",
    "parse_relationships",
]
