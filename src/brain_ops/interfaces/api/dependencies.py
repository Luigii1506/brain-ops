"""Shared API dependencies and path resolution."""

from __future__ import annotations

import os
from pathlib import Path


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
    return Path.home() / ".brain-ops" / "brain_ops.db"
