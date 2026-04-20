"""Tests for `llm_extractor` module — Campaña 2.2B Paso 1.

Scope: validación determinística post-LLM + stub del entry point.
NO ejerce LLM real todavía — eso es Paso 2+. Estos tests son puros
sobre funciones deterministas.
"""

from __future__ import annotations

from unittest import TestCase

from brain_ops.domains.knowledge.llm_extractor import (
    ALLOWED_FLAGS,
    RawLLMProposal,
    REASON_DUPLICATE_TYPED,
    REASON_EMPTY_FIELD,
    REASON_INVALID_CONFIDENCE,
    REASON_LOW_CONFIDENCE,
    REASON_QUOTE_NOT_IN_BODY,
    REASON_SELF_REFERENCE,
    REASON_UNKNOWN_PREDICATE,
    propose_triples_via_llm,
    validate_raw_proposal,
)


def _raw(**overrides) -> RawLLMProposal:
    """Factory con valores por default válidos, sobre-escribibles por test."""
    defaults = {
        "predicate": "studied_under",
        "object": "Platón",
        "confidence": "high",
        "evidence_quote": "Aristóteles fue alumno de Platón",
        "rationale": "Discípulo directo en la Academia por 20 años",
        "flags": (),
    }
    defaults.update(overrides)
    return RawLLMProposal(**defaults)


def _validate(
    raw: RawLLMProposal,
    *,
    entity_name: str = "Aristóteles",
    body: str | None = None,
    existing_typed: set = None,
    entity_index: dict = None,
    proposal_id: str = "llm-01",
):
    """Helper que pasa por defecto contexts no-bloqueantes."""
    if body is None:
        body = "Aristóteles fue alumno de Platón en la Academia."
    if existing_typed is None:
        existing_typed = set()
    if entity_index is None:
        entity_index = {"Platón": "entity", "Aristóteles": "entity"}
    return validate_raw_proposal(
        raw,
        entity_name=entity_name,
        body=body,
        existing_typed=existing_typed,
        entity_index=entity_index,
        proposal_id=proposal_id,
    )


# ---------------------------------------------------------------------------
# Check A — empty field sanity
# ---------------------------------------------------------------------------

class EmptyFieldCheckTestCase(TestCase):
    def test_empty_predicate_rejected(self) -> None:
        proposal, reason = _validate(_raw(predicate=""))
        self.assertIsNone(proposal)
        self.assertEqual(reason, REASON_EMPTY_FIELD)

    def test_empty_object_rejected(self) -> None:
        proposal, reason = _validate(_raw(object=""))
        self.assertIsNone(proposal)
        self.assertEqual(reason, REASON_EMPTY_FIELD)

    def test_empty_evidence_quote_rejected(self) -> None:
        proposal, reason = _validate(_raw(evidence_quote=""))
        self.assertIsNone(proposal)
        self.assertEqual(reason, REASON_EMPTY_FIELD)


# ---------------------------------------------------------------------------
# Check 1 — predicate must be canonical
# ---------------------------------------------------------------------------

class CanonicalPredicateCheckTestCase(TestCase):
    def test_non_canonical_predicate_rejected(self) -> None:
        proposal, reason = _validate(_raw(predicate="makes_burritos_with"))
        self.assertIsNone(proposal)
        self.assertEqual(reason, REASON_UNKNOWN_PREDICATE)

    def test_canonical_predicate_accepted(self) -> None:
        proposal, reason = _validate(_raw())  # studied_under is canonical
        self.assertIsNotNone(proposal)
        self.assertIsNone(reason)


# ---------------------------------------------------------------------------
# Check 2 — no self-reference
# ---------------------------------------------------------------------------

class SelfReferenceCheckTestCase(TestCase):
    def test_object_equal_to_entity_rejected(self) -> None:
        proposal, reason = _validate(
            _raw(object="Aristóteles"), entity_name="Aristóteles",
        )
        self.assertIsNone(proposal)
        self.assertEqual(reason, REASON_SELF_REFERENCE)


# ---------------------------------------------------------------------------
# Check 3 — confidence must be in enum
# ---------------------------------------------------------------------------

