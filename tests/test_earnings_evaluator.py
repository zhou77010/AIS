"""Tests for the earnings evaluator and its rules.

Earnings is the sixth category to be evaluated. Its question names both of its
parts, so these tests describe both, and describe that a business with no
positive reported earnings fails rather than producing a meaningless ratio.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from contracts.market_data_provider import (
    MarketDataPoint,
    MarketDataSnapshot,
    MarketMetric,
)
from data.yahoo_market_data_provider import _expected_earnings_change_point
from evaluation.earnings import expected_rule, reported_rule
from evaluation.earnings.earnings_evaluator import EarningsEvaluator
from evaluation.earnings.earnings_parts import EarningsPart
from evaluation.evaluation_rule import EvaluationRule
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


@pytest.mark.parametrize(
    ("rule", "rule_id"),
    [
        (reported_rule.RULE, "earnings.reported"),
        (expected_rule.RULE, "earnings.expected"),
    ],
)
def test_each_rule_exists_as_an_enabled_evaluation_rule(rule, rule_id) -> None:
    assert isinstance(rule, EvaluationRule)
    assert rule.id == rule_id
    assert rule.enabled is True


def test_reported_rule_reports_the_growth_of_reported_earnings() -> None:
    result = reported_rule.RULE.execute(_evidence(earnings_growth=0.23))

    assert result.score == pytest.approx(0.23)
    assert result.evidence_references == ("AAPL.market_data.earnings_growth",)


def test_expected_rule_reports_the_change_the_expectation_contains() -> None:
    result = expected_rule.RULE.execute(_evidence(expected_earnings_change=0.18))

    assert result.score == pytest.approx(0.18)
    assert result.evidence_references == ("AAPL.market_data.expected_earnings_change",)


@pytest.mark.parametrize("module", [reported_rule, expected_rule])
def test_a_rule_fails_when_the_source_did_not_provide_its_measurement(module) -> None:
    with pytest.raises(DataError):
        module.RULE.execute(_evidence())


@pytest.mark.parametrize("module", [reported_rule, expected_rule])
def test_a_rule_claims_no_evidence_when_no_source_was_consulted(module) -> None:
    result = module.RULE.execute(_no_source_evidence())

    assert "Placeholder" in result.reason
    assert result.evidence_references == ()


# --------------------------------------------------------------------------
# The expectation is only meaningful against positive reported earnings
# --------------------------------------------------------------------------


def test_the_expectation_is_measured_against_positive_reported_earnings() -> None:
    point = _expected_earnings_change_point(forward_eps=12.0, trailing_eps=10.0)

    assert point.value == pytest.approx(0.2)
    assert "divided by the reported figure" in point.reason


def test_the_expectation_is_absent_when_reported_earnings_are_a_loss() -> None:
    # Dividing by a loss produces a number that says nothing about what is
    # expected next, so no number is produced.
    point = _expected_earnings_change_point(forward_eps=-0.5, trailing_eps=-1.2)

    assert point.value is None
    assert "positive reported earnings per share" in point.reason


def test_the_expectation_is_absent_when_reported_earnings_are_zero() -> None:
    point = _expected_earnings_change_point(forward_eps=1.0, trailing_eps=0.0)

    assert point.value is None


def test_the_expectation_is_absent_when_the_source_reports_neither_figure() -> None:
    point = _expected_earnings_change_point(forward_eps=None, trailing_eps=None)

    assert point.value is None


# --------------------------------------------------------------------------
# The evaluator
# --------------------------------------------------------------------------


def test_evaluator_produces_an_earnings_category_score() -> None:
    score = EarningsEvaluator().evaluate(
        _evidence(earnings_growth=0.23, expected_earnings_change=0.18)
    )

    assert isinstance(score, CategoryScore)
    assert score.category is Category.EARNINGS
    assert score.coverage.describe() == "2/2"
    assert score.coverage.total == len(EarningsPart)


def test_evaluator_reports_partial_coverage_when_one_part_is_missing() -> None:
    score = EarningsEvaluator().evaluate(_evidence(earnings_growth=0.23))

    assert score.coverage.describe() == "1/2"
    assert score.coverage.is_complete is False


def test_evaluator_reports_no_coverage_when_nothing_could_be_measured() -> None:
    score = EarningsEvaluator().evaluate(_evidence(beta=1.2))

    assert score.coverage.describe() == "0/2"
    assert score.evidence_references == ()


def test_evaluator_reads_no_other_category_measurement() -> None:
    score = EarningsEvaluator().evaluate(
        _evidence(pe=26.8, profit_margin=0.27, trend_direction=0.31)
    )

    assert score.coverage.describe() == "0/2"


def test_evaluator_is_deterministic() -> None:
    evaluator = EarningsEvaluator()
    evidence = _evidence(earnings_growth=0.23)

    assert evaluator.evaluate(evidence) == evaluator.evaluate(evidence)
