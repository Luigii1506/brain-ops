from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from brain_ops.core.events import JsonlFileEventSink
from brain_ops.errors import BrainOpsError
from brain_ops.interfaces.cli.runtime import load_event_log_path, load_event_sink


class CliRuntimeTestCase(TestCase):
    def test_load_event_sink_returns_none_when_env_is_missing(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(load_event_sink())

    def test_load_event_sink_builds_jsonl_sink_from_env(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "events.jsonl"
            with patch.dict(os.environ, {"BRAIN_OPS_EVENT_LOG": str(target)}, clear=True):
                sink = load_event_sink()

        self.assertIsInstance(sink, JsonlFileEventSink)
        assert sink is not None
        self.assertEqual(sink.path, target)

    def test_load_event_log_path_prefers_explicit_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            path.write_text("", encoding="utf-8")

            self.assertEqual(load_event_log_path(path), path)

    def test_load_event_log_path_reads_env_and_requires_existing_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            path.write_text("", encoding="utf-8")
            with patch.dict(os.environ, {"BRAIN_OPS_EVENT_LOG": str(path)}, clear=True):
                resolved = load_event_log_path(None)

        self.assertEqual(resolved, path)

    def test_load_event_log_path_raises_when_missing(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(BrainOpsError):
                load_event_log_path(None)


if __name__ == "__main__":
    import unittest

    unittest.main()
