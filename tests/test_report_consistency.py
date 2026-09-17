"""Tests that the report does not contradict itself.

The report said an asset had a near term catalyst in one line and no clear catalyst
in the near term forty lines below it, about the same calendar from the same run.
It said a valuation was attractive directly above a sentence saying the cash flow
did not support it. Nothing caught either of those, because nothing was checking
the report as a whole — only its parts.

These tests check the whole. They read a rendered report and ask whether its
headline agrees with the sentences underneath it, so that the next disagreement is
found by a test and not by somebody reading their own report carefully.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from analysis.analysis_result import AnalysisResult
from analysis.insight.builder import build_insights, insight_for
from analysis.mobile_report import render_mobile_report
from contracts.market_data_provider import (
    MarketDataPoint,
    MarketDataSnapshot,
    MarketMetric,
)
from evaluation.hpo.opportunity_assessor import OpportunityAssessor
from evaluation.reading.category import read_category
from evaluation.reading.windows import NEAR_TERM_DAYS, is_near_term
from models.asset import Asset
from models.asset_profile import AssetProfile
from models.catalyst_event import CatalystEvent, CatalystEventKind
from models.category import CATEGORY_ORDER, Category
from models.category_score import CategoryScore
from models.coverage import Coverage
from models.decision_state import DecisionState
from models.opportunity_assessment import OpportunityCondition
from models.overall_assessment import OverallAssessment
from models.recommendation import Recommendation

_NOW = datetime(2026, 9, 16, 3, 20, 0, tzinfo=UTC)

# Sentences a category may be projected with that **deny** a condition claiming the
# category reads well. They are the statements that would make the report
# contradict itself, and every one of them was either seen in a real report or found
# by this test. A sentence that merely qualifies a good reading — "momentum has
# faded while the longer structure holds" — is not a denial and is not here.
_CONTRADICTIONS: dict[OpportunityCondition, tuple[str, ...]] = {
    OpportunityCondition.VALUATION: (
        "估值偏高",
        "缺少现金收益支撑",
    ),
    OpportunityCondition.TREND: (
        "趋势结构已经走坏",
        "尚未出现止跌信号",
    ),
    OpportunityCondition.RISK: (
        "负债水平偏高",
        "短期偿债能力偏紧",
    ),
    OpportunityCondition.POSITIONING: ("空头持仓较重",),
}

# Real values, kept because they are what produced the contradiction.
_APPLE: dict[str, float] = {
    "pe": 38.24,
    "peg": 2.67,
    "ev_ebitda": 28.92,
    "fcf_yield": 0.022,
    "beta": 1.08,
    "debt_to_equity": 78.44,
    "current_ratio": 1.0,
    "profit_margin": 0.276,
    "return_on_equity": 1.488,
    "free_cash_flow_margin": 0.231,
    "market_direction": 0.149,
    "trend_ma20_gap": 0.03,
    "trend_ma60_gap": 0.02,
    "trend_ma120_gap": 0.01,
    "trend_macd": 0.004,
    "trend_rsi": 58.0,
    "trend_volume_ratio": 0.05,
    "risk_volatility": 0.231,
    "risk_drawdown": -0.138,
    "short_percent_of_float": 0.0096,
    "short_ratio": 2.97,
    "institutional_ownership": 0.663,
    "insider_ownership": 0.0165,
}

# The valuation that was called attractive while its cash flow was negative.
_BABA: dict[str, float] = {
    **_APPLE,
    "pe": 24.44,
    "peg": 0.51,
    "ev_ebitda": 2.02,
    "fcf_yield": -0.307,
    "profit_margin": 0.070,
    "free_cash_flow_margin": -0.079,
    "trend_ma20_gap": -0.05,
    "trend_ma60_gap": -0.06,
    "trend_ma120_gap": -0.07,
    "trend_macd": -0.02,
    "trend_rsi": 38.0,
    "risk_volatility": 0.369,
    "risk_drawdown": -0.499,
    "institutional_ownership": 0.10,
}


def _snapshot(values: dict[str, float]) -> MarketDataSnapshot:
    return MarketDataSnapshot(
        symbol="AAPL",
        source="Test source",
        retrieved_at=_NOW,
        points=tuple(
            MarketDataPoint(
                metric=metric,
                value=values.get(metric.value),
                reason="test reason",
            )
            for metric in MarketMetric
        ),
    )


def _event(kind: CatalystEventKind, days: int) -> CatalystEvent:
    return CatalystEvent(
        kind=kind,
        occurs_on=_NOW.date() + timedelta(days=days),
        source="Test source",
        confirmed=True,
        description="",
        symbol="AAPL",
    )


def _result(
    values: dict[str, float], events: tuple[CatalystEvent, ...] = ()
) -> AnalysisResult:
    """Return a result with readings, insights and the opportunity judgement built."""
    snapshot = _snapshot(values)
    result = AnalysisResult(
        asset=Asset(
            ticker="AAPL",
            name="Apple Inc.",
            exchange="NASDAQ",
            currency="USD",
            profile=AssetProfile.MATURE_TECH,
        ),
        assessment=OverallAssessment(
            overall_score=1.0,
            confidence=1.0,
            grade="PLACEHOLDER",
            category_scores=tuple(
                CategoryScore(
                    category=category,
                    score=1.0,
                    confidence=1.0,
                    coverage=Coverage(assessed=1, total=1),
                    summary="summary",
                    evidence_references=(f"AAPL.market_data.{category.value}",),
                )
                for category in CATEGORY_ORDER
                if category is not Category.HPO
            ),
        ),
        recommendation=Recommendation(
            decision_state=DecisionState.WATCH,
            confidence=1.0,
            investment_thesis="Placeholder.",
            evidence_references=("AAPL.market_data.pe",),
        ),
        market_data=snapshot,
        events=events,
    )
    readings = {
        category: read_category(snapshot, category)
        for category in CATEGORY_ORDER
        if category is not Category.HPO
    }
    days = min(
        (event.days_from(_NOW) for event in events if not event.is_mechanical),
        default=None,
    )
    from dataclasses import replace

    result = replace(result, opportunity=OpportunityAssessor().assess(readings, days))
    return replace(result, insights=build_insights(result))


def _report(values: dict[str, float], events: tuple[CatalystEvent, ...] = ()) -> str:
    return render_mobile_report(_result(values, events), generated_at=_NOW)


def _condition_state(
    result: AnalysisResult, condition: OpportunityCondition
) -> bool | None:
    assert result.opportunity is not None
    return next(
        entry.satisfied
        for entry in result.opportunity.conditions
        if entry.condition is condition
    )


# --------------------------------------------------------------------------
# The headline agrees with the sentences under it
# --------------------------------------------------------------------------


@pytest.mark.parametrize("values", [_APPLE, _BABA], ids=["apple", "baba"])
def test_a_condition_that_holds_is_not_contradicted_by_its_category(
    values: dict[str, float],
) -> None:
    # The failure this replaces: the headline claimed a valuation was attractive
    # while the valuation sentence said the cash flow did not support it.
    events = (_event(CatalystEventKind.EARNINGS, 3),)
    result = _result(values, events)
    report = _report(values, events)

    for condition, phrases in _CONTRADICTIONS.items():
        if _condition_state(result, condition) is not True:
            continue
        for phrase in phrases:
            assert (
                phrase not in report
            ), f"{condition.value} holds while the report says {phrase!r}"


def test_the_valuation_that_was_called_attractive_is_no_longer_given_that_label() -> (
    None
):
    # Cheap multiples and a negative cash flow yield: the average reads well and
    # one reading does not, which is the case the mean could not see.
    events = (_event(CatalystEventKind.EARNINGS, 3),)

    assert (
        _condition_state(_result(_BABA, events), OpportunityCondition.VALUATION)
        is False
    )


def test_a_condition_fails_on_the_reading_that_disqualifies_it() -> None:
    # Apple's current ratio reads tight, so risk does not hold. The asset is not
    # being called risky; the balance sheet is being read, and one reading falls
    # below the bar the condition is set at.
    events = (_event(CatalystEventKind.EARNINGS, 3),)
    result = _result(_APPLE, events)
    report = _report(_APPLE, events)

    assert _condition_state(result, OpportunityCondition.VALUATION) is False
    assert _condition_state(result, OpportunityCondition.RISK) is False
    risk = insight_for(result, Category.RISK)
    assert risk is not None
    assert "短期偿债能力偏紧" in " ".join(line.text for line in risk.lines)
    assert "风险可控" not in report


# --------------------------------------------------------------------------
# The catalyst window is one window
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "days", [1, 7, 8, 29, NEAR_TERM_DAYS, NEAR_TERM_DAYS + 1, 90, 200, 400]
)
def test_the_headline_and_the_sentence_agree_about_the_near_term(days: int) -> None:
    # The failure this replaces: an asset with an event forty three days away was
    # given the near term catalyst condition while the sentence forty lines below
    # said there was no clear catalyst in the near term.
    events = (_event(CatalystEventKind.EARNINGS, days),)
    result = _result(_APPLE, events)
    report = _report(_APPLE, events)

    satisfied = _condition_state(result, OpportunityCondition.CATALYST)
    sentence_says_none_near = "近期暂无明确催化" in report

    assert satisfied is is_near_term(days)
    assert sentence_says_none_near is (not is_near_term(days)), (
        f"{days} days away: condition={satisfied}, "
        f"sentence says nothing near={sentence_says_none_near}"
    )


def test_the_condition_and_the_sentence_read_one_window() -> None:
    # Both take the boundary from the reading layer, so moving it moves both.
    events = (_event(CatalystEventKind.EARNINGS, NEAR_TERM_DAYS),)

    assert (
        _condition_state(_result(_APPLE, events), OpportunityCondition.CATALYST) is True
    )


# --------------------------------------------------------------------------
# A mean cannot hide a disqualifying reading
# --------------------------------------------------------------------------


def test_a_category_with_a_disqualifying_reading_never_holds_its_condition() -> None:
    # Every category that has a condition, checked against the weakest value its
    # scale can return while the mean still reads well.
    from evaluation.reading.conditions import OPPORTUNITY_CONDITIONS

    for category, bar in OPPORTUNITY_CONDITIONS.items():
        values = dict(_APPLE)
        if category is Category.VALUATION:
            values.update({"pe": 10.0, "peg": 0.8, "ev_ebitda": 6.0, "fcf_yield": -0.3})
        elif category is Category.TREND:
            values.update(
                {
                    "trend_ma20_gap": 0.20,
                    "trend_ma60_gap": 0.20,
                    "trend_ma120_gap": 0.20,
                    "trend_macd": -0.20,
                    "trend_rsi": 55.0,
                    "trend_volume_ratio": 0.0,
                }
            )
        elif category is Category.RISK:
            values.update(
                {
                    "beta": 0.5,
                    "risk_volatility": 0.1,
                    "risk_drawdown": -0.01,
                    "debt_to_equity": 400.0,
                    "current_ratio": 3.0,
                }
            )
        else:
            # A crowded short side beside an empty one: the mean still reads well
            # and one reading does not, which is the case being tested.
            values.update({"short_percent_of_float": 0.01, "short_ratio": 8.0})

        reading = read_category(_snapshot(values), category)
        if not reading.is_empty:
            assert reading.weakest_score is not None
            assert reading.weakest_score < bar.least_weakest, category


def test_the_report_shows_no_score_of_its_own() -> None:
    # HPO is a count of conditions and never a number, and the reading layer's
    # scores stay behind it.
    report = _report(_APPLE, (_event(CatalystEventKind.EARNINGS, 3),))

    assert "13.10" not in report
    assert "概率" not in report
