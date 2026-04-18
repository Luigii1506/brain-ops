"""Minimum-schema validation per subtype.

Each subtype declares:
- REQUIRED fields — missing → severity 'warning' (existing notes) / 'error' (new, gated)
- RECOMMENDED fields — missing → severity 'info'
- TYPED_RELATIONS — typed relation predicates this subtype should carry

No note is mutated. This module only REPORTS. Enforcement (if any) is
applied elsewhere (create-entity workflow, lint command).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


# ---------------------------------------------------------------------------
# Schema tables per subtype
# ---------------------------------------------------------------------------

# Fields every knowledge entity should have (universal baseline)
_UNIVERSAL_REQUIRED: set[str] = {
    "type", "object_kind", "subtype", "name",
}

# Per-subtype additional required fields
_REQUIRED_EXTRA: dict[str, set[str]] = {
    # ===== entity =====
    "person": {"domain", "era", "born", "died", "occupation", "nationality"},
    "civilization": {"domain", "start_date", "end_date", "region"},
    "polity": {"domain", "start_date", "end_date", "region"},
    "celestial_body": {"domain"},
    "deity": {"domain", "tradition"},
    "myth": {"domain"},
    "organism": {"domain"},
    "species": {"domain"},
    "anatomical_structure": {"domain"},
    "language": {"domain"},
    "script": {"domain"},
    # ===== concept =====
    "abstract_concept": {"domain", "field"},
    "philosophical_concept": {"domain", "field", "originated", "epistemic_mode"},
    "scientific_concept": {"domain", "field", "epistemic_mode"},
    "religious_concept": {"domain", "tradition"},
    "school_of_thought": {"domain", "origin", "epistemic_mode"},
    "discipline": {"domain", "field"},
    "theory": {"domain", "field"},
    "algorithm": {"domain", "subdomain"},
    "metric": {"domain", "subdomain"},
    "technical_concept": {"domain", "subdomain"},
    "architecture_pattern": {"domain", "subdomain"},
    "biological_process": {"domain", "epistemic_mode"},
    "cell": {"domain", "epistemic_mode"},
    "cell_type": {"domain", "epistemic_mode"},
    "gene": {"domain", "epistemic_mode"},
    "chemical_element": {"domain", "epistemic_mode"},
    "compound": {"domain", "epistemic_mode"},
    "molecule": {"domain", "epistemic_mode"},
    "disease": {"domain", "epistemic_mode"},
    "medical_theory": {"domain", "epistemic_mode"},
    "theorem": {"domain", "epistemic_mode"},
    "mathematical_object": {"domain", "epistemic_mode"},
    "mathematical_function": {"domain", "epistemic_mode"},
    "constant": {"domain", "epistemic_mode"},
    "proof_method": {"domain", "epistemic_mode"},
    "mathematical_field": {"domain", "epistemic_mode"},
    "symbolic_system": {"domain", "tradition", "epistemic_mode"},
    "divination_system": {"domain", "tradition", "epistemic_mode"},
    "mystical_concept": {"domain", "tradition", "epistemic_mode"},
    # ===== event =====
    "historical_event": {"domain", "date"},
    "battle": {"domain", "date", "participants"},
    "war": {"domain", "participants"},
    "revolution": {"domain"},
    "treaty": {"domain", "date", "participants"},
    "discovery": {"domain", "date"},
    "phenomenon": {"domain"},
    "historical_period": {"domain", "start_date", "end_date", "region"},
    "dynasty": {"domain", "start_date", "end_date"},
    "historical_process": {"domain"},
    "ritual": {"domain", "tradition"},
    # ===== place =====
    "country": {"domain", "continent"},
    "city": {"domain", "region"},
    "region": {"domain", "continent"},
    "empire": {"domain", "start_date", "end_date"},
    "continent": {"domain"},
    "landmark": {"domain", "region"},
    "geological_feature": {"domain"},
    "mythological_place": {"domain", "tradition"},
    # ===== work =====
    "book": {"author"},
    "paper": {"author"},
    "poem": {"author"},
    "play": {"author"},
    "artwork": {"author"},
    "sacred_text": {"tradition", "epistemic_mode"},
    "esoteric_text": {"tradition", "epistemic_mode"},
    # ===== organization =====
    "company": {"founded"},
    "institution": {"founded"},
    "religion": {"tradition"},
    "military_unit": {"domain"},
    "academic_school": {"founded"},
    "office_role": {"domain"},
    "esoteric_tradition": {"domain", "origin", "epistemic_mode"},
    "occult_movement": {"domain", "founded", "epistemic_mode"},
}

_RECOMMENDED_EXTRA: dict[str, set[str]] = {
    "person": {"tags", "status", "tradition"},
    "civilization": {"capital", "defining_traits"},
    "polity": {"capital", "key_figures"},
    "philosophical_concept": {"why_it_matters", "certainty_level"},
    "scientific_concept": {"certainty_level"},
    "esoteric_tradition": {"core_symbols", "certainty_level", "principal_texts"},
    "historical_period": {"defining_traits", "key_figures"},
    "book": {"published", "genre", "language"},
    "battle": {"outcome", "significance"},
    "war": {"outcome", "start_date", "end_date"},
    "dynasty": {"rulers", "region"},
    "deity": {"cult_center"},
    "sacred_text": {"composition_date", "structure"},
    "disease": {"prevalence"},
}

# Typed relation predicates each subtype SHOULD carry (guidance for Campaña 2).
_TYPED_RELATIONS_EXTRA: dict[str, set[str]] = {
    "person": {"influenced_by", "influenced", "studied_under", "mentor_of", "contemporary_of"},
    "philosophical_concept": {"developed", "extended", "reacted_against", "derived_from"},
    "school_of_thought": {"influenced_by", "influenced", "reacted_against", "synthesized"},
    "historical_event": {"caused_by", "caused", "participated_in", "occurred_in", "belongs_to_period"},
    "battle": {"participated_in", "part_of", "occurred_in"},
    "war": {"caused_by", "caused", "participated_in"},
    "historical_period": {"preceded_by", "followed", "contains", "emerged_from", "transformed_into"},
    "dynasty": {"ruled", "preceded_by", "followed"},
    "historical_process": {"caused_by", "caused", "emerged_from", "transformed_into"},
    "civilization": {"ruled_by", "preceded_by", "followed", "contains"},
    "polity": {"ruled_by", "preceded_by", "followed", "contains"},
    "deity": {"worshipped_by", "associated_with", "symbolizes", "appears_in", "parent_of", "sibling_of"},
    "myth": {"depicts", "describes", "appears_in"},
    "sacred_text": {"appears_in", "describes", "based_on"},
    "esoteric_text": {"written_in", "influenced_by", "based_on"},
    "book": {"depicts", "describes", "argues_for", "argues_against", "based_on", "influenced_by"},
    "paper": {"describes", "argues_for", "argues_against", "based_on"},
    "scientific_concept": {"explains", "depends_on", "part_of_system"},
    "theorem": {"depends_on", "part_of_system"},
    "biological_process": {"precedes_in_process", "depends_on", "part_of_system"},
    "esoteric_tradition": {"influenced_by", "influenced", "reacted_against", "derived_from"},
    "occult_movement": {"founded", "influenced_by", "influenced"},
    "ritual": {"practiced_by", "used_in", "appears_in"},
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def required_fields_for(subtype: str | None) -> set[str]:
    """Return the full required field set for a subtype."""
    required = set(_UNIVERSAL_REQUIRED)
    if subtype:
        required |= _REQUIRED_EXTRA.get(subtype, set())
    return required


def recommended_fields_for(subtype: str | None) -> set[str]:
    if not subtype:
        return set()
    return set(_RECOMMENDED_EXTRA.get(subtype, set()))


def typed_relations_for(subtype: str | None) -> set[str]:
    if not subtype:
        return set()
    return set(_TYPED_RELATIONS_EXTRA.get(subtype, set()))


# ---------------------------------------------------------------------------
# Violations
# ---------------------------------------------------------------------------

SEVERITIES = ("error", "warning", "info")


@dataclass(slots=True, frozen=True)
class SchemaViolation:
    note_path: str
    note_name: str
    subtype: str | None
    severity: str
    field: str
    message: str

    def to_dict(self) -> dict[str, object]:
        return {
            "note_path": self.note_path,
            "note_name": self.note_name,
            "subtype": self.subtype,
            "severity": self.severity,
            "field": self.field,
            "message": self.message,
        }


def _field_missing(fm: dict[str, object], field_name: str) -> bool:
    value = fm.get(field_name)
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    if isinstance(value, (list, dict)) and len(value) == 0:
        return True
    return False


def validate_note(
    note_path: str,
    note_name: str,
    frontmatter: dict[str, object],
    *,
    new_note: bool = False,
    gated_domains: Iterable[str] = (),
) -> list[SchemaViolation]:
    """Return schema violations for a single note.

    If `new_note` is True and the note's domain is in `gated_domains`, missing
    required fields become 'error' instead of 'warning'. Existing notes always
    get 'warning' for missing required fields.
    """
    subtype = frontmatter.get("subtype")
    if not isinstance(subtype, str):
        subtype = None

    required = required_fields_for(subtype)
    recommended = recommended_fields_for(subtype)

    violations: list[SchemaViolation] = []

    domain = frontmatter.get("domain")
    is_gated = new_note and isinstance(domain, str) and domain in set(gated_domains)

    for f in sorted(required):
        if _field_missing(frontmatter, f):
            severity = "error" if is_gated else "warning"
            violations.append(SchemaViolation(
                note_path=note_path,
                note_name=note_name,
                subtype=subtype,
                severity=severity,
                field=f,
                message=f"required field '{f}' missing",
            ))

    for f in sorted(recommended):
        if _field_missing(frontmatter, f):
            violations.append(SchemaViolation(
                note_path=note_path,
                note_name=note_name,
                subtype=subtype,
                severity="info",
                field=f,
                message=f"recommended field '{f}' missing",
            ))

    return violations


# ---------------------------------------------------------------------------
# Aggregated vault report
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class ValidationReport:
    total_notes: int = 0
    violations: list[SchemaViolation] = field(default_factory=list)
    per_subtype: dict[str, dict[str, int]] = field(default_factory=dict)
    per_domain: dict[str, dict[str, int]] = field(default_factory=dict)

    @property
    def error_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "warning")

    @property
    def info_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "info")

    def to_dict(self) -> dict[str, object]:
        return {
            "total_notes": self.total_notes,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "per_subtype": dict(self.per_subtype),
            "per_domain": dict(self.per_domain),
            "violations": [v.to_dict() for v in self.violations],
        }


def validate_vault_notes(
    notes: Iterable[tuple[str, str, dict[str, object]]],
    *,
    gated_domains: Iterable[str] = (),
) -> ValidationReport:
    """Run schema validation across all notes.

    Each input tuple is (note_path, note_name, frontmatter).
    `gated_domains` is informational here (existing notes always get 'warning').
    """
    report = ValidationReport()
    for note_path, note_name, fm in notes:
        report.total_notes += 1
        subtype = fm.get("subtype")
        subtype_key = subtype if isinstance(subtype, str) else "(none)"
        domain = fm.get("domain")

        # Resolve domain_keys: supports string or list (list-domain for bridge figures).
        # For list-domain, count the note under EACH of its domains (so per_domain
        # stats reflect actual coverage; primary-first is preserved by list order).
        if isinstance(domain, str) and domain:
            domain_keys = [domain]
        elif isinstance(domain, list) and domain:
            domain_keys = [d for d in domain if isinstance(d, str) and d]
            if not domain_keys:
                domain_keys = ["(none)"]
        else:
            domain_keys = ["(none)"]

        subtype_stats = report.per_subtype.setdefault(subtype_key, {"total": 0, "violations": 0})
        subtype_stats["total"] += 1
        for dk in domain_keys:
            domain_stats = report.per_domain.setdefault(dk, {"total": 0, "violations": 0})
            domain_stats["total"] += 1

        note_violations = validate_note(
            note_path, note_name, fm,
            new_note=False,
            gated_domains=gated_domains,
        )
        if note_violations:
            subtype_stats["violations"] += 1
            for dk in domain_keys:
                report.per_domain[dk]["violations"] += 1
            report.violations.extend(note_violations)

    return report


# ---------------------------------------------------------------------------
# Frontmatter loader (pure helper — caller can bypass and provide notes directly)
# ---------------------------------------------------------------------------

def load_frontmatter_from_vault(vault_path: Path) -> list[tuple[str, str, dict[str, object]]]:
    """Read every .md file under `<vault>/02 - Knowledge/` and parse frontmatter.

    Returns a list of (relative_path, note_name, frontmatter). Kept as a
    pure helper for convenience — tests can bypass by passing their own list.
    """
    from brain_ops.frontmatter import split_frontmatter

    knowledge_dir = vault_path / "02 - Knowledge"
    if not knowledge_dir.exists():
        return []

    results: list[tuple[str, str, dict[str, object]]] = []
    for md in knowledge_dir.rglob("*.md"):
        try:
            text = md.read_text(encoding="utf-8")
        except OSError:
            continue
        fm, _ = split_frontmatter(text)
        if not isinstance(fm, dict):
            continue
        rel = str(md.relative_to(vault_path))
        results.append((rel, md.stem, fm))
    return results


__all__ = [
    "SEVERITIES",
    "SchemaViolation",
    "ValidationReport",
    "load_frontmatter_from_vault",
    "recommended_fields_for",
    "required_fields_for",
    "typed_relations_for",
    "validate_note",
    "validate_vault_notes",
]
