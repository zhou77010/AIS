"""Tests for the insight layer.

An insight is an interpretation of evidence that has already been collected. It
is not a summary and it is not a forecast. These tests describe all three: what
each category says about its own evidence, that every sentence can name the
evidence it came from, and that nothing in the layer predicts anything.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from analysis.analysis_result import AnalysisResult
from analysis.insight.builder import build_insights, insight_for
from contracts.market_data_provider import (
    MarketDataPoint,
    MarketDataSnapshot,
    MarketMetric,
)
from models.asset import Asset
from models.asset_profile import AssetProfile
from models.catalyst_event import (
    CATALYST_EVENT_PRIORITY,
    CatalystEvent,
    CatalystEventKind,
)
from models.category import CATEGORY_ORDER, Category
from models.category_score import CategoryScore
from models.coverage import Coverage
from models.decision_state import DecisionState
from models.insight import InsightLine
from models.overall_assessment import OverallAssessment
from models.recommendation import Recommendation

# The moment the fixtures are dated from, and the moment the calendar fixtures fall
# relative to. It follows the real clock rather than a constant, because a result
# that carries no market data is read against the current moment: dated from a fixed
# day, these fixtures passed on the day they were written and started failing once
# that day left the catalyst window.
_MOMENT = datetime.now(UTC)


def _asset() -> Asset:
    return Asset(
        ticker="NVDA",
        name="NVDA",
        exchange="NASDAQ",
        currency="USD",
        profile=AssetProfile.HIGH_GROWTH,
    )


def _result(
    categories: tuple[Category, ...],
    *,
    market_data: MarketDataSnapshot | None = None,
    events: tuple[CatalystEvent, ...] = (),
) -> AnalysisResult:
    """Return an analysis result with its insights built, as the analyzer does."""
    result = AnalysisResult(
        asset=_asset(),
        assessment=OverallAssessment(
            overall_score=13.10,
            confidence=1.0,
            grade="PLACEHOLDER",
            category_scores=tuple(
                CategoryScore(
                    category=category,
                    score=13.10,
                    confidence=1.0,
                    coverage=Coverage(assessed=1, total=1),
                    summary="summary",
                    evidence_references=(f"NVDA.market_data.{category.value}",),
                )
                for category in categories
            ),
        ),
        recommendation=Recommendation(
            decision_state=DecisionState.WATCH,
            confidence=1.0,
            investment_thesis="Placeholder decision.",
            evidence_references=("NVDA.market_data.pe",),
        ),
        market_data=market_data,
        events=events,
    )
    return replace(result, insights=build_insights(result))


def _snapshot(**values: float) -> MarketDataSnapshot:
    return MarketDataSnapshot(
        symbol="NVDA",
        source="Test source",
        retrieved_at=_MOMENT,
        points=tuple(
            MarketDataPoint(
                metric=metric,
                value=values.get(metric.value),
                reason="test reason",
            )
            for metric in MarketMetric
        ),
    )


def _insight(category: Category, **values: float):
    """Return the insight built for one category from the given measurements."""
    result = _result((category,), market_data=_snapshot(**values))
    return insight_for(result, category)


def _text(insight) -> str:
    return " ".join(line.text for line in insight.lines) if insight else ""


# --------------------------------------------------------------------------
# What an insight is
# --------------------------------------------------------------------------


def test_a_line_that_cannot_name_its_evidence_is_refused() -> None:
    # The alternative is an opinion presented as a reading.
    with pytest.raises(ValueError):
        InsightLine("趋势向好。", ())


def test_every_line_names_the_evidence_behind_it() -> None:
    insight = _insight(
        Category.TREND,
        trend_ma20_gap=0.03,
        trend_ma60_gap=0.02,
        trend_ma120_gap=0.01,
        trend_macd=0.02,
    )

    assert insight.lines
    for line in insight.lines:
        assert line.references, line.text
    assert "NVDA.market_data.trend_ma120_gap" in insight.references


def test_only_the_measurements_a_line_was_read_from_are_cited() -> None:
    insight = _insight(
        Category.TREND,
        trend_ma20_gap=0.03,
        trend_ma60_gap=0.02,
        trend_ma120_gap=0.01,
        trend_macd=0.02,
    )
    structure, momentum = insight.lines[0], insight.lines[1]

    assert structure.references == (
        "NVDA.market_data.trend_ma20_gap",
        "NVDA.market_data.trend_ma60_gap",
        "NVDA.market_data.trend_ma120_gap",
    )
    assert momentum.references == ("NVDA.market_data.trend_macd",)


def test_a_category_with_no_evidence_says_nothing() -> None:
    assert _insight(Category.TREND) is None
    assert _insight(Category.RISK) is None
    assert _insight(Category.VALUATION) is None


def test_an_insight_is_never_empty_when_it_is_built() -> None:
    result = _result(tuple(CATEGORY_ORDER), market_data=_snapshot(pe=20.0, beta=1.1))

    for insight in build_insights(result):
        assert not insight.is_empty


# --------------------------------------------------------------------------
# Interpretation, not prediction
# --------------------------------------------------------------------------

# Wording that would turn an interpretation into a forecast. None of it may
# appear, because AIS cannot support any of it from evidence it holds.
_FORECASTING = ("预计上涨", "预计会", "将会", "必然", "一定会上涨", "目标价", "概率")


@pytest.mark.parametrize(
    ("category", "values"),
    [
        (Category.TREND, {"trend_ma20_gap": 0.05, "trend_ma60_gap": 0.04}),
        (Category.TREND, {"trend_ma20_gap": -0.05, "trend_ma60_gap": -0.04}),
        (Category.RISK, {"beta": 2.2, "risk_volatility": 0.6, "risk_drawdown": -0.5}),
        (Category.VALUATION, {"pe": 38.0, "peg": 2.7, "ev_ebitda": 29.0}),
        (Category.VALUATION, {"pe": 9.0, "earnings_growth": 0.4}),
        (Category.FUNDAMENTAL, {"profit_margin": 0.3, "free_cash_flow_margin": -0.1}),
        (Category.MARKET, {"market_direction": -0.2}),
        (Category.POSITIONING, {"short_percent_of_float": 0.2, "short_ratio": 6.0}),
        (Category.EARNINGS, {"earnings_growth": -0.2, "expected_earnings_change": 0.3}),
    ],
)
def test_an_insight_never_predicts(category, values) -> None:
    text = _text(_insight(category, **values))

    assert text
    for phrase in _FORECASTING:
        assert phrase not in text, phrase


def test_the_catalyst_insight_never_calls_an_event_the_nearest_one() -> None:
    # Distance is not importance, so the wording that confuses them is banned.
    result = _result(
        (Category.CATALYST,),
        events=(
            _event(CatalystEventKind.EARNINGS, 40),
            _event(CatalystEventKind.FOMC, 2),
        ),
    )

    text = _text(insight_for(result, Category.CATALYST))

    assert "最近" not in text


# --------------------------------------------------------------------------
# Each category reads its own evidence
# --------------------------------------------------------------------------


def test_the_trend_insight_reads_its_moving_averages() -> None:
    above = _text(
        _insight(
            Category.TREND,
            trend_ma20_gap=0.06,
            trend_ma60_gap=0.06,
            trend_ma120_gap=0.03,
        )
    )
    below = _text(
        _insight(
            Category.TREND,
            trend_ma20_gap=-0.10,
            trend_ma60_gap=-0.10,
            trend_ma120_gap=-0.15,
        )
    )

    assert "站稳全部均线" in above
    assert "跌破全部均线" in below


def test_a_falling_momentum_under_an_intact_structure_reads_as_slowing() -> None:
    # The clause that needs two measurements to say: momentum fading while the
    # longer structure still holds is a different thing from a broken trend.
    text = _text(
        _insight(
            Category.TREND,
            trend_ma20_gap=0.02,
            trend_ma60_gap=0.01,
            trend_ma120_gap=0.03,
            trend_macd=-0.02,
        )
    )

    assert "结构尚未破坏" in text


def test_the_risk_insight_says_where_the_risk_comes_from() -> None:
    text = _text(
        _insight(
            Category.RISK,
            beta=2.2,
            risk_volatility=0.55,
            debt_to_equity=17.0,
            current_ratio=4.6,
        )
    )

    assert "风险主要来自价格波动，而非财务质量" in text


def test_the_risk_insight_says_when_the_balance_sheet_is_the_risk() -> None:
    text = _text(_insight(Category.RISK, debt_to_equity=180.0, current_ratio=0.8))

    assert "负债水平偏高" in text


def test_the_valuation_insight_reads_the_multiples_together() -> None:
    cheap = _text(_insight(Category.VALUATION, pe=9.0, peg=0.8, ev_ebitda=6.0))
    dear = _text(_insight(Category.VALUATION, pe=45.0, peg=3.2, ev_ebitda=30.0))

    assert "估值偏低" in cheap
    assert "估值偏高" in dear


def test_a_high_multiple_without_the_growth_to_match_it_is_called_out() -> None:
    text = _text(_insight(Category.VALUATION, pe=45.0, earnings_growth=0.02))

    assert "缺少增长匹配" in text


def test_the_fundamental_insight_calls_out_profit_without_cash() -> None:
    # The clause that earns its place: the two halves of the evidence disagree.
    text = _text(
        _insight(
            Category.FUNDAMENTAL,
            profit_margin=0.20,
            free_cash_flow_margin=0.005,
            debt_to_equity=20.0,
            current_ratio=1.8,
        )
    )

    assert "利润质量存疑" in text


def test_the_fundamental_insight_reads_a_sound_business_as_sound() -> None:
    text = _text(
        _insight(
            Category.FUNDAMENTAL,
            profit_margin=0.28,
            free_cash_flow_margin=0.15,
            debt_to_equity=20.0,
            current_ratio=1.8,
        )
    )

    assert "盈利质量较好" in text
    assert "资产负债结构稳健" in text


def test_the_market_insight_reads_the_environment_not_the_asset() -> None:
    rising = _text(_insight(Category.MARKET, market_direction=0.15))
    falling = _text(_insight(Category.MARKET, market_direction=-0.15))

    assert "上行" in rising
    assert "下行" in falling


def test_the_positioning_insight_reads_the_register_and_the_crowding() -> None:
    text = _text(
        _insight(
            Category.POSITIONING,
            institutional_ownership=0.66,
            insider_ownership=0.02,
            short_percent_of_float=0.009,
            short_ratio=1.5,
        )
    )

    assert "筹码以机构为主" in text
    assert "暂未看到明显的拥挤交易" in text


def test_the_earnings_insight_calls_out_a_disagreement() -> None:
    text = _text(
        _insight(
            Category.EARNINGS,
            earnings_growth=-0.2,
            expected_earnings_change=0.3,
        )
    )

    assert "分歧较大" in text


# --------------------------------------------------------------------------
# Catalyst reads priority, not distance
# --------------------------------------------------------------------------


def _event(kind: CatalystEventKind, days: int, **overrides) -> CatalystEvent:
    return CatalystEvent(
        kind=kind,
        occurs_on=_MOMENT.date() + timedelta(days=days),
        source="Test source",
        confirmed=True,
        description=overrides.get("description", ""),
        symbol="NVDA",
    )


def test_every_kind_of_event_has_a_priority() -> None:
    assert set(CATALYST_EVENT_PRIORITY) == set(CatalystEventKind)


def test_a_primary_event_outranks_a_nearer_secondary_one() -> None:
    result = _result(
        (Category.CATALYST,),
        events=(
            _event(CatalystEventKind.FOMC, 2),
            _event(CatalystEventKind.EARNINGS, 40),
        ),
    )

    text = _text(insight_for(result, Category.CATALYST))

    assert "当前最值得关注的是" in text
    assert text.index("财报") < text.index("美联储")


def test_a_minor_event_is_not_offered_as_something_to_watch() -> None:
    result = _result(
        (Category.CATALYST,),
        events=(
            _event(CatalystEventKind.DIVIDEND, 3),
            _event(CatalystEventKind.EARNINGS, 30),
        ),
    )

    text = _text(insight_for(result, Category.CATALYST))

    assert "派息" not in text


def test_the_catalyst_insight_names_what_matters_and_what_follows_it() -> None:
    result = _result(
        (Category.CATALYST,),
        events=(
            _event(CatalystEventKind.EARNINGS, 30),
            _event(CatalystEventKind.FOMC, 12),
        ),
    )

    text = _text(insight_for(result, Category.CATALYST))

    assert "当前最值得关注的是" in text
    assert "其次是" in text


def test_an_empty_calendar_produces_no_insight() -> None:
    result = _result((Category.CATALYST,))

    assert insight_for(result, Category.CATALYST) is None


def test_an_event_beyond_the_window_is_not_written_about() -> None:
    result = _result(
        (Category.CATALYST,), events=(_event(CatalystEventKind.EARNINGS, 300),)
    )

    assert insight_for(result, Category.CATALYST) is None


# --------------------------------------------------------------------------
# Where the insight lives
# --------------------------------------------------------------------------


def test_hpo_has_no_insight_because_it_is_one() -> None:
    result = _result((Category.VALUATION,), market_data=_snapshot(pe=20.0))

    assert insight_for(result, Category.HPO) is None


def test_no_category_writes_more_than_a_reader_will_take_in() -> None:
    result = _result(
        tuple(CATEGORY_ORDER),
        market_data=_snapshot(
            trend_ma20_gap=0.01,
            trend_ma60_gap=0.01,
            trend_ma120_gap=-0.01,
            trend_macd=-0.02,
            beta=2.2,
            risk_volatility=0.6,
            risk_drawdown=-0.5,
            debt_to_equity=180.0,
            current_ratio=0.8,
        ),
    )

    for insight in build_insights(result):
        assert len(insight.lines) <= 3, insight.category
