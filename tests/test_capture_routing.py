"""Tests for capture routing improvements: normalization, multi-intent, reflective detection, routing log."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from brain_ops.interfaces.conversation.routing_input import (
    normalize_capture_text,
    route_input,
    route_input_multi,
    split_multi_intent,
)
from brain_ops.storage.db import initialize_database
from brain_ops.storage.sqlite.capture_log import (
    fetch_recent_capture_logs,
    insert_capture_log,
)


# ---------------------------------------------------------------------------
# normalize_capture_text
# ---------------------------------------------------------------------------


class TestNormalizeCaptureText:
    def test_strips_whitespace(self):
        original, lowered, accent = normalize_capture_text("  hello world  ")
        assert original == "hello world"
        assert lowered == "hello world"

    def test_removes_duplicate_spaces(self):
        original, lowered, accent = normalize_capture_text("comí  dos   huevos")
        assert original == "comí dos huevos"
        assert "  " not in original

    def test_preserves_original_case(self):
        original, lowered, accent = normalize_capture_text("Comí Dos Huevos")
        assert original == "Comí Dos Huevos"
        assert lowered == "comí dos huevos"

    def test_strips_accents_for_matching(self):
        original, lowered, accent = normalize_capture_text("comí café después")
        assert accent == "comi cafe despues"

    def test_empty_string(self):
        original, lowered, accent = normalize_capture_text("")
        assert original == ""
        assert lowered == ""
        assert accent == ""


# ---------------------------------------------------------------------------
# split_multi_intent
# ---------------------------------------------------------------------------


class TestSplitMultiIntent:
    def test_single_intent_no_split(self):
        result = split_multi_intent("comí dos huevos con jamón")
        assert result == ["comí dos huevos con jamón"]

    def test_split_on_y(self):
        result = split_multi_intent("comí dos huevos y entrené pierna 40 min")
        assert len(result) == 2
        assert "comí dos huevos" in result[0]
        assert "entrené pierna" in result[1]

    def test_split_on_semicolon(self):
        result = split_multi_intent("comí dos huevos; entrené pierna 40 min")
        assert len(result) == 2

    def test_triple_split(self):
        result = split_multi_intent(
            "comí dos huevos y entrené pierna 40 min; gasté 200 pesos en uber"
        )
        assert len(result) == 3

    def test_no_split_when_segment_too_short(self):
        # "y pan" is only 2 words and has no known keyword
        result = split_multi_intent("comí huevos y pan")
        assert len(result) == 1

    def test_split_with_keyword_in_short_segment(self):
        # "tomé creatina" has a known keyword even though only 2 words
        result = split_multi_intent("comí dos huevos y tomé creatina")
        assert len(result) == 2

    def test_split_on_despues(self):
        result = split_multi_intent(
            "comí dos huevos después entrené pierna una hora"
        )
        assert len(result) == 2

    def test_split_on_tambien(self):
        result = split_multi_intent(
            "comí dos huevos también entrené pierna una hora"
        )
        assert len(result) == 2


# ---------------------------------------------------------------------------
# Reflective detection
# ---------------------------------------------------------------------------


class TestReflectiveDetection:
    def test_reflective_me_senti(self):
        # Avoid "todo" which triggers project router
        decision = route_input("hoy me sentí muy cansado en la mañana")
        assert decision.domain == "daily"
        assert decision.confidence >= 0.70

    def test_reflective_creo_que(self):
        # "creo que" is a reflective keyword; avoid "necesito" triggering knowledge
        decision = route_input("creo que debería cambiar mi rutina de sueño")
        assert decision.domain == "daily"
        assert decision.confidence >= 0.70
        assert "reflective" in decision.reason.lower() or "journal" in decision.reason.lower()

    def test_reflective_fue_un_dia(self):
        decision = route_input("fue un día largo y difícil en la oficina")
        assert decision.domain == "daily"
        assert decision.confidence >= 0.70

    def test_non_reflective_fallback_lower_confidence(self):
        decision = route_input("algo random sin señal clara de nada")
        assert decision.confidence == 0.55


# ---------------------------------------------------------------------------
# capture_log insert and fetch
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "test.db"
    initialize_database(db_path)
    return db_path


class TestCaptureLogInsertAndFetch:
    def test_insert_and_fetch(self, tmp_db: Path):
        insert_capture_log(
            tmp_db,
            input_text="comí dos huevos",
            command="log-meal",
            domain="nutrition",
            confidence=0.90,
            reason="Detected meal keywords.",
            routing_source="heuristic",
            executed=True,
            source="cli",
        )
        logs = fetch_recent_capture_logs(tmp_db, limit=10)
        assert len(logs) == 1
        log = logs[0]
        assert log["input_text"] == "comí dos huevos"
        assert log["command"] == "log-meal"
        assert log["domain"] == "nutrition"
        assert log["confidence"] == 0.90
        assert log["reason"] == "Detected meal keywords."
        assert log["routing_source"] == "heuristic"
        assert log["executed"] == 1
        assert log["source"] == "cli"
        assert log["logged_at"] is not None

    def test_fetch_respects_limit(self, tmp_db: Path):
        for i in range(5):
            insert_capture_log(
                tmp_db,
                input_text=f"entry {i}",
                command="daily-log",
                domain="daily",
                confidence=0.55,
                reason="fallback",
                routing_source="heuristic",
            )
        logs = fetch_recent_capture_logs(tmp_db, limit=3)
        assert len(logs) == 3

    def test_fetch_returns_newest_first(self, tmp_db: Path):
        insert_capture_log(
            tmp_db,
            input_text="first",
            command="daily-log",
            domain="daily",
            confidence=0.55,
            reason="fallback",
            routing_source="heuristic",
        )
        insert_capture_log(
            tmp_db,
            input_text="second",
            command="daily-log",
            domain="daily",
            confidence=0.55,
            reason="fallback",
            routing_source="heuristic",
        )
        logs = fetch_recent_capture_logs(tmp_db, limit=10)
        assert logs[0]["input_text"] == "second"
        assert logs[1]["input_text"] == "first"


# ---------------------------------------------------------------------------
# Multi-intent routing (route_input_multi)
# ---------------------------------------------------------------------------


class TestMultiIntentRouting:
    def test_single_segment_returns_one(self):
        results = route_input_multi("comí dos huevos con jamón")
        assert len(results) == 1

    def test_two_segments_return_two(self):
        results = route_input_multi(
            "comí dos huevos y entrené pierna una hora"
        )
        assert len(results) == 2
        # Each result should have its own input_text
        assert results[0].input_text != results[1].input_text

    def test_each_segment_routed_independently(self):
        results = route_input_multi(
            "comí dos huevos; hoy me sentí muy cansado en la mañana"
        )
        assert len(results) == 2
        # First should be nutrition, second should be reflective/daily
        domains = [r.domain for r in results]
        assert "nutrition" in domains
        assert "daily" in domains
