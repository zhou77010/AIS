"""Tests for the risk evaluator and its rules.

Risk is the second category to be evaluated. These tests describe which risk
dimensions AIS can truthfully measure today, and — just as importantly — that a
dimension it cannot measure fails loudly rather than producing a number.
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
from evaluation.risk import (
    financial_cover_rule,
    financial_leverage_rule,
    liquidity_rule,
    market_risk_rule,
)
from evaluation.risk.risk_dimensions import RiskDimension
from evaluation.risk.risk_evaluator import RiskEvaluator
from evidence.evidence_collection import EvidenceCollection
from models.asset import Asset
from models.asset_profile import AssetProfile
from models.category import Category
from models.category_score import CategoryScore
from pipeline.evidence_builder import EvidenceBuilder
from utils.exceptions import DataError

_RETRIEVED_AT = datetime(2026, 9, 16, 3, 20, 0, tzinfo=UTC)


def _asset() -> Asset:
    return Asset(
        ticker="AAPL",
        name="Apple Inc.",
        exchange="NASDAQ",
        currency="USD",
        profile=AssetProfile.MATURE_TECH,
    )


def _evidence(**values: float) -> EvidenceCollection:
    """Return evidence carrying the given measurements; the rest unavailable.

    A measurement left out of ``values`` is present in the evidence with no
    value, which is what a source that was asked and did not answer looks like.
    """
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
    """Return evidence built without any market data source at all."""
    return EvidenceBuilder().build(_asset())


# --------------------------------------------------------------------------
# The rules
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("rule", "rule_id"),
    [
        (market_risk_rule.RULE, "risk.market"),
        (financial_leverage_rule.RULE, "risk.financial_leverage"),
        (financial_cover_rule.RULE, "risk.financial_cover"),
        (liquidity_rule.RULE, "risk.liquidity"),
    ],
)
def test_each_rule_exists_as_an_enabled_evaluation_rule(rule, rule_id) -> None:
    assert isinstance(rule, EvaluationRule)
    assert rule.id == rule_id
    assert rule.enabled is True


def test_market_risk_rule_reports_the_retrieved_beta() -> None:
    result = market_risk_rule.RULE.execute(_evidence(beta=1.24))

    assert result.score == pytest.approx(1.24)
    assert "1.24" in result.reason
    assert result.evidence_references == ("AAPL.market_data.beta",)


def test_financial_leverage_rule_reports_the_retrieved_ratio() -> None:
    result = financial_leverage_rule.RULE.execute(_evidence(debt_to_equity=0.87))

    assert result.score == pytest.approx(0.87)
    assert result.evidence_references == ("AAPL.market_data.debt_to_equity",)


def test_financial_cover_rule_reports_the_retrieved_ratio() -> None:
    result = financial_cover_rule.RULE.execute(_evidence(current_ratio=0.94))

    assert result.score == pytest.approx(0.94)
    assert result.evidence_references == ("AAPL.market_data.current_ratio",)


def test_liquidity_rule_measures_the_share_of_the_float_traded_each_day() -> None:
    result = liquidity_rule.RULE.execute(
        _evidence(average_volume=50_000_000.0, float_shares=2_500_000_000.0)
    )

    assert result.score == pytest.approx(0.02)
    assert "2.00%" in result.reason
    assert result.evidence_references == (
        "AAPL.market_data.average_volume",
        "AAPL.market_data.float_shares",
    )


# --------------------------------------------------------------------------
# A measurement that does not exist is never invented
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "rule",
    [
        market_risk_rule.RULE,
        financial_leverage_rule.RULE,
        financial_cover_rule.RULE,
        liquidity_rule.RULE,
    ],
)
def test_a_rule_fails_when_the_source_did_not_provide_its_measurement(rule) -> None:
    with pytest.raises(DataError):
        rule.execute(_evidence())


def test_liquidity_rule_refuses_to_divide_by_an_empty_float() -> None:
    with pytest.raises(DataError, match="float is not a positive number"):
        liquidity_rule.RULE.execute(_evidence(average_volume=1_000.0, float_shares=0.0))


@pytest.mark.parametrize(
    "rule",
    [
        market_risk_rule.RULE,
        financial_leverage_rule.RULE,
        financial_cover_rule.RULE,
        liquidity_rule.RULE,
    ],
)
def test_a_rule_claims_no_evidence_when_no_source_was_consulted(rule) -> None:
    result = rule.execute(_no_source_evidence())

    assert "Placeholder" in result.reason
    assert result.evidence_references == ()


# --------------------------------------------------------------------------
# The evaluator
# --------------------------------------------------------------------------


def test_evaluator_produces_a_risk_category_score() -> None:
    score = RiskEvaluator().evaluate(
        _evidence(
            beta=1.24,
            debt_to_equity=0.87,
            current_ratio=0.94,
            average_volume=50_000_000.0,
            float_shares=2_500_000_000.0,
        )
    )

    assert isinstance(score, CategoryScore)
    assert score.category is Category.RISK
    assert score.evidence_references == (
        "AAPL.market_data.beta",
        "AAPL.market_data.debt_to_equity",
        "AAPL.market_data.current_ratio",
        "AAPL.market_data.average_volume",
        "AAPL.market_data.float_shares",
    )


def test_evaluator_keeps_going_when_one_measurement_is_missing() -> None:
    evaluation = RiskEvaluator().collect_results(_evidence(beta=1.24))

    assert [result.rule_id for result in evaluation.results] == ["risk.market"]
    assert [failure.rule_id for failure in evaluation.failures] == [
        "risk.financial_leverage",
        "risk.financial_cover",
        "risk.liquidity",
    ]


def test_evaluator_assesses_what_it_can_for_an_asset_with_no_company_finances() -> None:
    # An exchange-traded fund reports no debt, no current ratio and no debt to
    # equity, but it does report a volume and a float.
    evaluation = RiskEvaluator().collect_results(
        _evidence(average_volume=1_000_000.0, float_shares=100_000_000.0)
    )

    assert [result.rule_id for result in evaluation.results] == ["risk.liquidity"]


def test_evaluator_reads_no_valuation_measurement() -> None:
    score = RiskEvaluator().evaluate(_evidence(pe=26.8, peg=0.46))

    assert score.evidence_references == ()


def test_evaluator_reports_coverage_over_all_eight_dimensions() -> None:
    score = RiskEvaluator().evaluate(
        _evidence(
            beta=1.24,
            debt_to_equity=0.87,
            current_ratio=0.94,
            average_volume=50_000_000.0,
            float_shares=2_500_000_000.0,
        )
    )

    # Three dimensions measured, with two financial rules between them.
    assert score.coverage.describe() == "3/8"
    assert score.coverage.total == len(RiskDimension)


def test_evaluator_counts_dimensions_rather_than_rules() -> None:
    # Both financial rules succeed, but they cover one dimension, not two.
    score = RiskEvaluator().evaluate(_evidence(debt_to_equity=0.87, current_ratio=0.94))

    assert score.coverage.describe() == "1/8"


def test_evaluator_reports_no_coverage_when_nothing_could_be_measured() -> None:
    score = RiskEvaluator().evaluate(_evidence(pe=26.8))

    assert score.coverage.describe() == "0/8"
    assert score.evidence_references == ()


def test_every_rule_declares_the_dimension_it_speaks_for() -> None:
    for module in (
        market_risk_rule,
        financial_leverage_rule,
        financial_cover_rule,
        liquidity_rule,
    ):
        assert isinstance(module.DIMENSION, RiskDimension)


def test_evaluator_is_deterministic() -> None:
    evaluator = RiskEvaluator()
    evidence = _evidence(beta=1.24, debt_to_equity=0.87)

    assert evaluator.evaluate(evidence) == evaluator.evaluate(evidence)
