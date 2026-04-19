"""SQL-level queries over the typed-relations graph in knowledge.db.

Used by `brain query-relations` and `brain show-entity-relations`. All
functions are pure: they open a short-lived sqlite connection, run a
SELECT, and return dataclasses. No side effects, no schema writes.

The typed-vs-legacy discriminant is `WHERE predicate IS NOT NULL` for
typed and `WHERE predicate IS NULL` for legacy. See RELATIONS_FORMAT.md §9.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass(slots=True, frozen=True)
class QueriedRelation:
    source_entity: str
    target_entity: str
    predicate: str | None
    confidence: str | None
    source_type: str | None

    @property
    def is_typed(self) -> bool:
        return self.predicate is not None

    def to_dict(self) -> dict[str, object]:
        return {
            "source_entity": self.source_entity,
            "target_entity": self.target_entity,
            "predicate": self.predicate,
            "confidence": self.confidence,
            "source_type": self.source_type,
            "is_typed": self.is_typed,
        }


def query_relations(
    db_path: Path,
    *,
    from_entity: str | None = None,
    to_entity: str | None = None,
    predicate: str | None = None,
    include_legacy: bool = False,
    limit: int | None = None,
) -> list[QueriedRelation]:
    """Query typed relations (and optionally legacy) from `knowledge.db`.

    Parameters
    ----------
    db_path
        Path to `knowledge.db` (or any SQLite file with `entity_relations`).
    from_entity
        If set, filter `source_entity = from_entity`.
    to_entity
        If set, filter `target_entity = to_entity`.
    predicate
        If set, filter `predicate = predicate`. Mutually-exclusive with
        `include_legacy=True` (a predicate filter implies typed).
    include_legacy
        If True, include rows with `predicate IS NULL` (legacy `related:`).
        Default is False — only typed rows returned.
    limit
        Optional row cap. Safety default: 1000 if neither from/to/predicate
        is provided (prevents accidentally dumping the whole graph).

    Returns
    -------
    list[QueriedRelation]
        Ordered by (source_entity, predicate, target_entity). Empty if
        the DB is absent or the table doesn't exist.
    """
    if not db_path.exists():
        return []

    where: list[str] = []
    params: list[object] = []

    if from_entity is not None:
        where.append("source_entity = ?")
        params.append(from_entity)
    if to_entity is not None:
        where.append("target_entity = ?")
        params.append(to_entity)
    if predicate is not None:
        where.append("predicate = ?")
        params.append(predicate)
    if not include_legacy and predicate is None:
        # Default: only typed rows
        where.append("predicate IS NOT NULL")

    # Safety cap when neither from/to/predicate is set (broad scan)
    if limit is None:
        if from_entity is None and to_entity is None and predicate is None:
            limit = 1000

    sql = (
        "SELECT source_entity, target_entity, predicate, confidence, source_type "
        "FROM entity_relations"
    )
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY source_entity, predicate IS NULL, predicate, target_entity"
    if limit is not None:
        sql += " LIMIT ?"
        params.append(int(limit))

    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.execute(sql, params)
        rows = cur.fetchall()
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()

    return [
        QueriedRelation(
            source_entity=r[0],
            target_entity=r[1],
            predicate=r[2],
            confidence=r[3],
            source_type=r[4],
        )
        for r in rows
    ]


@dataclass(slots=True, frozen=True)
class EntityRelationsSummary:
    """All relations (typed grouped by predicate + legacy) for one entity."""

    entity: str
    typed_by_predicate: dict[str, list[QueriedRelation]]
    legacy: list[QueriedRelation]
    incoming_typed_by_predicate: dict[str, list[QueriedRelation]]
    incoming_legacy: list[QueriedRelation]

    @property
    def typed_count(self) -> int:
        return sum(len(v) for v in self.typed_by_predicate.values())

    @property
    def legacy_count(self) -> int:
        return len(self.legacy)

    @property
    def incoming_typed_count(self) -> int:
        return sum(len(v) for v in self.incoming_typed_by_predicate.values())

    def to_dict(self) -> dict[str, object]:
        return {
            "entity": self.entity,
            "outgoing": {
                "typed_count": self.typed_count,
                "legacy_count": self.legacy_count,
                "typed_by_predicate": {
                    p: [r.to_dict() for r in rels]
                    for p, rels in sorted(self.typed_by_predicate.items())
                },
                "legacy": [r.to_dict() for r in self.legacy],
            },
            "incoming": {
                "typed_count": self.incoming_typed_count,
                "legacy_count": len(self.incoming_legacy),
                "typed_by_predicate": {
                    p: [r.to_dict() for r in rels]
                    for p, rels in sorted(self.incoming_typed_by_predicate.items())
                },
                "legacy": [r.to_dict() for r in self.incoming_legacy],
            },
        }


def summarize_entity_relations(
    db_path: Path,
    entity: str,
) -> EntityRelationsSummary:
    """Return all relations centered on `entity`, grouped and bucketed.

    Outgoing: entity is source. Incoming: entity is target.
    Both split into typed (grouped by predicate) and legacy.
    """
    outgoing = query_relations(
        db_path, from_entity=entity, include_legacy=True, limit=10_000,
    )
    incoming = query_relations(
        db_path, to_entity=entity, include_legacy=True, limit=10_000,
    )

    out_typed: dict[str, list[QueriedRelation]] = {}
    out_legacy: list[QueriedRelation] = []
    for r in outgoing:
        if r.is_typed:
            out_typed.setdefault(r.predicate, []).append(r)  # type: ignore[arg-type]
        else:
            out_legacy.append(r)

    in_typed: dict[str, list[QueriedRelation]] = {}
    in_legacy: list[QueriedRelation] = []
    for r in incoming:
        if r.is_typed:
            in_typed.setdefault(r.predicate, []).append(r)  # type: ignore[arg-type]
        else:
            in_legacy.append(r)

    return EntityRelationsSummary(
        entity=entity,
        typed_by_predicate=out_typed,
        legacy=out_legacy,
        incoming_typed_by_predicate=in_typed,
        incoming_legacy=in_legacy,
    )


__all__ = [
    "EntityRelationsSummary",
    "QueriedRelation",
    "query_relations",
    "summarize_entity_relations",
]
