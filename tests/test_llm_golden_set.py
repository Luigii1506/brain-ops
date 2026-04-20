"""Tests for `llm_golden_set` — Campaña 2.2B Paso 6.

No real LLM calls. All tests use MockLLMClient with canned JSON responses
that simulate ideal or degraded LLM behavior per fixture.

Scope:
- fixture loader correctness (YAML → GoldenFixture)
- evaluator logic (must_catch, must_not_propose, policy_checks)
- runner aggregates metrics across fixtures
- D12 policy check (hijastro de Tiberio) enforces medium + flag
"""

from __future__ import annotations

from pathlib import Path
from unittest import TestCase

from brain_ops.domains.knowledge.llm_extractor import MockLLMClient
from brain_ops.domains.knowledge.llm_golden_set import (
    GoldenFixture,
    MustCatchItem,
    MustNotProposeItem,
    PolicyCheck,
    evaluate_fixture_against_proposals,
    run_fixture,
    run_golden_set,
)
from brain_ops.domains.knowledge.relations_proposer import (
    EvidenceExcerpt, ProposedRelation,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "golden_set"


def _build_proposal(
    predicate: str, object_: str,
    *,
    confidence: str = "high",
    note: str = "",
) -> ProposedRelation:
    return ProposedRelation(
        id="x",
        predicate=predicate,
        object=object_,
        confidence=confidence,
        status="approved" if confidence == "high" else "needs-refinement",
        evidence_source=["llm"],
        evidence_excerpts=[EvidenceExcerpt(location="body.llm", text="q")],
        object_status="canonical_entity_exists",
        note=note,
    )


# ---------------------------------------------------------------------------
# Fixture loader
# ---------------------------------------------------------------------------


class FixtureLoaderTestCase(TestCase):
    def test_load_zeus_fixture(self) -> None:
        fixture = GoldenFixture.from_yaml(FIXTURES_DIR / "01_zeus.yaml")
        self.assertEqual(fixture.entity, "Zeus")
        self.assertEqual(fixture.subtype, "deity")
        self.assertEqual(fixture.domain, "religion")
        self.assertIn(("child_of", "Cronos"),
                      [(m.predicate, m.object) for m in fixture.must_catch])
        self.assertIn(("located_in", "Olimpo"), fixture.existing_typed)

    def test_load_tiberio_fixture_with_policy_checks(self) -> None:
        fixture = GoldenFixture.from_yaml(FIXTURES_DIR / "09_tiberio_hijastro.yaml")
        self.assertEqual(fixture.entity, "Tiberio")
        # Verificar el policy_check D12
        self.assertEqual(len(fixture.policy_checks), 1)
        policy = fixture.policy_checks[0]
        self.assertEqual(policy.when_predicate, "adopted_by")
        self.assertEqual(policy.when_object, "Augusto")
        self.assertEqual(policy.require_confidence, "medium")
        self.assertEqual(policy.require_flag, "hijastro_step_relation")

    def test_all_ten_fixtures_load(self) -> None:
        """Smoke test: todas las fixtures cargan sin excepción."""
        paths = sorted(FIXTURES_DIR.glob("*.yaml"))
        self.assertEqual(len(paths), 10, "golden set debe tener 10 fixtures")
        for path in paths:
            fixture = GoldenFixture.from_yaml(path)
            self.assertTrue(fixture.entity, f"{path.name}: entity vacío")
            self.assertTrue(fixture.body.strip(), f"{path.name}: body vacío")


# ---------------------------------------------------------------------------
# Evaluator
# ---------------------------------------------------------------------------


class EvaluatorTestCase(TestCase):
    def _make_fixture(
        self,
        must_catch: list[tuple[str, str]] | None = None,
        must_not_propose: list[MustNotProposeItem] | None = None,
        policy_checks: list[PolicyCheck] | None = None,
    ) -> GoldenFixture:
        return GoldenFixture(
            fixture_id="test", entity="X", subtype="person", domain="historia",
            body="body", existing_typed=set(), candidate_targets=[],
            entity_index={},
            must_catch=[MustCatchItem(p, o) for p, o in (must_catch or [])],
            must_not_propose=must_not_propose or [],
            policy_checks=policy_checks or [],
        )

    def test_must_catch_hit(self) -> None:
        fixture = self._make_fixture(
            must_catch=[("studied_under", "Platón"),
                        ("mentor_of", "Alejandro Magno")],
        )
        proposals = [_build_proposal("studied_under", "Platón")]
        result = evaluate_fixture_against_proposals(fixture, proposals)
        self.assertEqual(result.must_catch_hits, [("studied_under", "Platón")])
        self.assertEqual(result.must_catch_misses, [("mentor_of", "Alejandro Magno")])
        self.assertAlmostEqual(result.must_catch_rate, 0.5)

    def test_must_not_propose_violation_any_confidence(self) -> None:
        fixture = self._make_fixture(
            must_not_propose=[MustNotProposeItem(
                predicate="child_of", object="Julio César",
                reason="adoptivo, no biológico",
            )],
        )
        proposals = [_build_proposal("child_of", "Julio César", confidence="high")]
        result = evaluate_fixture_against_proposals(fixture, proposals)
        self.assertEqual(len(result.must_not_propose_violations), 1)

    def test_must_not_propose_with_confidence_filter(self) -> None:
        """Si confidence_in=[high], un proposal medium NO viola."""
        fixture = self._make_fixture(
            must_not_propose=[MustNotProposeItem(
                predicate="adopted_by", object="Augusto",
                confidence_in=("high",),
            )],
        )
        # medium → no viola
        proposals = [_build_proposal("adopted_by", "Augusto", confidence="medium")]
        result = evaluate_fixture_against_proposals(fixture, proposals)
        self.assertEqual(len(result.must_not_propose_violations), 0)
        # high → viola
        proposals = [_build_proposal("adopted_by", "Augusto", confidence="high")]
        result = evaluate_fixture_against_proposals(fixture, proposals)
        self.assertEqual(len(result.must_not_propose_violations), 1)

    def test_must_not_propose_with_without_flag(self) -> None:
        """Si without_flag=hijastro_step_relation, viola solo si el flag NO
        está en la nota."""
        fixture = self._make_fixture(
            must_not_propose=[MustNotProposeItem(
                predicate="adopted_by", object="Augusto",
                without_flag="hijastro_step_relation",
            )],
        )
        # Con flag → no viola
        proposals = [_build_proposal(
            "adopted_by", "Augusto", confidence="medium",
            note="rationale [flags: hijastro_step_relation]",
        )]
        result = evaluate_fixture_against_proposals(fixture, proposals)
        self.assertEqual(len(result.must_not_propose_violations), 0)
        # Sin flag → viola
        proposals = [_build_proposal(
            "adopted_by", "Augusto", confidence="high",
            note="rationale sin flag",
        )]
        result = evaluate_fixture_against_proposals(fixture, proposals)
        self.assertEqual(len(result.must_not_propose_violations), 1)

    def test_policy_check_d12_satisfied(self) -> None:
        """D12: adopted_by → Augusto con medium + flag → pass."""
        fixture = self._make_fixture(
            policy_checks=[PolicyCheck(
                description="D12",
                when_predicate="adopted_by", when_object="Augusto",
                require_confidence="medium",
                require_flag="hijastro_step_relation",
            )],
        )
        proposals = [_build_proposal(
            "adopted_by", "Augusto", confidence="medium",
            note="rationale [flags: hijastro_step_relation]",
        )]
        result = evaluate_fixture_against_proposals(fixture, proposals)
        self.assertEqual(len(result.policy_passes), 1)
        self.assertEqual(len(result.policy_failures), 0)

    def test_policy_check_d12_violated_high_confidence(self) -> None:
        """D12 violado: adopted_by → Augusto con HIGH (no medium)."""
        fixture = self._make_fixture(
            policy_checks=[PolicyCheck(
                description="D12",
                when_predicate="adopted_by", when_object="Augusto",
                require_confidence="medium",
                require_flag="hijastro_step_relation",
            )],
        )
        proposals = [_build_proposal(
            "adopted_by", "Augusto", confidence="high",
            note="rationale [flags: hijastro_step_relation]",
        )]
        result = evaluate_fixture_against_proposals(fixture, proposals)
        self.assertEqual(len(result.policy_failures), 1)
        self.assertIn("confidence", result.policy_failures[0]["reasons"][0])

    def test_policy_check_vacuously_passes_when_trigger_absent(self) -> None:
        """Si el LLM NO emite el triple-trigger, el policy check pasa
        vacuamente (no hay nada que verificar)."""
        fixture = self._make_fixture(
            policy_checks=[PolicyCheck(
                description="D12",
                when_predicate="adopted_by", when_object="Augusto",
                require_confidence="medium",
            )],
        )
        proposals = [_build_proposal("succeeded", "Augusto")]  # NO adopted_by
        result = evaluate_fixture_against_proposals(fixture, proposals)
        self.assertEqual(len(result.policy_passes), 1)
        self.assertEqual(len(result.policy_failures), 0)

    def test_extra_proposals_classified(self) -> None:
        """Proposals que NO están en must_catch NI must_not_propose quedan
        como 'extras' — ni TP ni FP. Señal informativa."""
        fixture = self._make_fixture(
            must_catch=[("studied_under", "Platón")],
            must_not_propose=[MustNotProposeItem("child_of", "X")],
        )
        proposals = [
            _build_proposal("studied_under", "Platón"),    # hit
            _build_proposal("born_in", "Atenas"),          # extra
        ]
        result = evaluate_fixture_against_proposals(fixture, proposals)
        self.assertEqual(len(result.must_catch_hits), 1)
        self.assertIn(("born_in", "Atenas"), result.extra_proposals)


# ---------------------------------------------------------------------------
# Runner (end-to-end con mock)
# ---------------------------------------------------------------------------


class RunnerTestCase(TestCase):
    def test_run_single_fixture_with_good_mock(self) -> None:
        """Zeus con respuesta LLM que captura la mitad de must_catch.
        Uso quotes cortos garantizados substring del body (el block literal
        `|` de YAML preserva los saltos de línea; quotes largos pueden
        cruzarlos)."""
        fixture = GoldenFixture.from_yaml(FIXTURES_DIR / "01_zeus.yaml")
        canned = (
            '{"proposals": ['
            '{"predicate": "child_of", "object": "Cronos", '
            ' "confidence": "high", '
            ' "evidence_quote": "Hijo menor de [[Cronos]]", '
            ' "rationale": "filiación mitológica", "flags": []},'
            '{"predicate": "child_of", "object": "Rea", '
            ' "confidence": "high", '
            ' "evidence_quote": "[[Rea]], escapó", '
            ' "rationale": "filiación mitológica", "flags": []}'
            ']}'
        )
        client = MockLLMClient(canned_response=canned)
        result = run_fixture(fixture, client=client, mode="strict")
        self.assertIn(("child_of", "Cronos"), result.must_catch_hits)
        self.assertIn(("child_of", "Rea"), result.must_catch_hits)
        # Otros must_catch no cumplidos
        self.assertGreater(len(result.must_catch_misses), 0)

    def test_run_golden_set_empty_responses(self) -> None:
        """Con LLM devolviendo 0 proposals en todas las fixtures, el
        must_catch_rate overall = 0. Verifica aggregation."""
        client = MockLLMClient(canned_response='{"proposals": []}')
        report = run_golden_set(FIXTURES_DIR, client=client, mode="strict")
        self.assertEqual(len(report.results), 10)
        self.assertEqual(report.total_must_catch_hits, 0)
        self.assertEqual(report.overall_must_catch_rate, 0.0)
        self.assertEqual(report.overall_must_not_propose_rate, 1.0)
        self.assertAlmostEqual(report.composite_score, 0.0)

    def test_tiberio_with_correct_hijastro_handling(self) -> None:
        """El LLM sigue D12: emite adopted_by → Augusto con medium + flag.
        Policy check debe pasar, must_not_propose no debe violarse
        (gracias a `without_flag`). Quotes cortos que no cruzan saltos
        de línea del YAML block."""
        fixture = GoldenFixture.from_yaml(FIXTURES_DIR / "09_tiberio_hijastro.yaml")
        canned = (
            '{"proposals": ['
            '{"predicate": "succeeded", "object": "Augusto", '
            ' "confidence": "high", '
            ' "evidence_quote": "Hijastro y sucesor reluctante", '
            ' "rationale": "sucesión imperial directa", "flags": []},'
            '{"predicate": "adopted_by", "object": "Augusto", '
            ' "confidence": "medium", '
            ' "evidence_quote": "Hijastro y sucesor reluctante", '
            ' "rationale": "caso hijastro — reviewer decide", '
            ' "flags": ["hijastro_step_relation"]}'
            ']}'
        )
        client = MockLLMClient(canned_response=canned)
        result = run_fixture(fixture, client=client, mode="strict")
        # succeeded must_catch hit
        self.assertIn(("succeeded", "Augusto"), result.must_catch_hits)
        # adopted_by emitido con flag → must_not_propose NO viola
        self.assertEqual(len(result.must_not_propose_violations), 0)
        # policy_check D12 → pass
        self.assertEqual(len(result.policy_failures), 0)
        self.assertGreaterEqual(len(result.policy_passes), 1)

    def test_tiberio_with_hijastro_violation_high_confidence(self) -> None:
        """El LLM emite adopted_by → Augusto con HIGH (viola D12).
        Quote corta garantizada substring del body."""
        fixture = GoldenFixture.from_yaml(FIXTURES_DIR / "09_tiberio_hijastro.yaml")
        canned = (
            '{"proposals": ['
            '{"predicate": "adopted_by", "object": "Augusto", '
            ' "confidence": "high", '
            ' "evidence_quote": "Hijastro y sucesor reluctante", '
            ' "rationale": "infered adoption", '
            ' "flags": ["hijastro_step_relation"]}'
            ']}'
        )
        client = MockLLMClient(canned_response=canned)
        result = run_fixture(fixture, client=client, mode="strict")
        self.assertEqual(len(result.policy_failures), 1)
        # Razón específica: confidence incorrecto
        self.assertIn("confidence", result.policy_failures[0]["reasons"][0])

    def test_aggregate_metrics_produce_composite_score(self) -> None:
        """Verifica que el composite_score se calcula de forma consistente."""
        client = MockLLMClient(canned_response='{"proposals": []}')
        report = run_golden_set(FIXTURES_DIR, client=client, mode="strict")
        # composite = catch_rate * mnp_rate
        expected = (
            report.overall_must_catch_rate
            * report.overall_must_not_propose_rate
        )
        self.assertAlmostEqual(report.composite_score, expected)


# ---------------------------------------------------------------------------
# Green-light threshold check (decisión 2.2B)
# ---------------------------------------------------------------------------


class GreenLightThresholdTestCase(TestCase):
    """Placeholder de Paso 7: cuando el benchmark real corra, composite_score
    ≥ 0.65 es la señal para proceder con benchmark sobre 5 batches del vault.
    Este test documenta esa decisión numérica."""

    def test_composite_above_065_signals_green_light(self) -> None:
        """Hipotéticamente: si must_catch=0.7 y mnp=1.0, composite=0.7 ≥ 0.65."""
        from brain_ops.domains.knowledge.llm_golden_set import GoldenSetReport
        report = GoldenSetReport(mode="strict")
        report.total_must_catch = 10
        report.total_must_catch_hits = 7
        report.total_must_not_propose = 5
        report.total_mnp_violations = 0
        self.assertGreaterEqual(report.composite_score, 0.65)

    def test_composite_below_065_signals_tune_or_abandon(self) -> None:
        """Si must_catch=0.4 o mnp=0.5, composite<0.65 → revisar o abandonar."""
        from brain_ops.domains.knowledge.llm_golden_set import GoldenSetReport
        report = GoldenSetReport(mode="strict")
        report.total_must_catch = 10
        report.total_must_catch_hits = 4
        report.total_must_not_propose = 5
        report.total_mnp_violations = 0
        self.assertLess(report.composite_score, 0.65)
