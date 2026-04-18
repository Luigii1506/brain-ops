"""SQLite storage for compiled knowledge entities."""

from __future__ import annotations

import datetime
import json
import sqlite3
from pathlib import Path


class _DateSafeEncoder(json.JSONEncoder):
    """JSON encoder that converts date/datetime objects to ISO strings."""

    def default(self, o: object) -> object:
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()
        return super().default(o)

from brain_ops.domains.knowledge.compile import CompileResult, CompiledEntity, CompiledRelation


ENTITY_SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS entities (
        name TEXT PRIMARY KEY,
        entity_type TEXT NOT NULL,
        relative_path TEXT NOT NULL,
        summary TEXT,
        aliases TEXT,
        metadata_json TEXT NOT NULL DEFAULT '{}'
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS entity_relations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_entity TEXT NOT NULL,
        target_entity TEXT NOT NULL,
        predicate TEXT,
        confidence TEXT DEFAULT 'medium',
        source_type TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS entity_facts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_name TEXT NOT NULL,
        fact_text TEXT NOT NULL,
        source_id TEXT,
        confidence TEXT DEFAULT 'medium'
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS entity_timeline (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_name TEXT NOT NULL,
        date TEXT NOT NULL,
        event_text TEXT NOT NULL,
        source_id TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS entity_insights (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_name TEXT NOT NULL,
        insight_text TEXT NOT NULL,
        insight_type TEXT DEFAULT 'insight',
        source_id TEXT
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_entity_relations_source ON entity_relations(source_entity)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_entity_relations_target ON entity_relations(target_entity)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_entity_facts_name ON entity_facts(entity_name)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_entity_timeline_name ON entity_timeline(entity_name)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_entity_insights_name ON entity_insights(entity_name)
    """,
]


def initialize_entity_tables(db_path: Path) -> None:
    """Initialise the knowledge DB schema for a fresh or current DB.

    Runs `CREATE TABLE IF NOT EXISTS` for every base table. The DDL already
    contains the full current schema (including `predicate` and `confidence`
    columns on `entity_relations`), so fresh DBs get the correct shape.

    This function does NOT migrate pre-existing tables with outdated shapes.
    For legacy DBs that lack columns added by migrations, run the explicit
    CLI command `brain migrate-knowledge-db`. That is the only path by which
    migrations are applied to the production DB.

    See `docs/operations/MIGRATIONS.md`.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        for statement in ENTITY_SCHEMA_STATEMENTS:
            cursor.execute(statement)
        conn.commit()
    finally:
        conn.close()


def check_schema_is_current(db_path: Path) -> None:
    """Raise SchemaOutOfDateError if entity_relations lacks migration columns.

    Call at the entry of any write path that depends on post-Campaña-0 columns
    (`predicate`, `confidence`). A fresh DB (no table yet) and a fully-migrated
    DB both pass silently. A legacy DB with the old shape raises with an
    actionable message telling the user to run `brain migrate-knowledge-db`.
    """
    from brain_ops.errors import SchemaOutOfDateError

    if not db_path.exists():
        return
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='entity_relations'"
        ).fetchone()
        if row is None:
            return
        cols = {r[1] for r in conn.execute("PRAGMA table_info(entity_relations)")}
    finally:
        conn.close()

    missing = {"predicate", "confidence"} - cols
    if missing:
        raise SchemaOutOfDateError(
            f"Knowledge DB at {db_path} is missing columns {sorted(missing)} "
            f"in entity_relations. Run `brain migrate-knowledge-db --config <path>` "
            f"to upgrade the schema."
        )


def write_compiled_entities(db_path: Path, result: CompileResult) -> int:
    initialize_entity_tables(db_path)
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM entity_insights")
        cursor.execute("DELETE FROM entity_timeline")
        cursor.execute("DELETE FROM entity_facts")
        cursor.execute("DELETE FROM entity_relations")
        cursor.execute("DELETE FROM entities")
        for entity in result.entities:
            cursor.execute(
                "INSERT OR REPLACE INTO entities (name, entity_type, relative_path, metadata_json) VALUES (?, ?, ?, ?)",
                (entity.name, entity.entity_type, entity.relative_path, json.dumps(entity.metadata, ensure_ascii=False, cls=_DateSafeEncoder)),
            )
        for relation in result.relations:
            # Campaña 2.0: typed relations populate `predicate` + `confidence`;
            # legacy `related:` entries (predicate=None) keep those columns NULL/default.
            cursor.execute(
                "INSERT INTO entity_relations "
                "(source_entity, target_entity, predicate, confidence, source_type) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    relation.source_entity,
                    relation.target_entity,
                    relation.predicate,
                    relation.confidence if relation.predicate is not None else None,
                    relation.source_type,
                ),
            )
        conn.commit()
        return len(result.entities)
    finally:
        conn.close()


def write_extraction_intelligence(
    db_path: Path,
    extractions: list[dict[str, object]],
) -> int:
    """Write facts, timeline, and insights from extraction records into SQLite.

    Requires a post-migration schema (columns `predicate` and `confidence` on
    `entity_relations`). Raises SchemaOutOfDateError on a legacy DB with a
    clear message telling the user to run the CLI migration.
    """
    from brain_ops.domains.knowledge.object_model import normalize_predicate

    initialize_entity_tables(db_path)
    check_schema_is_current(db_path)
    conn = sqlite3.connect(str(db_path))
    total = 0
    try:
        cursor = conn.cursor()
        for extraction in extractions:
            raw = extraction.get("raw_llm_json", {})
            if not isinstance(raw, dict):
                continue
            source_title = str(extraction.get("source_title", ""))
            source_url = extraction.get("source_url")
            source_id = str(source_url) if source_url else source_title

            # Facts — assign to main entity (first entity with high importance, or source_title)
            main_entity = source_title
            entities_raw = raw.get("entities", [])
            for e in entities_raw:
                if isinstance(e, dict) and e.get("importance") == "high":
                    main_entity = str(e.get("name", source_title))
                    break

            # Core facts — canonical, high confidence
            for fact in raw.get("core_facts", []):
                if fact:
                    cursor.execute(
                        "INSERT INTO entity_facts (entity_name, fact_text, source_id, confidence) VALUES (?, ?, ?, ?)",
                        (main_entity, str(fact), source_id, "high"),
                    )
                    total += 1

            # Timeline
            for entry in raw.get("timeline", []):
                if isinstance(entry, dict):
                    cursor.execute(
                        "INSERT INTO entity_timeline (entity_name, date, event_text, source_id) VALUES (?, ?, ?, ?)",
                        (main_entity, str(entry.get("date", "")), str(entry.get("event", "")), source_id),
                    )
                    total += 1

            # Key insights — interpretive, moderate confidence
            for insight in raw.get("key_insights", []):
                if insight:
                    cursor.execute(
                        "INSERT INTO entity_insights (entity_name, insight_text, insight_type, source_id) VALUES (?, ?, ?, ?)",
                        (main_entity, str(insight), "insight", source_id),
                    )
                    total += 1

            # Strategic patterns — behavioral/analytical, moderate confidence
            for pattern in raw.get("strategic_patterns", []):
                if pattern:
                    cursor.execute(
                        "INSERT INTO entity_insights (entity_name, insight_text, insight_type, source_id) VALUES (?, ?, ?, ?)",
                        (main_entity, str(pattern), "pattern", source_id),
                    )
                    total += 1

            # Contradictions — disputed/uncertain, low confidence
            for contradiction in raw.get("contradictions_or_uncertainties", []):
                if contradiction:
                    cursor.execute(
                        "INSERT INTO entity_insights (entity_name, insight_text, insight_type, source_id) VALUES (?, ?, ?, ?)",
                        (main_entity, str(contradiction), "contradiction", source_id),
                    )
                    total += 1

            # Relations with normalized predicates
            for rel in raw.get("relationships", []):
                if isinstance(rel, dict):
                    raw_pred = str(rel.get("predicate", ""))
                    cursor.execute(
                        "INSERT INTO entity_relations (source_entity, target_entity, predicate, confidence, source_type) VALUES (?, ?, ?, ?, ?)",
                        (
                            str(rel.get("subject", "")),
                            str(rel.get("object", "")),
                            normalize_predicate(raw_pred),
                            str(rel.get("confidence", "medium")),
                            source_id,
                        ),
                    )
                    total += 1

        conn.commit()
        return total
    finally:
        conn.close()


def read_compiled_entities(db_path: Path) -> list[CompiledEntity]:
    if not db_path.exists():
        return []
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name, entity_type, relative_path, metadata_json FROM entities ORDER BY name")
        return [
            CompiledEntity(
                name=row[0],
                entity_type=row[1],
                relative_path=row[2],
                metadata=json.loads(row[3]),
            )
            for row in cursor.fetchall()
        ]
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()


def read_compiled_entity(db_path: Path, name: str) -> CompiledEntity | None:
    if not db_path.exists():
        return None
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, entity_type, relative_path, metadata_json FROM entities WHERE name = ?",
            (name,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return CompiledEntity(
            name=row[0],
            entity_type=row[1],
            relative_path=row[2],
            metadata=json.loads(row[3]),
        )
    except sqlite3.OperationalError:
        return None
    finally:
        conn.close()


def read_entity_connections(db_path: Path, name: str) -> list[str]:
    if not db_path.exists():
        return []
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT DISTINCT target_entity FROM entity_relations WHERE source_entity = ?
            UNION
            SELECT DISTINCT source_entity FROM entity_relations WHERE target_entity = ?
            ORDER BY 1
            """,
            (name, name),
        )
        return [row[0] for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()


def traverse_entity_graph(db_path: Path, start_name: str, max_depth: int = 2) -> dict[str, list[str]]:
    """Traverse the entity graph from a starting entity up to max_depth hops."""
    if not db_path.exists():
        return {}
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        visited: set[str] = set()
        result: dict[str, list[str]] = {}
        current_level = {start_name}

        for depth in range(max_depth):
            next_level: set[str] = set()
            for entity in current_level:
                if entity in visited:
                    continue
                visited.add(entity)
                cursor.execute(
                    """
                    SELECT DISTINCT target_entity FROM entity_relations WHERE source_entity = ?
                    UNION
                    SELECT DISTINCT source_entity FROM entity_relations WHERE target_entity = ?
                    """,
                    (entity, entity),
                )
                connections = [row[0] for row in cursor.fetchall() if row[0] not in visited]
                if connections:
                    result[entity] = connections
                    next_level.update(connections)
            current_level = next_level

        return result
    except sqlite3.OperationalError:
        return {}
    finally:
        conn.close()


__all__ = [
    "ENTITY_SCHEMA_STATEMENTS",
    "check_schema_is_current",
    "initialize_entity_tables",
    "read_compiled_entities",
    "read_compiled_entity",
    "read_entity_connections",
    "traverse_entity_graph",
    "write_compiled_entities",
    "write_extraction_intelligence",
]
