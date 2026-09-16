"""Tests for the positioning evaluator and its rules.

Positioning is the eighth category to be evaluated. It asks who else holds the
asset and how crowded that is, so these tests describe both halves of the
question, and describe that flow — which no connected source reports — is named
as not covered rather than approximated.
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
from evaluation.positioning import (
    insider_rule,
    institutional_rule,
    short_interest_rule,
    short_ratio_rule,
)
from evaluation.positioning.positioning_evaluator import PositioningEvaluator
from evaluation.positioning.positioning_parts import PositioningPart
from evidence.evidence_collection import EvidenceCollection
from models.asset import Asset
from models.asset_profile import AssetProfile
from models.category import Category
from models.category_score import CategoryScore
from pipeline.evidence_builder import EvidenceBuilder
from utils.exceptions import DataError

_RETRIEVED_AT = datetime(2026, 9, 16, 3, 20, 0, tzinfo=UTC)

_RULES = (
    (institutional_rule.RULE, "positioning.institutional"),
    (insider_rule.RULE, "positioning.insider"),
    (short_interest_rule.RULE, "positioning.short_interest"),
    (short_ratio_rule.RULE, "positioning.short_ratio"),
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


@pytest.mark.parametrize(("rule", "rule_id"), _RULES)
def test_each_rule_exists_as_an_enabled_evaluation_rule(rule, rule_id) -> None:
    assert isinstance(rule, EvaluationRule)
    assert rule.id == rule_id
    assert rule.enabled is True


def test_institutional_rule_reports_the_institutional_holding() -> None:
    result = institutional_rule.RULE.execute(_evidence(institutional_ownership=0.66))

    assert result.score == pytest.approx(0.66)
    assert result.evidence_references == ("AAPL.market_data.institutional_ownership",)


def test_insider_rule_reports_the_insider_holding() -> None:
    result = insider_rule.RULE.execute(_evidence(insider_ownership=0.016))

    assert result.score == pytest.approx(0.016)
    assert result.evidence_references == ("AAPL.market_data.insider_ownership",)


def test_short_interest_rule_reports_the_share_of_float_sold_short() -> None:
    result = short_interest_rule.RULE.execute(_evidence(short_percent_of_float=0.0096))

    assert result.score == pytest.approx(0.0096)


def test_short_ratio_rule_reports_the_days_needed_to_cover() -> None:
    result = short_ratio_rule.RULE.execute(_evidence(short_ratio=2.97))

    assert result.score == pytest.approx(2.97)


@pytest.mark.parametrize(("rule", "rule_id"), _RULES)
def test_a_rule_fails_when_the_source_did_not_provide_its_measurement(
    rule, rule_id
) -> None:
    with pytest.raises(DataError):
        rule.execute(_evidence())


@pytest.mark.parametrize(("rule", "rule_id"), _RULES)
def test_a_rule_claims_no_evidence_when_no_source_was_consulted(rule, rule_id) -> None:
    result = rule.execute(_no_source_evidence())

    assert "Placeholder" in result.reason
    assert result.evidence_references == ()


# --------------------------------------------------------------------------
# The evaluator
# --------------------------------------------------------------------------


def _full(**overrides: float) -> EvidenceCollection:
    values = {
        "institutional_ownership": 0.66,
        "insider_ownership": 0.016,
        "short_percent_of_float": 0.0096,
        "short_ratio": 2.97,
    }
    values.update(overrides)
    return _evidence(**values)


def test_evaluator_produces_a_positioning_category_score() -> None:
    score = PositioningEvaluator().evaluate(_full())

    assert isinstance(score, CategoryScore)
    assert score.category is Category.POSITIONING
    assert len(score.evidence_references) == 4


def test_evaluator_never_claims_the_whole_question_was_answered() -> None:
    # Fund flow, options positioning and sentiment are parts of the question
    # with no connected source, so coverage can never be complete.
    score = PositioningEvaluator().evaluate(_full())

    assert score.coverage.describe() == "2/3"
    assert score.coverage.total == len(PositioningPart)
    assert score.coverage.is_complete is False


def test_evaluator_reports_partial_coverage_when_only_ownership_was_measured() -> None:
    score = PositioningEvaluator().evaluate(
        _evidence(institutional_ownership=0.66, insider_ownership=0.016)
    )

    assert score.coverage.describe() == "1/3"


def test_evaluator_reports_no_coverage_when_nothing_could_be_measured() -> None:
    score = PositioningEvaluator().evaluate(_evidence(beta=1.2))

    assert score.coverage.describe() == "0/3"
    assert score.evidence_references == ()


def test_evaluator_reads_no_other_category_measurement() -> None:
    # How many shares trade belongs to Risk, and what the price has done belongs
    # to Trend. Neither answers who is holding.
    score = PositioningEvaluator().evaluate(
        _evidence(average_volume=53_800_000.0, trend_direction=0.31)
    )

    assert score.coverage.describe() == "0/3"


def test_evaluator_is_deterministic() -> None:
    evaluator = PositioningEvaluator()
    evidence = _full()

    assert evaluator.evaluate(evidence) == evaluator.evaluate(evidence)
