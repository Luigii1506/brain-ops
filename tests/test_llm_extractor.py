"""Tests for `llm_extractor` module — Campaña 2.2B Paso 1.

Scope: validación determinística post-LLM + stub del entry point.
NO ejerce LLM real todavía — eso es Paso 2+. Estos tests son puros
sobre funciones deterministas.
"""

from __future__ import annotations

from unittest import TestCase

from pathlib import Path
from tempfile import TemporaryDirectory

from brain_ops.domains.knowledge.llm_extractor import (
    ALLOWED_FLAGS,
    AnthropicLLMClient,
    LLMExtractionResult,
    LLMResponseCache,
    MockLLMClient,
    RawLLMProposal,
    REASON_DUPLICATE_TYPED,
    REASON_EMPTY_FIELD,
    REASON_INVALID_CONFIDENCE,
    REASON_LOW_CONFIDENCE,
    REASON_QUOTE_NOT_IN_BODY,
    REASON_SELF_REFERENCE,
    REASON_UNKNOWN_PREDICATE,
    build_prompt,
    extract_and_validate,
    parse_llm_response,
    prioritize_candidate_targets,
    propose_triples_via_llm,
    validate_raw_proposal,
)
from brain_ops.domains.knowledge.llm_extractor import (
    _MAX_BODY_CHARS_DEEP,
    _MAX_BODY_CHARS_STRICT,
    _BODY_TRUNCATION_MARKER,
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

class PromptBuilderTestCase(TestCase):
    """Paso 2: prompt builder para strict y deep."""

    def test_strict_prompt_includes_all_required_blocks(self) -> None:
        prompt = build_prompt(
            "Tiberio", "Tiberio fue emperador.", "strict",
            subtype="person", domain="historia",
            existing_typed={("ruled", "Imperio Romano")},
            candidate_targets=["Augusto", "Julia la Mayor"],
        )
        # Bloques estructurales
        self.assertIn("REGLAS INVIOLABLES", prompt)
        self.assertIn("MODO: strict", prompt)
        self.assertIn("CATÁLOGO DE PREDICADOS CANÓNICOS", prompt)
        self.assertIn("FLAGS SEMÁNTICOS PERMITIDOS", prompt)
        self.assertIn("ENTIDAD:", prompt)
        self.assertIn("TRIPLES YA TÍPADOS", prompt)
        self.assertIn("TARGETS CANDIDATOS", prompt)
        self.assertIn("BODY:", prompt)
        self.assertIn("INSTRUCCIONES DE SALIDA", prompt)
        # Contenido específico
        self.assertIn("Tiberio", prompt)
        self.assertIn("Tiberio fue emperador.", prompt)
        self.assertIn("ruled -> Imperio Romano", prompt)
        self.assertIn("Augusto", prompt)
        # JSON schema literal debe estar
        self.assertIn('"predicate":', prompt)
        self.assertIn('"evidence_quote":', prompt)

    def test_deep_prompt_has_implicit_inference_rule(self) -> None:
        prompt = build_prompt(
            "Zeus", "Zeus es el dios supremo.", "deep",
            subtype="deity", domain="religion",
        )
        self.assertIn("MODO: deep", prompt)
        self.assertIn("implicit_context_inference", prompt)
        self.assertIn("contextuales", prompt.lower())

    def test_strict_and_deep_share_core_rules(self) -> None:
        """Ambos modos deben tener las mismas reglas inviolables + catálogo."""
        strict_prompt = build_prompt("X", "body", "strict")
        deep_prompt = build_prompt("X", "body", "deep")
        for shared_rule in [
            "Solo propones triples donde la evidencia está LITERALMENTE",
            "hijastro de X",
            "nacido fuera de Italia",
            "hijo adoptivo de X",
            "CATÁLOGO DE PREDICADOS CANÓNICOS",
        ]:
            self.assertIn(shared_rule, strict_prompt)
            self.assertIn(shared_rule, deep_prompt)

    def test_strict_prompt_forbids_hijastro_auto_mapping(self) -> None:
        """D12 del plan: el prompt debe instruir explícitamente que hijastro
        NO se auto-mapea a adopted_by."""
        prompt = build_prompt("X", "body", "strict")
        self.assertIn("hijastro de X", prompt)
        self.assertIn("NO se auto-mapea", prompt)
        self.assertIn("hijastro_step_relation", prompt)

    def test_canonical_predicates_block_contains_key_predicates(self) -> None:
        prompt = build_prompt("X", "body", "strict")
        for pred in ["studied_under", "adopted_by", "succeeded",
                     "founded", "born_in", "reacted_against"]:
            self.assertIn(f"- {pred}:", prompt)

    def test_existing_typed_rendered_correctly(self) -> None:
        prompt = build_prompt(
            "X", "body", "strict",
            existing_typed={("studied_under", "Platón"),
                            ("mentor_of", "Alejandro Magno")},
        )
        self.assertIn("studied_under -> Platón", prompt)
        self.assertIn("mentor_of -> Alejandro Magno", prompt)

    def test_empty_existing_typed_shows_placeholder(self) -> None:
        prompt = build_prompt("X", "body", "strict", existing_typed=set())
        self.assertIn("(ninguno)", prompt)

    def test_candidate_targets_truncated_to_cap(self) -> None:
        many = [f"E{i}" for i in range(200)]
        prompt = build_prompt(
            "X", "body", "strict",
            candidate_targets=many, candidate_cap=50,
        )
        self.assertIn("E0", prompt)
        self.assertIn("E49", prompt)
        self.assertNotIn("E50", prompt)
        self.assertIn("150 más omitidos", prompt)

    def test_cheap_mode_does_not_build_prompt(self) -> None:
        with self.assertRaises(ValueError):
            build_prompt("X", "body", "cheap")


class ResponseParserTestCase(TestCase):
    """Paso 2: parse_llm_response — tolerante a errores, silencioso ante campos
    faltantes (la validación semántica vive en validate_raw_proposal)."""

    def test_valid_json_parses_to_raw_proposals(self) -> None:
        raw = '''{"proposals": [
          {"predicate": "studied_under", "object": "Platón",
           "confidence": "high", "evidence_quote": "alumno de Platón",
           "rationale": "directo", "flags": []}
        ]}'''
        out = parse_llm_response(raw)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].predicate, "studied_under")

    def test_malformed_json_returns_empty(self) -> None:
        self.assertEqual(parse_llm_response("{not valid json"), [])

    def test_missing_proposals_key_returns_empty(self) -> None:
        self.assertEqual(parse_llm_response('{"other_key": []}'), [])

    def test_proposal_with_missing_fields_silently_skipped(self) -> None:
        """Un proposal sin evidence_quote se omite; el resto del array pasa."""
        raw = '''{"proposals": [
          {"predicate": "studied_under", "object": "Platón"},
          {"predicate": "mentor_of", "object": "X", "confidence": "high",
           "evidence_quote": "maestro de X", "rationale": "ok"}
        ]}'''
        out = parse_llm_response(raw)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].predicate, "mentor_of")

    def test_non_list_proposals_returns_empty(self) -> None:
        raw = '{"proposals": "not a list"}'
        self.assertEqual(parse_llm_response(raw), [])


