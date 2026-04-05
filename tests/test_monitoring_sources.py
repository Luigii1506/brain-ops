from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from brain_ops.domains.monitoring.sources import (
    MonitorSource,
    build_monitor_source,
    load_source_registry,
    save_source_registry,
)
from brain_ops.domains.monitoring.snapshots import (
    SourceSnapshot,
    build_snapshot,
    load_latest_snapshot,
    save_snapshot,
)
from brain_ops.domains.monitoring.diffs import (
    SourceDiff,
    compute_diff,
)
from brain_ops.application.sources import (
    execute_add_source_workflow,
    execute_check_source_workflow,
    execute_list_sources_workflow,
    execute_remove_source_workflow,
)
from brain_ops.errors import ConfigError


class MonitorSourceModelTestCase(TestCase):
    def test_build_source_creates_valid_source(self) -> None:
        source = build_monitor_source("example", url="https://example.com", source_type="web")
        self.assertEqual(source.name, "example")
        self.assertEqual(source.url, "https://example.com")
        self.assertEqual(source.source_type, "web")
        self.assertEqual(source.check_interval, "daily")

    def test_build_source_rejects_empty_name(self) -> None:
        with self.assertRaises(ValueError):
            build_monitor_source("", url="https://example.com")

    def test_build_source_rejects_empty_url(self) -> None:
        with self.assertRaises(ValueError):
            build_monitor_source("test", url="")

    def test_build_source_rejects_unknown_type(self) -> None:
        with self.assertRaises(ValueError):
            build_monitor_source("test", url="https://example.com", source_type="ftp")

    def test_build_source_normalizes_type(self) -> None:
        source = build_monitor_source("test", url="https://api.example.com", source_type="API")
        self.assertEqual(source.source_type, "api")

    def test_source_to_dict_and_from_dict_roundtrip(self) -> None:
        source = build_monitor_source(
            "blog", url="https://blog.example.com", source_type="web",
            selector=".content", description="A blog", tags=["tech"],
        )
        data = source.to_dict()
        restored = MonitorSource.from_dict(data)
        self.assertEqual(restored.name, "blog")
        self.assertEqual(restored.selector, ".content")
        self.assertEqual(restored.tags, ["tech"])


class SourceRegistryPersistenceTestCase(TestCase):
    def test_save_and_load_roundtrip(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "sources.json"
            source = build_monitor_source("example", url="https://example.com")
            save_source_registry(path, {"example": source})

            loaded = load_source_registry(path)
            self.assertIn("example", loaded)
            self.assertEqual(loaded["example"].url, "https://example.com")

    def test_load_returns_empty_when_missing(self) -> None:
        result = load_source_registry(Path("/tmp/nonexistent_sources_12345.json"))
        self.assertEqual(result, {})


class SnapshotTestCase(TestCase):
    def test_build_snapshot_computes_hash_and_length(self) -> None:
        snap = build_snapshot("test", "hello world")
        self.assertEqual(snap.source_name, "test")
        self.assertEqual(snap.content, "hello world")
        self.assertEqual(snap.content_length, 11)
        self.assertTrue(len(snap.content_hash) == 64)

    def test_save_and_load_snapshot_roundtrip(self) -> None:
        with TemporaryDirectory() as temp_dir:
            snapshots_dir = Path(temp_dir) / "snapshots"
            snap = build_snapshot("example", "page content here")
            save_snapshot(snapshots_dir, snap)

            loaded = load_latest_snapshot(snapshots_dir, "example")
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded.content, "page content here")
            self.assertEqual(loaded.content_hash, snap.content_hash)

    def test_load_returns_none_when_missing(self) -> None:
        result = load_latest_snapshot(Path("/tmp/nonexistent_12345"), "missing")
        self.assertIsNone(result)


