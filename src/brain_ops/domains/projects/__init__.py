"""Projects domain — dev project registry and context management."""

from .registry import (
    Project,
    ProjectContext,
    build_project,
    build_project_context,
    update_project_context,
)
from .claude_md import render_claude_md

__all__ = [
    "Project",
    "ProjectContext",
    "build_project",
    "build_project_context",
    "render_claude_md",
    "update_project_context",
]
