"""SQLite storage layer for entity mastery tracking (SRS)."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from brain_ops.storage.db import connect_sqlite, require_database_file


def _compute_next_review(score: int, times_reviewed: int) -> str:
    """SM-2 simplified: compute next review date based on recall score and history.

    Score: 1=no recordé nada, 2=poco, 3=con esfuerzo, 4=bien, 5=perfecto.
    Higher score = longer interval (don't need to review soon).
    Lower score = shorter interval (need to review again quickly).
    """
    base_intervals = {1: 1, 2: 1, 3: 3, 4: 7, 5: 14}
    base = base_intervals.get(score, 3)

    # Multiply by 1.5 for each successful review (capped at 90 days)
    multiplier = min(1.5 ** max(0, times_reviewed - 1), 30)
    days = min(int(base * multiplier), 90)

    next_date = datetime.now() + timedelta(days=days)
    return next_date.strftime("%Y-%m-%d")


def record_review(
    db_path: Path,
    entity_name: str,
    difficulty: int,
) -> dict:
    """Record a review result for an entity. Returns updated mastery info."""
    target = require_database_file(db_path)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    difficulty = max(1, min(5, difficulty))  # clamp 1-5

    with connect_sqlite(target) as conn:
        cursor = conn.cursor()

        # Get existing record
        cursor.execute("SELECT * FROM entity_mastery WHERE entity_name = ?", (entity_name,))
        row = cursor.fetchone()

        if row is None:
            # First review (score: 1=bad, 5=perfect)
            times = 1
            avg_diff = float(difficulty)
            level = 1 if difficulty >= 3 else 0  # score 3+ = at least "visto"
            next_rev = _compute_next_review(difficulty, times)

            cursor.execute(
                """INSERT INTO entity_mastery
                   (entity_name, mastery_level, last_reviewed, next_review,
                    times_reviewed, avg_difficulty)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (entity_name, level, now, next_rev, times, avg_diff),
            )
        else:
            # Update existing
            col_names = [desc[0] for desc in cursor.description]
            old = dict(zip(col_names, row))

            times = old["times_reviewed"] + 1
            avg_diff = (old["avg_difficulty"] * old["times_reviewed"] + difficulty) / times

            # Level progression (score: 1=bad, 5=perfect)
            level = old["mastery_level"]
            if difficulty >= 4:
                level = min(level + 1, 4)  # good recall → progress
            elif difficulty == 3:
                pass  # medium → stay
            else:
                level = max(level - 1, 0)  # poor recall → regress

            next_rev = _compute_next_review(difficulty, times)

            cursor.execute(
                """UPDATE entity_mastery
                   SET mastery_level = ?, last_reviewed = ?, next_review = ?,
                       times_reviewed = ?, avg_difficulty = ?
                   WHERE entity_name = ?""",
                (level, now, next_rev, times, round(avg_diff, 2), entity_name),
            )

        return {
            "entity_name": entity_name,
            "mastery_level": level,
            "next_review": next_rev,
            "times_reviewed": times,
            "avg_difficulty": round(avg_diff, 2),
        }


def fetch_due_entities(
    db_path: Path,
    limit: int = 10,
    topic_filter: set[str] | None = None,
) -> list[dict]:
    """Get entities due for review today (next_review <= today).

    If topic_filter is provided, only return entities whose names are in the set.
    """
    target = require_database_file(db_path)
    today = datetime.now().strftime("%Y-%m-%d")

    with connect_sqlite(target) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """SELECT entity_name, mastery_level, last_reviewed, next_review,
                      times_reviewed, avg_difficulty
               FROM entity_mastery
               WHERE next_review <= ?
               ORDER BY mastery_level ASC, avg_difficulty DESC, next_review ASC""",
            (today,),
        )
        results = [dict(row) for row in cursor.fetchall()]

    if topic_filter:
        results = [r for r in results if r["entity_name"] in topic_filter]

    return results[:limit]