class MockClientTestCase(TestCase):
    def test_mock_returns_canned_response(self) -> None:
        mock = MockLLMClient(canned_response='{"proposals": []}')
        out = mock.extract(prompt="anything", temperature=0.0)
        self.assertEqual(out, '{"proposals": []}')

    def test_mock_records_calls(self) -> None:
        mock = MockLLMClient(canned_response='{"proposals": []}')
        mock.extract(prompt="prompt-a", temperature=0.0)
        mock.extract(prompt="prompt-b", temperature=0.2)
        self.assertEqual(len(mock.calls), 2)
        self.assertEqual(mock.calls[0]["prompt"], "prompt-a")
        self.assertEqual(mock.calls[1]["temperature"], 0.2)


class EndToEndWithMockTestCase(TestCase):
    """Paso 2: end-to-end con MockLLMClient.

    Prompt → mock → parse → validate → LLMExtractionResult. Cuatro casos
    canónicos que cubren los comportamientos clave del pipeline.
    """

    BODY = (
        "Tiberio fue el segundo emperador romano. Hijastro y sucesor "
        "reluctante de [[Augusto]]. Llegó al poder tarde."
    )
    ENTITY_INDEX = {"Augusto": "entity", "Tiberio": "entity"}

    def test_good_case_emits_valid_proposal(self) -> None:
        """Caso bueno: LLM emite proposal con cita literal + predicado
        canónico + confidence high → accepted."""
        canned = '''{"proposals": [
          {"predicate": "succeeded", "object": "Augusto",
           "confidence": "high",
           "evidence_quote": "sucesor reluctante de [[Augusto]]",
           "rationale": "Sucesión imperial directa.",
           "flags": []}
        ]}'''
        result = extract_and_validate(
            "Tiberio", self.BODY, mode="strict",
            client=MockLLMClient(canned_response=canned),
            existing_typed=set(),
            entity_index=self.ENTITY_INDEX,
        )
        self.assertIsInstance(result, LLMExtractionResult)
        self.assertEqual(len(result.accepted), 1)
        self.assertEqual(result.accepted[0].predicate, "succeeded")
        self.assertEqual(result.accepted[0].object, "Augusto")
        self.assertEqual(result.accepted[0].status, "approved")
        self.assertEqual(result.rejections, [])

    def test_invalid_predicate_case_rejected_with_reason(self) -> None:
        """Caso con predicado no-canónico: rejected con razón explícita."""
        canned = '''{"proposals": [
          {"predicate": "was_best_friends_with", "object": "Augusto",
           "confidence": "high",
           "evidence_quote": "sucesor reluctante de [[Augusto]]",
           "rationale": "amistad imperial", "flags": []}
        ]}'''
        result = extract_and_validate(
            "Tiberio", self.BODY, mode="strict",
            client=MockLLMClient(canned_response=canned),
            existing_typed=set(),
            entity_index=self.ENTITY_INDEX,
        )
        self.assertEqual(result.accepted, [])
        self.assertEqual(len(result.rejections), 1)
        self.assertEqual(result.rejections[0]["reason"], REASON_UNKNOWN_PREDICATE)
        self.assertEqual(result.rejections[0]["raw"]["predicate"],
                         "was_best_friends_with")

    def test_fabricated_quote_case_rejected(self) -> None:
        """Anti-alucinación: si el LLM inventa una cita, rejected."""
        canned = '''{"proposals": [
          {"predicate": "succeeded", "object": "Augusto",
           "confidence": "high",
           "evidence_quote": "Tiberio bebió vino con Augusto cada martes",
           "rationale": "fabricated",
           "flags": []}
        ]}'''
        result = extract_and_validate(
            "Tiberio", self.BODY, mode="strict",
            client=MockLLMClient(canned_response=canned),
            existing_typed=set(),
            entity_index=self.ENTITY_INDEX,
        )
        self.assertEqual(result.accepted, [])
        self.assertEqual(len(result.rejections), 1)
        self.assertEqual(result.rejections[0]["reason"], REASON_QUOTE_NOT_IN_BODY)

    def test_hijastro_case_emits_medium_with_flag(self) -> None:
        """D12 del plan: el LLM debe emitir hijastro como medium + flag,
        NUNCA auto-mapearlo a adopted_by high. Aquí simulamos que el LLM
        respetó la instrucción del prompt."""
        canned = '''{"proposals": [
          {"predicate": "adopted_by", "object": "Augusto",
           "confidence": "medium",
           "evidence_quote": "Hijastro y sucesor reluctante de [[Augusto]]",
           "rationale": "Caso hijastro — reviewer debe decidir.",
           "flags": ["hijastro_step_relation"]}
        ]}'''
        result = extract_and_validate(
            "Tiberio", self.BODY, mode="strict",
            client=MockLLMClient(canned_response=canned),
            existing_typed=set(),
            entity_index=self.ENTITY_INDEX,
        )
        self.assertEqual(len(result.accepted), 1)
        p = result.accepted[0]
        # Mapeo automático medium → needs-refinement preserva la decisión
        # para el reviewer humano.
        self.assertEqual(p.confidence, "medium")
        self.assertEqual(p.status, "needs-refinement")
        self.assertIn("hijastro_step_relation", p.note)

    def test_cheap_mode_short_circuits_without_calling_client(self) -> None:
        """Cheap mode no debe llamar al cliente (ahorro de $)."""
        mock = MockLLMClient(canned_response='{"proposals": [...]}')
        result = extract_and_validate(
            "X", "body", mode="cheap", client=mock,
            existing_typed=set(), entity_index={},
        )
        self.assertEqual(result.accepted, [])
        self.assertEqual(len(mock.calls), 0)

    def test_rejections_log_contains_raw_payload(self) -> None:
        """Rejections deben conservar el payload raw para auditoría."""
        canned = '''{"proposals": [
          {"predicate": "xxx", "object": "Y",
           "confidence": "high",
           "evidence_quote": "not in body",
           "rationale": "r", "flags": []}
        ]}'''
        result = extract_and_validate(
            "Tiberio", self.BODY, mode="strict",
            client=MockLLMClient(canned_response=canned),
            existing_typed=set(),
            entity_index=self.ENTITY_INDEX,
        )
        rejection = result.rejections[0]
        self.assertEqual(rejection["raw"]["object"], "Y")
        self.assertEqual(rejection["raw"]["confidence"], "high")