class DiffTestCase(TestCase):
    def test_first_snapshot_reports_changes(self) -> None:
        current = build_snapshot("test", "content")
        diff = compute_diff("test", previous=None, current=current)
        self.assertTrue(diff.has_changes)
        self.assertIsNone(diff.previous_hash)
        self.assertIn("First snapshot", diff.summary)

    def test_identical_snapshots_report_no_changes(self) -> None:
        snap1 = build_snapshot("test", "same content")
        snap2 = build_snapshot("test", "same content")
        diff = compute_diff("test", previous=snap1, current=snap2)
        self.assertFalse(diff.has_changes)
        self.assertIn("No changes", diff.summary)

    def test_different_content_reports_changes(self) -> None:
        snap1 = build_snapshot("test", "old content")
        snap2 = build_snapshot("test", "new content here")
        diff = compute_diff("test", previous=snap1, current=snap2)
        self.assertTrue(diff.has_changes)
        self.assertIn("changed", diff.summary)
        self.assertIn("grew", diff.summary)

    def test_shrinking_content_reports_direction(self) -> None:
        snap1 = build_snapshot("test", "long content here")
        snap2 = build_snapshot("test", "short")
        diff = compute_diff("test", previous=snap1, current=snap2)
        self.assertTrue(diff.has_changes)
        self.assertIn("shrank", diff.summary)


class SourceWorkflowsTestCase(TestCase):
    def test_add_and_list_sources(self) -> None:
        with TemporaryDirectory() as temp_dir:
            registry_path = Path(temp_dir) / "sources.json"
            loader = lambda: registry_path

            result = execute_add_source_workflow(
                name="blog",
                url="https://blog.example.com",
                source_type="web",
                selector=None,
                check_interval="daily",
                description="A blog",
                tags=None,
                load_registry_path=loader,
            )
            self.assertTrue(result.is_new)

            sources = execute_list_sources_workflow(load_registry_path=loader)
            self.assertEqual(len(sources), 1)
            self.assertEqual(sources[0].name, "blog")

    def test_remove_source_workflow(self) -> None:
        with TemporaryDirectory() as temp_dir:
            registry_path = Path(temp_dir) / "sources.json"
            loader = lambda: registry_path

            execute_add_source_workflow(
                name="temp", url="https://temp.com", source_type="web",
                selector=None, check_interval="daily", description=None, tags=None,
                load_registry_path=loader,
            )
            removed = execute_remove_source_workflow(name="temp", load_registry_path=loader)
            self.assertEqual(removed.name, "temp")

            sources = execute_list_sources_workflow(load_registry_path=loader)
            self.assertEqual(len(sources), 0)

    def test_remove_nonexistent_source_raises(self) -> None:
        with TemporaryDirectory() as temp_dir:
            registry_path = Path(temp_dir) / "sources.json"
            with self.assertRaises(ConfigError):
                execute_remove_source_workflow(
                    name="ghost", load_registry_path=lambda: registry_path,
                )

    def test_check_source_with_injected_fetcher(self) -> None:
        with TemporaryDirectory() as temp_dir:
            registry_path = Path(temp_dir) / "sources.json"
            snapshots_dir = Path(temp_dir) / "snapshots"
            loader = lambda: registry_path

            execute_add_source_workflow(
                name="mock-page", url="https://mock.example.com", source_type="web",
                selector=None, check_interval="daily", description=None, tags=None,
                load_registry_path=loader,
            )

            result = execute_check_source_workflow(
                name="mock-page",
                load_registry_path=loader,
                load_snapshots_dir=lambda: snapshots_dir,
                fetch_content=lambda url: "<html>Hello World</html>",
            )
            self.assertTrue(result.diff.has_changes)
            self.assertIn("First snapshot", result.diff.summary)
            self.assertEqual(result.snapshot.content, "<html>Hello World</html>")

            result2 = execute_check_source_workflow(
                name="mock-page",
                load_registry_path=loader,
                load_snapshots_dir=lambda: snapshots_dir,
                fetch_content=lambda url: "<html>Hello World</html>",
            )
            self.assertFalse(result2.diff.has_changes)

            result3 = execute_check_source_workflow(
                name="mock-page",
                load_registry_path=loader,
                load_snapshots_dir=lambda: snapshots_dir,
                fetch_content=lambda url: "<html>Updated Content!</html>",
            )
            self.assertTrue(result3.diff.has_changes)
            self.assertIn("changed", result3.diff.summary)


if __name__ == "__main__":
    import unittest

    unittest.main()
