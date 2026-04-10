"""Shared API dependencies and path resolution."""

from __future__ import annotations

import os
from pathlib import Path


def resolve_config_path() -> Path | None:
    env_path = os.getenv("BRAIN_OPS_CONFIG")
    if env_path:
        path = Path(env_path).expanduser()
        return path if path.exists() else None
    default_path = Path.cwd() / "config" / "vault.yaml"
    return default_path if default_path.exists() else None


def resolve_knowledge_db_path() -> Path:
    env_path = os.getenv("BRAIN_OPS_KNOWLEDGE_DB")
    if env_path:
        return Path(env_path)
    vault_path = os.getenv("BRAIN_OPS_VAULT_PATH")
    if vault_path:
        return Path(vault_path) / ".brain-ops" / "knowledge.db"
    return Path.home() / ".brain-ops" / "knowledge.db"


def resolve_project_registry_path() -> Path:
    env_path = os.getenv("BRAIN_OPS_PROJECT_REGISTRY")
    if env_path:
        return Path(env_path)
    return Path.home() / ".brain-ops" / "projects.json"


def resolve_source_registry_path() -> Path:
    env_path = os.getenv("BRAIN_OPS_SOURCE_REGISTRY")
    if env_path:
        return Path(env_path)
    return Path.home() / ".brain-ops" / "sources.json"


def resolve_database_path() -> Path:
    env_path = os.getenv("BRAIN_OPS_DATABASE")
    if env_path:
        return Path(env_path)
    config_path = resolve_config_path()
    if config_path is not None:
        from brain_ops.interfaces.cli.runtime import load_database_path as load_runtime_database_path

        return load_runtime_database_path(config_path)
    return Path.home() / ".brain-ops" / "brain_ops.db"
