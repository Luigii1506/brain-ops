"""Golden set runner — Campaña 2.2B Paso 6.

Provides a test-bed for the LLM-assisted extractor against curated
fixtures. Each fixture declares:

- `must_catch`: triples the LLM should propose (recall signal).
- `must_not_propose`: triples that would be semantic errors; emitting them
  counts as hallucination / FP signal.
- `policy_checks`: conditional constraints (e.g. "if `adopted_by → Augusto`
  is proposed, it MUST carry the `hijastro_step_relation` flag and
  confidence=medium"). Captures Campaña 2.2B D12 (hijastro-de policy) and
  similar nuanced decisions cleanly.

The runner orchestrates: load fixture → run LLM via extract_and_validate →
evaluate against the three groups → aggregate metrics. The composite score
`must_catch_rate * must_not_propose_rate` is the green-light metric for
Paso 7 benchmark (target ≥ 0.65).

Runner works with any `LLMClient`: tests pass `MockLLMClient` with canned
responses; the real benchmark (Paso 7) will pass `AnthropicLLMClient`.
No vault mutation, no network in tests, no $ spent until opt-in.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from brain_ops.domains.knowledge.llm_extractor import (
    LLMClient,
    LLMMode,
    extract_and_validate,
)
from brain_ops.domains.knowledge.relations_proposer import ProposedRelation


# ---------------------------------------------------------------------------
# Fixture schema
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class MustCatchItem:
    predicate: str
    object: str
    notes: str = ""


@dataclass(frozen=True, slots=True)
class MustNotProposeItem:
    """A triple that should NOT be proposed. Optional filters narrow when
    the rule violates (e.g. only if confidence=high)."""
    predicate: str
    object: str
    reason: str = ""
    # If set, only flag as violation when the emitted proposal's confidence
    # is in this list. Empty means "any confidence violates".
    confidence_in: tuple[str, ...] = ()
    # If set, only flag as violation when the emitted proposal lacks this
    # flag. Empty means "flag presence is irrelevant".
    without_flag: str = ""


@dataclass(frozen=True, slots=True)
class PolicyCheck:
    """Conditional invariant. If a proposal matches `when.{predicate, object}`,
    it must satisfy `require.{confidence, flag, max_confidence}`.

    Example — Campaña 2.2B D12 for Tiberio:
        when:    predicate=adopted_by, object=Augusto
        require: confidence=medium, flag=hijastro_step_relation
    """
    description: str
    when_predicate: str
    when_object: str
    require_confidence: str | None = None          # exact match
    require_confidence_max: str | None = None      # "medium" means not "high"
    require_flag: str | None = None


@dataclass(frozen=True, slots=True)
class GoldenFixture:
    fixture_id: str
    entity: str
    subtype: str | None
    domain: str | list[str] | None
    body: str
    existing_typed: set[tuple[str, str]]
    candidate_targets: list[str]
    entity_index: dict[str, str]
    must_catch: list[MustCatchItem]
    must_not_propose: list[MustNotProposeItem]
    policy_checks: list[PolicyCheck]

    @classmethod
    def from_yaml(cls, path: Path) -> "GoldenFixture":
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"{path}: top-level must be a mapping")

        existing = {
            (item[0], item[1])
            for item in (data.get("existing_typed") or [])
            if isinstance(item, (list, tuple)) and len(item) == 2
        }

        def _parse_mc(raw: Any) -> list[MustCatchItem]:
            out: list[MustCatchItem] = []
            for item in raw or []:
                if isinstance(item, (list, tuple)) and len(item) == 2:
                    out.append(MustCatchItem(
                        predicate=item[0], object=item[1], notes="",
                    ))
                elif isinstance(item, dict):
                    out.append(MustCatchItem(
                        predicate=item["predicate"],
                        object=item["object"],
                        notes=item.get("notes", ""),
                    ))
            return out

        def _parse_mnp(raw: Any) -> list[MustNotProposeItem]:
            out: list[MustNotProposeItem] = []
            for item in raw or []:
                if isinstance(item, (list, tuple)) and len(item) == 2:
                    out.append(MustNotProposeItem(
                        predicate=item[0], object=item[1],
                    ))
                elif isinstance(item, dict):
                    out.append(MustNotProposeItem(
                        predicate=item["predicate"],
                        object=item["object"],
                        reason=item.get("reason", ""),
                        confidence_in=tuple(item.get("confidence_in") or ()),
                        without_flag=item.get("without_flag", ""),
                    ))
            return out

        def _parse_policy(raw: Any) -> list[PolicyCheck]:
            out: list[PolicyCheck] = []
            for item in raw or []:
                if not isinstance(item, dict):
                    continue
                when = item.get("when", {}) or {}
                require = item.get("require", {}) or {}
                out.append(PolicyCheck(
                    description=item.get("description", ""),
                    when_predicate=when.get("predicate", ""),
                    when_object=when.get("object", ""),
                    require_confidence=require.get("confidence"),
                    require_confidence_max=require.get("confidence_max"),
                    require_flag=require.get("flag"),
                ))
            return out

        return cls(
            fixture_id=data.get("fixture_id") or path.stem,
            entity=data["entity"],
            subtype=data.get("subtype"),
            domain=data.get("domain"),
            body=data.get("body", ""),
            existing_typed=existing,
            candidate_targets=list(data.get("candidate_targets") or []),
            entity_index=dict(data.get("entity_index") or {}),
            must_catch=_parse_mc(data.get("must_catch")),
            must_not_propose=_parse_mnp(data.get("must_not_propose")),
            policy_checks=_parse_policy(data.get("policy_checks")),
        )


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------


@dataclass
class FixtureResult:
    fixture_id: str
    entity: str
    proposals: list[ProposedRelation]
    must_catch_hits: list[tuple[str, str]]
    must_catch_misses: list[tuple[str, str]]
    must_not_propose_violations: list[dict]
    policy_passes: list[str]  # descriptions
    policy_failures: list[dict]  # {description, reason, proposal}
    extra_proposals: list[tuple[str, str]]  # neither in catch nor not_propose

    @property
    def must_catch_total(self) -> int:
        return len(self.must_catch_hits) + len(self.must_catch_misses)

    @property
    def must_catch_rate(self) -> float:
        total = self.must_catch_total
        return (len(self.must_catch_hits) / total) if total > 0 else 1.0

    @property
    def must_not_propose_rate(self) -> float:
        # "1 - violation rate" semantic: 1.0 = zero violations.
        # If there are no MNP rules, we treat the score as perfect.
        # If there are rules, we score as 1 - (violations / rules_count), bounded [0, 1].
        total = 0  # total will be count of rules, computed by caller, stored elsewhere
        return 1.0 - min(len(self.must_not_propose_violations), 1.0)

    def must_not_propose_rate_over(self, total_rules: int) -> float:
        if total_rules == 0:
            return 1.0
        return max(0.0, 1.0 - (len(self.must_not_propose_violations) / total_rules))

    def composite_score(self, total_mnp_rules: int) -> float:
        return self.must_catch_rate * self.must_not_propose_rate_over(total_mnp_rules)


@dataclass
class GoldenSetReport:
    mode: LLMMode
    results: list[FixtureResult] = field(default_factory=list)
    total_must_catch: int = 0
    total_must_catch_hits: int = 0
    total_must_not_propose: int = 0
    total_mnp_violations: int = 0
    total_policy_checks: int = 0
    total_policy_failures: int = 0

    @property
    def overall_must_catch_rate(self) -> float:
        if self.total_must_catch == 0:
            return 1.0
        return self.total_must_catch_hits / self.total_must_catch

    @property
    def overall_must_not_propose_rate(self) -> float:
        if self.total_must_not_propose == 0:
            return 1.0
        return max(0.0, 1.0 - (self.total_mnp_violations / self.total_must_not_propose))

    @property
    def overall_policy_pass_rate(self) -> float:
        if self.total_policy_checks == 0:
            return 1.0
        passed = self.total_policy_checks - self.total_policy_failures
        return passed / self.total_policy_checks

    @property
    def composite_score(self) -> float:
        """Campaña 2.2B green-light metric: composite of catch + no-error."""
        return self.overall_must_catch_rate * self.overall_must_not_propose_rate


def _check_confidence_max(actual: str, max_allowed: str) -> bool:
    """Return True if `actual` ≤ `max_allowed` in ordering high > medium > low."""
    order = {"low": 0, "medium": 1, "high": 2}
    return order.get(actual, -1) <= order.get(max_allowed, -1)


def evaluate_fixture_against_proposals(
    fixture: GoldenFixture,
    proposals: list[ProposedRelation],
) -> FixtureResult:
    """Apply the 3-group evaluation: must_catch, must_not_propose, policy_checks."""
    proposed_keys = {(p.predicate, p.object) for p in proposals}
    by_key = {(p.predicate, p.object): p for p in proposals}

    # must_catch
    hits: list[tuple[str, str]] = []
    misses: list[tuple[str, str]] = []
    catch_keys: set[tuple[str, str]] = set()
    for item in fixture.must_catch:
        key = (item.predicate, item.object)
        catch_keys.add(key)
        if key in proposed_keys:
            hits.append(key)
        else:
            misses.append(key)

    # must_not_propose
    violations: list[dict] = []
    mnp_keys: set[tuple[str, str]] = set()
    for item in fixture.must_not_propose:
        key = (item.predicate, item.object)
        mnp_keys.add(key)
        if key not in proposed_keys:
            continue
        p = by_key[key]
        # Apply filters
        if item.confidence_in and p.confidence not in item.confidence_in:
            continue
        if item.without_flag:
            # Violate only if flag is absent from the note.
            flag_present = item.without_flag in (p.note or "")
            if flag_present:
                continue
        violations.append({
            "predicate": item.predicate,
            "object": item.object,
            "reason": item.reason,
            "emitted_confidence": p.confidence,
            "emitted_note": p.note,
        })

    # policy_checks
    policy_passes: list[str] = []
    policy_failures: list[dict] = []
    for policy in fixture.policy_checks:
        key = (policy.when_predicate, policy.when_object)
        if key not in proposed_keys:
            # Policy is conditional — if trigger didn't fire, nothing to check.
            # Count as pass (vacuously satisfied).
            policy_passes.append(policy.description)
            continue
        p = by_key[key]
        fails: list[str] = []
        if (policy.require_confidence is not None
                and p.confidence != policy.require_confidence):
            fails.append(
                f"expected confidence={policy.require_confidence}, got {p.confidence}"
            )
        if (policy.require_confidence_max is not None
                and not _check_confidence_max(p.confidence, policy.require_confidence_max)):
            fails.append(
                f"expected confidence ≤ {policy.require_confidence_max}, got {p.confidence}"
            )
        if policy.require_flag is not None:
            if policy.require_flag not in (p.note or ""):
                fails.append(f"expected flag `{policy.require_flag}` absent in note")
        if fails:
            policy_failures.append({
                "description": policy.description,
                "reasons": fails,
                "emitted": {
                    "predicate": p.predicate,
                    "object": p.object,
                    "confidence": p.confidence,
                    "note": p.note,
                },
            })
        else:
            policy_passes.append(policy.description)

    extras = [
        key for key in proposed_keys
        if key not in catch_keys and key not in mnp_keys
    ]

    return FixtureResult(
        fixture_id=fixture.fixture_id,
        entity=fixture.entity,
        proposals=proposals,
        must_catch_hits=hits,
        must_catch_misses=misses,
        must_not_propose_violations=violations,
        policy_passes=policy_passes,
        policy_failures=policy_failures,
        extra_proposals=extras,
    )


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_fixture(
    fixture: GoldenFixture,
    *,
    client: LLMClient,
    mode: LLMMode = "strict",
) -> FixtureResult:
    """Run a single fixture through the LLM extractor and evaluate.

    Uses `extract_and_validate` with `candidate_targets` and `entity_index`
    from the fixture itself. No vault needed — fixtures are self-contained.
    """
    result = extract_and_validate(
        fixture.entity, fixture.body,
        mode=mode,
        client=client,
        existing_typed=fixture.existing_typed,
        entity_index=fixture.entity_index,
        subtype=fixture.subtype,
        domain=fixture.domain,
        candidate_targets=fixture.candidate_targets,
    )
    return evaluate_fixture_against_proposals(fixture, result.accepted)


def run_golden_set(
    fixtures_dir: Path,
    *,
    client: LLMClient,
    mode: LLMMode = "strict",
) -> GoldenSetReport:
    """Iterate every `*.yaml` in fixtures_dir (except hidden files) and
    aggregate the evaluation into a `GoldenSetReport`.

    Fixtures are sorted by filename so the report is deterministic.
    """
    report = GoldenSetReport(mode=mode)
    for path in sorted(fixtures_dir.glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        fixture = GoldenFixture.from_yaml(path)
        fx_result = run_fixture(fixture, client=client, mode=mode)
        report.results.append(fx_result)
        report.total_must_catch += fx_result.must_catch_total
        report.total_must_catch_hits += len(fx_result.must_catch_hits)
        report.total_must_not_propose += len(fixture.must_not_propose)
        report.total_mnp_violations += len(fx_result.must_not_propose_violations)
        report.total_policy_checks += len(fixture.policy_checks)
        report.total_policy_failures += len(fx_result.policy_failures)
    return report


__all__ = [
    "FixtureResult",
    "GoldenFixture",
    "GoldenSetReport",
    "MustCatchItem",
    "MustNotProposeItem",
    "PolicyCheck",
    "evaluate_fixture_against_proposals",
    "run_fixture",
    "run_golden_set",
]
