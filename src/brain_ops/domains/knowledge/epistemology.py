"""Epistemic layer — distinguishes the kind of truth claim a note represents.

This module defines the vocabulary used to tag every knowledge note with
its epistemic status: historical, scientific, religious, mythological,
esoteric, philosophical, or speculative.

The layer exists because the vault covers domains with very different
warrant structures (verified science, documented history, religious tradition,
symbolic esoterism, open speculation). Mixing them in the same graph without
marking the distinction erodes the meaning of every assertion.

See docs/operations/EPISTEMOLOGY.md for the full rationale.
"""

from __future__ import annotations


EPISTEMIC_MODES: frozenset[str] = frozenset({
    "historical",
    "scientific",
    "religious",
    "mythological",
    "esoteric",
    "philosophical",
    "speculative",
})

CERTAINTY_LEVELS: frozenset[str] = frozenset({
    "well_supported",
    "tradition_based",
    "symbolic",
    "contested",
    "speculative",
})

# Spanish labels for UI / docs
EPISTEMIC_MODE_LABELS: dict[str, str] = {
    "historical": "histórico",
    "scientific": "científico",
    "religious": "religioso",
    "mythological": "mitológico",
    "esoteric": "esotérico",
    "philosophical": "filosófico",
    "speculative": "especulativo",
}

CERTAINTY_LEVEL_LABELS: dict[str, str] = {
    "well_supported": "bien sustentado",
    "tradition_based": "basado en tradición",
    "symbolic": "simbólico",
    "contested": "en disputa",
    "speculative": "especulativo",
}

# Domains where notes NEW must carry epistemic_mode.
# Existing notes are only warned about via the linter — never blocked.
EPISTEMIC_GATED_DOMAINS: frozenset[str] = frozenset({
    "religion",
    "esoterismo",
    "filosofia",
    "ciencia",
})

# Default epistemic_mode per subtype. Applied automatically by create-entity
# when the subtype has an unambiguous default. Subtypes NOT in this map are
# left without default — the writer must choose.
DEFAULT_EPISTEMIC_BY_SUBTYPE: dict[str, str] = {
    # mythological
    "deity": "mythological",
    "myth": "mythological",
    "mythological_place": "mythological",
    # esoteric
    "esoteric_tradition": "esoteric",
    "ritual": "esoteric",
    "symbolic_system": "esoteric",
    "divination_system": "esoteric",
    "mystical_concept": "esoteric",
    "esoteric_text": "esoteric",
    "occult_movement": "esoteric",
    # philosophical
    "philosophical_concept": "philosophical",
    "school_of_thought": "philosophical",
    # scientific
    "scientific_concept": "scientific",
    "theorem": "scientific",
    "mathematical_object": "scientific",
    "mathematical_function": "scientific",
    "constant": "scientific",
    "mathematical_field": "scientific",
    "proof_method": "scientific",
    "chemical_element": "scientific",
    "compound": "scientific",
    "molecule": "scientific",
    "biological_process": "scientific",
    "gene": "scientific",
    "disease": "scientific",
    "medical_theory": "scientific",
    "cell": "scientific",
    "cell_type": "scientific",
    "organism": "scientific",
    "species": "scientific",
    "anatomical_structure": "scientific",
    # historical
    "historical_event": "historical",
    "historical_period": "historical",
    "historical_process": "historical",
    "dynasty": "historical",
    # religious
    "sacred_text": "religious",
    "religious_concept": "religious",
}


def is_valid_epistemic_mode(mode: str | None) -> bool:
    return isinstance(mode, str) and mode in EPISTEMIC_MODES


def is_valid_certainty_level(level: str | None) -> bool:
    return isinstance(level, str) and level in CERTAINTY_LEVELS


def default_epistemic_mode(subtype: str | None) -> str | None:
    """Return the default epistemic_mode for a subtype, or None if ambiguous."""
    if not subtype:
        return None
    return DEFAULT_EPISTEMIC_BY_SUBTYPE.get(subtype)


def is_gated_domain(domain: str | None) -> bool:
    """True if NEW notes in this domain should carry epistemic_mode."""
    if not isinstance(domain, str):
        return False
    return domain in EPISTEMIC_GATED_DOMAINS


def apply_epistemic_default(
    frontmatter: dict[str, object],
    subtype: str | None,
) -> tuple[dict[str, object], bool]:
    """Fill epistemic_mode with the subtype default if absent.

    Returns the (possibly updated) frontmatter and a boolean indicating
    whether a change was made. Never overwrites an existing value.
    """
    if frontmatter.get("epistemic_mode"):
        return frontmatter, False
    default = default_epistemic_mode(subtype)
    if default is None:
        return frontmatter, False
    updated = dict(frontmatter)
    updated["epistemic_mode"] = default
    return updated, True


__all__ = [
    "CERTAINTY_LEVELS",
    "CERTAINTY_LEVEL_LABELS",
    "DEFAULT_EPISTEMIC_BY_SUBTYPE",
    "EPISTEMIC_GATED_DOMAINS",
    "EPISTEMIC_MODES",
    "EPISTEMIC_MODE_LABELS",
    "apply_epistemic_default",
    "default_epistemic_mode",
    "is_gated_domain",
    "is_valid_certainty_level",
    "is_valid_epistemic_mode",
]
