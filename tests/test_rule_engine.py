"""Tests for the rule engine (Sprint 8)."""

from __future__ import annotations

from evaluation.evaluation_result import (
    EvaluationResult,
    ExecutionStatistics,
    RuleFailure,
)
from evaluation.evaluation_rule import EvaluationRule
from evaluation.rule_engine import RuleEngine
from evaluation.rule_result import RuleResult
from evidence.evidence_collection import EvidenceCollection
from models.asset import Asset
from models.asset_profile import AssetProfile


def _evidence() -> EvidenceCollection:
    asset = Asset(
        ticker="AAPL",
        name="Apple Inc.",
        exchange="NASDAQ",
        currency="USD",
        profile=AssetProfile.MATURE_TECH,
    )
    return EvidenceCollection(asset=asset, items=())


def _rule(rule_id: str, *, enabled: bool = True, fail: bool = False) -> EvaluationRule:
    """Return a rule that either succeeds or raises, for engine tests."""

    def execute(evidence: EvidenceCollection) -> RuleResult:
        if fail:
            raise RuntimeError(f"{rule_id} failed")
        return RuleResult(
            rule_id=rule_id,
            score=1.0,
            reason=f"{rule_id} ran",
            evidence_references=(),
        )

    return EvaluationRule(
        id=rule_id,
        name=rule_id,
        description="engine test rule",
        enabled=enabled,
        execute=execute,
    )


def test_executes_enabled_rules_in_order() -> None:
    rules = (_rule("a"), _rule("b"), _rule("c"))

    evaluation = RuleEngine().run(rules, _evidence())

    assert isinstance(evaluation, EvaluationResult)
    assert [result.rule_id for result in evaluation.results] == ["a", "b", "c"]


def test_skips_disabled_rules() -> None:
    rules = (_rule("a"), _rule("b", enabled=False), _rule("c"))

    evaluation = RuleEngine().run(rules, _evidence())

    assert [result.rule_id for result in evaluation.results] == ["a", "c"]
    assert evaluation.skipped_rule_ids == ("b",)


def test_failure_does_not_stop_execution() -> None:
    rules = (_rule("a"), _rule("b", fail=True), _rule("c"))

    evaluation = RuleEngine().run(rules, _evidence())

    assert [result.rule_id for result in evaluation.results] == ["a", "c"]
    assert evaluation.failures == (
        RuleFailure(rule_id="b", error_type="RuntimeError", message="b failed"),
    )


def test_statistics_describe_the_run() -> None:
    rules = (_rule("a"), _rule("b", enabled=False), _rule("c", fail=True))

    statistics = RuleEngine().run(rules, _evidence()).statistics

    assert statistics == ExecutionStatistics(total=3, succeeded=1, skipped=1, failed=1)


def test_empty_rule_collection_produces_empty_result() -> None:
    evaluation = RuleEngine().run((), _evidence())

    assert evaluation.results == ()
    assert evaluation.skipped_rule_ids == ()
    assert evaluation.failures == ()
    assert evaluation.statistics == ExecutionStatistics(
        total=0, succeeded=0, skipped=0, failed=0
    )


def test_run_is_deterministic() -> None:
    rules = (_rule("a"), _rule("b", fail=True), _rule("c", enabled=False))
    engine = RuleEngine()
    evidence = _evidence()

    assert engine.run(rules, evidence) == engine.run(rules, evidence)
