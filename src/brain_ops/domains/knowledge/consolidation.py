"""Vault consolidation operations — Campaña 1.

Each operation follows the same pattern:

1. `plan_<op>(vault_path, ...)` scans the vault and returns a structured
   report of what WOULD change. No mutation.
2. `apply_<op>(vault_path, report, *, exclude=...)` writes the changes
   described in the report, optionally skipping specific notes.

The CLI layer calls `plan_*` in dry-run mode and `apply_*` with `--apply`.
All operations touch ONLY frontmatter — bodies stay untouched.

Campaña 1 subfases implemented here:
- Subfase 1.1: normalize_domain (philosophy/history/science → canonical)
  Also handles Subfase 1.2 (astronomía → ciencia + subdomain hint).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from brain_ops.frontmatter import dump_frontmatter, split_frontmatter

from .naming_rules import (
    canonical_domain,
    is_canonical_domain,
    suggested_subdomain_for_alias,
)


# ---------------------------------------------------------------------------
# Subfase 1.1 / 1.2 — normalize_domain
# ---------------------------------------------------------------------------

@dataclass(slots=True, frozen=True)
class NormalizeDomainChange:
    note_path: str
    note_name: str
    current_domain: str
    new_domain: str
    subdomain_current: str | None
    subdomain_new: str | None

    @property
    def subdomain_changed(self) -> bool:
        return self.subdomain_current != self.subdomain_new

    def to_dict(self) -> dict[str, object]:
        return {
            "note_path": self.note_path,
            "note_name": self.note_name,
            "current_domain": self.current_domain,
            "new_domain": self.new_domain,
            "subdomain_current": self.subdomain_current,
            "subdomain_new": self.subdomain_new,
            "subdomain_changed": self.subdomain_changed,
        }


@dataclass(slots=True)
class NormalizeDomainReport:
    vault_path: str
    total_notes_scanned: int = 0
    notes_already_canonical: int = 0
    notes_without_domain: int = 0
    changes: list[NormalizeDomainChange] = field(default_factory=list)

    @property
    def total_changes(self) -> int:
        return len(self.changes)

    def counts_by_transition(self) -> dict[str, int]:
        """Count of changes grouped by 'from → to' transition."""
        counts: dict[str, int] = {}
        for change in self.changes:
            key = f"{change.current_domain} → {change.new_domain}"
            counts[key] = counts.get(key, 0) + 1
        return counts

    def to_dict(self) -> dict[str, object]:
        return {
            "vault_path": self.vault_path,
            "total_notes_scanned": self.total_notes_scanned,
            "notes_already_canonical": self.notes_already_canonical,
            "notes_without_domain": self.notes_without_domain,
            "total_changes": self.total_changes,
            "transitions": self.counts_by_transition(),
            "changes": [c.to_dict() for c in self.changes],
        }


def _iter_knowledge_notes(vault_path: Path) -> Iterable[Path]:
    """Yield every .md file under <vault>/02 - Knowledge/."""
    knowledge_dir = vault_path / "02 - Knowledge"
    if not knowledge_dir.exists():
        return
    for md in sorted(knowledge_dir.rglob("*.md")):
        yield md


def plan_normalize_domain(vault_path: Path) -> NormalizeDomainReport:
    """Scan the vault and return the set of domain normalizations needed.

    Does NOT mutate anything. Pure read operation.

    Rules:
    - If `domain` is absent → not our concern (Subfase 1.4 handles that).
    - If `domain` is already canonical → skip.
    - If `domain` maps to a canonical via `canonical_domain()` → propose change.
    - If the alias has a subdomain hint and the note has NO current subdomain →
      propose adding the hint as subdomain.
    - If the note already has a `subdomain`, it is preserved (never overwritten).
    """
    report = NormalizeDomainReport(vault_path=str(vault_path))
    for md in _iter_knowledge_notes(vault_path):
        try:
            text = md.read_text(encoding="utf-8")
        except OSError:
            continue
        try:
            fm, _body = split_frontmatter(text)
        except ValueError:
            continue
        if not isinstance(fm, dict):
            continue

        report.total_notes_scanned += 1

        current = fm.get("domain")
        if not current:
            report.notes_without_domain += 1
            continue
        if not isinstance(current, str):
            continue

        if is_canonical_domain(current):
            report.notes_already_canonical += 1
            continue

        target = canonical_domain(current)
        if not target:
            # Neither canonical nor aliased → left for Subfase 1.4 to decide
            continue

        # Subdomain handling: only suggest hint if note has NO subdomain today
        subdomain_current = fm.get("subdomain")
        if isinstance(subdomain_current, str):
            subdomain_current_value: str | None = subdomain_current
        else:
            subdomain_current_value = None

        if subdomain_current_value is None:
            hint = suggested_subdomain_for_alias(current)
            subdomain_new_value = hint
        else:
            subdomain_new_value = subdomain_current_value

        report.changes.append(NormalizeDomainChange(
            note_path=str(md.relative_to(vault_path)),
            note_name=md.stem,
            current_domain=current,
            new_domain=target,
            subdomain_current=subdomain_current_value,
            subdomain_new=subdomain_new_value,
        ))

    return report


def apply_normalize_domain(
    vault_path: Path,
    report: NormalizeDomainReport,
    *,
    exclude: Iterable[str] = (),
    transitions_filter: Iterable[str] | None = None,
) -> dict[str, object]:
    """Apply the changes in the report. Returns a summary of what was applied.

    Parameters
    ----------
    vault_path
        Root of the vault.
    report
        A report produced by `plan_normalize_domain`.
    exclude
        Iterable of note_path strings (relative to vault) to skip.
    transitions_filter
        If given, only apply changes whose transition is in this set.
        Example: {"philosophy → filosofia"} to apply only one alias at a time.
    """
    excluded = set(exclude)
    filter_set: set[str] | None = (
        set(transitions_filter) if transitions_filter is not None else None
    )

    applied: list[dict[str, object]] = []
    skipped_excluded: list[str] = []
    skipped_filter: list[str] = []

    for change in report.changes:
        if change.note_path in excluded:
            skipped_excluded.append(change.note_path)
            continue
        transition = f"{change.current_domain} → {change.new_domain}"
        if filter_set is not None and transition not in filter_set:
            skipped_filter.append(change.note_path)
            continue

        md = vault_path / change.note_path
        if not md.exists():
            # Note disappeared between plan and apply — skip safely
            continue
        text = md.read_text(encoding="utf-8")
        try:
            fm, body = split_frontmatter(text)
        except ValueError:
            continue
        if not isinstance(fm, dict):
            continue

        # Defensive re-check: only mutate if current_domain still matches what
        # we planned for. Protects against concurrent edits between plan and apply.
        if fm.get("domain") != change.current_domain:
            continue

        fm["domain"] = change.new_domain
        if change.subdomain_new is not None and not fm.get("subdomain"):
            fm["subdomain"] = change.subdomain_new

        new_text = dump_frontmatter(fm, body)
        md.write_text(new_text, encoding="utf-8")
        applied.append(change.to_dict())

    return {
        "applied_count": len(applied),
        "applied": applied,
        "skipped_excluded": skipped_excluded,
        "skipped_filter": skipped_filter,
    }


__all__ = [
    "CapitalizationFix",
    "CapitalizationFixReport",
    "DisambiguateBareChange",
    "DisambiguateBareReport",
    "FillDomainDecision",
    "FillDomainReport",
    "NormalizeDomainChange",
    "NormalizeDomainReport",
    "apply_disambiguate_bare",
    "apply_fill_domain",
    "apply_fix_capitalization",
    "apply_normalize_domain",
    "plan_disambiguate_bare",
    "plan_fill_domain",
    "plan_fix_capitalization",
    "plan_normalize_domain",
]


# ---------------------------------------------------------------------------
# Subfase 1.4a — fill_domain (auto, high-confidence rules only)
# ---------------------------------------------------------------------------

# Rule R1: subtype uniquely determines domain — safe to auto-apply
_SUBTYPE_TO_DOMAIN: dict[str, str] = {
    # religion
    "deity": "religion",
    "myth": "religion",
    "mythological_place": "religion",
    "religious_concept": "religion",
    "sacred_text": "religion",
    # filosofia
    "philosophical_concept": "filosofia",
    "school_of_thought": "filosofia",
    # machine_learning
    "algorithm": "machine_learning",
    "metric": "machine_learning",
    "technical_concept": "machine_learning",
    "architecture_pattern": "machine_learning",
    "case_study": "machine_learning",
    # ciencia
    "scientific_concept": "ciencia",
    "celestial_body": "ciencia",
    "geological_feature": "ciencia",
    "chemical_element": "ciencia",
    "compound": "ciencia",
    "molecule": "ciencia",
    "biological_process": "ciencia",
    "cell": "ciencia",
    "cell_type": "ciencia",
    "gene": "ciencia",
    "disease": "ciencia",
    "medical_theory": "ciencia",
    "theorem": "ciencia",
    "mathematical_object": "ciencia",
    "constant": "ciencia",
    "mathematical_function": "ciencia",
    "mathematical_field": "ciencia",
    "proof_method": "ciencia",
    "organism": "ciencia",
    "species": "ciencia",
    "anatomical_structure": "ciencia",
    # historia
    "historical_event": "historia",
    "historical_period": "historia",
    "historical_process": "historia",
    "dynasty": "historia",
    "war": "historia",
    "battle": "historia",
    "treaty": "historia",
    "revolution": "historia",
    "civilization": "historia",
    "polity": "historia",
    # esoterismo
    "esoteric_tradition": "esoterismo",
    "ritual": "esoterismo",
    "symbolic_system": "esoterismo",
    "divination_system": "esoterismo",
    "mystical_concept": "esoterismo",
    "esoteric_text": "esoterismo",
    "occult_movement": "esoterismo",
}

# Subtypes that don't need domain (skipped, not deferred)
_SKIP_SUBTYPES: frozenset[str] = frozenset({"disambiguation_page"})

# Subtypes explicitly deferred to manual review (1.4b)
_DEFER_TO_MANUAL: frozenset[str] = frozenset({
    "abstract_concept",  # too generic
    "discipline",        # filosofia vs ciencia vs varies
    "phenomenon",        # ciencia vs religion vs mitología
    "process",           # varies
    "theory",            # varies
    "emotion",           # varies
    "value",             # varies
    "symbol",            # varies
    "artifact",          # varies
    "classification",    # varies
    "weapon",            # usually historia but varies
    "animal",            # varies
    "plant",             # ciencia usually but mythic ones exist
    "technology",        # varies
    "programming_language",  # machine_learning? varies
    "language",          # varies
    "script",            # varies
    # work types — MUST be domain by content, not by author
    "book", "paper", "poem", "play", "artwork", "dataset", "software_project",
    # place types without era → needs manual review
    "country", "city", "region", "landmark", "continent",
    "empire",            # usually historia but check
    # organizations varying
    "company", "institution", "government", "religion", "academic_school",
    "military_unit", "office_role",
})

# Rule R2: person occupation keyword → domain
# Order matters: more specific keywords first (matched literally, case-insensitive).
_PERSON_OCCUPATION_RULES: list[tuple[str, str]] = [
    # filosofia
    ("filósofo", "filosofia"),
    ("filósofa", "filosofia"),
    ("filosofo", "filosofia"),
    ("philosopher", "filosofia"),
    ("sofista", "filosofia"),
    ("pensador estoico", "filosofia"),
    ("teólogo", "filosofia"),  # often falls under filosofia in this vault
    ("estoico", "filosofia"),
    # ciencia
    ("científico", "ciencia"),
    ("científica", "ciencia"),
    ("cientifico", "ciencia"),
    ("astrónomo", "ciencia"),
    ("astronoma", "ciencia"),
    ("matemático", "ciencia"),
    ("matematico", "ciencia"),
    ("físico", "ciencia"),
    ("fisico", "ciencia"),
    ("biólogo", "ciencia"),
    ("biologo", "ciencia"),
    ("químico", "ciencia"),
    ("quimico", "ciencia"),
    ("médico", "ciencia"),
    ("medico", "ciencia"),
    ("arqueólogo", "ciencia"),
    ("naturalista", "ciencia"),
    # historia — military/political
    ("emperador", "historia"),
    ("emperatriz", "historia"),
    ("rey ", "historia"),          # space-padded to avoid matching "creyente"
    ("reina ", "historia"),
    ("faraón", "historia"),
    ("general", "historia"),
    ("cónsul", "historia"),
    ("dictador", "historia"),
    ("comandante", "historia"),
    ("estadista", "historia"),
    ("conquistador", "historia"),
    ("militar", "historia"),
    ("senador", "historia"),
    ("tribuno", "historia"),
    ("tirano", "historia"),
    ("hegemón", "historia"),
    ("caudillo", "historia"),
    ("gobernante", "historia"),
    ("político", "historia"),
    ("politico", "historia"),
    ("diplomático", "historia"),
    ("historiador", "historia"),
    ("cronista", "historia"),
    ("sacerdote", "historia"),  # ancient priests — fits historia+religion; picking historia
    # machine_learning roles intentionally omitted (zero match in dataset)
]


@dataclass(slots=True, frozen=True)
class FillDomainDecision:
    note_path: str
    note_name: str
    subtype: str | None
    proposed_domain: str | None  # None when deferred
    rule: str  # "subtype", "person_occupation", "skip", "deferred", "already_has_domain"
    rationale: str

    @property
    def is_auto_applicable(self) -> bool:
        return self.proposed_domain is not None and self.rule in {
            "subtype", "person_occupation",
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "note_path": self.note_path,
            "note_name": self.note_name,
            "subtype": self.subtype,
            "proposed_domain": self.proposed_domain,
            "rule": self.rule,
            "rationale": self.rationale,
            "is_auto_applicable": self.is_auto_applicable,
        }


@dataclass(slots=True)
class FillDomainReport:
    vault_path: str
    total_notes_scanned: int = 0
    notes_already_have_domain: int = 0
    decisions: list[FillDomainDecision] = field(default_factory=list)

    @property
    def auto_apply_count(self) -> int:
        return sum(1 for d in self.decisions if d.is_auto_applicable)

    @property
    def deferred_count(self) -> int:
        return sum(1 for d in self.decisions if d.rule == "deferred")

    @property
    def skipped_count(self) -> int:
        return sum(1 for d in self.decisions if d.rule == "skip")

    def counts_by_rule(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for d in self.decisions:
            counts[d.rule] = counts.get(d.rule, 0) + 1
        return counts

    def counts_by_subtype(self, *, auto_only: bool = True) -> dict[str, dict[str, int]]:
        """Return {subtype: {domain: count}} for the decisions."""
        out: dict[str, dict[str, int]] = {}
        for d in self.decisions:
            if auto_only and not d.is_auto_applicable:
                continue
            st = d.subtype or "(none)"
            dm = d.proposed_domain or "(none)"
            out.setdefault(st, {}).setdefault(dm, 0)
            out[st][dm] += 1
        return out

    def to_dict(self) -> dict[str, object]:
        return {
            "vault_path": self.vault_path,
            "total_notes_scanned": self.total_notes_scanned,
            "notes_already_have_domain": self.notes_already_have_domain,
            "total_decisions": len(self.decisions),
            "auto_apply": self.auto_apply_count,
            "deferred": self.deferred_count,
            "skipped": self.skipped_count,
            "counts_by_rule": self.counts_by_rule(),
            "counts_by_subtype_auto": self.counts_by_subtype(auto_only=True),
            "decisions": [d.to_dict() for d in self.decisions],
        }


def _match_person_occupation(occupation: str) -> tuple[str, str] | None:
    """Return (domain, matched_keyword) if occupation matches a rule."""
    lower = f" {occupation.lower()} "
    for keyword, domain in _PERSON_OCCUPATION_RULES:
        if keyword in lower:
            return domain, keyword.strip()
    return None


def plan_fill_domain(vault_path: Path) -> FillDomainReport:
    """Scan the knowledge folder and decide what to auto-fill for missing domain.

    Does not mutate anything. Produces a report with per-note decisions.
    """
    knowledge_dir = vault_path / "02 - Knowledge"
    report = FillDomainReport(vault_path=str(vault_path))

    if not knowledge_dir.exists():
        return report

    for md in sorted(knowledge_dir.glob("*.md")):
        report.total_notes_scanned += 1
        try:
            text = md.read_text(encoding="utf-8")
        except OSError:
            continue
        try:
            fm, _ = split_frontmatter(text)
        except ValueError:
            continue
        if not isinstance(fm, dict):
            continue

        note_name = md.stem
        rel = str(md.relative_to(vault_path))
        subtype = fm.get("subtype") if isinstance(fm.get("subtype"), str) else None

        # Skip notes that already have a domain
        if fm.get("domain"):
            report.notes_already_have_domain += 1
            continue

        # Rule: skip disambiguation pages entirely
        if subtype in _SKIP_SUBTYPES:
            report.decisions.append(FillDomainDecision(
                note_path=rel, note_name=note_name, subtype=subtype,
                proposed_domain=None, rule="skip",
                rationale=f"subtype '{subtype}' does not require domain",
            ))
            continue

        # Rule R1: subtype → domain (hard rule)
        if subtype and subtype in _SUBTYPE_TO_DOMAIN:
            target = _SUBTYPE_TO_DOMAIN[subtype]
            report.decisions.append(FillDomainDecision(
                note_path=rel, note_name=note_name, subtype=subtype,
                proposed_domain=target, rule="subtype",
                rationale=f"subtype '{subtype}' uniquely maps to '{target}'",
            ))
            continue

        # Rule R2: person + occupation keyword
        if subtype == "person":
            occupation = fm.get("occupation")
            if isinstance(occupation, str) and occupation.strip():
                match = _match_person_occupation(occupation)
                if match:
                    target, keyword = match
                    report.decisions.append(FillDomainDecision(
                        note_path=rel, note_name=note_name, subtype=subtype,
                        proposed_domain=target, rule="person_occupation",
                        rationale=f"occupation contains '{keyword}' → '{target}'",
                    ))
                    continue
            # No match → defer
            report.decisions.append(FillDomainDecision(
                note_path=rel, note_name=note_name, subtype=subtype,
                proposed_domain=None, rule="deferred",
                rationale=(
                    "person without matching occupation keyword — needs manual review"
                    if occupation else "person without occupation field — needs manual review"
                ),
            ))
            continue

        # Rule R3: explicitly deferred subtypes
        if subtype in _DEFER_TO_MANUAL:
            report.decisions.append(FillDomainDecision(
                note_path=rel, note_name=note_name, subtype=subtype,
                proposed_domain=None, rule="deferred",
                rationale=f"subtype '{subtype}' requires content/context review (1.4b)",
            ))
            continue

        # Unknown subtype — defer
        report.decisions.append(FillDomainDecision(
            note_path=rel, note_name=note_name, subtype=subtype,
            proposed_domain=None, rule="deferred",
            rationale=f"subtype '{subtype}' has no auto-rule — manual review",
        ))

    return report


def apply_fill_domain(
    vault_path: Path,
    report: FillDomainReport,
    *,
    exclude: Iterable[str] = (),
) -> dict[str, object]:
    """Apply only the auto-applicable decisions from the report.

    Only touches `domain:` frontmatter (adds or fails if present).
    Never touches bodies.
    """
    excluded = set(exclude)
    applied: list[dict[str, object]] = []
    skipped: list[str] = []

    for d in report.decisions:
        if not d.is_auto_applicable:
            continue
        if d.note_path in excluded or d.note_name in excluded:
            skipped.append(d.note_path)
            continue
        md = vault_path / d.note_path
        if not md.exists():
            continue
        text = md.read_text(encoding="utf-8")
        try:
            fm, body = split_frontmatter(text)
        except ValueError:
            continue
        if not isinstance(fm, dict):
            continue
        if fm.get("domain"):
            # Defensive: was set between plan and apply
            skipped.append(d.note_path)
            continue
        fm["domain"] = d.proposed_domain
        md.write_text(dump_frontmatter(fm, body), encoding="utf-8")
        applied.append({
            "note_path": d.note_path,
            "note_name": d.note_name,
            "domain": d.proposed_domain,
            "rule": d.rule,
        })

    return {
        "applied_count": len(applied),
        "applied": applied,
        "skipped": skipped,
    }


# ---------------------------------------------------------------------------
# Subfase 1.3 — fix_capitalization
# Rename entities with inconsistent capitalization (e.g. `Imperio romano` →
# `Imperio Romano`) and update all incoming wikilinks and related entries.
# ---------------------------------------------------------------------------

from .naming_rules import has_capitalization_violation, suggest_capitalization


@dataclass(slots=True, frozen=True)
class CapitalizationFix:
    old_name: str
    new_name: str
    old_path: str
    new_path: str
    body_wikilink_mentions: int
    body_wikilink_files: list[str]
    related_entries: list[str]
    can_apply: bool
    error_message: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "old_name": self.old_name,
            "new_name": self.new_name,
            "old_path": self.old_path,
            "new_path": self.new_path,
            "body_wikilink_mentions": self.body_wikilink_mentions,
            "body_wikilink_files_count": len(self.body_wikilink_files),
            "related_entries_count": len(self.related_entries),
            "can_apply": self.can_apply,
            "error_message": self.error_message,
        }


@dataclass(slots=True)
class CapitalizationFixReport:
    vault_path: str
    total_notes_scanned: int = 0
    fixes: list[CapitalizationFix] = field(default_factory=list)

    @property
    def applicable_count(self) -> int:
        return sum(1 for f in self.fixes if f.can_apply)

    @property
    def blocked_count(self) -> int:
        return sum(1 for f in self.fixes if not f.can_apply)

    def to_dict(self) -> dict[str, object]:
        return {
            "vault_path": self.vault_path,
            "total_notes_scanned": self.total_notes_scanned,
            "total_fixes": len(self.fixes),
            "applicable": self.applicable_count,
            "blocked": self.blocked_count,
            "fixes": [f.to_dict() for f in self.fixes],
        }


def plan_fix_capitalization(vault_path: Path) -> CapitalizationFixReport:
    """Scan the knowledge folder for notes whose filename violates capitalization.

    For each violation, compute the suggested rename and count incoming
    body-wikilink + related-list references (dot-dirs excluded).
    """
    knowledge_dir = vault_path / "02 - Knowledge"
    report = CapitalizationFixReport(vault_path=str(vault_path))

    if not knowledge_dir.exists():
        return report

    for md in sorted(knowledge_dir.glob("*.md")):
        report.total_notes_scanned += 1
        old_name = md.stem
        if not has_capitalization_violation(old_name):
            continue
        new_name = suggest_capitalization(old_name)
        if not new_name:
            continue

        new_path = knowledge_dir / f"{new_name}.md"

        # Pre-flight checks. On case-insensitive filesystems (macOS APFS by
        # default), `Imperio romano.md` and `Imperio Romano.md` resolve to
        # the same inode — that's a case-only rename, not a collision.
        can_apply = True
        err: str | None = None
        if new_path.exists():
            try:
                is_same_file = new_path.samefile(md)
            except OSError:
                is_same_file = False
            if not is_same_file:
                can_apply = False
                err = f"Target file already exists: {new_path.name}"

        # Scan for incoming references (excluding dot-dirs and the file itself)
        body_regex = _build_body_wikilink_regex(old_name)
        body_files: list[str] = []
        body_count = 0
        related_files: list[str] = []

        for other in sorted(vault_path.rglob("*.md")):
            if other == md:
                continue
            if any(p.startswith(".") for p in other.relative_to(vault_path).parts):
                continue
            try:
                text = other.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            rel = str(other.relative_to(vault_path))

            split = _split_frontmatter_and_body(text)
            if split:
                fm_block, body = split
            else:
                fm_block, body = "", text

            matches = body_regex.findall(body)
            if matches:
                body_count += len(matches)
                body_files.append(rel)

            if fm_block and _is_in_related_section(fm_block, old_name):
                related_files.append(rel)

        report.fixes.append(CapitalizationFix(
            old_name=old_name,
            new_name=new_name,
            old_path=str(md.relative_to(vault_path)),
            new_path=str(new_path.relative_to(vault_path)),
            body_wikilink_mentions=body_count,
            body_wikilink_files=body_files,
            related_entries=related_files,
            can_apply=can_apply,
            error_message=err,
        ))

    return report


def apply_fix_capitalization(
    vault_path: Path,
    report: CapitalizationFixReport,
    *,
    exclude: Iterable[str] = (),
) -> dict[str, object]:
    """Apply the planned renames. Returns a summary.

    For each fix:
      1. Rename the file on disk: `old.md` → `new.md`.
      2. Update `name:` field in the renamed file's frontmatter.
      3. For every referencing file:
         - Body: `[[old]]` → `[[new]]`, `[[old|X]]` → `[[new|X]]`.
         - Related plain: `- old` → `- new`.
         - Related wikilink-in-string: `- '[[old]]'` → `- '[[new]]'`.
    """
    excluded = set(exclude)
    applied: list[dict[str, object]] = []
    skipped: list[str] = []

    for fix in report.fixes:
        if not fix.can_apply:
            skipped.append(f"{fix.old_name}: {fix.error_message}")
            continue
        if fix.old_name in excluded:
            skipped.append(f"{fix.old_name}: excluded by user")
            continue

        old_path = vault_path / fix.old_path
        new_path = vault_path / fix.new_path

        if not old_path.exists():
            skipped.append(f"{fix.old_name}: source file missing")
            continue

        # 1. Read + update frontmatter
        original_text = old_path.read_text(encoding="utf-8")
        fm, body = split_frontmatter(original_text)
        fm["name"] = fix.new_name

        # 2. Case-safe rename. On case-insensitive filesystems (macOS APFS)
        # a direct write to new_path + unlink(old_path) can destroy content
        # because both paths resolve to the same inode. We rename via a temp
        # name first, which works on both case-sensitive and case-insensitive
        # filesystems.
        import os as _os
        temp_path = old_path.with_name(f".__rename_tmp_{_os.getpid()}.md")
        old_path.rename(temp_path)
        try:
            temp_path.write_text(dump_frontmatter(fm, body), encoding="utf-8")
            temp_path.rename(new_path)
        except Exception:
            # best-effort restore
            if temp_path.exists():
                temp_path.rename(old_path)
            raise

        # 3. Update every referencing file
        body_updated = 0
        related_updated = 0

        referencing = set(fix.body_wikilink_files) | set(fix.related_entries)
        for rel_path in referencing:
            md = vault_path / rel_path
            if not md.exists():
                continue
            text = md.read_text(encoding="utf-8")
            split = _split_frontmatter_and_body(text)
            if split:
                fm_block, old_body = split
            else:
                fm_block, old_body = "", text

            new_body, body_count = _update_body_wikilinks_direct(
                old_body, fix.old_name, fix.new_name,
            )
            new_fm, fm_changed = _update_related_entry_direct(
                fm_block, fix.old_name, fix.new_name,
            )

            if body_count > 0 or fm_changed:
                md.write_text(new_fm + new_body, encoding="utf-8")
                if body_count > 0:
                    body_updated += 1
                if fm_changed:
                    related_updated += 1

        applied.append({
            "old_name": fix.old_name,
            "new_name": fix.new_name,
            "body_files_updated": body_updated,
            "related_files_updated": related_updated,
        })

    return {"applied": applied, "skipped": skipped}


def _update_body_wikilinks_direct(
    body: str, old_name: str, new_name: str,
) -> tuple[str, int]:
    """Direct rename (no display-alias wrapping). Used by fix_capitalization.

    [[old]]      → [[new]]
    [[old|X]]    → [[new|X]]
    Does NOT touch [[old (variant)]].
    """
    escaped = _re.escape(old_name)
    count = [0]

    def _repl_plain(m: _re.Match[str]) -> str:
        count[0] += 1
        return f"[[{new_name}]]"

    body = _re.sub(r"\[\[" + escaped + r"\]\]", _repl_plain, body)

    def _repl_aliased(m: _re.Match[str]) -> str:
        count[0] += 1
        return f"[[{new_name}|"

    body = _re.sub(r"\[\[" + escaped + r"\|", _repl_aliased, body)

    return body, count[0]


def _update_related_entry_direct(
    frontmatter_block: str, old_name: str, new_name: str,
) -> tuple[str, bool]:
    """Direct rename (no alias wrapping) of related: entries.

    Handles both patterns:
      `- old` → `- new`
      `- '[[old]]'` → `- '[[new]]'`
    Used by fix_capitalization where preserving display text is NOT desired
    (the whole point of the fix is to update the display).
    """
    changed = [False]

    plain_pat = _related_entry_regex(old_name)

    def _repl_plain(m: _re.Match[str]) -> str:
        changed[0] = True
        return f"{m.group(1)}{new_name}{m.group(3)}"

    frontmatter_block = plain_pat.sub(_repl_plain, frontmatter_block)

    wl_pat = _related_wikilink_string_regex(old_name)

    def _repl_wl(m: _re.Match[str]) -> str:
        changed[0] = True
        indent = m.group(1)
        open_q = m.group(2)
        close_q = m.group(3)
        trailing = m.group(4)
        return f"{indent}{open_q}[[{new_name}]]{close_q}{trailing}"

    frontmatter_block = wl_pat.sub(_repl_wl, frontmatter_block)

    return frontmatter_block, changed[0]


# ---------------------------------------------------------------------------
# Subfase 1.5 — disambiguate_bare
# Convert a bare-name entity into a disambiguation_page, renaming the
# original to a discriminated form and updating incoming wikilinks.
# ---------------------------------------------------------------------------

import re as _re


@dataclass(slots=True, frozen=True)
class DisambiguateBareChange:
    action: str  # "rename", "create_disambig", "update_body_wikilink", "update_related"
    path: str
    before: str
    after: str

    def to_dict(self) -> dict[str, object]:
        return {
            "action": self.action,
            "path": self.path,
            "before": self.before,
            "after": self.after,
        }


@dataclass(slots=True)
class DisambiguateBareReport:
    vault_path: str
    bare_name: str
    discriminator: str
    new_canonical_name: str
    existing_variants: list[str] = field(default_factory=list)
    body_wikilink_mentions: int = 0
    body_wikilink_files: list[str] = field(default_factory=list)
    related_entries: list[str] = field(default_factory=list)
    disambig_page_preview: str = ""
    sample_body_changes: list[str] = field(default_factory=list)
    can_apply: bool = True
    error_message: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "vault_path": self.vault_path,
            "bare_name": self.bare_name,
            "discriminator": self.discriminator,
            "new_canonical_name": self.new_canonical_name,
            "existing_variants": list(self.existing_variants),
            "body_wikilink_mentions": self.body_wikilink_mentions,
            "body_wikilink_files_count": len(self.body_wikilink_files),
            "body_wikilink_files": list(self.body_wikilink_files),
            "related_entries_count": len(self.related_entries),
            "related_entries": list(self.related_entries),
            "disambig_page_preview": self.disambig_page_preview,
            "sample_body_changes": list(self.sample_body_changes),
            "can_apply": self.can_apply,
            "error_message": self.error_message,
        }


def _build_body_wikilink_regex(bare: str) -> _re.Pattern[str]:
    """Match [[Bare]] or [[Bare|...]] but NOT [[Bare (variant)...]]."""
    escaped = _re.escape(bare)
    return _re.compile(r"\[\[" + escaped + r"(\||\]\])")


def _split_frontmatter_and_body(text: str) -> tuple[str, str] | None:
    """Return (frontmatter_block, body) or None if no frontmatter."""
    m = _re.match(r"^(---\s*\n.*?\n---\s*\n?)(.*)$", text, _re.DOTALL)
    if not m:
        return None
    return m.group(1), m.group(2)


def _related_entry_regex(bare: str) -> _re.Pattern[str]:
    """Match a `related:` list item that is EXACTLY `- <bare>` (quoted or not).

    Matches lines like:
      - Tebas
      - "Tebas"
      - 'Tebas'
      -   Tebas
    Does NOT match `- Tebas (Egipto)` or `- Tebas algo`.
    """
    escaped = _re.escape(bare)
    return _re.compile(
        r"^(\s*-\s+)([\"']?)" + escaped + r"\2(\s*)$",
        _re.MULTILINE,
    )


def _related_wikilink_string_regex(bare: str) -> _re.Pattern[str]:
    """Match a `related:` list item that is a wikilink inside a YAML string.

    Matches lines like:
      - '[[Tebas]]'
      - "[[Tebas]]"
    Does NOT match `- '[[Tebas (Egipto)]]'` or `- '[[Tebas|X]]'`.
    """
    escaped = _re.escape(bare)
    return _re.compile(
        r"^(\s*-\s+)(['\"])\[\[" + escaped + r"\]\](['\"])(\s*)$",
        _re.MULTILINE,
    )


def _is_in_related_section(frontmatter_block: str, bare: str) -> bool:
    """Shallow check: does the frontmatter contain `related:` anywhere with this bare?"""
    if "related:" not in frontmatter_block:
        return False
    if _related_entry_regex(bare).search(frontmatter_block):
        return True
    if _related_wikilink_string_regex(bare).search(frontmatter_block):
        return True
    return False


def _count_body_wikilinks(body: str, bare: str) -> int:
    pattern = _build_body_wikilink_regex(bare)
    return len(pattern.findall(body))


def _update_body_wikilinks(body: str, bare: str, new_canonical: str) -> tuple[str, int]:
    """Return (new_body, count_replaced)."""
    escaped = _re.escape(bare)
    count = [0]

    # Replace [[Bare]] → [[New|Bare]]
    def _replace_unaliased(m: _re.Match[str]) -> str:
        count[0] += 1
        return f"[[{new_canonical}|{bare}]]"

    body = _re.sub(r"\[\[" + escaped + r"\]\]", _replace_unaliased, body)

    # Replace [[Bare|display]] → [[New|display]]
    def _replace_aliased(m: _re.Match[str]) -> str:
        count[0] += 1
        return f"[[{new_canonical}|"

    body = _re.sub(r"\[\[" + escaped + r"\|", _replace_aliased, body)

    return body, count[0]


def _update_related_entry(frontmatter_block: str, bare: str, new_canonical: str) -> tuple[str, bool]:
    """Replace related-list entries referring to the bare name.

    Handles both patterns found in the vault:
      1. Plain bare: `- Tebas` → `- Tebas (Grecia)`
      2. Wikilink-in-string: `- '[[Tebas]]'` → `- '[[Tebas (Grecia)|Tebas]]'`
         (preserves display text via alias form, consistent with body wikilink update)

    Preserves quoting and whitespace. Does NOT touch pre-existing disambiguated
    forms like `- Tebas (Egipto)` or `- '[[Tebas (Egipto)]]'`.
    """
    changed = [False]

    # Pattern 1: plain bare `- Tebas`
    plain_pat = _related_entry_regex(bare)

    def _repl_plain(m: _re.Match[str]) -> str:
        changed[0] = True
        return f"{m.group(1)}{new_canonical}{m.group(3)}"

    frontmatter_block = plain_pat.sub(_repl_plain, frontmatter_block)

    # Pattern 2: wikilink-in-string `- '[[Tebas]]'` or `- "[[Tebas]]"`
    wl_pat = _related_wikilink_string_regex(bare)

    def _repl_wl(m: _re.Match[str]) -> str:
        changed[0] = True
        indent = m.group(1)
        open_q = m.group(2)
        close_q = m.group(3)
        trailing = m.group(4)
        # Produce `[[new|bare]]` inside the same quote style, preserving display
        return f"{indent}{open_q}[[{new_canonical}|{bare}]]{close_q}{trailing}"

    frontmatter_block = wl_pat.sub(_repl_wl, frontmatter_block)

    return frontmatter_block, changed[0]


def _disambig_page_content(
    bare: str,
    variants: list[str],
    variant_descriptions: dict[str, str] | None = None,
) -> str:
    """Generate a disambiguation_page markdown file, Roma-style."""
    import yaml
    frontmatter = {
        "type": "disambiguation",
        "object_kind": "disambiguation",
        "subtype": "disambiguation_page",
        "name": bare,
        "entity": False,
        "status": "canonical",
        "disambiguates": list(variants),
    }
    fm_yaml = yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True).strip()
    descriptions = variant_descriptions or {}
    lines = [f"---\n{fm_yaml}\n---", ""]
    lines.append(f"**{bare}** puede referirse a:")
    lines.append("")
    for v in variants:
        desc = descriptions.get(v, "")
        if desc:
            lines.append(f"- [[{v}]] — {desc}")
        else:
            lines.append(f"- [[{v}]]")
    lines.append("")
    lines.append("## Related notes")
    lines.append("")
    return "\n".join(lines)


def plan_disambiguate_bare(
    vault_path: Path,
    bare_name: str,
    discriminator: str,
) -> DisambiguateBareReport:
    """Scan the vault and plan the conversion of `bare_name` into a disambig_page.

    Does NOT mutate anything.
    """
    knowledge_dir = vault_path / "02 - Knowledge"
    new_canonical = f"{bare_name} ({discriminator})"

    report = DisambiguateBareReport(
        vault_path=str(vault_path),
        bare_name=bare_name,
        discriminator=discriminator,
        new_canonical_name=new_canonical,
    )

    bare_file = knowledge_dir / f"{bare_name}.md"
    if not bare_file.exists():
        report.can_apply = False
        report.error_message = f"Bare note not found: {bare_file}"
        return report

    target_file = knowledge_dir / f"{new_canonical}.md"
    if target_file.exists():
        report.can_apply = False
        report.error_message = (
            f"Target file already exists: {target_file}. "
            f"Pick a different discriminator or resolve manually."
        )
        return report

    # Verify bare is NOT already a disambiguation_page
    try:
        bare_fm, _ = split_frontmatter(bare_file.read_text(encoding="utf-8"))
    except ValueError:
        bare_fm = {}
    if isinstance(bare_fm, dict) and bare_fm.get("subtype") == "disambiguation_page":
        report.can_apply = False
        report.error_message = f"'{bare_name}' is already a disambiguation_page"
        return report

    # Find existing disambiguated variants
    variants: list[str] = [new_canonical]  # the new one we'll create
    for md in sorted(knowledge_dir.glob(f"{bare_name} (*.md")):
        name = md.stem
        if name != new_canonical:
            variants.append(name)
    report.existing_variants = sorted(variants)

    # Scan the whole vault for incoming mentions. Skip dot-directories
    # (.brain-ops/ backups, .obsidian/ plugin data, .git/ if any) — their
    # .md contents are not real vault notes.
    body_regex = _build_body_wikilink_regex(bare_name)

    for md in sorted(vault_path.rglob("*.md")):
        # skip the bare file itself (it'll be renamed)
        if md == bare_file:
            continue
        # skip anything under a dot-directory
        if any(part.startswith(".") for part in md.relative_to(vault_path).parts):
            continue
        try:
            text = md.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        rel = str(md.relative_to(vault_path))

        # Body wikilink check
        split = _split_frontmatter_and_body(text)
        if split:
            fm_block, body = split
        else:
            fm_block, body = "", text

        body_matches = body_regex.findall(body)
        if body_matches:
            report.body_wikilink_mentions += len(body_matches)
            report.body_wikilink_files.append(rel)
            # Capture a sample
            if len(report.sample_body_changes) < 8:
                sample = _build_body_wikilink_regex(bare_name).search(body)
                if sample:
                    start = max(0, sample.start() - 25)
                    end = min(len(body), sample.end() + 25)
                    snippet = body[start:end].replace("\n", " ")
                    report.sample_body_changes.append(
                        f"{rel}: …{snippet}…"
                    )

        # related: list entry check
        if fm_block and _is_in_related_section(fm_block, bare_name):
            report.related_entries.append(rel)

    # Build preview of the disambig page body
    report.disambig_page_preview = _disambig_page_content(
        bare_name,
        report.existing_variants,
    )

    return report


def apply_disambiguate_bare(
    vault_path: Path,
    report: DisambiguateBareReport,
) -> dict[str, object]:
    """Apply the disambiguation plan. Returns a summary of changes made.

    Sequence (atomic best-effort):
      1. Write renamed file with updated frontmatter (new name, base_name, aliases)
      2. Update body wikilinks in every file that mentions the bare (excluding bare itself)
      3. Update `related:` list entries in every file
      4. Create new disambig page at bare_name.md (replaces the bare file)
      5. Delete the old bare file (which was copied to the renamed path in step 1)
    """
    if not report.can_apply:
        return {"applied": False, "error": report.error_message}

    knowledge_dir = vault_path / "02 - Knowledge"
    bare_file = knowledge_dir / f"{report.bare_name}.md"
    target_file = knowledge_dir / f"{report.new_canonical_name}.md"

    applied: dict[str, list[str]] = {
        "renamed": [],
        "body_wikilinks_updated": [],
        "related_entries_updated": [],
        "disambig_page_created": [],
        "errors": [],
    }

    # Step 1: write the renamed file with updated frontmatter
    original_text = bare_file.read_text(encoding="utf-8")
    fm, body = split_frontmatter(original_text)
    fm["name"] = report.new_canonical_name
    fm["base_name"] = report.bare_name
    aliases = fm.get("aliases")
    if not isinstance(aliases, list):
        aliases = []
    if report.bare_name not in aliases:
        aliases.append(report.bare_name)
    fm["aliases"] = aliases

    target_file.write_text(dump_frontmatter(fm, body), encoding="utf-8")
    applied["renamed"].append(f"{bare_file.name} → {target_file.name}")

    # Step 2: update body wikilinks in OTHER files
    # Note: we exclude the bare file (which will be overwritten with disambig page)
    # but INCLUDE the renamed target (its own body might reference the bare).
    # The report already excluded dot-directories, so we iterate report-provided paths only.
    for rel_path in report.body_wikilink_files:
        md = vault_path / rel_path
        if md == bare_file:
            continue
        try:
            text = md.read_text(encoding="utf-8")
        except OSError:
            continue
        split = _split_frontmatter_and_body(text)
        if split:
            fm_block, old_body = split
        else:
            fm_block, old_body = "", text
        new_body, count = _update_body_wikilinks(
            old_body, report.bare_name, report.new_canonical_name
        )
        if count > 0:
            md.write_text(fm_block + new_body, encoding="utf-8")
            applied["body_wikilinks_updated"].append(f"{rel_path} ({count})")

    # Step 3: update `related:` list entries
    for rel_path in report.related_entries:
        md = vault_path / rel_path
        if md == bare_file:
            continue
        try:
            text = md.read_text(encoding="utf-8")
        except OSError:
            continue
        split = _split_frontmatter_and_body(text)
        if not split:
            continue
        fm_block, rest = split
        new_fm, changed = _update_related_entry(
            fm_block, report.bare_name, report.new_canonical_name
        )
        if changed:
            md.write_text(new_fm + rest, encoding="utf-8")
            applied["related_entries_updated"].append(rel_path)

    # Step 4: write the disambig page at bare_name.md (overwriting the old bare)
    bare_file.write_text(report.disambig_page_preview, encoding="utf-8")
    applied["disambig_page_created"].append(bare_file.name)

    return {
        "applied": True,
        "bare_name": report.bare_name,
        "new_canonical_name": report.new_canonical_name,
        "counts": {
            "renamed": len(applied["renamed"]),
            "body_wikilinks_updated": len(applied["body_wikilinks_updated"]),
            "related_entries_updated": len(applied["related_entries_updated"]),
            "disambig_page_created": len(applied["disambig_page_created"]),
        },
        "details": applied,
    }
