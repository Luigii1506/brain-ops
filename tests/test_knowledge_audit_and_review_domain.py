from __future__ import annotations

import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from brain_ops.domains.knowledge.audit import accumulate_audit_note, analyze_audit_note
from brain_ops.domains.knowledge.review import accumulate_review_note, analyze_review_note
from brain_ops.models import VaultAuditSummary, WeeklyReviewSummary


class KnowledgeAuditAndReviewDomainTestCase(unittest.TestCase):
    def test_analyze_and_accumulate_audit_note_updates_summary(self) -> None:
        summary = VaultAuditSummary(generated_at=datetime(2026, 4, 4, 12, 0, 0))
        relative = Path("02 - Knowledge/MOC-SQLite.md")
        text = "short"
        frontmatter = {"type": "mocx"}

        analysis = analyze_audit_note(
            text,
            frontmatter,
            relative,
            maps_folder="03 - Maps",
            systems_folder="05 - Systems",
            sources_folder="01 - Sources",
        )
        accumulate_audit_note(
            summary,
            relative_path=relative,
            frontmatter=frontmatter,
            analysis=analysis,
            in_root=True,
        )

        self.assertEqual(summary.total_notes, 1)
        self.assertEqual(summary.with_frontmatter, 1)
        self.assertEqual(summary.folder_stats["02 - Knowledge"].total, 1)
        self.assertEqual(summary.folder_stats["02 - Knowledge"].with_frontmatter, 1)
        self.assertIn(relative, summary.very_short_notes)
        self.assertIn(relative, summary.moc_outside_maps)
        self.assertIn(relative, summary.notes_in_root)
        self.assertEqual(summary.notes_with_unknown_type[0].path, relative)
        self.assertIn("Unknown note type", summary.notes_with_unknown_type[0].reason)

    def test_audit_note_detects_folder_mismatches_and_map_link_quality(self) -> None:
        map_analysis = analyze_audit_note(
            "## Links\n\n- [[One]]",
            {"type": "map"},
            Path("03 - Maps/SQLite Map.md"),
            maps_folder="03 - Maps",
            systems_folder="05 - Systems",
            sources_folder="01 - Sources",
        )
        source_analysis = analyze_audit_note(
            "Source body",
            {"type": "source"},
            Path("02 - Knowledge/SQLite Source.md"),
            maps_folder="03 - Maps",
            systems_folder="05 - Systems",
            sources_folder="01 - Sources",
        )
        system_analysis = analyze_audit_note(
            "System body",
            {"type": "runbook"},
            Path("02 - Knowledge/Deploy.md"),
            maps_folder="03 - Maps",
            systems_folder="05 - Systems",
            sources_folder="01 - Sources",
        )

        self.assertEqual(map_analysis.maps_with_few_links_reason, "Only 1 wikilinks found.")
        self.assertTrue(source_analysis.source_note_outside_sources)
        self.assertTrue(system_analysis.system_note_outside_systems)

    def test_analyze_and_accumulate_review_note_updates_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "stale-project.md"
            project_path.write_text("No links here", encoding="utf-8")
            old_timestamp = datetime(2020, 1, 1).timestamp()
            os.utime(project_path, (old_timestamp, old_timestamp))

            analysis = analyze_review_note(
                project_path,
                Path("04 - Projects/Stale Project.md"),
                {},
                "No links here",
                inbox_folder="00 - Inbox",
                stale_days=21,
            )

            summary = WeeklyReviewSummary(generated_at=datetime(2026, 4, 4, 12, 0, 0))
            accumulate_review_note(
                summary,
                relative_path=Path("04 - Projects/Stale Project.md"),
                analysis=analysis,
            )

            self.assertTrue(analysis.missing_frontmatter)
            self.assertTrue(analysis.stale_project)
            self.assertTrue(analysis.possible_orphan)
            self.assertIn(Path("04 - Projects/Stale Project.md"), summary.notes_missing_frontmatter)
            self.assertIn(Path("04 - Projects/Stale Project.md"), summary.stale_project_notes)
            self.assertIn(Path("04 - Projects/Stale Project.md"), summary.possible_orphans)

    def test_review_note_detects_inbox_and_ignored_roots_correctly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            inbox_path = Path(temp_dir) / "inbox-note.md"
            inbox_path.write_text("", encoding="utf-8")
            analysis = analyze_review_note(
                inbox_path,
                Path("00 - Inbox/Inbox Note.md"),
                {"type": "inbox"},
                "",
                inbox_folder="00 - Inbox",
                stale_days=21,
            )

            self.assertTrue(analysis.inbox_note)
            self.assertFalse(analysis.possible_orphan)


if __name__ == "__main__":
    unittest.main()
