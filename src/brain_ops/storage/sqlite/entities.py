"""SQLite storage for compiled knowledge entities."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from brain_ops.domains.knowledge.compile import CompileResult, CompiledEntity, CompiledRelation


ENTITY_SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS entities (
        name TEXT PRIMARY KEY,
        entity_type TEXT NOT NULL,
        relative_path TEXT NOT NULL,
        metadata_json TEXT NOT NULL DEFAULT '{}'
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS entity_relations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_entity TEXT NOT NULL,
        target_entity TEXT NOT NULL,
        source_type TEXT
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
]


def initialize_entity_tables(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        for statement in ENTITY_SCHEMA_STATEMENTS:
            cursor.execute(statement)
        conn.commit()
    finally:
        conn.close()


def write_compiled_entities(db_path: Path, result: CompileResult) -> int:
    initialize_entity_tables(db_path)
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM entity_relations")
        cursor.execute("DELETE FROM entities")
        for entity in result.entities:
            cursor.execute(
                "INSERT OR REPLACE INTO entities (name, entity_type, relative_path, metadata_json) VALUES (?, ?, ?, ?)",
                (entity.name, entity.entity_type, entity.relative_path, json.dumps(entity.metadata, ensure_ascii=False)),
            )
        for relation in result.relations:
            cursor.execute(
                "INSERT INTO entity_relations (source_entity, target_entity, source_type) VALUES (?, ?, ?)",
                (relation.source_entity, relation.target_entity, relation.source_type),
            )
        conn.commit()
        return len(result.entities)
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


__all__ = [
    "ENTITY_SCHEMA_STATEMENTS",
    "initialize_entity_tables",
    "read_compiled_entities",
    "read_compiled_entity",
    "read_entity_connections",
    "write_compiled_entities",
]
