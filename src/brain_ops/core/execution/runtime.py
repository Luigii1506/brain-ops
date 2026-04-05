from __future__ import annotations

from dataclasses import dataclass

from brain_ops.config import VaultConfig
from brain_ops.models import OperationRecord
from brain_ops.vault import Vault


@dataclass(slots=True)
class ExecutionRuntime:
    config: VaultConfig
    db_path: object
    vault: Vault
    dry_run: bool = False


class IntentExecutionOutcome:
    def __init__(
        self,
        *,
        payload: object,
        operations: list[OperationRecord] | None = None,
        normalized_fields: dict[str, object] | None = None,
        reason: str,
    ) -> None:
        self.payload = payload
        self.operations = operations or []
        self.normalized_fields = normalized_fields or {}
        self.reason = reason


def build_execution_runtime(config: VaultConfig, *, dry_run: bool = False) -> ExecutionRuntime:
    return ExecutionRuntime(
        config=config,
        db_path=config.database_path,
        vault=Vault(config=config, dry_run=dry_run),
        dry_run=dry_run,
    )


def build_execution_outcome(
    *,
    payload: object,
    operations: list[OperationRecord] | None = None,
    normalized_fields: dict[str, object] | None = None,
    reason: str,
) -> IntentExecutionOutcome:
    return IntentExecutionOutcome(
        payload=payload,
        operations=operations,
        normalized_fields=normalized_fields,
        reason=reason,
    )
