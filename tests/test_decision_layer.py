"""Tests for the Decision Layer: one answer, from judgements already formed.

The requirement this file exists for is one sentence long: the layer answers **whether
this asset is worth becoming a standard position today**, using judgements other layers
have already reached, and it names which condition it could not get past.

So the tests below are about three things. The answer follows the conditions. The answer
distinguishes "not favourable" from "could not be answered", because stating a no for a
question nobody could answer would be claiming an answer that was never reached. And the
bars are not in this layer: they are read from Policy, so that changing what "reads well
enough" means is a change in one place.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from analysis.analysis_result import AnalysisResult
from config.decision_policy import BARS, CONDITION_CATEGORY
from contracts.market_data_provider import (
    MarketDataPoint,
    MarketDataSnapshot,
    MarketMetric,
)
from evaluation.decision.decision_assessor import DecisionAssessor
from models.asset import Asset
from models.asset_profile import AssetProfile
from models.category import CATEGORY_ORDER, Category
from models.category_score import CategoryScore
from models.coverage import Coverage
from models.decision_result import (
    DecisionCondition,
    DecisionOutcome,
    DecisionResult,
)
from models.decision_state import DecisionState
from models.overall_assessment import OverallAssessment
from models.recommendation import Recommendation

_MOMENT = datetime(2026, 9, 23, 1, 0, tzinfo=UTC)

# A valuation that reads well on every measurement, and a risk profile that does too.
_GOOD: dict[str, float] = {
    "pe": 12.0,
    "peg": 1.0,
    "ev_ebitda": 8.0,
    "fcf_yield": 0.06,
    "beta": 0.9,
    "risk_volatility": 0.20,
    "risk_drawdown": -0.05,
}

# The same asset with a valuation nothing could call cheap, and a risk profile that
# reads
# badly on every measurement.
_POOR: dict[str, float] = {
    "pe": 90.0,
    "peg": 4.0,
    "ev_ebitda": 30.0,
    "fcf_yield": 0.0,
    "beta": 2.5,
    "risk_volatility": 0.9,
    "risk_drawdown": -0.6,
}


def _snapshot(values: dict[str, float]) -> MarketDataSnapshot:
    """Return a snapshot holding the given measurements and one point per metric."""
    return MarketDataSnapshot(
        symbol="AAPL",
        source="Test source",
        retrieved_at=_MOMENT,
        points=tuple(
            MarketDataPoint(
                metric=metric,
                value=values.get(metric.value),
                reason=f"Test source: {metric.value}",
            )
            for metric in MarketMetric
        ),
    )


def _result(values: dict[str, float], *, data: bool = True) -> AnalysisResult:
    """Return a result carrying judgements already reached, as a run produces them."""
    snapshot = _snapshot(values) if data else None
    return AnalysisResult(
        asset=Asset(
            ticker="AAPL",
            name="Apple Inc.",
            exchange="NASDAQ",
            currency="USD",
            profile=AssetProfile.UNKNOWN,
        ),
        assessment=OverallAssessment(
            overall_score=0.0,
            confidence=1.0,
            grade="PLACEHOLDER",
            category_scores=tuple(
                CategoryScore(
                    category=category,
                    score=4.0,
                    confidence=1.0,
                    coverage=Coverage(assessed=1, total=1),
                    summary="summary",
                    evidence_references=(f"AAPL.{category.value}.pe",),
                )
                for category in CATEGORY_ORDER
                if category is not Category.HPO
            ),
        ),
        recommendation=Recommendation(
            decision_state=DecisionState.WATCH,
            confidence=1.0,
            investment_thesis="Placeholder decision.",
            evidence_references=(),
        ),
        market_data=snapshot,
    )


def _decide(values: dict[str, float], *, data: bool = True) -> DecisionResult:
    return DecisionAssessor().assess(_result(values, data=data))


# --------------------------------------------------------------------------
# The answer follows the conditions
# --------------------------------------------------------------------------


def test_an_asset_that_clears_every_condition_is_answered_favourably() -> None:
    decision = _decide(_GOOD)

    assert decision.outcome is DecisionOutcome.FAVOURABLE
    assert all(outcome.satisfied for outcome in decision.conditions)


def test_a_valuation_that_reads_badly_is_named_rather_than_averaged_away() -> None:
    decision = _decide(_POOR)

    assert decision.outcome is DecisionOutcome.NOT_FAVOURABLE
    terms = decision.outcome_for(DecisionCondition.TERMS)
    assert terms is not None and terms.satisfied is False
    assert "valuation" in terms.reason


def test_a_run_with_no_data_cannot_answer_rather_than_answering_no() -> None:
    decision = _decide({}, data=False)

    assert decision.outcome is DecisionOutcome.CANNOT_ANSWER
    assert "not evaluated" in decision.summary


def test_the_answer_says_which_condition_failed() -> None:
    # The point of the layer: a reader can disagree with the reason, not only with the
    # verdict. A verdict with no named condition cannot be argued with.
    decision = _decide(_POOR)

    assert "does not hold" in decision.summary
    assert "terms" in decision.summary and "risk" in decision.summary
    # And each condition's own line says what it was read from, so "terms" is not left
    # to
    # the reader to decode.
    reasons = " ".join(outcome.reason for outcome in decision.conditions)
    assert "valuation" in reasons and "risk" in reasons


def test_a_good_reading_the_rest_of_which_is_missing_cannot_be_answered() -> None:
    # Not evaluated is not failed: a valuation with one good measurement clears its
    # condition, while a risk judgement that was never made leaves the question open.
    decision = _decide({"pe": 12.0})

    terms = decision.outcome_for(DecisionCondition.TERMS)
    risk = decision.outcome_for(DecisionCondition.RISK)

    assert terms is not None and terms.satisfied is True
    assert risk is not None and risk.satisfied is None
    assert decision.outcome is DecisionOutcome.CANNOT_ANSWER


def test_a_run_without_the_risk_category_cannot_answer() -> None:
    decision = _decide({"pe": 12.0, "peg": 1.0, "ev_ebitda": 8.0, "fcf_yield": 0.06})

    risk = decision.outcome_for(DecisionCondition.RISK)
    assert risk is not None and risk.satisfied is None
    assert decision.outcome is DecisionOutcome.CANNOT_ANSWER


# --------------------------------------------------------------------------
# What the layer rests on, and what it must not hold itself
# --------------------------------------------------------------------------


def test_the_answer_carries_the_evidence_of_the_judgements_it_rests_on() -> None:
    decision = _decide(_GOOD)

    assert "AAPL.valuation.pe" in decision.evidence_references
    assert "AAPL.risk.pe" in decision.evidence_references


def test_every_condition_is_answered_and_every_condition_has_a_bar() -> None:
    # The Necessary Set is three conditions, and Policy has to cover all of them: a
    # condition with no bar would be one the layer silently decides for itself.
    assert set(CONDITION_CATEGORY) | {DecisionCondition.CURRENCY} == set(
        DecisionCondition
    )
    assert set(BARS) == set(CONDITION_CATEGORY)


def test_the_layer_holds_no_bar_of_its_own() -> None:
    # The bars live in Policy. This test states the boundary rather than the numbers: if
    # a
    # bar moves in Policy, the answer moves with it, and nothing here has to change.
    assessor = DecisionAssessor()

    assert not hasattr(assessor, "_bar")
    assert BARS[DecisionCondition.TERMS].least_mean > 0
    assert BARS[DecisionCondition.RISK].least_mean > 0


@pytest.mark.parametrize("condition", list(DecisionCondition))
def test_a_condition_outcome_always_explains_itself(
    condition: DecisionCondition,
) -> None:
    decision = _decide(_GOOD)

    outcome = decision.outcome_for(condition)
    assert outcome is not None
    assert outcome.reason
