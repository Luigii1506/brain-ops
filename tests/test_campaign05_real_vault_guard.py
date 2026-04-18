"""Campaña 0.5 — verify the real-vault guard blocks production-path access.

When BRAIN_OPS_BLOCK_REAL_VAULT=1 (or a test runner is detected in
sys.modules), any call to `load_validated_vault` with a config pointing
to the user's real vault must raise RealVaultAccessError before any
filesystem interaction.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

import yaml

from brain_ops.constants import DEFAULT_INIT_CONFIG_PATH
from brain_ops.errors import RealVaultAccessError
from brain_ops.interfaces.cli.runtime import (
    _real_vault_guard_active,
    _real_vault_paths,
    load_validated_vault,
)


class GuardActivationTestCase(TestCase):
    def test_guard_active_under_tests(self) -> None:
        # Tests run with conftest.py setting the env var; additionally the
        # sys.modules detection catches pytest/unittest.
        self.assertTrue(_real_vault_guard_active())


class RealVaultPathsTestCase(TestCase):
    def test_real_vault_paths_resolves(self) -> None:
        # The repo ships a default config/vault.yaml — we rely on it existing
        # to detect the "real" vault path.
        if not DEFAULT_INIT_CONFIG_PATH.exists():
            self.skipTest("No default config/vault.yaml in this checkout")
        paths = _real_vault_paths()
        self.assertIsNotNone(paths)
        vault_path, db_path = paths
        self.assertIsInstance(vault_path, Path)
        self.assertIsInstance(db_path, Path)


class LoadValidatedVaultBlocksRealVaultTestCase(TestCase):
    def test_loading_real_vault_config_is_blocked(self) -> None:
        """Loading the default config/vault.yaml under the guard must raise."""
        if not DEFAULT_INIT_CONFIG_PATH.exists():
            self.skipTest("No default config/vault.yaml in this checkout")

        with self.assertRaises(RealVaultAccessError) as ctx:
            load_validated_vault(DEFAULT_INIT_CONFIG_PATH, dry_run=True)

        msg = str(ctx.exception)
        self.assertIn("real vault", msg)
        self.assertIn("BRAIN_OPS_BLOCK_REAL_VAULT", msg)

    def test_loading_temp_vault_is_allowed(self) -> None:
        """A config pointing to a temp path must NOT trigger the guard."""
        with tempfile.TemporaryDirectory() as td:
            vault_path = Path(td) / "fake_vault"
            for subfolder in (
                "00 - Inbox", "01 - Sources", "02 - Knowledge",
                "03 - Maps", "04 - Projects", "05 - Systems",
                "06 - Daily", "07 - Archive",
            ):
                (vault_path / subfolder).mkdir(parents=True)
            (vault_path / "Templates").mkdir()

            temp_config = Path(td) / "vault.yaml"
            temp_config.write_text(yaml.safe_dump({
                "vault_path": str(vault_path),
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
                "database_path": str(Path(td) / "brain_ops.db"),
            }))

            # Should NOT raise — this is a temp vault, not the real one
            vault = load_validated_vault(temp_config, dry_run=True)
            self.assertEqual(
                Path(vault.config.vault_path).resolve(),
                vault_path.resolve(),
            )


class GuardDisabledScenarioTestCase(TestCase):
    """Belt-and-suspenders: even with env var unset, sys.modules catches tests."""

    def test_sys_modules_catches_when_env_unset(self) -> None:
        # Temporarily unset the env var; sys.modules detection must still fire.
        original = os.environ.get("BRAIN_OPS_BLOCK_REAL_VAULT")
        try:
            os.environ.pop("BRAIN_OPS_BLOCK_REAL_VAULT", None)
            # We are inside unittest, so _test_runner_detected() returns True,
            # which keeps _real_vault_guard_active() True
            self.assertTrue(_real_vault_guard_active())
        finally:
            if original is not None:
                os.environ["BRAIN_OPS_BLOCK_REAL_VAULT"] = original