class BodyTruncationTestCase(TestCase):
    """Paso 3 micro-adjustment #1: body se trunca según modo."""

    def test_short_body_untouched_in_strict(self) -> None:
        prompt = build_prompt("X", "body corto", "strict")
        self.assertIn("body corto", prompt)
        self.assertNotIn(_BODY_TRUNCATION_MARKER, prompt)

    def test_long_body_truncated_in_strict(self) -> None:
        long_body = "A" * 20000
        prompt = build_prompt("X", long_body, "strict")
        # El prompt completo incluye el marcador — verificamos que está
        self.assertIn(_BODY_TRUNCATION_MARKER, prompt)
        # Y que el body original (20k chars) no cabe completo — usamos
        # una firma unique al body para aislar conteo de chars accidentales
        # en otros bloques del prompt.
        a_count = prompt.count("A")
        self.assertLessEqual(a_count, _MAX_BODY_CHARS_STRICT + 50)  # margen
                                                                     # pequeño
                                                                     # por "A"
                                                                     # en headers
        self.assertGreater(a_count, _MAX_BODY_CHARS_STRICT - 100)

    def test_deep_cap_is_larger_than_strict(self) -> None:
        """Un body de 20k debería caber entero en deep, no en strict."""
        body = "B" * 20000
        strict = build_prompt("X", body, "strict")
        deep = build_prompt("X", body, "deep")
        self.assertIn(_BODY_TRUNCATION_MARKER, strict)
        self.assertNotIn(_BODY_TRUNCATION_MARKER, deep)

    def test_deep_truncates_only_when_exceeds_deep_cap(self) -> None:
        body = "C" * 30000  # > 25k cap
        deep = build_prompt("X", body, "deep")
        self.assertIn(_BODY_TRUNCATION_MARKER, deep)


