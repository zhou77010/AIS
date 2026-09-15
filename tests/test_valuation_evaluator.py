"""Tests for the valuation evaluator (Sprint 7)."""

from __future__ import annotations

import pytest

from evaluation.evaluation_result import EvaluationResult
from evaluation.evaluation_rule import EvaluationRule
from evaluation.rule_result import RuleResult
from evaluation.valuation import (
    dcf_rule,
    ev_ebitda_rule,
    fcf_yield_rule,
    pe_rule,
    peg_rule,
)
from evaluation.valuation.valuation_evaluator import ValuationEvaluator
from evidence.evidence_collection import EvidenceCollection
from models.asset import Asset
from models.asset_profile import AssetProfile
from models.category import Category
from models.category_score import CategoryScore


def _evidence() -> EvidenceCollection:
    asset = Asset(
        ticker="AAPL",
        name="Apple Inc.",
        exchange="NASDAQ",
        currency="USD",
        profile=AssetProfile.MATURE_TECH,
    )
    return EvidenceCollection(asset=asset, items=())


@pytest.mark.parametrize(
    ("rule", "rule_id"),
    [
        (pe_rule.RULE, "valuation.pe"),
        (peg_rule.RULE, "valuation.peg"),
        (ev_ebitda_rule.RULE, "valuation.ev_ebitda"),
        (fcf_yield_rule.RULE, "valuation.fcf_yield"),
        (dcf_rule.RULE, "valuation.dcf"),
    ],
)
def test_each_rule_exists_as_an_enabled_evaluation_rule(rule, rule_id) -> None:
    assert isinstance(rule, EvaluationRule)
    assert rule.id == rule_id
    assert rule.enabled is True

    result = rule.execute(_evidence())

    assert isinstance(result, RuleResult)
    assert result.rule_id == rule_id
    assert isinstance(result.score, float)
    assert result.reason
    assert result.evidence_references


def test_collect_results_preserves_every_rule_result() -> None:
    results = ValuationEvaluator().collect_results(_evidence())

    assert isinstance(results, EvaluationResult)
    assert [result.rule_id for result in results.results] == [
        "valuation.pe",
        "valuation.peg",
        "valuation.ev_ebitda",
        "valuation.fcf_yield",
        "valuation.dcf",
    ]
    assert results.failures == ()
    assert results.skipped_rule_ids == ()


def test_evaluate_returns_valid_category_score() -> None:
    score = ValuationEvaluator().evaluate(_evidence())

    assert isinstance(score, CategoryScore)
    assert score.category is Category.VALUATION
    assert score.confidence == 1.0
    assert score.evidence_references == (
        "valuation.pe",
        "valuation.peg",
        "valuation.ev_ebitda",
        "valuation.fcf_yield",
        "valuation.dcf",
    )


def test_evaluate_aggregates_as_placeholder_mean() -> None:
    evaluator = ValuationEvaluator()
    evidence = _evidence()
    results = evaluator.collect_results(evidence)

    expected = sum(result.score for result in results.results) / len(results.results)
    assert evaluator.evaluate(evidence).score == pytest.approx(expected)


def test_evaluate_includes_reasons_and_references() -> None:
    evaluator = ValuationEvaluator()
    evidence = _evidence()
    results = evaluator.collect_results(evidence)
    score = evaluator.evaluate(evidence)

    for result in results.results:
        assert result.reason in score.summary
        assert result.evidence_references[0] in score.evidence_references


def test_evaluate_is_deterministic() -> None:
    evaluator = ValuationEvaluator()
    evidence = _evidence()

    assert evaluator.evaluate(evidence) == evaluator.evaluate(evidence)
