from __future__ import annotations

from datetime import datetime
from pathlib import Path

from brain_ops.models import OperationRecord, OperationStatus
from brain_ops.vault import Vault


def write_report_text(vault: Vault, report_name: str, text: str) -> OperationRecord:
    report_path = vault.report_path(report_name)
    return vault.write_text(report_path, text, overwrite=False)


def build_report_operation(path: Path, detail: str) -> OperationRecord:
    return OperationRecord(
        action="report",
        path=path,
        detail=detail,
        status=OperationStatus.REPORT,
    )


def build_in_memory_report_operation(vault: Vault, detail: str) -> OperationRecord:
    return build_report_operation(vault.root, detail)


def timestamped_report_name(prefix: str, now: datetime | None = None) -> str:
    now = now or datetime.now()
    return f"{prefix}-{now.strftime('%Y%m%d-%H%M%S')}"
