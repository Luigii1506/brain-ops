"""Projects domain — dev project registry and context management."""

from .registry import (
    Project,
    ProjectContext,
    build_project,
    build_project_context,
    update_project_context,
)
from .claude_md import render_claude_md
from .doc_layout import (
    DocLayout,
    PROJECT_LAYERS,
    SCAFFOLD_DIRS_V1,
    SCAFFOLD_SPEC_V1,
    resolve_doc_path,
)

__all__ = [
    "DocLayout",
    "PROJECT_LAYERS",
    "Project",
    "ProjectContext",
    "SCAFFOLD_DIRS_V1",
    "SCAFFOLD_SPEC_V1",
    "build_project",
    "build_project_context",
    "render_claude_md",
    "resolve_doc_path",
    "update_project_context",
]
