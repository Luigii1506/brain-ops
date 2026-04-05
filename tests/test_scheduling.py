from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from brain_ops.core.scheduling import (
    DEFAULT_JOBS,
    SCHEDULE_PRESETS,
    ScheduledJob,
    build_scheduled_job,
    generate_crontab_entries,
    load_job_registry,
    record_job_run,
    save_job_registry,
)


class ScheduledJobModelTestCase(TestCase):
    def test_build_job_creates_valid_job(self) -> None:
        job = build_scheduled_job("check", schedule="daily", command="brain-ops check-all-sources")
        self.assertEqual(job.name, "check")
        self.assertEqual(job.schedule, "daily")
        self.assertEqual(job.command, "brain-ops check-all-sources")
        self.assertTrue(job.enabled)

    def test_build_job_rejects_empty_name(self) -> None:
        with self.assertRaises(ValueError):
            build_scheduled_job("", schedule="daily", command="cmd")

    def test_build_job_rejects_empty_command(self) -> None:
        with self.assertRaises(ValueError):
            build_scheduled_job("test", schedule="daily", command="")

    def test_job_roundtrip(self) -> None:
        job = build_scheduled_job("test", schedule="hourly", command="brain-ops entity-index", description="Reindex")
        data = job.to_dict()
        restored = ScheduledJob.from_dict(data)
        self.assertEqual(restored.name, "test")
        self.assertEqual(restored.schedule, "hourly")
        self.assertEqual(restored.description, "Reindex")


class JobRegistryPersistenceTestCase(TestCase):
    def test_save_and_load_roundtrip(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "jobs.json"
            job = build_scheduled_job("audit", schedule="weekly", command="brain-ops audit-vault")
            save_job_registry(path, {"audit": job})

            loaded = load_job_registry(path)
            self.assertIn("audit", loaded)
            self.assertEqual(loaded["audit"].schedule, "weekly")

    def test_load_returns_empty_when_missing(self) -> None:
        result = load_job_registry(Path("/tmp/nonexistent_jobs_12345.json"))
        self.assertEqual(result, {})


class RecordJobRunTestCase(TestCase):
    def test_record_updates_job_and_returns_result(self) -> None:
        job = build_scheduled_job("test", schedule="daily", command="cmd")
        result = record_job_run(job, status="ok", detail="3 sources checked")
        self.assertEqual(result.job_name, "test")
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.detail, "3 sources checked")
        self.assertIsNotNone(job.last_run)
        self.assertEqual(job.last_status, "ok")


class DefaultJobsTestCase(TestCase):
    def test_default_jobs_exist(self) -> None:
        names = {j.name for j in DEFAULT_JOBS}
        self.assertIn("check-all-sources", names)
        self.assertIn("audit-vault", names)
        self.assertIn("compile-knowledge", names)
        self.assertIn("entity-index", names)


class SchedulePresetsTestCase(TestCase):
    def test_presets_contain_expected_schedules(self) -> None:
        self.assertIn("daily", SCHEDULE_PRESETS)
        self.assertIn("hourly", SCHEDULE_PRESETS)
        self.assertIn("weekly", SCHEDULE_PRESETS)


class GenerateCrontabTestCase(TestCase):
    def test_generates_crontab_entries_for_enabled_jobs(self) -> None:
        jobs = {
            "a": ScheduledJob(name="a", schedule="daily", command="brain-ops a", enabled=True),
            "b": ScheduledJob(name="b", schedule="hourly", command="brain-ops b", enabled=False),
            "c": ScheduledJob(name="c", schedule="0 3 * * *", command="brain-ops c", enabled=True),
        }
        crontab = generate_crontab_entries(jobs)
        self.assertIn("0 6 * * *", crontab)  # daily preset
        self.assertIn("brain-ops a", crontab)
        self.assertNotIn("brain-ops b", crontab)  # disabled
        self.assertIn("0 3 * * *", crontab)  # custom cron expression
        self.assertIn("brain-ops c", crontab)

    def test_empty_jobs_returns_header_only(self) -> None:
        crontab = generate_crontab_entries({})
        self.assertIn("# brain-ops", crontab)


if __name__ == "__main__":
    import unittest

    unittest.main()
