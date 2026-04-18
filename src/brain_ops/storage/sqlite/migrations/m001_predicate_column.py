"""Migration 001 — add `predicate` and `confidence` columns to entity_relations.

The production `knowledge.db` in existing vaults was created before the
schema in `storage/sqlite/entities.py` was updated to include the typed-
predicate columns. CREATE TABLE IF NOT EXISTS does not alter existing
tables, so the columns declared in code were never actually created in
disk. This migration fixes that gap.

After this migration:
- entity_relations has columns: id, source_entity, target_entity, predicate,
  confidence, source_type.
- Existing rows have predicate=NULL, confidence=NULL — they are preserved,
  their type simply remains untyped until Campaña 2 recompiles them.

Safe to run on:
- a fresh DB (table created with all columns)
- an old DB missing the columns (columns added via ALTER TABLE)
- a DB already updated (no-op thanks to column existence check)
"""

from __future__ import annotations

import sqlite3


VERSION = 1
DESCRIPTION = "Add predicate and confidence columns to entity_relations"


def _existing_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {row[1] for row in rows}


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None


def up(conn: sqlite3.Connection) -> None:
    if not _table_exists(conn, "entity_relations"):
        # Fresh DB — create the table in its final form so future migrations
        # do not need to worry about it.
        conn.execute(
            """
            CREATE TABLE entity_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_entity TEXT NOT NULL,
                target_entity TEXT NOT NULL,
                predicate TEXT,
                confidence TEXT DEFAULT 'medium',
                source_type TEXT
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_entity_relations_source "
            "ON entity_relations(source_entity)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_entity_relations_target "
            "ON entity_relations(target_entity)"
        )
        return

    cols = _existing_columns(conn, "entity_relations")
    if "predicate" not in cols:
        conn.execute("ALTER TABLE entity_relations ADD COLUMN predicate TEXT")
    if "confidence" not in cols:
        conn.execute(
            "ALTER TABLE entity_relations ADD COLUMN confidence TEXT DEFAULT 'medium'"
        )


def down(conn: sqlite3.Connection) -> None:
    """SQLite does not support DROP COLUMN natively on older versions.

    If a rollback is needed, restore from the pre-migration backup instead.
    This function is intentionally a no-op to avoid data-loss surprises.
    """
    return
