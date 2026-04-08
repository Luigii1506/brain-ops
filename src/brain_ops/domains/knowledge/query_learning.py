"""Query learning — make the system smarter with every question asked."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass(slots=True, frozen=True)
class QueryRecord:
    query: str
    timestamp: str
    entities_found: list[str]
    entities_missing: list[str]
    sources_used: int
    had_llm_answer: bool
    filed_back: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "query": self.query,
            "timestamp": self.timestamp,
            "entities_found": list(self.entities_found),
            "entities_missing": list(self.entities_missing),
            "sources_used": self.sources_used,
            "had_llm_answer": self.had_llm_answer,
            "filed_back": self.filed_back,
        }


def detect_mentioned_entities(text: str) -> list[str]:
    """Extract entity names mentioned with [[wikilinks]] in text."""
    return list(set(re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", text)))


def detect_knowledge_gaps(
    query: str,
    answer: str,
    existing_entity_names: set[str],
) -> list[str]:
    """Detect entities mentioned in the answer that don't exist as notes."""
    mentioned = detect_mentioned_entities(answer)
    gaps = [name for name in mentioned if name not in existing_entity_names]
    return sorted(gaps)


def build_query_record(
    query: str,
    answer: str,
    sources_used: list[str],
    existing_entity_names: set[str],
    *,
    had_llm_answer: bool,
    filed_back: bool,
) -> QueryRecord:
    entities_found = [name for name in detect_mentioned_entities(answer) if name in existing_entity_names]
    entities_missing = detect_knowledge_gaps(query, answer, existing_entity_names)
    return QueryRecord(
        query=query,
        timestamp=datetime.now(timezone.utc).isoformat(),
        entities_found=sorted(entities_found),
        entities_missing=entities_missing,
        sources_used=len(sources_used),
        had_llm_answer=had_llm_answer,
        filed_back=filed_back,
    )


def save_query_log(log_path: Path, record: QueryRecord) -> None:
    """Append query record to JSONL log."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")


def load_query_log(log_path: Path) -> list[QueryRecord]:
    """Load all query records from JSONL log."""
    if not log_path.exists():
        return []
    records: list[QueryRecord] = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            data = json.loads(line)
            records.append(QueryRecord(
                query=str(data.get("query", "")),
                timestamp=str(data.get("timestamp", "")),
                entities_found=list(data.get("entities_found", [])),
                entities_missing=list(data.get("entities_missing", [])),
                sources_used=int(data.get("sources_used", 0)),
                had_llm_answer=bool(data.get("had_llm_answer", False)),
                filed_back=bool(data.get("filed_back", False)),
            ))
    return records


def get_most_queried_entities(log_path: Path, *, top_n: int = 10) -> list[tuple[str, int]]:
    """Get the most frequently queried entities."""
    records = load_query_log(log_path)
    counts: dict[str, int] = {}
    for record in records:
        for entity in record.entities_found:
            counts[entity] = counts.get(entity, 0) + 1
    sorted_entities = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    return sorted_entities[:top_n]


def get_recurring_gaps(log_path: Path, *, min_count: int = 2) -> list[tuple[str, int]]:
    """Get entities that are repeatedly missing across queries."""
    records = load_query_log(log_path)
    counts: dict[str, int] = {}
    for record in records:
        for entity in record.entities_missing:
            counts[entity] = counts.get(entity, 0) + 1
    return sorted(
        [(name, count) for name, count in counts.items() if count >= min_count],
        key=lambda x: x[1],
        reverse=True,
    )


@dataclass(slots=True)
class GapEntry:
    entity_name: str
    times_seen_in_queries: int = 0
    times_seen_in_sources: int = 0
    first_seen_at: str = ""
    last_seen_at: str = ""
    suggested_subtype: str | None = None
    gap_score: float = 0.0

    def to_dict(self) -> dict[str, object]:
        return {
            "entity_name": self.entity_name,
            "times_seen_in_queries": self.times_seen_in_queries,
            "times_seen_in_sources": self.times_seen_in_sources,
            "first_seen_at": self.first_seen_at,
            "last_seen_at": self.last_seen_at,
            "suggested_subtype": self.suggested_subtype,
            "gap_score": self.gap_score,
        }


def update_gap_registry(
    gap_registry_path: Path,
    missing_entities: list[str],
) -> None:
    """Update gap registry with newly detected missing entities."""
    gaps: dict[str, GapEntry] = {}
    if gap_registry_path.exists():
        data = json.loads(gap_registry_path.read_text(encoding="utf-8"))
        for name, entry in data.items():
            gaps[name] = GapEntry(
                entity_name=name,
                times_seen_in_queries=int(entry.get("times_seen_in_queries", 0)),
                times_seen_in_sources=int(entry.get("times_seen_in_sources", 0)),
                first_seen_at=str(entry.get("first_seen_at", "")),
                last_seen_at=str(entry.get("last_seen_at", "")),
                suggested_subtype=entry.get("suggested_subtype"),
                gap_score=float(entry.get("gap_score", 0)),
            )

    now = datetime.now(timezone.utc).isoformat()
    for name in missing_entities:
        if name in gaps:
            gaps[name].times_seen_in_queries += 1
            gaps[name].last_seen_at = now
        else:
            gaps[name] = GapEntry(
                entity_name=name,
                times_seen_in_queries=1,
                first_seen_at=now,
                last_seen_at=now,
            )
        # Recalculate gap score
        g = gaps[name]
        g.gap_score = g.times_seen_in_queries * 0.6 + g.times_seen_in_sources * 0.3

    gap_registry_path.parent.mkdir(parents=True, exist_ok=True)
    gap_registry_path.write_text(
        json.dumps(
            {name: entry.to_dict() for name, entry in gaps.items()},
            indent=2, sort_keys=True, ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )


__all__ = [
    "GapEntry",
    "QueryRecord",
    "build_query_record",
    "detect_knowledge_gaps",
    "detect_mentioned_entities",
    "get_most_queried_entities",
    "get_recurring_gaps",
    "load_query_log",
    "save_query_log",
    "update_gap_registry",
]
