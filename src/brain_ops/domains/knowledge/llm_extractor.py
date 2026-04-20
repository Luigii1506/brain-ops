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

import json
from dataclasses import dataclass, field
from typing import Iterable, Literal, Protocol

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


# ---------------------------------------------------------------------------
# Prompt templates — Campaña 2.2B Paso 2
# ---------------------------------------------------------------------------
#
# Two modes share 95% of the prompt. The `_strict` template is the default
# operational mode: LLM only proposes triples where the evidence_quote is
# LITERALLY in the body. The `_deep` template adds a single extra rule
# permitting implicit-context inferences with confidence=medium and flag
# `implicit_context_inference`. Use deep only on notes explicitly blocked
# (Zeus, Einstein post-cluster) where strict returned 0.
#
# Placeholders use Python `.format()` substitution. JSON literal braces are
# doubled `{{ ... }}` for escape. Keep this file single-source until the
# vocabulary stabilizes; move to versioned files once we commit to a v2.

PROMPT_VERSION = "v1.0"

_SHARED_HEADER = """\
Eres un extractor de relaciones tipadas para un knowledge graph personal.
Lees prosa biográfica/histórica/científica en español e inglés y propones
triples (source, predicate, object) conformes al catálogo canónico.

REGLAS INVIOLABLES:
- Solo propones triples donde la evidencia está LITERALMENTE en el body.
- NUNCA inventas hechos que no aparecen explícitamente en el texto dado.
- Respetas negaciones: si el body dice "X no aparece en Y", NO emites triple.
- Distingues adopción de biología: "hijo adoptivo de X" -> `adopted_by`,
  NUNCA `child_of`.
- Distingues dirección: "nacido fuera de Italia" NO implica ruled -> Italia.
- "hijastro de X" NO se auto-mapea: emite con confidence=medium y flag
  `hijastro_step_relation`; el reviewer humano decide entre adopted_by,
  child_of, o rechazar.
- Si dudas entre 2 predicados canónicos, emites con confidence=medium y
  flag `multi_candidate_predicate`.
- Si ningún predicado canónico encaja con precisión, NO emites proposal.
- Si el body presenta versiones contradictorias de una relación, NO emites
  proposal para ese par; puedes emitir una proposal medium con flag
  `conflicting_traditions` como señal para el reviewer.
"""

_STRICT_ADDITIONAL = """\
MODO: strict
- No incluyas inferencias contextuales. Solo relaciones con cita textual
  inequívoca en el body.
- Confidence `high` solo si la relación está afirmada sin ambigüedad.
- Confidence `medium` si el predicado tiene múltiples candidatos o si la
  cita requiere interpretación mínima.
- Confidence `low` NO debe emitirse.
"""

_DEEP_ADDITIONAL = """\
MODO: deep (exploratorio)
- Puedes inferir relaciones contextuales cuando el body las sugiere sin
  afirmarlas textualmente, PERO siempre con confidence=medium y flag
  `implicit_context_inference`.
- Confidence `high` sigue requiriendo cita textual directa.
- Aún así, `evidence_quote` debe ser substring LITERAL del body (puede ser
  una oración breve adyacente al contexto inferido).
- Confidence `low` NO debe emitirse.
"""

_SHARED_FOOTER = """\
CATÁLOGO DE PREDICADOS CANÓNICOS (usa EXACTAMENTE estos nombres):
{canonical_predicates}

FLAGS SEMÁNTICOS PERMITIDOS (lista cerrada):
{allowed_flags}

ENTIDAD:
- name: {entity_name}
- subtype: {subtype}
- domain: {domain}

TRIPLES YA TÍPADOS (NO PROPONGAS ESTOS):
{existing_typed}

TARGETS CANDIDATOS (entidades canónicas del vault; preferir estos como
object cuando encajen; otros targets generan MISSING_ENTITY downstream):
{candidate_targets}

BODY:
---
{body}
---

INSTRUCCIONES DE SALIDA:
Devuelve EXCLUSIVAMENTE un JSON válido (sin markdown fences, sin texto
adicional) con este schema:
{{
  "proposals": [
    {{
      "predicate": "<uno del catálogo>",
      "object": "<nombre canónico>",
      "confidence": "high" | "medium",
      "evidence_quote": "<substring LITERAL del body>",
      "rationale": "<1 línea explicando por qué ese predicado>",
      "flags": ["<opcional, de la lista cerrada>"]
    }}
  ]
}}

Si no hay relaciones extraíbles, devuelve {{"proposals": []}}.
"""


