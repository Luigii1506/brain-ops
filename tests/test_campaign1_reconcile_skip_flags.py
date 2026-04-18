"""Subfase 1 hardening — `reconcile --skip-wikify --skip-cross-enrich` contract.

Proves the safety contract for Campaña 1:
- With both skip flags, reconcile does NOT modify any .md file body.
- `knowledge.db` IS updated (compile ran).
- `entity_registry.json` IS updated (registry sync ran).
- Without the skip flags, default behavior is preserved (regression test).
"""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock

import typer
from rich.console import Console
from typer.testing import CliRunner
import yaml

from brain_ops.config import load_config
from brain_ops.interfaces.cli.commands_notes import register_note_and_knowledge_commands
from brain_ops.vault import Vault


def _make_vault_config_file(vault_dir: Path) -> Path:
    """Write a minimal vault.yaml pointing to vault_dir."""
    config_path = vault_dir / "vault.yaml"
    config_path.write_text(yaml.safe_dump({
        "vault_path": str(vault_dir / "vault"),
        "default_timezone": "UTC",
        "inbox_folder": "00 - Inbox",
        "sources_folder": "01 - Sources",
        "knowledge_folder": "02 - Knowledge",
        "maps_folder": "03 - Maps",
        "projects_folder": "04 - Projects",
        "systems_folder": "05 - Systems",
        "daily_folder": "06 - Daily",
        "archive_folder": "07 - Archive",
        "templates_folder": "Templates",
        "database_path": str(vault_dir / "data" / "brain_ops.db"),
    }))
    return config_path


def _scaffold_vault(vault_dir: Path) -> Path:
    """Create the minimum vault folder structure."""
    vault_path = vault_dir / "vault"
    for folder in (
        "00 - Inbox", "01 - Sources", "02 - Knowledge",
        "03 - Maps", "04 - Projects", "05 - Systems",
        "06 - Daily", "07 - Archive", "Templates",
    ):
        (vault_path / folder).mkdir(parents=True, exist_ok=True)
    return vault_path


def _write_entity(vault_path: Path, name: str, body: str, related: list[str] | None = None) -> Path:
    """Write a realistic entity note that could trigger wikify/cross-enrich."""
    note = vault_path / "02 - Knowledge" / f"{name}.md"
    fm = ["---"]
    fm.append(f"name: {name}")
    fm.append("type: person")
    fm.append("object_kind: entity")
    fm.append("subtype: person")
    fm.append("entity: true")
    fm.append("status: canonical")
    fm.append("domain: filosofia")
    if related:
        fm.append("related:")
        for r in related:
            fm.append(f"  - {r}")
    fm.append("---")
    fm.append("")
    text = "\n".join(fm) + "\n" + body + "\n"
    note.write_text(text, encoding="utf-8")
    return note


def _snapshot_md_bytes(vault_path: Path) -> dict[str, bytes]:
    """Return a dict mapping relative path → file bytes for every .md."""
    snapshot: dict[str, bytes] = {}
    for md in sorted(vault_path.rglob("*.md")):
        rel = str(md.relative_to(vault_path))
        snapshot[rel] = md.read_bytes()
    return snapshot


def _build_test_vault(tmp: Path) -> tuple[Path, Path]:
    """Build a vault that WOULD trigger wikify (2+ word entity referenced in prose)
    and cross-enrich (entity mentioned in body but missing from Related notes).

    Returns (config_path, vault_path).
    """
    vault_path = _scaffold_vault(tmp)
    config_path = _make_vault_config_file(tmp)

    # Entity with 2+ word name — wikify target
    _write_entity(
        vault_path,
        "Agustín de Hipona",
        body=(
            "## Identity\n\n"
            "Filósofo y teólogo cristiano.\n\n"
            "## Key Facts\n\n"
            "- Nació en el año 354.\n\n"
            "## Related notes\n\n"
            "- [[Platón]]\n"
        ),
    )

    # Another entity that mentions "Agustín de Hipona" in plain text but NOT in Related notes
    # This is what wikify + cross-enrich would try to fix.
    _write_entity(
        vault_path,
        "Tomás de Aquino",
        body=(
            "## Identity\n\n"
            "Teólogo dominico influido por Agustín de Hipona y por Aristóteles.\n\n"
            "## Related notes\n\n"
            "- [[Aristóteles]]\n"
        ),
        related=["Aristóteles"],
    )

    # Short-name entity (wikify ignores < 2 words, but cross-enrich does not)
    _write_entity(vault_path, "Platón", body="## Identity\n\nFilósofo griego.\n")

    return config_path, vault_path


