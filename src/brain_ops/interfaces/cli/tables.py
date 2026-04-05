"""Table builders for CLI output."""

from __future__ import annotations

from rich.table import Table

from brain_ops.config import VaultConfig
from brain_ops.models import OperationRecord


def build_operations_table(operations: list[OperationRecord]) -> Table:
    table = Table(title="Operations")
    table.add_column("Status")
    table.add_column("Action")
    table.add_column("Path")
    table.add_column("Detail")
    for operation in operations:
        table.add_row(
            operation.status.value,
            operation.action,
            str(operation.path),
            operation.detail,
        )
    return table


def build_info_table(version: str, config: VaultConfig) -> Table:
    table = Table(title=f"brain-ops {version}")
    table.add_column("Setting")
    table.add_column("Value")
    table.add_row("Vault path", str(config.vault_path))
    table.add_row("Timezone", config.default_timezone)
    table.add_row("Template dir", str(config.template_dir))
    table.add_row("Data dir", str(config.data_dir))
    table.add_row("Database path", str(config.database_path))
    table.add_row("AI provider", config.ai.provider)
    table.add_row("Ollama host", config.ai.ollama_host)
    table.add_row("Orchestrator", config.ai.orchestrator)
    table.add_row("Inbox folder", config.folders.inbox)
    table.add_row("Projects folder", config.folders.projects)
    table.add_row("Reports folder", config.folders.reports)
    return table


__all__ = ["build_info_table", "build_operations_table"]