class PrioritizeCandidateTargetsTestCase(TestCase):
    """Paso 3 micro-adjustment #2: orden por proximidad contextual."""

    def test_related_before_wikilinks_before_sqlite(self) -> None:
        out = prioritize_candidate_targets(
            note_related=["A", "B"],
            body_wikilinks=["C", "D"],
            sqlite_related=["E", "F"],
        )
        self.assertEqual(out, ["A", "B", "C", "D", "E", "F"])

    def test_dedup_preserves_first_appearance(self) -> None:
        out = prioritize_candidate_targets(
            note_related=["Platón", "Aristóteles"],
            body_wikilinks=["Platón", "Sócrates"],  # Platón dup
            sqlite_related=["Aristóteles", "Kant"],  # Aristóteles dup
        )
        self.assertEqual(out, ["Platón", "Aristóteles", "Sócrates", "Kant"])

    def test_empty_inputs_returns_empty(self) -> None:
        self.assertEqual(prioritize_candidate_targets(), [])

    def test_none_and_empty_strings_ignored(self) -> None:
        out = prioritize_candidate_targets(
            note_related=["A", "", None, "B"],  # type: ignore
        )
        self.assertEqual(out, ["A", "B"])


class LLMResponseCacheTestCase(TestCase):
    """Paso 3: cache file-based keyed por sha256(prompt+model+temp)."""

    def test_put_then_get_returns_same_response(self) -> None:
        with TemporaryDirectory() as td:
            cache = LLMResponseCache(Path(td))
            cache.put("my prompt", "model-x", 0.0, '{"proposals": []}')
            got = cache.get("my prompt", "model-x", 0.0)
            self.assertEqual(got, '{"proposals": []}')

    def test_cache_miss_returns_none(self) -> None:
        with TemporaryDirectory() as td:
            cache = LLMResponseCache(Path(td))
            self.assertIsNone(cache.get("never put", "m", 0.0))

    def test_different_prompt_different_key(self) -> None:
        with TemporaryDirectory() as td:
            cache = LLMResponseCache(Path(td))
            cache.put("prompt A", "m", 0.0, "resp-A")
            cache.put("prompt B", "m", 0.0, "resp-B")
            self.assertEqual(cache.get("prompt A", "m", 0.0), "resp-A")
            self.assertEqual(cache.get("prompt B", "m", 0.0), "resp-B")

    def test_different_temperature_invalidates_cache(self) -> None:
        with TemporaryDirectory() as td:
            cache = LLMResponseCache(Path(td))
            cache.put("prompt", "m", 0.0, "resp-strict")
            self.assertIsNone(cache.get("prompt", "m", 0.2))

    def test_different_model_invalidates_cache(self) -> None:
        with TemporaryDirectory() as td:
            cache = LLMResponseCache(Path(td))
            cache.put("prompt", "haiku", 0.0, "resp-h")
            self.assertIsNone(cache.get("prompt", "sonnet", 0.0))

    def test_persists_across_instances(self) -> None:
        with TemporaryDirectory() as td:
            cache1 = LLMResponseCache(Path(td))
            cache1.put("prompt", "m", 0.0, "resp")
            # Nueva instancia en el mismo directorio
            cache2 = LLMResponseCache(Path(td))
            self.assertEqual(cache2.get("prompt", "m", 0.0), "resp")