def _format_canonical_predicates_block() -> str:
    """Emite el catálogo canónico en formato tabular compacto."""
    lines = []
    for pred, desc in sorted(CANONICAL_PREDICATES.items()):
        lines.append(f"- {pred}: {desc}")
    return "\n".join(lines)


def _format_allowed_flags_block() -> str:
    return "\n".join(f"- {f}" for f in sorted(ALLOWED_FLAGS))


def _format_existing_typed_block(existing_typed: Iterable[tuple[str, str]]) -> str:
    items = sorted(existing_typed)
    if not items:
        return "(ninguno)"
    return "\n".join(f"- {pred} -> {obj}" for pred, obj in items)


def _format_candidate_targets_block(targets: Iterable[str], cap: int) -> str:
    deduped = list(dict.fromkeys(targets))  # preserve order, drop duplicates
    truncated = deduped[:cap]
    if not truncated:
        return "(ninguno curado para esta entidad)"
    lines = [f"- {t}" for t in truncated]
    if len(deduped) > cap:
        lines.append(f"... ({len(deduped) - cap} más omitidos por cap={cap})")
    return "\n".join(lines)


def _format_domain(domain: str | list[str] | None) -> str:
    if domain is None:
        return "(sin domain)"
    if isinstance(domain, list):
        return ", ".join(domain)
    return str(domain)


def build_prompt(
    entity_name: str,
    body: str,
    mode: LLMMode,
    *,
    subtype: str | None = None,
    domain: str | list[str] | None = None,
    existing_typed: Iterable[tuple[str, str]] = (),
    candidate_targets: Iterable[str] = (),
    candidate_cap: int = 150,
) -> str:
    """Construye el prompt completo para el LLM según `mode`.

    Devuelve un único string que puede enviarse como user message. El
    prompt está estructurado en bloques claramente separados para que
    tanto humanos como el LLM los lean con facilidad.

    - `strict` y `deep` comparten header + catalog + footer completos.
    - La única diferencia entre modos es el bloque de reglas específicas
      del modo (_STRICT_ADDITIONAL vs _DEEP_ADDITIONAL).
    """
    if mode == "cheap":
        raise ValueError("cheap mode should not build a prompt (no LLM call)")
    if mode == "strict":
        mode_block = _STRICT_ADDITIONAL
    elif mode == "deep":
        mode_block = _DEEP_ADDITIONAL
    else:
        raise ValueError(f"Unknown LLM mode: {mode!r}")

    full_template = _SHARED_HEADER + "\n" + mode_block + "\n" + _SHARED_FOOTER

    return full_template.format(
        canonical_predicates=_format_canonical_predicates_block(),
        allowed_flags=_format_allowed_flags_block(),
        entity_name=entity_name,
        subtype=subtype or "(sin subtype)",
        domain=_format_domain(domain),
        existing_typed=_format_existing_typed_block(existing_typed),
        candidate_targets=_format_candidate_targets_block(
            candidate_targets, candidate_cap,
        ),
        body=body,
    )


# ---------------------------------------------------------------------------
# LLM client abstraction + mock (testing only)
# ---------------------------------------------------------------------------


class LLMClient(Protocol):
    """Protocolo mínimo para clientes LLM compatibles con 2.2B.

    Paso 3 implementará un cliente real sobre Anthropic Messages API. Por
    ahora, `MockLLMClient` satisface este Protocolo para tests sin red.
    """

    def extract(self, *, prompt: str, temperature: float) -> str:
        """Envía el prompt al LLM, devuelve la respuesta raw (JSON esperado)."""
        ...


@dataclass
class MockLLMClient:
    """Cliente de testing. Devuelve una respuesta canned y guarda el prompt
    para inspección por los tests."""
    canned_response: str = '{"proposals": []}'
    calls: list[dict] = field(default_factory=list)

    def extract(self, *, prompt: str, temperature: float) -> str:
        self.calls.append({"prompt": prompt, "temperature": temperature})
        return self.canned_response


# ---------------------------------------------------------------------------
# LLM response parser
# ---------------------------------------------------------------------------


