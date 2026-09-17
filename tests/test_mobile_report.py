"""Tests for the language the mobile report is written in.

What the report is allowed to contain, how long it may be and what has to be on
the first screen are asserted in ``test_report_projection.py``. This module is
about the words: that a reader is given the vocabulary they use rather than the
model's, and that nothing the model thinks in reaches the screen.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from analysis.analysis_result import AnalysisResult
from analysis.insight.builder import build_insights
from analysis.labels import METRIC_NAMES, category_label, decision_label
from analysis.mobile_report import render_mobile_report
from contracts.market_data_provider import (
    MarketDataPoint,
    MarketDataSnapshot,
    MarketMetric,
)
from evaluation.hpo.opportunity_assessor import OpportunityAssessor
from models.asset import Asset
from models.asset_profile import AssetProfile
from models.catalyst_event import CatalystEvent, CatalystEventKind
from models.category import CATEGORY_ORDER, Category
from models.category_rating import CategoryRating
from models.category_score import CategoryScore
from models.coverage import Coverage
from models.decision_state import DecisionState
from models.overall_assessment import OverallAssessment
from models.recommendation import Recommendation

_NOW = datetime(2026, 9, 16, 3, 20, 0, tzinfo=UTC)

_VALUES: dict[str, float] = {
    "pe": 27.3,
    "peg": 0.46,
    "ev_ebitda": 25.3,
    "fcf_yield": 0.022,
    "beta": 2.22,
    "debt_to_equity": 16.97,
    "current_ratio": 4.59,
    "profit_margin": 0.637,
    "return_on_equity": 1.172,
    "free_cash_flow_margin": 0.138,
    "market_direction": 0.149,
    "trend_ma20_gap": 0.03,
    "trend_ma60_gap": 0.02,
    "trend_ma120_gap": 0.01,
    "trend_macd": 0.02,
    "trend_rsi": 61.0,
    "risk_volatility": 0.35,
    "risk_drawdown": -0.25,
    "earnings_growth": 0.271,
    "expected_earnings_change": 0.100,
    "short_percent_of_float": 0.0096,
    "short_ratio": 2.97,
    "institutional_ownership": 0.663,
    "insider_ownership": 0.0165,
    "average_volume": 53_800_000.0,
    "float_shares": 14_600_000_000.0,
}


def _asset() -> Asset:
    return Asset(
        ticker="NVDA",
        name="NVDA",
        exchange="NASDAQ",
        currency="USD",
        profile=AssetProfile.HIGH_GROWTH,
    )


def _snapshot(**values: float) -> MarketDataSnapshot:
    merged = dict(_VALUES)
    merged.update(values)
    return MarketDataSnapshot(
        symbol="NVDA",
        source="Yahoo Finance",
        retrieved_at=_NOW,
        points=tuple(
            MarketDataPoint(
                metric=metric,
                value=merged.get(metric.value),
                reason="test reason",
            )
            for metric in MarketMetric
        ),
    )


def _rating(**overrides) -> CategoryRating:
    settings = {
        "category": Category.TREND,
        "grade": 4,
        "momentum": 0.05,
        "changed_at": _NOW,
        "changed": False,
        "previous_grade": None,
        "reason": "reason",
        "since": _NOW - timedelta(days=6),
        "driver": MarketMetric.TREND_MA20_GAP,
        "driver_from": 0.01,
        "driver_to": 0.02,
    }
    settings.update(overrides)
    return CategoryRating(**settings)


def _result(
    categories: tuple[Category, ...] | None = None,
    *,
    market_data: MarketDataSnapshot | None = None,
    events: tuple[CatalystEvent, ...] = (),
    ratings: tuple[CategoryRating, ...] = (),
    grades: dict[Category, int | None] | None = None,
) -> AnalysisResult:
    judged = categories or tuple(
        category for category in CATEGORY_ORDER if category is not Category.HPO
    )
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
                for category in judged
            ),
        ),
        recommendation=Recommendation(
            decision_state=DecisionState.WATCH,
            confidence=1.0,
            investment_thesis="Placeholder decision.",
            evidence_references=("NVDA.market_data.pe",),
        ),
        market_data=_snapshot() if market_data is None else market_data,
        events=events,
        ratings=ratings,
    )
    chosen = {
        Category.VALUATION: 5,
        Category.TREND: 4,
        Category.RISK: 3,
        Category.CATALYST: 3,
        Category.POSITIONING: 3,
    }
    chosen.update(grades or {})
    result = replace(result, opportunity=OpportunityAssessor().assess(chosen))
    return replace(result, insights=build_insights(result))


def _render(result: AnalysisResult | None = None) -> str:
    return render_mobile_report(result or _result(), generated_at=_NOW)


def _event(kind: CatalystEventKind, days: int, *, confirmed: bool = True):
    return CatalystEvent(
        kind=kind,
        occurs_on=_NOW.date() + timedelta(days=days),
        source="Test source",
        confirmed=confirmed,
        description="",
        symbol="NVDA",
    )


# --------------------------------------------------------------------------
# The reader's language
# --------------------------------------------------------------------------


def test_the_decision_is_written_in_the_readers_language() -> None:
    report = _render()

    assert "结论  观望" in report
    assert DecisionState.WATCH.value not in report
    assert decision_label(DecisionState.WATCH) == "观望"


def test_every_category_is_named_in_the_readers_language() -> None:
    report = _render()

    for category in CATEGORY_ORDER:
        assert category_label(category) in report, category
        assert category.value not in report, category


def test_the_report_carries_the_symbol_and_the_time() -> None:
    lines = _render().splitlines()

    assert lines[0] == "AIS 日报 · NVDA"
    assert "2026-09-16 03:20" in lines[1]
    assert "北京时间" in lines[1]


def test_a_measurement_keeps_the_name_an_investor_reads_elsewhere() -> None:
    # The name is still defined for the evidence and for the expanded report;
    # the phone report simply does not need it once the meaning is written.
    assert METRIC_NAMES[MarketMetric.PE] == "市盈率"


# --------------------------------------------------------------------------
# What the report must never show
# --------------------------------------------------------------------------


def test_the_report_never_shows_a_raw_category_score() -> None:
    report = _render()

    assert "13.10" not in report
    assert "13.1" not in report


def test_the_report_never_shows_how_much_of_a_category_was_assessed() -> None:
    report = _render()

    assert "已评估" not in report
    assert "覆盖" not in report


def test_the_report_never_shows_a_probability_or_a_target() -> None:
    report = _render()

    assert "概率" not in report
    assert "目标价" not in report


def test_the_report_never_shows_a_raw_metric_key() -> None:
    report = _render()

    for metric in MarketMetric:
        assert metric.value not in report, metric


def test_the_report_never_shows_the_models_own_gap_names() -> None:
    report = _render()

    for name in ("业务风险", "估值风险", "证据风险", "长期风险", "价格路径"):
        assert name not in report, name


# --------------------------------------------------------------------------
# What each part says
# --------------------------------------------------------------------------


def test_the_opportunity_is_stated_as_conditions_and_not_as_a_score() -> None:
    report = _render()

    # A sentence is wrapped to fit the screen, so the check is made against what
    # a reader sees once the wrapping is undone.
    flat = "".join(report.split())

    assert "HPO" in report
    assert "当前属于值得优先配置的机会" in flat
    assert "估值具备吸引力" in flat


def test_a_condition_that_could_not_be_judged_is_named() -> None:
    result = _result(grades={Category.CATALYST: None})

    report = _render(result)

    assert "未评估" in report
    assert "有近期催化" in report or "暂无近期催化" in report


def test_a_category_is_explained_rather_than_listed() -> None:
    report = _render()

    assert "趋势结构完好，价格站稳全部均线。" in report
    assert "市盈率" not in report


def test_a_movement_says_how_much_how_long_and_what_moved() -> None:
    report = _render(_result(ratings=(_rating(),)))

    assert "▲5%" in report
    assert "6天" in report
    assert "重新站上 20 日均线" in report


def test_a_movement_that_rounds_to_nothing_is_not_shown() -> None:
    report = _render(_result(ratings=(_rating(momentum=0.0002),)))

    assert "▲0%" not in report
    assert "▼0%" not in report


def test_a_grade_change_is_reported_as_a_change_of_grade() -> None:
    rating = _rating(changed=True, previous_grade=3, grade=4, momentum=0.0)

    assert "趋势 升级" in _render(_result(ratings=(rating,)))


def test_a_downgrade_is_reported_too() -> None:
    rating = _rating(changed=True, previous_grade=4, grade=3, momentum=0.0)

    assert "趋势 降级" in _render(_result(ratings=(rating,)))


def test_the_report_shows_no_stars_for_a_category_with_no_graded_measurement() -> None:
    snapshot = _snapshot(
        **dict.fromkeys((), 0.0),
    )
    thin = MarketDataSnapshot(
        symbol="NVDA",
        source="Yahoo Finance",
        retrieved_at=_NOW,
        points=tuple(
            MarketDataPoint(
                metric=metric,
                value=(1.0 if metric is MarketMetric.TREND_RANGE_POSITION else None),
                reason="test reason",
            )
            for metric in MarketMetric
        ),
    )

    report = _render(_result((Category.MARKET,), market_data=thin))

    assert "暂无评级" in report
    assert snapshot is not None


def test_a_category_nothing_was_judged_for_is_named_at_the_end() -> None:
    report = _render(_result((Category.MARKET,)))

    assert "尚未评估  基本面" in report


def test_the_block_is_left_out_when_every_category_was_judged() -> None:
    report = _render()

    assert "尚未评估" not in report


def test_the_closing_line_names_the_source_and_the_disclaimer() -> None:
    lines = _render().splitlines()

    assert "Yahoo Finance" in lines[-1]
    assert "不构成投资建议" in lines[-1]


def test_the_report_is_deterministic() -> None:
    result = _result(ratings=(_rating(),))

    assert _render(result) == _render(result)


@pytest.mark.parametrize("ticker", ["AAPL", "RKLB", "CGDV"])
def test_the_symbol_reaches_the_title(ticker: str) -> None:
    result = replace(_result(), asset=replace(_asset(), ticker=ticker))

    assert _render(result).splitlines()[0] == f"AIS 日报 · {ticker}"
