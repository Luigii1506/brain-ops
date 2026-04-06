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
    # Entity subtypes → Knowledge
    "person": DEFAULT_FOLDER_MAP["knowledge"],
    "animal": DEFAULT_FOLDER_MAP["knowledge"],
    "plant": DEFAULT_FOLDER_MAP["knowledge"],
    "celestial_body": DEFAULT_FOLDER_MAP["knowledge"],
    "civilization": DEFAULT_FOLDER_MAP["knowledge"],
    "deity": DEFAULT_FOLDER_MAP["knowledge"],
    "artifact": DEFAULT_FOLDER_MAP["knowledge"],
    "technology": DEFAULT_FOLDER_MAP["knowledge"],
    "programming_language": DEFAULT_FOLDER_MAP["knowledge"],
    # Concept subtypes → Knowledge
    "concept": DEFAULT_FOLDER_MAP["knowledge"],
    "abstract_concept": DEFAULT_FOLDER_MAP["knowledge"],
    "emotion": DEFAULT_FOLDER_MAP["knowledge"],
    "value": DEFAULT_FOLDER_MAP["knowledge"],
    "theory": DEFAULT_FOLDER_MAP["knowledge"],
    "discipline": DEFAULT_FOLDER_MAP["knowledge"],
    "school_of_thought": DEFAULT_FOLDER_MAP["knowledge"],
    "scientific_concept": DEFAULT_FOLDER_MAP["knowledge"],
    "philosophical_concept": DEFAULT_FOLDER_MAP["knowledge"],
    "religious_concept": DEFAULT_FOLDER_MAP["knowledge"],
    # Work subtypes → Knowledge
    "book": DEFAULT_FOLDER_MAP["knowledge"],
    "paper": DEFAULT_FOLDER_MAP["knowledge"],
    "poem": DEFAULT_FOLDER_MAP["knowledge"],
    "play": DEFAULT_FOLDER_MAP["knowledge"],
    "artwork": DEFAULT_FOLDER_MAP["knowledge"],
    "dataset": DEFAULT_FOLDER_MAP["knowledge"],
    "software_project": DEFAULT_FOLDER_MAP["knowledge"],
    # Event subtypes → Knowledge
    "event": DEFAULT_FOLDER_MAP["knowledge"],
    "war": DEFAULT_FOLDER_MAP["knowledge"],
    "battle": DEFAULT_FOLDER_MAP["knowledge"],
    "revolution": DEFAULT_FOLDER_MAP["knowledge"],
    "treaty": DEFAULT_FOLDER_MAP["knowledge"],
    "discovery": DEFAULT_FOLDER_MAP["knowledge"],
    "historical_event": DEFAULT_FOLDER_MAP["knowledge"],
    "era": DEFAULT_FOLDER_MAP["knowledge"],
    # Place subtypes → Knowledge
    "place": DEFAULT_FOLDER_MAP["knowledge"],
    "country": DEFAULT_FOLDER_MAP["knowledge"],
    "city": DEFAULT_FOLDER_MAP["knowledge"],
    "region": DEFAULT_FOLDER_MAP["knowledge"],
    "empire": DEFAULT_FOLDER_MAP["knowledge"],
    "continent": DEFAULT_FOLDER_MAP["knowledge"],
    "landmark": DEFAULT_FOLDER_MAP["knowledge"],
    # Organization subtypes → Knowledge
    "organization": DEFAULT_FOLDER_MAP["knowledge"],
    "company": DEFAULT_FOLDER_MAP["knowledge"],
    "institution": DEFAULT_FOLDER_MAP["knowledge"],
    "religion": DEFAULT_FOLDER_MAP["knowledge"],
    "military_unit": DEFAULT_FOLDER_MAP["knowledge"],
    "academic_school": DEFAULT_FOLDER_MAP["knowledge"],
    # Other
    "author": DEFAULT_FOLDER_MAP["knowledge"],
    "topic": DEFAULT_FOLDER_MAP["knowledge"],
    "umbrella_topic": DEFAULT_FOLDER_MAP["knowledge"],
    "research_area": DEFAULT_FOLDER_MAP["knowledge"],
    "study_track": DEFAULT_FOLDER_MAP["knowledge"],
}

PROJECT_SCAFFOLD_FILES = (
    ("project", "{title}"),
    ("architecture", "Architecture"),
    ("decision", "Decisions"),
    ("debugging_note", "Debugging"),
    ("changelog", "Changelog"),
    ("runbook", "Runbook"),
)
