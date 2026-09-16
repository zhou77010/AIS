"""Tests for the trend evaluator and its rules.

Trend is the fifth category to be evaluated. These tests describe what the
category measures, that the window travels with the measurement, and that the
category reports how much of price behaviour it could not see.
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
from evaluation.trend import direction_rule, position_rule
from evaluation.trend.trend_aspects import TrendAspect
from evaluation.trend.trend_evaluator import TrendEvaluator
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
        (position_rule.RULE, "trend.position"),
        (direction_rule.RULE, "trend.direction"),
    ],
)
def test_each_rule_exists_as_an_enabled_evaluation_rule(rule, rule_id) -> None:
    assert isinstance(rule, EvaluationRule)
    assert rule.id == rule_id
    assert rule.enabled is True


def test_position_rule_reports_where_the_price_sits_in_its_range() -> None:
    result = position_rule.RULE.execute(_evidence(trend_range_position=0.78))

    assert result.score == pytest.approx(0.78)
    assert result.evidence_references == ("AAPL.market_data.trend_range_position",)


def test_direction_rule_reports_the_change_over_the_window() -> None:
    result = direction_rule.RULE.execute(_evidence(trend_direction=0.31))

    assert result.score == pytest.approx(0.31)
    assert result.evidence_references == ("AAPL.market_data.trend_direction",)


@pytest.mark.parametrize("module", [position_rule, direction_rule])
def test_a_rule_fails_when_the_source_did_not_provide_its_measurement(module) -> None:
    with pytest.raises(DataError):
        module.RULE.execute(_evidence())


@pytest.mark.parametrize("module", [position_rule, direction_rule])
def test_a_rule_claims_no_evidence_when_no_source_was_consulted(module) -> None:
    result = module.RULE.execute(_no_source_evidence())

    assert "Placeholder" in result.reason
    assert result.evidence_references == ()


def test_the_window_travels_with_every_measurement_name() -> None:
    # A trend means nothing without the window it was measured over, so the
    # window is part of the name rather than something left in the code.
    for metric in (MarketMetric.TREND_RANGE_POSITION, MarketMetric.TREND_DIRECTION):
        assert "52 week" in metric.label


def test_evaluator_produces_a_trend_category_score() -> None:
    score = TrendEvaluator().evaluate(
        _evidence(trend_range_position=0.78, trend_direction=0.31)
    )

    assert isinstance(score, CategoryScore)
    assert score.category is Category.TREND
    assert score.coverage.describe() == "2/3"


def test_evaluator_coverage_names_the_aspect_it_cannot_see() -> None:
    score = TrendEvaluator().evaluate(_evidence(trend_range_position=0.78))

    assert score.coverage.describe() == "1/3"
    assert score.coverage.total == len(TrendAspect)
    assert score.coverage.is_complete is False


def test_evaluator_reports_no_coverage_when_nothing_could_be_measured() -> None:
    score = TrendEvaluator().evaluate(_evidence(market_direction=0.14))

    assert score.coverage.describe() == "0/3"
    assert score.evidence_references == ()


def test_evaluator_is_deterministic() -> None:
    evaluator = TrendEvaluator()
    evidence = _evidence(trend_range_position=0.78)

    assert evaluator.evaluate(evidence) == evaluator.evaluate(evidence)
