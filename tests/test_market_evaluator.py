"""Tests for the market evaluator and its rule.

Market is the fourth category to be evaluated. Its evidence is thin, and these
tests describe both what it measures and that it reports how little of the
environment it covers.
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
from evaluation.market import market_direction_rule
from evaluation.market.market_aspects import MarketAspect
from evaluation.market.market_evaluator import MarketEvaluator
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


def test_the_rule_exists_as_an_enabled_evaluation_rule() -> None:
    rule = market_direction_rule.RULE

    assert isinstance(rule, EvaluationRule)
    assert rule.id == "market.direction"
    assert rule.enabled is True


def test_rule_reports_the_broad_market_change() -> None:
    result = market_direction_rule.RULE.execute(_evidence(market_direction=0.14))

    assert result.score == pytest.approx(0.14)
    assert result.evidence_references == ("AAPL.market_data.market_direction",)


def test_rule_fails_when_the_source_did_not_provide_the_measurement() -> None:
    with pytest.raises(DataError):
        market_direction_rule.RULE.execute(_evidence())


def test_rule_claims_no_evidence_when_no_source_was_consulted() -> None:
    result = market_direction_rule.RULE.execute(_no_source_evidence())

    assert "Placeholder" in result.reason
    assert result.evidence_references == ()


def test_evaluator_produces_a_market_category_score() -> None:
    score = MarketEvaluator().evaluate(_evidence(market_direction=0.14))

    assert isinstance(score, CategoryScore)
    assert score.category is Category.MARKET
    assert score.coverage.total == len(MarketAspect)


def test_evaluator_reports_how_little_of_the_environment_it_covers() -> None:
    # One aspect of four. Reporting one of one would claim the environment had been
    # examined when almost none of it had.
    score = MarketEvaluator().evaluate(_evidence(market_direction=0.14))

    assert score.coverage.describe() == "1/4"
    assert score.coverage.is_complete is False


def test_evaluator_reports_no_coverage_when_nothing_could_be_measured() -> None:
    score = MarketEvaluator().evaluate(_evidence(pe=26.8))

    assert score.coverage.describe() == "0/4"
    assert score.evidence_references == ()


def test_a_placeholder_is_not_an_assessed_aspect() -> None:
    # A run with no source at all produces a placeholder per rule so that the
    # pipeline stays deterministic. Nothing was read, so nothing is covered: a
    # placeholder counted as coverage would report the environment as examined when
    # not one measurement of it exists.
    score = MarketEvaluator().evaluate(_no_source_evidence())

    assert score.coverage.describe() == "0/4"
    assert score.evidence_references == ()


def test_evaluator_reads_no_other_category_measurement() -> None:
    score = MarketEvaluator().evaluate(_evidence(beta=1.2, profit_margin=0.27))

    assert score.coverage.describe() == "0/4"


def test_evaluator_is_deterministic() -> None:
    evaluator = MarketEvaluator()
    evidence = _evidence(market_direction=0.14)

    assert evaluator.evaluate(evidence) == evaluator.evaluate(evidence)
