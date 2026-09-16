"""Tests for the catalyst evaluator and its rules.

Catalyst is the seventh category to be evaluated. Its question has an answerable
half and an unanswerable one, so these tests describe both: the dates a source
can supply are measured, and the events it cannot supply are named as not
covered rather than approximated.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from contracts.market_data_provider import (
    MarketDataPoint,
    MarketDataSnapshot,
    MarketMetric,
)
from data.yahoo_market_data_provider import _days_until_point
from evaluation.catalyst import dividend_date_rule, earnings_date_rule
from evaluation.catalyst.catalyst_evaluator import CatalystEvaluator
from evaluation.catalyst.catalyst_parts import CatalystPart
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
        (earnings_date_rule.RULE, "catalyst.earnings_date"),
        (dividend_date_rule.RULE, "catalyst.dividend_date"),
    ],
)
def test_each_rule_exists_as_an_enabled_evaluation_rule(rule, rule_id) -> None:
    assert isinstance(rule, EvaluationRule)
    assert rule.id == rule_id
    assert rule.enabled is True


def test_earnings_rule_reports_the_distance_to_the_next_report() -> None:
    result = earnings_date_rule.RULE.execute(_evidence(next_earnings_days=43.0))

    assert result.score == pytest.approx(43.0)
    assert result.evidence_references == ("AAPL.market_data.next_earnings_days",)


def test_dividend_rule_reports_the_distance_to_the_next_ex_dividend_date() -> None:
    result = dividend_date_rule.RULE.execute(_evidence(next_ex_dividend_days=12.0))

    assert result.score == pytest.approx(12.0)
    assert result.evidence_references == ("AAPL.market_data.next_ex_dividend_days",)


@pytest.mark.parametrize("module", [earnings_date_rule, dividend_date_rule])
def test_a_rule_fails_when_no_forthcoming_event_was_retrieved(module) -> None:
    with pytest.raises(DataError):
        module.RULE.execute(_evidence())


@pytest.mark.parametrize("module", [earnings_date_rule, dividend_date_rule])
def test_a_rule_claims_no_evidence_when_no_source_was_consulted(module) -> None:
    result = module.RULE.execute(_no_source_evidence())

    assert "Placeholder" in result.reason
    assert result.evidence_references == ()


# --------------------------------------------------------------------------
# The distance is what makes an event a catalyst
# --------------------------------------------------------------------------


def test_a_forthcoming_date_is_measured_as_a_distance() -> None:
    point = _days_until_point(
        MarketMetric.NEXT_EARNINGS_DAYS,
        (_RETRIEVED_AT + timedelta(days=30)).timestamp(),
        _RETRIEVED_AT,
        "the next quarterly earnings report",
    )

    assert point.value == pytest.approx(30.0)
    assert "30 days" in point.reason


def test_a_date_that_has_passed_is_not_a_forthcoming_event() -> None:
    # A negative distance would read as an event behind us rather than as an
    # event that is not coming, so it is reported as absent.
    point = _days_until_point(
        MarketMetric.NEXT_EARNINGS_DAYS,
        (_RETRIEVED_AT - timedelta(days=5)).timestamp(),
        _RETRIEVED_AT,
        "the next quarterly earnings report",
    )

    assert point.value is None
    assert "has already passed" in point.reason


def test_a_missing_date_is_reported_with_its_reason() -> None:
    point = _days_until_point(
        MarketMetric.NEXT_EX_DIVIDEND_DAYS,
        None,
        _RETRIEVED_AT,
        "the next ex-dividend date",
    )

    assert point.value is None
    assert "did not report the next ex-dividend date" in point.reason


# --------------------------------------------------------------------------
# The evaluator
# --------------------------------------------------------------------------


def test_evaluator_produces_a_catalyst_category_score() -> None:
    score = CatalystEvaluator().evaluate(
        _evidence(next_earnings_days=43.0, next_ex_dividend_days=12.0)
    )

    assert isinstance(score, CategoryScore)
    assert score.category is Category.CATALYST
    assert len(score.evidence_references) == 2


def test_evaluator_never_claims_the_whole_question_was_answered() -> None:
    # The events no source can date are named in the parts, so coverage can
    # never be complete however much of the calendar was retrieved.
    score = CatalystEvaluator().evaluate(
        _evidence(next_earnings_days=43.0, next_ex_dividend_days=12.0)
    )

    assert score.coverage.describe() == "1/2"
    assert score.coverage.total == len(CatalystPart)
    assert score.coverage.is_complete is False


def test_evaluator_reports_no_coverage_when_nothing_could_be_measured() -> None:
    score = CatalystEvaluator().evaluate(_evidence(beta=1.2))

    assert score.coverage.describe() == "0/2"
    assert score.evidence_references == ()


def test_evaluator_reads_no_other_category_measurement() -> None:
    # Earnings asks what the results said; catalyst asks when the next ones are.
    score = CatalystEvaluator().evaluate(
        _evidence(earnings_growth=0.23, expected_earnings_change=0.18)
    )

    assert score.coverage.describe() == "0/2"


def test_evaluator_is_deterministic() -> None:
    evaluator = CatalystEvaluator()
    evidence = _evidence(next_earnings_days=43.0)

    assert evaluator.evaluate(evidence) == evaluator.evaluate(evidence)
