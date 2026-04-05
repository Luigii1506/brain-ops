from __future__ import annotations

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = PACKAGE_ROOT.parent.parent
DEFAULT_CONFIG_CANDIDATES = (
    REPOSITORY_ROOT / "config" / "vault.yaml",
    REPOSITORY_ROOT / "config" / "vault.yml",
)
DEFAULT_TEMPLATE_DIR = REPOSITORY_ROOT / "templates"
DEFAULT_INIT_CONFIG_PATH = REPOSITORY_ROOT / "config" / "vault.yaml"
DEFAULT_DATA_DIR = REPOSITORY_ROOT / "data"
DEFAULT_DATABASE_PATH = DEFAULT_DATA_DIR / "brain_ops.db"

DEFAULT_FOLDER_MAP = {
    "inbox": "00 - Inbox",
    "sources": "01 - Sources",
    "knowledge": "02 - Knowledge",
    "maps": "03 - Maps",
    "projects": "04 - Projects",
    "systems": "05 - Systems",
    "daily": "06 - Daily",
    "archive": "07 - Archive",
    "templates": "Templates",
    "reports": "05 - Systems/Reports",
}

DEFAULT_TYPE_FOLDER_MAP = {
    "project": DEFAULT_FOLDER_MAP["projects"],
    "project_note": DEFAULT_FOLDER_MAP["projects"],
    "knowledge": DEFAULT_FOLDER_MAP["knowledge"],
    "source": DEFAULT_FOLDER_MAP["sources"],
    "permanent_note": DEFAULT_FOLDER_MAP["knowledge"],
    "study_note": DEFAULT_FOLDER_MAP["knowledge"],
    "idea": DEFAULT_FOLDER_MAP["knowledge"],
    "map": DEFAULT_FOLDER_MAP["maps"],
    "moc": DEFAULT_FOLDER_MAP["maps"],
    "system": DEFAULT_FOLDER_MAP["systems"],
    "sop": DEFAULT_FOLDER_MAP["systems"],
    "runbook": DEFAULT_FOLDER_MAP["systems"],
    "prompt": DEFAULT_FOLDER_MAP["systems"],
    "script_doc": DEFAULT_FOLDER_MAP["systems"],
    "command": DEFAULT_FOLDER_MAP["systems"],
    "security_note": DEFAULT_FOLDER_MAP["systems"],
    "daily": DEFAULT_FOLDER_MAP["daily"],
    "inbox": DEFAULT_FOLDER_MAP["inbox"],
    "architecture": DEFAULT_FOLDER_MAP["projects"],
    "decision": DEFAULT_FOLDER_MAP["projects"],
    "debugging_note": DEFAULT_FOLDER_MAP["projects"],
    "changelog": DEFAULT_FOLDER_MAP["projects"],
    "person": DEFAULT_FOLDER_MAP["knowledge"],
    "event": DEFAULT_FOLDER_MAP["knowledge"],
    "place": DEFAULT_FOLDER_MAP["knowledge"],
    "concept": DEFAULT_FOLDER_MAP["knowledge"],
    "book": DEFAULT_FOLDER_MAP["knowledge"],
    "author": DEFAULT_FOLDER_MAP["knowledge"],
    "war": DEFAULT_FOLDER_MAP["knowledge"],
    "era": DEFAULT_FOLDER_MAP["knowledge"],
    "organization": DEFAULT_FOLDER_MAP["knowledge"],
    "topic": DEFAULT_FOLDER_MAP["knowledge"],
}

PROJECT_SCAFFOLD_FILES = (
    ("project", "{title}"),
    ("architecture", "Architecture"),
    ("decision", "Decisions"),
    ("debugging_note", "Debugging"),
    ("changelog", "Changelog"),
    ("runbook", "Runbook"),
)