class ReconcileSkipFlagsTestCase(TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()
        self.console = Console(record=True)
        self.handle_error = Mock()

        self.app = typer.Typer()
        register_note_and_knowledge_commands(self.app, self.console, self.handle_error)

    def test_both_skip_flags_leave_bodies_byte_exact(self) -> None:
        """Contract: with --skip-wikify and --skip-cross-enrich, no .md body changes."""
        with TemporaryDirectory() as td:
            tmp = Path(td)
            config_path, vault_path = _build_test_vault(tmp)

            pre_snapshot = _snapshot_md_bytes(vault_path)

            result = self.runner.invoke(
                self.app,
                [
                    "reconcile",
                    "--config", str(config_path),
                    "--skip-wikify",
                    "--skip-cross-enrich",
                    "--json",
                ],
            )

            self.assertEqual(result.exit_code, 0, f"stderr: {result.output}")

            post_snapshot = _snapshot_md_bytes(vault_path)
            # Byte-exact contract
            self.assertEqual(
                pre_snapshot, post_snapshot,
                "reconcile with --skip-wikify --skip-cross-enrich modified file bodies!",
            )

    def test_knowledge_db_is_updated_with_skip_flags(self) -> None:
        """Compile must still run even under skip flags."""
        with TemporaryDirectory() as td:
            tmp = Path(td)
            config_path, vault_path = _build_test_vault(tmp)

            db_path = vault_path / ".brain-ops" / "knowledge.db"
            self.assertFalse(db_path.exists())

            result = self.runner.invoke(
                self.app,
                [
                    "reconcile",
                    "--config", str(config_path),
                    "--skip-wikify", "--skip-cross-enrich",
                    "--json",
                ],
            )
            self.assertEqual(result.exit_code, 0, f"stderr: {result.output}")

            self.assertTrue(db_path.exists(), "knowledge.db was not created")

            import sqlite3
            conn = sqlite3.connect(str(db_path))
            try:
                count = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
            finally:
                conn.close()
            self.assertEqual(count, 3, "Expected 3 entities compiled")

    def test_registry_is_updated_with_skip_flags(self) -> None:
        """Registry sync must still run even under skip flags."""
        with TemporaryDirectory() as td:
            tmp = Path(td)
            config_path, vault_path = _build_test_vault(tmp)

            registry_path = vault_path / ".brain-ops" / "entity_registry.json"
            self.assertFalse(registry_path.exists())

            result = self.runner.invoke(
                self.app,
                [
                    "reconcile",
                    "--config", str(config_path),
                    "--skip-wikify", "--skip-cross-enrich",
                    "--json",
                ],
            )
            self.assertEqual(result.exit_code, 0, f"stderr: {result.output}")

            self.assertTrue(registry_path.exists(), "entity_registry.json was not created")
            data = json.loads(registry_path.read_text())
            # Registry writes as a list of entities under 'entities' key
            entities_data = data.get("entities", data)
            self.assertGreater(
                len(entities_data), 0,
                "Registry should contain at least one entity",
            )

    def test_json_output_reports_skipped_flags(self) -> None:
        with TemporaryDirectory() as td:
            tmp = Path(td)
            config_path, vault_path = _build_test_vault(tmp)

            result = self.runner.invoke(
                self.app,
                [
                    "reconcile",
                    "--config", str(config_path),
                    "--skip-wikify", "--skip-cross-enrich",
                    "--json",
                ],
            )
            self.assertEqual(result.exit_code, 0)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["wikify_skipped"])
            self.assertTrue(payload["cross_enrich_skipped"])
            self.assertEqual(payload["wikified"], 0)
            self.assertEqual(payload["cross_enriched"], 0)


