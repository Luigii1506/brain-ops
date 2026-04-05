"""CLI setup/init helpers."""

from __future__ import annotations

from pathlib import Path

from brain_ops.config import VaultConfig
from brain_ops.models import OperationRecord, OperationStatus
from brain_ops.vault import Vault


def initialize_cli_config(
    *,
    config: VaultConfig,
    config_output: Path,
    dry_run: bool,
) -> list[OperationRecord]:
    output_path = config_output.expanduser()
    existed_before = output_path.exists()

    vault = Vault(config=config, dry_run=dry_run)
    operations: list[OperationRecord] = []
    if not dry_run:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(config.to_yaml(), encoding="utf-8")
    operations.append(
        OperationRecord(
            action="write",
            path=output_path,
            detail="updated config file" if existed_before else "created config file",
            status=OperationStatus.UPDATED if existed_before else OperationStatus.CREATED,
        )
    )
    operations.extend(vault.ensure_structure())
    return operations


__all__ = ["initialize_cli_config"]
