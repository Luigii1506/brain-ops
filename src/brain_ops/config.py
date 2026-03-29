from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator

from brain_ops.constants import (
    DEFAULT_CONFIG_CANDIDATES,
    DEFAULT_FOLDER_MAP,
    DEFAULT_INIT_CONFIG_PATH,
    DEFAULT_TEMPLATE_DIR,
    DEFAULT_TYPE_FOLDER_MAP,
)
from brain_ops.errors import ConfigError


class FolderConfig(BaseModel):
    inbox: str = DEFAULT_FOLDER_MAP["inbox"]
    sources: str = DEFAULT_FOLDER_MAP["sources"]
    knowledge: str = DEFAULT_FOLDER_MAP["knowledge"]
    maps: str = DEFAULT_FOLDER_MAP["maps"]
    projects: str = DEFAULT_FOLDER_MAP["projects"]
    systems: str = DEFAULT_FOLDER_MAP["systems"]
    daily: str = DEFAULT_FOLDER_MAP["daily"]
    archive: str = DEFAULT_FOLDER_MAP["archive"]
    templates: str = DEFAULT_FOLDER_MAP["templates"]
    reports: str = DEFAULT_FOLDER_MAP["reports"]


class VaultConfig(BaseModel):
    vault_path: Path
    default_timezone: str = "America/Tijuana"
    folders: FolderConfig = Field(default_factory=FolderConfig)
    template_dir: Path = DEFAULT_TEMPLATE_DIR
    type_folder_map: dict[str, str] = Field(default_factory=lambda: DEFAULT_TYPE_FOLDER_MAP.copy())

    @field_validator("vault_path", "template_dir", mode="before")
    @classmethod
    def _expand_paths(cls, value: str | Path) -> Path:
        return Path(value).expanduser()

    def folder_path(self, name: str) -> Path:
        try:
            folder_value = getattr(self.folders, name)
        except AttributeError as exc:
            raise ConfigError(f"Unknown folder key: {name}") from exc
        return self.vault_path / folder_value

    def folder_for_note_type(self, note_type: str) -> str | None:
        return self.type_folder_map.get(note_type)

    def to_yaml(self) -> str:
        data = {
            "vault_path": str(self.vault_path),
            "default_timezone": self.default_timezone,
            "inbox_folder": self.folders.inbox,
            "sources_folder": self.folders.sources,
            "knowledge_folder": self.folders.knowledge,
            "maps_folder": self.folders.maps,
            "projects_folder": self.folders.projects,
            "systems_folder": self.folders.systems,
            "daily_folder": self.folders.daily,
            "archive_folder": self.folders.archive,
            "templates_folder": self.folders.templates,
            "reports_folder": self.folders.reports,
        }
        return yaml.safe_dump(data, sort_keys=False)


def resolve_config_path(explicit_path: Path | None = None) -> Path:
    if explicit_path is not None:
        path = explicit_path.expanduser()
        if not path.exists():
            raise ConfigError(f"Config file not found: {path}")
        return path

    for candidate in DEFAULT_CONFIG_CANDIDATES:
        if candidate.exists():
            return candidate

    raise ConfigError(
        "Config file not found. Run `brain init --vault-path /path/to/vault` "
        f"or create {DEFAULT_INIT_CONFIG_PATH}."
    )


def load_config(explicit_path: Path | None = None) -> VaultConfig:
    path = resolve_config_path(explicit_path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    folders = FolderConfig(
        inbox=raw.get("inbox_folder", DEFAULT_FOLDER_MAP["inbox"]),
        sources=raw.get("sources_folder", DEFAULT_FOLDER_MAP["sources"]),
        knowledge=raw.get("knowledge_folder", DEFAULT_FOLDER_MAP["knowledge"]),
        maps=raw.get("maps_folder", raw.get("mocs_folder", DEFAULT_FOLDER_MAP["maps"])),
        projects=raw.get("projects_folder", DEFAULT_FOLDER_MAP["projects"]),
        systems=raw.get("systems_folder", DEFAULT_FOLDER_MAP["systems"]),
        daily=raw.get("daily_folder", DEFAULT_FOLDER_MAP["daily"]),
        archive=raw.get("archive_folder", DEFAULT_FOLDER_MAP["archive"]),
        templates=raw.get("templates_folder", DEFAULT_FOLDER_MAP["templates"]),
        reports=raw.get("reports_folder", DEFAULT_FOLDER_MAP["reports"]),
    )
    return VaultConfig(
        vault_path=raw["vault_path"],
        default_timezone=raw.get("default_timezone", "America/Tijuana"),
        folders=folders,
        template_dir=DEFAULT_TEMPLATE_DIR,
    )