def parse_llm_response(raw_text: str) -> list[RawLLMProposal]:
    """Parsea la respuesta raw del LLM a una lista de `RawLLMProposal`.

    Tolerante a:
    - JSON malformado (devuelve []).
    - Falta la clave `proposals` (devuelve []).
    - Proposals con campos faltantes (se omiten silenciosamente — el
      validator posterior aplica los checks más estrictos).

    NO aplica validación semántica. Solo extrae lo que parece estructura
    mínima. La validación real (canonical predicate, quote literal, etc.)
    vive en `validate_raw_proposal`.
    """
    try:
        payload = json.loads(raw_text)
    except (json.JSONDecodeError, TypeError):
        return []

    if not isinstance(payload, dict):
        return []

    proposals = payload.get("proposals")
    if not isinstance(proposals, list):
        return []

    out: list[RawLLMProposal] = []
    for item in proposals:
        if not isinstance(item, dict):
            continue
        # Campos mínimos para construir RawLLMProposal
        predicate = item.get("predicate")
        obj = item.get("object")
        confidence = item.get("confidence")
        evidence_quote = item.get("evidence_quote")
        if not all(isinstance(x, str) for x in (predicate, obj, confidence, evidence_quote)):
            continue
        rationale = item.get("rationale", "")
        if not isinstance(rationale, str):
            rationale = ""
        flags_raw = item.get("flags", [])
        if isinstance(flags_raw, list):
            flags = tuple(f for f in flags_raw if isinstance(f, str))
        else:
            flags = ()
        out.append(RawLLMProposal(
            predicate=predicate,
            object=obj,
            confidence=confidence,
            evidence_quote=evidence_quote,
            rationale=rationale,
            flags=flags,
        ))
    return out


# ---------------------------------------------------------------------------
# End-to-end: prompt -> client -> parse -> validate
# ---------------------------------------------------------------------------


@dataclass
class LLMExtractionResult:
    """Resultado completo de una extracción LLM-assisted para una entidad."""
    accepted: list[ProposedRelation]
    rejections: list[dict]
    prompt: str
    raw_response: str
    mode: LLMMode


def extract_and_validate(
    entity_name: str,
    body: str,
    *,
    mode: LLMMode,
    client: LLMClient,
    existing_typed: set[tuple[str, str]],
    entity_index: dict[str, str],
    subtype: str | None = None,
    domain: str | list[str] | None = None,
    candidate_targets: Iterable[str] = (),
    candidate_cap: int = 150,
    temperature: float | None = None,
) -> LLMExtractionResult:
    """End-to-end: construye prompt, llama al cliente, parsea, valida.

    `temperature` default per mode: strict=0.0, deep=0.2 (per plan D3).
    Cheap mode short-circuits con resultado vacío (no llamada).
    """
    if mode == "cheap":
        return LLMExtractionResult(
            accepted=[], rejections=[], prompt="", raw_response="", mode="cheap",
        )

    if temperature is None:
        temperature = 0.0 if mode == "strict" else 0.2

    prompt = build_prompt(
        entity_name, body, mode,
        subtype=subtype, domain=domain,
        existing_typed=existing_typed,
        candidate_targets=candidate_targets,
        candidate_cap=candidate_cap,
    )
    raw_response = client.extract(prompt=prompt, temperature=temperature)
    raw_proposals = parse_llm_response(raw_response)

    accepted: list[ProposedRelation] = []
    rejections: list[dict] = []
    for i, raw in enumerate(raw_proposals, start=1):
        proposal, reason = validate_raw_proposal(
            raw,
            entity_name=entity_name,
            body=body,
            existing_typed=existing_typed,
            entity_index=entity_index,
            proposal_id=f"llm-{i:02d}",
        )
        if proposal is not None:
            accepted.append(proposal)
        else:
            rejections.append({
                "reason": reason,
                "raw": {
                    "predicate": raw.predicate,
                    "object": raw.object,
                    "confidence": raw.confidence,
                    "evidence_quote": raw.evidence_quote,
                    "rationale": raw.rationale,
                    "flags": list(raw.flags),
                },
            })
    return LLMExtractionResult(
        accepted=accepted,
        rejections=rejections,
        prompt=prompt,
        raw_response=raw_response,
        mode=mode,
    )


__all__ = [
    "ALLOWED_FLAGS",
    "LLM_MODES",
    "LLMClient",
    "LLMExtractionResult",
    "LLMMode",
    "MockLLMClient",
    "PROMPT_VERSION",
    "RawLLMProposal",
    "REASON_DUPLICATE_TYPED",
    "REASON_EMPTY_FIELD",
    "REASON_INVALID_CONFIDENCE",
    "REASON_LOW_CONFIDENCE",
    "REASON_QUOTE_NOT_IN_BODY",
    "REASON_SELF_REFERENCE",
    "REASON_UNKNOWN_PREDICATE",
    "build_prompt",
    "extract_and_validate",
    "parse_llm_response",
    "propose_triples_via_llm",
    "validate_raw_proposal",
]