class ReconcileExcludesBackupDirsTestCase(TestCase):
    """`.brain-ops/` (snapshot backups) must not be scanned during registry sync.

    Otherwise a rename operation would re-register the old name from the
    pre-rename snapshot that lives at `.brain-ops/backups/...`.
    """

    def setUp(self) -> None:
        self.runner = CliRunner()
        self.console = Console(record=True)
        self.handle_error = Mock()
        self.app = typer.Typer()
        register_note_and_knowledge_commands(self.app, self.console, self.handle_error)

    def test_backup_copies_do_not_reregister_stale_names(self) -> None:
        with TemporaryDirectory() as td:
            tmp = Path(td)
            config_path, vault_path = _build_test_vault(tmp)

            # Simulate a backup containing the OLD (pre-rename) version of a note
            backup_dir = vault_path / ".brain-ops" / "backups" / "old-snapshot"
            backup_dir.mkdir(parents=True)
            # The snapshot has a note with name 'Imperio romano' (stale case)
            (backup_dir / "Imperio romano.md").write_text(
                "---\nname: Imperio romano\ntype: place\nobject_kind: place\n"
                "subtype: empire\nentity: true\nstatus: canonical\n---\n\n"
                "## Identity\n\nStale entity.\n",
                encoding="utf-8",
            )

            result = self.runner.invoke(
                self.app,
                [
                    "reconcile", "--config", str(config_path),
                    "--skip-wikify", "--skip-cross-enrich", "--json",
                ],
            )
            self.assertEqual(result.exit_code, 0, f"stderr: {result.output}")

            # Registry must NOT contain the stale 'Imperio romano' from the backup
            registry_path = vault_path / ".brain-ops" / "entity_registry.json"
            import json
            data = json.loads(registry_path.read_text())
            self.assertNotIn(
                "Imperio romano", data,
                "Backup-dir file was scanned — .brain-ops must be excluded",
            )


class ReconcileDefaultBehaviorRegressionTestCase(TestCase):
    """Without the skip flags, reconcile must preserve its old behavior."""

    def setUp(self) -> None:
        self.runner = CliRunner()
        self.console = Console(record=True)
        self.handle_error = Mock()
        self.app = typer.Typer()
        register_note_and_knowledge_commands(self.app, self.console, self.handle_error)

    def test_default_reconcile_still_wikifies(self) -> None:
        """Regression guard: no skip flag → wikify still runs (modifies bodies)."""
        with TemporaryDirectory() as td:
            tmp = Path(td)
            config_path, vault_path = _build_test_vault(tmp)

            pre_snapshot = _snapshot_md_bytes(vault_path)

            result = self.runner.invoke(
                self.app,
                ["reconcile", "--config", str(config_path), "--json"],
            )
            self.assertEqual(result.exit_code, 0, f"stderr: {result.output}")

            payload = json.loads(result.stdout)
            self.assertFalse(payload.get("wikify_skipped", True))
            self.assertFalse(payload.get("cross_enrich_skipped", True))

            post_snapshot = _snapshot_md_bytes(vault_path)
            # Bodies MAY have changed under default mode — that's the existing behavior
            # we're preserving. We assert that at LEAST one body changed (Tomás de Aquino
            # mentions "Agustín de Hipona" in plain text, so wikify should convert it).
            changed = [k for k in pre_snapshot if pre_snapshot[k] != post_snapshot.get(k)]
            tomas_key = "02 - Knowledge/Tomás de Aquino.md"
            self.assertIn(
                tomas_key, changed,
                "Wikify default behavior regressed — expected Tomás de Aquino body to change",
            )