class AnthropicLLMClientTestCase(TestCase):
    """Paso 3: cliente real con mock inyectado — NO requiere `anthropic` SDK."""

    class _FakeAnthropicClient:
        """Mock del SDK anthropic con shape compatible."""
        def __init__(self, response_text: str = '{"proposals": []}'):
            self.response_text = response_text
            self.call_count = 0
            self.last_kwargs = None

            class _Messages:
                outer = self
                def create(cls, **kwargs):
                    cls.outer.call_count += 1
                    cls.outer.last_kwargs = kwargs
                    class Block:
                        text = cls.outer.response_text
                    class Resp:
                        content = [Block()]
                    return Resp()
            self.messages = _Messages()

    def test_instantiation_with_injected_client_does_not_require_sdk(self) -> None:
        """No import de anthropic cuando se inyecta _client — testeable
        sin SDK instalado."""
        fake = self._FakeAnthropicClient()
        client = AnthropicLLMClient(model="test", _client=fake)
        self.assertEqual(client.model, "test")

    def test_extract_calls_underlying_messages_create(self) -> None:
        fake = self._FakeAnthropicClient('{"proposals": [{"predicate": "x"}]}')
        client = AnthropicLLMClient(model="test-m", _client=fake)
        out = client.extract(prompt="hello", temperature=0.0)
        self.assertEqual(out, '{"proposals": [{"predicate": "x"}]}')
        self.assertEqual(fake.call_count, 1)
        self.assertEqual(fake.last_kwargs["model"], "test-m")
        self.assertEqual(fake.last_kwargs["temperature"], 0.0)
        self.assertEqual(
            fake.last_kwargs["messages"],
            [{"role": "user", "content": "hello"}],
        )

    def test_cache_hit_skips_underlying_call(self) -> None:
        with TemporaryDirectory() as td:
            cache = LLMResponseCache(Path(td))
            cache.put("cached prompt", "test-m", 0.0, "cached response")
            fake = self._FakeAnthropicClient("fresh")
            client = AnthropicLLMClient(
                model="test-m", _client=fake, cache=cache,
            )
            out = client.extract(prompt="cached prompt", temperature=0.0)
            self.assertEqual(out, "cached response")
            self.assertEqual(fake.call_count, 0)

    def test_cache_miss_calls_api_then_caches(self) -> None:
        with TemporaryDirectory() as td:
            cache = LLMResponseCache(Path(td))
            fake = self._FakeAnthropicClient("fresh response")
            client = AnthropicLLMClient(
                model="test-m", _client=fake, cache=cache,
            )
            out = client.extract(prompt="new prompt", temperature=0.0)
            self.assertEqual(out, "fresh response")
            self.assertEqual(fake.call_count, 1)
            # Segunda llamada debe ir al cache
            out2 = client.extract(prompt="new prompt", temperature=0.0)
            self.assertEqual(out2, "fresh response")
            self.assertEqual(fake.call_count, 1)  # no re-llamada

    def test_retry_on_transient_error_then_success(self) -> None:
        """Error retryable → retry + éxito. Simulamos una RateLimitError
        inicial, luego success."""
        class RateLimitError(Exception):
            pass

        class FlakyAnthropic:
            def __init__(self):
                self.attempts = 0
                class _Messages:
                    outer = self
                    def create(cls, **kwargs):
                        cls.outer.attempts += 1
                        if cls.outer.attempts == 1:
                            raise RateLimitError("too fast")
                        class Block:
                            text = "ok"
                        class Resp:
                            content = [Block()]
                        return Resp()
                self.messages = _Messages()

        flaky = FlakyAnthropic()
        client = AnthropicLLMClient(
            model="test-m", _client=flaky, max_retries=3,
        )
        # Patch time.sleep to avoid real waits in test
        import unittest.mock
        with unittest.mock.patch(
            "brain_ops.domains.knowledge.llm_extractor.time.sleep"
        ):
            out = client.extract(prompt="p", temperature=0.0)
        self.assertEqual(out, "ok")
        self.assertEqual(flaky.attempts, 2)

    def test_no_retry_on_non_retryable_error(self) -> None:
        """Error no-retryable (ej. BadRequestError) debe propagarse en el
        primer intento, sin retries."""
        class BadRequestError(Exception):
            pass

        class BadAnthropic:
            def __init__(self):
                self.attempts = 0
                class _Messages:
                    outer = self
                    def create(cls, **kwargs):
                        cls.outer.attempts += 1
                        raise BadRequestError("malformed")
                self.messages = _Messages()

        bad = BadAnthropic()
        client = AnthropicLLMClient(
            model="test-m", _client=bad, max_retries=3,
        )
        with self.assertRaises(BadRequestError):
            client.extract(prompt="p", temperature=0.0)
        self.assertEqual(bad.attempts, 1)  # single attempt, no retries

    def test_max_retries_exhausted_reraises(self) -> None:
        """Si los retries se agotan, la última excepción retryable se
        propaga."""
        class RateLimitError(Exception):
            pass

        class AlwaysFails:
            def __init__(self):
                self.attempts = 0
                class _Messages:
                    outer = self
                    def create(cls, **kwargs):
                        cls.outer.attempts += 1
                        raise RateLimitError("keeps failing")
                self.messages = _Messages()

        flaky = AlwaysFails()
        client = AnthropicLLMClient(
            model="test-m", _client=flaky, max_retries=2,
        )
        import unittest.mock
        with unittest.mock.patch(
            "brain_ops.domains.knowledge.llm_extractor.time.sleep"
        ):
            with self.assertRaises(RateLimitError):
                client.extract(prompt="p", temperature=0.0)
        # initial + 2 retries = 3 attempts total
        self.assertEqual(flaky.attempts, 3)


class ClosedSetInvariantsTestCase(TestCase):
    def test_hijastro_flag_present_in_allowed_set(self) -> None:
        """D12 adjustment: `hijastro_step_relation` debe existir como flag válido."""
        self.assertIn("hijastro_step_relation", ALLOWED_FLAGS)

    def test_core_semantic_flags_present(self) -> None:
        """Los 3 flags que capturan los tipos de FPs semánticos de 2.2A."""
        self.assertIn("negation_handled", ALLOWED_FLAGS)
        self.assertIn("adoption_distinct_from_biological", ALLOWED_FLAGS)
        self.assertIn("reverse_preposition_handled", ALLOWED_FLAGS)
