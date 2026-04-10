"""Project documentation layout definitions.

Defines the 4-layer documentation standard for projects:
- 00 - Canonical: stable truth (architecture, invariants, ADRs, reference)
- 01 - Pedagogy: learning & onboarding (narratives, MOCs, concepts, questions)
- 02 - Operations: day-to-day (runbooks, workflows, debugging, sessions)
- 03 - Direction: strategic (priorities, tech debt, open questions)
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path


class DocLayout(str, Enum):
    FLAT = "flat"
    LAYERED_V1 = "layered-v1"


PROJECT_LAYERS = (
    ("00 - Canonical", "canonical"),
    ("01 - Pedagogy", "pedagogy"),
    ("02 - Operations", "operations"),
    ("03 - Direction", "direction"),
)

# (layer_folder, subfolder | None, template_name, title_template)
SCAFFOLD_SPEC_V1: tuple[tuple[str, str | None, str, str], ...] = (
    # Canonical — stable truth
    ("00 - Canonical", None, "project", "{title}"),
    ("00 - Canonical", None, "architecture", "ARCHITECTURE"),
    ("00 - Canonical", None, "invariants", "INVARIANTS"),
    ("00 - Canonical", None, "domain_glossary", "DOMAIN_GLOSSARY"),
    ("00 - Canonical", "REFERENCE", "reference_cli", "CLI"),
    # Operations — day-to-day
    ("02 - Operations", None, "runbook", "Runbook"),
    ("02 - Operations", None, "changelog", "Changelog"),
    # Direction — strategic
    ("03 - Direction", None, "priorities", "PRIORITIES"),
    ("03 - Direction", None, "tech_debt", "TECH_DEBT"),
    ("03 - Direction", None, "open_questions", "OPEN_QUESTIONS"),
)

# Directories to create even if empty (so the structure is visible in Obsidian).
SCAFFOLD_DIRS_V1: tuple[str, ...] = (
    "00 - Canonical/ADR",
    "00 - Canonical/REFERENCE",
    "02 - Operations/RUNBOOKS",
    "02 - Operations/WORKFLOWS",
    "02 - Operations/DEBUGGING",
    "02 - Operations/SESSIONS",
    "02 - Operations/CHANGELOGS",
    "02 - Operations/CONTEXT_PACKS",
)

# Mapping from logical doc type to layer path for each layout.
_LAYERED_V1_PATHS: dict[str, str] = {
    "root_note": "00 - Canonical",
    "architecture": "00 - Canonical",
    "invariants": "00 - Canonical",
    "domain_glossary": "00 - Canonical",
    "decisions": "00 - Canonical/ADR",
    "cli_reference": "00 - Canonical/REFERENCE",
    "runbook": "02 - Operations/RUNBOOKS",
    "workflows": "02 - Operations/WORKFLOWS",
    "debugging": "02 - Operations/DEBUGGING",
    "sessions": "02 - Operations/SESSIONS",
    "changelog": "02 - Operations/CHANGELOGS",
    "context_packs": "02 - Operations/CONTEXT_PACKS",
    "priorities": "03 - Direction",
    "tech_debt": "03 - Direction",
    "open_questions": "03 - Direction",
}

_FLAT_PATHS: dict[str, str] = {
    "root_note": "",
    "architecture": "",
    "decisions": "",
    "debugging": "",
    "runbook": "",
    "workflows": "",
    "changelog": "",
    "cli_reference": "",
    "sessions": "Sessions",
    "context_packs": "Context Packs",
}


def resolve_doc_path(
    project_dir: Path,
    doc_type: str,
    layout: str,
) -> Path:
    """Resolve the directory path for a document type within a project.

    Returns the directory where the document lives, not the file itself.
    """
    if layout == DocLayout.LAYERED_V1:
        sub = _LAYERED_V1_PATHS.get(doc_type, "")
    else:
        sub = _FLAT_PATHS.get(doc_type, "")
    if sub:
        return project_dir / sub
    return project_dir


__all__ = [
    "DocLayout",
    "PROJECT_LAYERS",
    "SCAFFOLD_DIRS_V1",
    "SCAFFOLD_SPEC_V1",
    "resolve_doc_path",
]