def _has_recovery_questions(body: str) -> bool:
    """Check if a note body contains ## Preguntas de recuperación with content."""
    import re
    match = re.search(r"## Preguntas de recuperación\n(.+?)(?=\n## |\Z)", body, re.DOTALL)
    if not match:
        return False
    content = match.group(1).strip()
    return any(line.strip().startswith("-") for line in content.splitlines())


def fetch_new_entities(
    db_path: Path,
    vault_path: Path,
    limit: int = 10,
    topic: str | None = None,
    require_questions: bool = True,
) -> list[str]:
    """Get entity names that exist in vault but have never been reviewed.

    If topic is provided, only return entities whose tags contain the topic.
    If require_questions is True, only return entities that have recovery questions.
    """
    target = require_database_file(db_path)

    from brain_ops.frontmatter import split_frontmatter

    vault_entities: set[str] = set()
    knowledge_dir = vault_path / "02 - Knowledge"
    if knowledge_dir.is_dir():
        for md in knowledge_dir.glob("*.md"):
            try:
                text = md.read_text(encoding="utf-8")
                fm, body = split_frontmatter(text)
                if fm.get("entity") is not True:
                    continue
                name = fm.get("name", "")
                if not name:
                    continue

                if require_questions and not _has_recovery_questions(body):
                    continue

                if topic:
                    tags = fm.get("tags") or []
                    if not isinstance(tags, list):
                        tags = [str(tags)]
                    tags_lower = [str(t).lower() for t in tags]
                    if not any(topic.lower() in t for t in tags_lower):
                        continue

                vault_entities.add(name)
            except Exception:
                pass

    with connect_sqlite(target) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT entity_name FROM entity_mastery")
        reviewed = {row[0] for row in cursor.fetchall()}

    unreviewed = sorted(vault_entities - reviewed)
    return unreviewed[:limit]


def get_entities_by_topic(vault_path: Path, topic: str) -> set[str]:
    """Get all entity names that have a specific tag/topic."""
    from brain_ops.frontmatter import split_frontmatter

    entities: set[str] = set()
    knowledge_dir = vault_path / "02 - Knowledge"
    if not knowledge_dir.is_dir():
        return entities

    for md in knowledge_dir.glob("*.md"):
        try:
            text = md.read_text(encoding="utf-8")
            fm, _ = split_frontmatter(text)
            if fm.get("entity") is not True:
                continue
            name = fm.get("name", "")
            tags = fm.get("tags") or []
            if not isinstance(tags, list):
                tags = [str(tags)]
            tags_lower = [str(t).lower() for t in tags]
            if any(topic.lower() in t for t in tags_lower):
                entities.add(name)
        except Exception:
            pass
    return entities


def fetch_mastery_summary(db_path: Path) -> dict:
    """Get summary counts by mastery level."""
    target = require_database_file(db_path)

    with connect_sqlite(target) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT mastery_level, COUNT(*) FROM entity_mastery GROUP BY mastery_level"
        )
        by_level = {row[0]: row[1] for row in cursor.fetchall()}

        cursor.execute("SELECT COUNT(*) FROM entity_mastery")
        total_reviewed = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM entity_mastery WHERE next_review <= date('now', 'localtime')"
        )
        due_today = cursor.fetchone()[0]

        cursor.execute("SELECT AVG(avg_difficulty) FROM entity_mastery")
        avg_diff = cursor.fetchone()[0] or 0

    level_names = {0: "nuevo", 1: "visto", 2: "recordado", 3: "explicado", 4: "dominado"}

    return {
        "total_reviewed": total_reviewed,
        "due_today": due_today,
        "avg_difficulty": round(avg_diff, 2),
        "by_level": {level_names.get(k, f"level_{k}"): v for k, v in sorted(by_level.items())},
    }


def fetch_entity_mastery(db_path: Path, entity_name: str) -> dict | None:
    """Get mastery info for a specific entity."""
    target = require_database_file(db_path)
    with connect_sqlite(target) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM entity_mastery WHERE entity_name = ?", (entity_name,))
        row = cursor.fetchone()
        return dict(row) if row else None


__all__ = [
    "fetch_due_entities",
    "fetch_entity_mastery",
    "fetch_mastery_summary",
    "fetch_new_entities",
    "record_review",
]
