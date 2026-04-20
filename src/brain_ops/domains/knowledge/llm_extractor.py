"""LLM-assisted extractor — Campaña 2.2B Paso 1.

Schema + deterministic post-validation + stub entry point. This module is
intentionally isolated from any real LLM client in Paso 1:

- `RawLLMProposal`: dataclass mirroring the JSON contract the LLM must emit.
- `validate_raw_proposal(...)`: pure function implementing the 7-check
  validation pipeline decided in the 2.2B plan (§8). Returns either a
  `ProposedRelation` ready to enter the proposal YAML, or `None` plus a
  rejection reason string.
- `propose_triples_via_llm(...)`: entry point used by
  `propose_relations_for_entity`. Paso 1 returns an empty list unconditionally;
  Paso 3 will wire the prompt-builder, client, response parsing, and per-
  proposal validation into this function.

Design invariants honored here (see plan §8):

1. Evidence-quote literal substring check is the primary anti-hallucination
   defense. Anything the LLM writes as `evidence_quote` that is not a
   substring of the body is rejected silently.
2. Only canonical predicates survive validation — no ad-hoc predicates.
3. `confidence: low` never reaches the reviewer (too noisy).
4. Self-references are dropped.
5. Deduplication against already-typed `(predicate, object)` pairs.
6. `object_status` is resolved deterministically against the vault's entity
   index — same classes as 2.1: `canonical_entity_exists`,
   `DISAMBIGUATION_PAGE`, `MISSING_ENTITY`.

The hijastro-de case (Campaña 2.2B D12 adjustment): NOT handled here. It is
a prompt-level concern addressed in Paso 2: the prompt instructs the LLM to
emit such cases with `confidence: medium` and flag `hijastro_step_relation`,
which maps naturally to `status: needs-refinement` and lands on the reviewer
without forcing a `adopted_by` or `child_of` decision at extraction time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from brain_ops.domains.knowledge.object_model import CANONICAL_PREDICATES
from brain_ops.domains.knowledge.relations_proposer import (
    EvidenceExcerpt,
    ObjectStatus,
    ProposedRelation,
)

# ---------------------------------------------------------------------------
# Mode enum (cheap / strict / deep)
# ---------------------------------------------------------------------------

LLMMode = Literal["cheap", "strict", "deep"]
LLM_MODES: tuple[LLMMode, ...] = ("cheap", "strict", "deep")


# ---------------------------------------------------------------------------
# Rejection reasons (log keys — stable across runs for analytics)
# ---------------------------------------------------------------------------

REASON_UNKNOWN_PREDICATE = "unknown_predicate"
REASON_SELF_REFERENCE = "self_reference"
REASON_INVALID_CONFIDENCE = "invalid_confidence"
REASON_LOW_CONFIDENCE = "low_confidence"
REASON_QUOTE_NOT_IN_BODY = "quote_not_in_body"
REASON_DUPLICATE_TYPED = "duplicate_typed"
REASON_EMPTY_FIELD = "empty_field"


# ---------------------------------------------------------------------------
# Closed set of semantic flags the LLM may emit
# ---------------------------------------------------------------------------
#
# The prompt (Paso 2) will include this list verbatim so the LLM picks from a
# fixed vocabulary. Any flag not in this set is silently stripped at
# validation time — it does not cause rejection, just sanitization.

ALLOWED_FLAGS: frozenset[str] = frozenset({
    "negation_handled",
    "adoption_distinct_from_biological",
    "reverse_preposition_handled",
    "multi_candidate_predicate",
    "ambiguous_subject",
    "conflicting_traditions",
    "hijastro_step_relation",          # Campaña 2.2B D12 — keep as
                                        # needs-refinement, never auto-map.
    "implicit_context_inference",      # deep mode only
})


# ---------------------------------------------------------------------------
# Raw proposal from LLM (mirror of the JSON schema in the prompt)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RawLLMProposal:
    """Pre-validation proposal as parsed from the LLM JSON response."""
    predicate: str
    object: str
    confidence: str  # expected in {high, medium, low}
    evidence_quote: str
    rationale: str
    flags: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Validation — the anti-hallucination pipeline
# ---------------------------------------------------------------------------


def _resolve_object_status(obj: str, entity_index: dict[str, str]) -> ObjectStatus:
    """Translate vault entity index into the `ObjectStatus` enum.

    entity_index maps canonical name → object_kind (`entity`,
    `disambiguation_page`). Absence from the map means MISSING_ENTITY.
    """
    kind = entity_index.get(obj)
    if kind == "entity":
        return "canonical_entity_exists"
    if kind == "disambiguation_page":
        return "DISAMBIGUATION_PAGE"
    return "MISSING_ENTITY"


def _sanitize_flags(flags: tuple[str, ...]) -> list[str]:
    """Drop unknown flags silently. Preserve order of the survivors."""
    return [f for f in flags if f in ALLOWED_FLAGS]


def validate_raw_proposal(
    raw: RawLLMProposal,
    *,
    entity_name: str,
    body: str,
    existing_typed: set[tuple[str, str]],
    entity_index: dict[str, str],
    proposal_id: str,
) -> tuple[ProposedRelation | None, str | None]:
    """Apply the 7-check validation pipeline to a raw LLM proposal.

    Returns `(proposal, None)` on success and `(None, reason_code)` on
    rejection. The reason code is one of the `REASON_*` constants so the
    caller can aggregate rejections into a structured log.

    Order of checks is the one decided in the plan §8 — cheap rejects first,
    expensive last. Quote-literal-in-body is the canonical anti-hallucination
    check: if the LLM invents prose that is not actually in the body, this
    filter catches it.
    """
    # Check A: basic field sanity.
    if not raw.predicate or not raw.object or not raw.evidence_quote:
        return None, REASON_EMPTY_FIELD

    # Check 1: predicate must be canonical.
    if raw.predicate not in CANONICAL_PREDICATES:
        return None, REASON_UNKNOWN_PREDICATE

    # Check 2: no self-reference.
    if raw.object == entity_name:
        return None, REASON_SELF_REFERENCE

    # Check 3: confidence from closed set.
    if raw.confidence not in ("high", "medium", "low"):
        return None, REASON_INVALID_CONFIDENCE

    # Check 4: low confidence filtered pre-reviewer.
    if raw.confidence == "low":
        return None, REASON_LOW_CONFIDENCE

    # Check 5: anti-hallucination — quote must literally appear in the body.
    # Case-insensitive comparison so the LLM doesn't need to match case.
    if raw.evidence_quote.lower() not in body.lower():
        return None, REASON_QUOTE_NOT_IN_BODY

    # Check 6: dedup against already-typed triples.
    if (raw.predicate, raw.object) in existing_typed:
        return None, REASON_DUPLICATE_TYPED

    # Check 7: resolve object_status. Never rejects — always labels.
    object_status = _resolve_object_status(raw.object, entity_index)

    # Map confidence → status. Medium requires reviewer approval;
    # high defaults to approved (reviewer can still override).
    status = "approved" if raw.confidence == "high" else "needs-refinement"

    flags_clean = _sanitize_flags(raw.flags)
    note = raw.rationale
    if flags_clean:
        note = f"{raw.rationale} [flags: {', '.join(flags_clean)}]"

    return ProposedRelation(
        id=proposal_id,
        predicate=raw.predicate,
        object=raw.object,
        confidence=raw.confidence,
        status=status,
        evidence_source=["llm"],
        evidence_excerpts=[EvidenceExcerpt(
            location="body.llm",
            text=raw.evidence_quote,
        )],
        object_status=object_status,
        note=note,
    ), None


# ---------------------------------------------------------------------------
# Entry point — Paso 1 stub
# ---------------------------------------------------------------------------


def propose_triples_via_llm(
    entity_name: str,
    body: str,
    *,
    mode: LLMMode,
    existing_typed: set[tuple[str, str]],
    entity_index: dict[str, str],
    llm_client: object | None = None,
) -> list[ProposedRelation]:
    """Entry point used by `propose_relations_for_entity`.

    Paso 1: returns `[]` unconditionally. The real path — build prompt, call
    LLM, parse JSON, validate each proposal, emit — lands in Paso 3.

    Paso 2 will write the prompt builder in isolation. Paso 3 will wire the
    client + cache + retry + logging + per-proposal validation into this
    function.

    Contract honored already in Paso 1: `cheap` mode is a no-op short-circuit;
    `strict` and `deep` return `[]` until wired. The caller
    (`propose_relations_for_entity`) must continue to function with an empty
    list from this call — it is meant to be additive to the pattern
    extractor, not a replacement.
    """
    if mode == "cheap":
        # No LLM call at all. Reserved mode for batches where the pattern
        # extractor is known sufficient (e.g. F1-consolidation re-runs, CI
        # tests). Returning early avoids instantiating the client.
        return []

    if mode not in ("strict", "deep"):
        raise ValueError(f"Unknown LLM mode: {mode!r}")

    # Paso 3 TODO:
    #   prompt = build_prompt(entity_name, body, mode, existing_typed,
    #                          entity_index, candidate_targets)
    #   response = llm_client.extract(prompt)
    #   raw_proposals = parse_llm_response(response)
    #   validated = []
    #   for i, raw in enumerate(raw_proposals):
    #       proposal, reason = validate_raw_proposal(
    #           raw, entity_name=entity_name, body=body,
    #           existing_typed=existing_typed, entity_index=entity_index,
    #           proposal_id=f"llm-{i+1:02d}",
    #       )
    #       if proposal is not None:
    #           validated.append(proposal)
    #       else:
    #           log_rejection(...)
    #   return validated
    return []


__all__ = [
    "ALLOWED_FLAGS",
    "LLM_MODES",
    "LLMMode",
    "RawLLMProposal",
    "REASON_DUPLICATE_TYPED",
    "REASON_EMPTY_FIELD",
    "REASON_INVALID_CONFIDENCE",
    "REASON_LOW_CONFIDENCE",
    "REASON_QUOTE_NOT_IN_BODY",
    "REASON_SELF_REFERENCE",
    "REASON_UNKNOWN_PREDICATE",
    "propose_triples_via_llm",
    "validate_raw_proposal",
]
