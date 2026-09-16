"""Tests for the fundamental evaluator and its rules.

Fundamental is the third category to be evaluated. These tests describe what the
category answers, that a measurement it cannot retrieve fails rather than
producing a number, and that a measurement shared with another category is read
rather than recorded twice.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from contracts.market_data_provider import (
    MarketDataPoint,
    MarketDataSnapshot,
    MarketMetric,
)
from evaluation.evaluation_rule import EvaluationRule
from evaluation.fundamental import (
    cash_conversion_rule,
    profitability_rule,
    return_on_capital_rule,
    short_term_cover_rule,
    solvency_rule,
)
from evaluation.fundamental.fundamental_evaluator import FundamentalEvaluator
from evaluation.risk.risk_evaluator import RiskEvaluator
from evidence.evidence_collection import EvidenceCollection
from models.asset import Asset
from models.asset_profile import AssetProfile
from models.category import Category
from models.category_score import CategoryScore
from pipeline.evidence_builder import EvidenceBuilder
from utils.exceptions import DataError

_RETRIEVED_AT = datetime(2026, 9, 16, 3, 20, 0, tzinfo=UTC)

RULE_MODULES = (
    profitability_rule,
    cash_conversion_rule,
    return_on_capital_rule,
    solvency_rule,
    short_term_cover_rule,
)


def _asset() -> Asset:
    return Asset(
        ticker="AAPL",
        name="Apple Inc.",
        exchange="NASDAQ",
        currency="USD",
        profile=AssetProfile.MATURE_TECH,
    )


def _evidence(**values: float) -> EvidenceCollection:
    """Return evidence carrying the given measurements; the rest unavailable."""
    points = tuple(
        MarketDataPoint(
            metric=metric,
            value=values.get(metric.value),
            reason="test reason",
        )
        for metric in MarketMetric
    )
    snapshot = MarketDataSnapshot(
        symbol="AAPL",
        source="Test source",
        retrieved_at=_RETRIEVED_AT,
        points=points,
    )
    return EvidenceBuilder().build(_asset(), snapshot)


def _no_source_evidence() -> EvidenceCollection:
    return EvidenceBuilder().build(_asset())


# --------------------------------------------------------------------------
# The rules
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("rule", "rule_id"),
    [
        (profitability_rule.RULE, "fundamental.profitability"),
        (cash_conversion_rule.RULE, "fundamental.cash_conversion"),
        (return_on_capital_rule.RULE, "fundamental.return_on_capital"),
        (solvency_rule.RULE, "fundamental.solvency"),
        (short_term_cover_rule.RULE, "fundamental.short_term_cover"),
    ],
)
def test_each_rule_exists_as_an_enabled_evaluation_rule(rule, rule_id) -> None:
    assert isinstance(rule, EvaluationRule)
    assert rule.id == rule_id
    assert rule.enabled is True


def test_profitability_rule_reports_the_retrieved_margin() -> None:
    result = profitability_rule.RULE.execute(_evidence(profit_margin=0.27))

    assert result.score == pytest.approx(0.27)
    assert result.evidence_references == ("AAPL.market_data.profit_margin",)


def test_cash_conversion_rule_reports_the_retrieved_margin() -> None:
    result = cash_conversion_rule.RULE.execute(_evidence(free_cash_flow_margin=0.22))

    assert result.score == pytest.approx(0.22)
    assert result.evidence_references == ("AAPL.market_data.free_cash_flow_margin",)


def test_return_on_capital_rule_reports_the_retrieved_return() -> None:
    result = return_on_capital_rule.RULE.execute(_evidence(return_on_equity=0.42))

    assert result.score == pytest.approx(0.42)


def test_solvency_rule_reports_the_retrieved_ratio() -> None:
    result = solvency_rule.RULE.execute(_evidence(debt_to_equity=0.87))

    assert result.score == pytest.approx(0.87)


def test_short_term_cover_rule_reports_the_retrieved_ratio() -> None:
    result = short_term_cover_rule.RULE.execute(_evidence(current_ratio=0.94))

    assert result.score == pytest.approx(0.94)


@pytest.mark.parametrize("module", RULE_MODULES)
def test_a_rule_fails_when_the_source_did_not_provide_its_measurement(module) -> None:
    with pytest.raises(DataError):
        module.RULE.execute(_evidence())


@pytest.mark.parametrize("module", RULE_MODULES)
def test_a_rule_claims_no_evidence_when_no_source_was_consulted(module) -> None:
    result = module.RULE.execute(_no_source_evidence())

    assert "Placeholder" in result.reason
    assert result.evidence_references == ()


# --------------------------------------------------------------------------
# The evaluator
# --------------------------------------------------------------------------


def test_evaluator_produces_a_fundamental_category_score() -> None:
    score = FundamentalEvaluator().evaluate(
        _evidence(
            profit_margin=0.27,
            free_cash_flow_margin=0.22,
            return_on_equity=0.42,
            debt_to_equity=0.87,
            current_ratio=0.94,
        )
    )

    assert isinstance(score, CategoryScore)
    assert score.category is Category.FUNDAMENTAL
    assert score.coverage.describe() == "5/5"


def test_evaluator_coverage_counts_measurements() -> None:
    # Fundamental has no dimension layer, so a unit is a measurement.
    score = FundamentalEvaluator().evaluate(_evidence(profit_margin=0.27))

    assert score.coverage.describe() == "1/5"


def test_evaluator_keeps_going_when_a_measurement_is_missing() -> None:
    evaluation = FundamentalEvaluator().collect_results(_evidence(profit_margin=0.27))

    assert [result.rule_id for result in evaluation.results] == [
        "fundamental.profitability"
    ]
    assert len(evaluation.failures) == 4


def test_evaluator_is_deterministic() -> None:
    evaluator = FundamentalEvaluator()
    evidence = _evidence(profit_margin=0.27, debt_to_equity=0.87)

    assert evaluator.evaluate(evidence) == evaluator.evaluate(evidence)


# --------------------------------------------------------------------------
# One measurement, two questions
# --------------------------------------------------------------------------


def test_a_measurement_may_support_two_categories() -> None:
    categories = MarketMetric.DEBT_TO_EQUITY.categories

    assert categories[0] is Category.RISK
    assert Category.FUNDAMENTAL in categories


def test_a_shared_measurement_is_read_twice_but_recorded_once() -> None:
    evidence = _evidence(debt_to_equity=0.87, current_ratio=0.94)

    fundamental = FundamentalEvaluator().collect_results(evidence)
    risk = RiskEvaluator().collect_results(evidence)

    assert "fundamental.solvency" in [r.rule_id for r in fundamental.results]
    assert "risk.financial_leverage" in [r.rule_id for r in risk.results]

    # One evidence item carries the fact, and both categories point at it.
    debt_items = [
        item
        for item in evidence.items
        if item.metadata.get("market_metric") == MarketMetric.DEBT_TO_EQUITY.value
    ]
    assert len(debt_items) == 1
    assert debt_items[0].category is Category.RISK
