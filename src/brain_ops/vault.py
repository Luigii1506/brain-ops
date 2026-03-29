from __future__ import annotations

from datetime import datetime
from pathlib import Path

from brain_ops.config import VaultConfig
from brain_ops.errors import ConfigError, VaultSafetyError
from brain_ops.models import OperationRecord, OperationStatus


def ensure_note_extension(path: Path) -> Path:
    return path if path.suffix == ".md" else path.with_suffix(".md")


def sanitize_note_title(title: str) -> str:
    cleaned = title.strip().replace("/", "-").replace("\\", "-")
    if not cleaned:
        raise ConfigError("Note title cannot be empty.")
    return cleaned


class Vault:
    def __init__(self, config: VaultConfig, dry_run: bool = False):
        self.config = config
        self.dry_run = dry_run

    @property
    def root(self) -> Path:
        return self.config.vault_path.expanduser().resolve(strict=False)

    def validate(self) -> None:
        if not self.root.exists():
            raise ConfigError(f"Vault path does not exist: {self.root}")
        if not self.root.is_dir():
            raise ConfigError(f"Vault path is not a directory: {self.root}")

    def ensure_structure(self) -> list[OperationRecord]:
        operations: list[OperationRecord] = []
        for folder_name in self.config.folders.model_dump().keys():
            path = self.config.folder_path(folder_name)
            operations.append(self._mkdir(path))
        return operations

    def path_for_folder(self, folder: str) -> Path:
        return self._safe_path(self.root / folder)

    def note_path(self, folder: str, title: str) -> Path:
        safe_title = sanitize_note_title(title)
        return ensure_note_extension(self.path_for_folder(folder) / safe_title)

    def write_text(self, path: Path, text: str, overwrite: bool = False) -> OperationRecord:
        target = self._safe_path(path)
        exists = target.exists()
        if exists and not overwrite:
            raise ConfigError(f"Refusing to overwrite existing file: {target}")
        if not self.dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        return OperationRecord(
            action="write",
            path=target,
            detail="updated file" if exists else "created file",
            status=OperationStatus.UPDATED if exists else OperationStatus.CREATED,
        )

    def move(self, source: Path, destination: Path) -> OperationRecord:
        src = self._safe_path(source)
        dst = self._safe_path(destination)
        if not src.exists():
            raise ConfigError(f"Source file not found: {src}")
        if dst.exists():
            raise ConfigError(f"Destination already exists: {dst}")
        if not self.dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            src.rename(dst)
        return OperationRecord(
            action="move",
            path=dst,
            detail=f"moved from {src}",
            status=OperationStatus.MOVED,
        )

    def list_markdown_files(self, folder: str) -> list[Path]:
        root = self.path_for_folder(folder)
        if not root.exists():
            return []
        return sorted(path for path in root.rglob("*.md") if path.is_file())

    def relative_path(self, path: Path) -> Path:
        safe = self._safe_path(path)
        return safe.relative_to(self.root)

    def report_path(self, report_name: str) -> Path:
        return self.note_path(self.config.folders.reports, report_name)

    def _mkdir(self, path: Path) -> OperationRecord:
        target = self._safe_path(path)
        existed = target.exists()
        if not self.dry_run:
            target.mkdir(parents=True, exist_ok=True)
        return OperationRecord(
            action="mkdir",
            path=target,
            detail="already present" if existed else "created directory",
            status=OperationStatus.SKIPPED if existed else OperationStatus.CREATED,
        )

    def _safe_path(self, path: Path) -> Path:
        resolved = path.expanduser().resolve(strict=False)
        root = self.root.expanduser().resolve(strict=False)
        if resolved != root and root not in resolved.parents:
            raise VaultSafetyError(f"Path escapes vault: {resolved}")
        return resolved


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")
