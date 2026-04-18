"""Canonical naming rules for knowledge entities.

Defines the canonical form for domain slugs, the alias mapping for existing
non-canonical labels, and detectors for common naming violations (inconsistent
capitalization on periods/empires, bare-name ambiguity, non-canonical domain).

None of these functions mutate the vault. They only report violations.
See docs/operations/NAMING_RULES.md for the full rationale.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


# ---------------------------------------------------------------------------
# Canonical domain slugs (Spanish, without accents, snake_case where needed).
# See Decision #2 of Campaña 0.
# ---------------------------------------------------------------------------

CANONICAL_DOMAINS: frozenset[str] = frozenset({
    "historia",
    "filosofia",
    "ciencia",
    "religion",
    "esoterismo",
    "machine_learning",
})

# Aliases from pre-existing domain labels to the canonical slug.
# When a collapse happens, the previous label is captured into the suggested
# subdomain (e.g. "astronomía" → domain=ciencia, subdomain=astronomía).
DOMAIN_ALIASES: dict[str, str] = {
    # English → Spanish canonicals
    "history": "historia",
    "philosophy": "filosofia",
    "science": "ciencia",
    # Already-canonical values (accept both accented and non-accented on read)
    "religión": "religion",
    # Astronomical labels that should collapse under ciencia
    "astronomía": "ciencia",
    "astronomia": "ciencia",
    # Filosofía with accent
    "filosofía": "filosofia",
    # esoteric variants
    "esotérico": "esoterismo",
    "esoteric": "esoterismo",
}

# When a domain alias is applied, this gives the suggested subdomain
# that preserves the original intent.
DOMAIN_ALIAS_SUBDOMAIN_HINT: dict[str, str] = {
    "astronomía": "astronomia",
    "astronomia": "astronomia",
}


# ---------------------------------------------------------------------------
# Violation severity
# ---------------------------------------------------------------------------

SEVERITIES = ("error", "warning", "info")


@dataclass(slots=True, frozen=True)
class NamingViolation:
    note_name: str
    severity: str
    rule: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {
            "note_name": self.note_name,
            "severity": self.severity,
            "rule": self.rule,
            "message": self.message,
        }


# ---------------------------------------------------------------------------
# Domain canonicalization
# ---------------------------------------------------------------------------

def canonical_domain(domain: str | None) -> str | None:
    """Return the canonical form for a domain label, or None if input is falsy."""
    if not domain or not isinstance(domain, str):
        return None
    stripped = domain.strip()
    if not stripped:
        return None
    if stripped in CANONICAL_DOMAINS:
        return stripped
    # Case-insensitive alias lookup, preserve accented form for hint detection
    alias = DOMAIN_ALIASES.get(stripped) or DOMAIN_ALIASES.get(stripped.lower())
    if alias:
        return alias
    return None


def suggested_subdomain_for_alias(raw_domain: str | None) -> str | None:
    """If the raw domain triggers an alias collapse, return the subdomain hint."""
    if not isinstance(raw_domain, str):
        return None
    key = raw_domain.strip()
    return DOMAIN_ALIAS_SUBDOMAIN_HINT.get(key) or DOMAIN_ALIAS_SUBDOMAIN_HINT.get(key.lower())


def is_canonical_domain(domain: str | None) -> bool:
    return isinstance(domain, str) and domain in CANONICAL_DOMAINS


# ---------------------------------------------------------------------------
# Capitalization detectors for periods / empires / republics
# ---------------------------------------------------------------------------

# These patterns flag names that mix lowercase adjectives with a capitalized
# head noun. We do NOT auto-correct — we only detect. Examples caught:
#   "Imperio medo"  → should be "Imperio Medo"
#   "Imperio romano" → should be "Imperio Romano"
_CAPITALIZATION_HEAD_NOUNS: tuple[str, ...] = (
    "Imperio",
    "Período",
    "Periodo",
    "República",
    "Reino",
    "Dinastía",
    "Edad",
    "Era",
    "Siglo",
    "Imperio Romano",
    "Imperio Bizantino",
)

# Known exceptions where lowercase-after-head-noun is the canonical form
_CAPITALIZATION_EXCEPTIONS: frozenset[str] = frozenset({
    "República de Roma",  # illustrative — none currently known
})


# Spanish prepositions / articles that should NOT be capitalized even when
# they follow a head noun like "Reino" or "Imperio". A name like "Reino de
# Macedonia" is canonically correct — `de` is a preposition, not a name part.
_SPANISH_LOWERCASE_WORDS: frozenset[str] = frozenset({
    "de", "del", "la", "las", "el", "los", "en", "a", "al",
    "y", "o", "u", "e",  # conjunctions
})


_cap_pattern = re.compile(
    r"^(?P<head>"
    + "|".join(re.escape(h) for h in _CAPITALIZATION_HEAD_NOUNS)
    + r")\s+(?P<adj>[a-záéíóúñ][a-záéíóúñ]+.*)$"
)


def _first_word_is_preposition(adj: str) -> bool:
    first = adj.split()[0] if adj else ""
    return first.lower() in _SPANISH_LOWERCASE_WORDS


def has_capitalization_violation(name: str) -> bool:
    """Detect names like 'Imperio medo' that should start the adjective uppercase.

    Skips names where the word after the head noun is a Spanish preposition
    or article (`de`, `del`, `la`, etc.) — those are canonically lowercase
    (e.g. `Reino de Macedonia` is correct, not a violation).
    """
    if name in _CAPITALIZATION_EXCEPTIONS:
        return False
    m = _cap_pattern.match(name)
    if not m:
        return False
    if _first_word_is_preposition(m.group("adj")):
        return False
    return True


def suggest_capitalization(name: str) -> str | None:
    """Return the suggested corrected name, or None if no violation."""
    if not has_capitalization_violation(name):
        return None
    m = _cap_pattern.match(name)
    head = m.group("head")
    adj = m.group("adj")
    fixed_adj = adj[0].upper() + adj[1:]
    return f"{head} {fixed_adj}"


# ---------------------------------------------------------------------------
# Bare-name disambiguation detector
#
# Rule (Decision #3 of Campaña 0):
# If a bare name X exists AND there are disambiguated variants X (foo), X (bar),
# then the bare name should be a disambiguation_page (or renamed to a clearly
# dominant canonical entity).
# ---------------------------------------------------------------------------

_DISAMBIG_SUFFIX = re.compile(r"\s+\([^)]+\)$")


def extract_bare_form(name: str) -> str:
    """Strip a trailing '(label)' suffix if present."""
    return _DISAMBIG_SUFFIX.sub("", name).strip()


def detect_bare_name_ambiguity(
    all_names: Iterable[str],
) -> dict[str, list[str]]:
    """Return mapping bare_name → [all variants] for ambiguous bare names.

    A bare name is considered ambiguous when:
    - it exists as a standalone name
    - at least one disambiguated variant of the same base exists
    """
    names = list(all_names)
    by_bare: dict[str, list[str]] = {}
    for n in names:
        bare = extract_bare_form(n)
        by_bare.setdefault(bare, []).append(n)

    ambiguous: dict[str, list[str]] = {}
    for bare, variants in by_bare.items():
        if len(variants) <= 1:
            continue
        # At least one variant must be the bare name exactly
        if bare in variants:
            ambiguous[bare] = sorted(variants)
    return ambiguous


# ---------------------------------------------------------------------------
# Top-level check for a single note
# ---------------------------------------------------------------------------

def _flag_domain_value(note_name: str, raw: str, context: str = "") -> NamingViolation | None:
    """Check a single domain string value; return violation if non-canonical."""
    if not raw:
        return None
    if is_canonical_domain(raw):
        return None
    canonical = canonical_domain(raw)
    suffix = f" ({context})" if context else ""
    if canonical:
        return NamingViolation(
            note_name=note_name,
            severity="warning",
            rule="domain_alias",
            message=f"domain '{raw}'{suffix} is not canonical; should be '{canonical}'",
        )
    return NamingViolation(
        note_name=note_name,
        severity="warning",
        rule="domain_unknown",
        message=f"domain '{raw}'{suffix} is neither canonical nor a known alias",
    )


def check_note_naming(
    note_name: str,
    frontmatter: dict[str, object],
) -> list[NamingViolation]:
    """Run naming checks on a single note and return its violations.

    This function does NOT check bare-name ambiguity — that requires the full
    vault and is handled by `check_vault_naming` separately.

    Handles `domain` as either a string (canonical single-domain) or a list
    (accepted as exception for bridge figures — max 2 values, canonicalized).
    """
    violations: list[NamingViolation] = []

    raw_domain = frontmatter.get("domain")
    if isinstance(raw_domain, str):
        v = _flag_domain_value(note_name, raw_domain)
        if v is not None:
            violations.append(v)
    elif isinstance(raw_domain, list):
        # list-domain: flag if any element is non-canonical
        for i, item in enumerate(raw_domain):
            if isinstance(item, str):
                v = _flag_domain_value(note_name, item, context=f"list item {i}")
                if v is not None:
                    violations.append(v)
        # Also flag if list has more than 2 elements (design rule: max 2)
        if len(raw_domain) > 2:
            violations.append(NamingViolation(
                note_name=note_name,
                severity="warning",
                rule="domain_list_too_long",
                message=(
                    f"domain has {len(raw_domain)} values; list-domain is an "
                    f"exception and must have at most 2"
                ),
            ))

    # Capitalization on periods/empires
    if has_capitalization_violation(note_name):
        suggestion = suggest_capitalization(note_name)
        violations.append(NamingViolation(
            note_name=note_name,
            severity="warning",
            rule="capitalization",
            message=f"name '{note_name}' mixes capitalization; suggested: '{suggestion}'",
        ))

    return violations


def check_vault_naming(
    names_and_frontmatter: Iterable[tuple[str, dict[str, object]]],
) -> list[NamingViolation]:
    """Run naming checks across the whole vault.

    Accepts an iterable of (note_name, frontmatter) pairs — keeps the module
    free of IO. Returns all violations including bare-name ambiguity.

    A bare name flagged as `disambiguation_dominant: true` in its frontmatter
    is treated as the canonical meaning for that name and does NOT trigger
    the bare_name_ambiguity warning, even if disambiguated variants exist.
    This is the opt-in marker for B-type bare-name decisions (see Subfase 1.5).
    """
    pairs = list(names_and_frontmatter)
    violations: list[NamingViolation] = []

    for note_name, fm in pairs:
        violations.extend(check_note_naming(note_name, fm))

    ambiguous = detect_bare_name_ambiguity(name for name, _ in pairs)
    # Build maps for per-note attributes used by the ambiguity skip logic
    subtype_of: dict[str, str] = {}
    dominant_of: dict[str, bool] = {}
    for note_name, fm in pairs:
        st = fm.get("subtype")
        if isinstance(st, str):
            subtype_of[note_name] = st
        dom = fm.get("disambiguation_dominant")
        if dom is True:
            dominant_of[note_name] = True

    for bare, variants in ambiguous.items():
        current_subtype = subtype_of.get(bare)
        if current_subtype == "disambiguation_page":
            continue  # already correctly handled
        if dominant_of.get(bare):
            continue  # bare is explicitly the dominant canonical meaning
        variants_str = ", ".join(v for v in variants if v != bare)
        violations.append(NamingViolation(
            note_name=bare,
            severity="warning",
            rule="bare_name_ambiguity",
            message=(
                f"bare name '{bare}' coexists with disambiguated variants "
                f"[{variants_str}] — should be a disambiguation_page"
            ),
        ))

    return violations


__all__ = [
    "CANONICAL_DOMAINS",
    "DOMAIN_ALIASES",
    "DOMAIN_ALIAS_SUBDOMAIN_HINT",
    "NamingViolation",
    "SEVERITIES",
    "canonical_domain",
    "check_note_naming",
    "check_vault_naming",
    "detect_bare_name_ambiguity",
    "extract_bare_form",
    "has_capitalization_violation",
    "is_canonical_domain",
    "suggest_capitalization",
    "suggested_subdomain_for_alias",
]