class ConfidenceCheckTestCase(TestCase):
    def test_invalid_confidence_rejected(self) -> None:
        proposal, reason = _validate(_raw(confidence="very-sure"))
        self.assertIsNone(proposal)
        self.assertEqual(reason, REASON_INVALID_CONFIDENCE)


# ---------------------------------------------------------------------------
# Check 4 — low confidence is filtered pre-reviewer
# ---------------------------------------------------------------------------

class LowConfidenceFilterTestCase(TestCase):
    def test_low_confidence_rejected(self) -> None:
        proposal, reason = _validate(_raw(confidence="low"))
        self.assertIsNone(proposal)
        self.assertEqual(reason, REASON_LOW_CONFIDENCE)

    def test_medium_maps_to_needs_refinement(self) -> None:
        proposal, reason = _validate(_raw(confidence="medium"))
        self.assertIsNotNone(proposal)
        self.assertIsNone(reason)
        self.assertEqual(proposal.confidence, "medium")
        self.assertEqual(proposal.status, "needs-refinement")

    def test_high_maps_to_approved(self) -> None:
        proposal, reason = _validate(_raw(confidence="high"))
        self.assertIsNotNone(proposal)
        self.assertEqual(proposal.status, "approved")


# ---------------------------------------------------------------------------
# Check 5 — THE anti-hallucination check: quote must be substring of body
# ---------------------------------------------------------------------------

class QuoteInBodyCheckTestCase(TestCase):
    def test_fabricated_quote_rejected(self) -> None:
        """Si el LLM inventa una cita que no está en el body, se rechaza."""
        body = "Aristóteles fue alumno de Platón en la Academia."
        fabricated = "Aristóteles y Platón compartían desayunos frecuentemente"
        proposal, reason = _validate(
            _raw(evidence_quote=fabricated), body=body,
        )
        self.assertIsNone(proposal)
        self.assertEqual(reason, REASON_QUOTE_NOT_IN_BODY)

    def test_quote_case_insensitive_match_accepted(self) -> None:
        """Caller no tiene que normalizar case — la validación es case-insensitive."""
        body = "Aristóteles fue alumno de Platón en la Academia."
        proposal, reason = _validate(
            _raw(evidence_quote="ARISTÓTELES FUE ALUMNO DE PLATÓN"),
            body=body,
        )
        self.assertIsNotNone(proposal)
        self.assertIsNone(reason)


# ---------------------------------------------------------------------------
# Check 6 — dedup against already-typed
# ---------------------------------------------------------------------------

class DedupCheckTestCase(TestCase):
    def test_already_typed_rejected(self) -> None:
        proposal, reason = _validate(
            _raw(predicate="studied_under", object="Platón"),
            existing_typed={("studied_under", "Platón")},
        )
        self.assertIsNone(proposal)
        self.assertEqual(reason, REASON_DUPLICATE_TYPED)

    def test_different_predicate_same_object_accepted(self) -> None:
        """Dedup key es `(predicate, object)`: multi-predicado al mismo target OK."""
        proposal, reason = _validate(
            _raw(predicate="reacted_against", object="Platón"),
            existing_typed={("studied_under", "Platón")},
            body="Aristóteles criticó a Platón sobre las Formas",
        )
        # The quote matches? Let me adjust the evidence quote and body to be consistent
        # Reject expected because evidence_quote contains "alumno de Platón", not this body
        # Actually the _raw default evidence_quote is "Aristóteles fue alumno de Platón"
        # which isn't in this body. Fix:
        proposal, reason = _validate(
            _raw(predicate="reacted_against", object="Platón",
                 evidence_quote="Aristóteles criticó a Platón"),
            existing_typed={("studied_under", "Platón")},
            body="Aristóteles criticó a Platón sobre las Formas",
        )
        self.assertIsNotNone(proposal)
        self.assertIsNone(reason)


# ---------------------------------------------------------------------------
# Check 7 — object_status resolution (labels, never rejects)
# ---------------------------------------------------------------------------

class ObjectStatusResolutionTestCase(TestCase):
    def test_canonical_entity_resolved(self) -> None:
        proposal, _ = _validate(
            _raw(),
            entity_index={"Platón": "entity", "Aristóteles": "entity"},
        )
        self.assertEqual(proposal.object_status, "canonical_entity_exists")

    def test_missing_entity_labeled_not_rejected(self) -> None:
        proposal, reason = _validate(
            _raw(object="Liceo",
                 evidence_quote="fundó el Liceo",
                 predicate="founded"),
            body="Aristóteles fundó el Liceo en 335 a.C.",
            entity_index={"Aristóteles": "entity"},  # Liceo missing
        )
        self.assertIsNotNone(proposal)
        self.assertIsNone(reason)
        self.assertEqual(proposal.object_status, "MISSING_ENTITY")

    def test_disambiguation_page_labeled_not_rejected(self) -> None:
        proposal, reason = _validate(
            _raw(object="Tebas",
                 evidence_quote="conquistó Tebas",
                 predicate="conquered"),
            entity_name="Alejandro Magno",
            body="Alejandro conquistó Tebas en 335 a.C.",
            entity_index={"Tebas": "disambiguation_page", "Alejandro Magno": "entity"},
        )
        self.assertIsNotNone(proposal)
        self.assertIsNone(reason)
        self.assertEqual(proposal.object_status, "DISAMBIGUATION_PAGE")


# ---------------------------------------------------------------------------
# Evidence / note construction
# ---------------------------------------------------------------------------

class EvidenceAndNoteTestCase(TestCase):
    def test_evidence_source_is_llm_only(self) -> None:
        proposal, _ = _validate(_raw())
        self.assertEqual(proposal.evidence_source, ["llm"])

    def test_single_excerpt_location_is_body_llm(self) -> None:
        proposal, _ = _validate(_raw())
        self.assertEqual(len(proposal.evidence_excerpts), 1)
        self.assertEqual(proposal.evidence_excerpts[0].location, "body.llm")

    def test_flags_appended_to_note_when_present(self) -> None:
        proposal, _ = _validate(
            _raw(flags=("negation_handled", "ambiguous_subject")),
        )
        self.assertIn("negation_handled", proposal.note)
        self.assertIn("ambiguous_subject", proposal.note)

    def test_unknown_flags_silently_stripped(self) -> None:
        proposal, _ = _validate(
            _raw(flags=("adoption_distinct_from_biological", "spurious_flag_xyz")),
        )
        self.assertIn("adoption_distinct_from_biological", proposal.note)
        self.assertNotIn("spurious_flag_xyz", proposal.note)


# ---------------------------------------------------------------------------
# Stub — propose_triples_via_llm returns [] until Paso 3 wires the client
# ---------------------------------------------------------------------------

class StubEntryPointTestCase(TestCase):
    def test_cheap_mode_returns_empty(self) -> None:
        out = propose_triples_via_llm(
            "Aristóteles", "body text", mode="cheap",
            existing_typed=set(), entity_index={},
        )
        self.assertEqual(out, [])

    def test_strict_mode_stub_returns_empty(self) -> None:
        """Paso 1 stub: strict mode returns [] hasta Paso 3."""
        out = propose_triples_via_llm(
            "Aristóteles", "body text", mode="strict",
            existing_typed=set(), entity_index={},
        )
        self.assertEqual(out, [])

    def test_deep_mode_stub_returns_empty(self) -> None:
        out = propose_triples_via_llm(
            "Aristóteles", "body text", mode="deep",
            existing_typed=set(), entity_index={},
        )
        self.assertEqual(out, [])

    def test_unknown_mode_raises(self) -> None:
        with self.assertRaises(ValueError):
            propose_triples_via_llm(
                "Aristóteles", "body", mode="banana",  # type: ignore
                existing_typed=set(), entity_index={},
            )


# ---------------------------------------------------------------------------
# Closed-set invariants
# ---------------------------------------------------------------------------

class ClosedSetInvariantsTestCase(TestCase):
    def test_hijastro_flag_present_in_allowed_set(self) -> None:
        """D12 adjustment: `hijastro_step_relation` debe existir como flag válido."""
        self.assertIn("hijastro_step_relation", ALLOWED_FLAGS)

    def test_core_semantic_flags_present(self) -> None:
        """Los 3 flags que capturan los tipos de FPs semánticos de 2.2A."""
        self.assertIn("negation_handled", ALLOWED_FLAGS)
        self.assertIn("adoption_distinct_from_biological", ALLOWED_FLAGS)
        self.assertIn("reverse_preposition_handled", ALLOWED_FLAGS)
