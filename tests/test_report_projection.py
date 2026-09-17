"""Tests for the report projection.

The daily report is a projection of one analysis result onto a phone screen. Two
things are asserted here that were previously only described in comments: how
wide a line may be, and how long the report may be. A budget that is not asserted
is a wish, and the report had already grown past its own stated width before
anyone noticed.

The shapes below are the ones AIS actually produces: an asset with everything
measured, an asset with almost nothing measured, an asset whose categories moved,
and an asset with no calendar at all.
"""

from __future__ import annotations

import unicodedata
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from analysis.analysis_result import AnalysisResult
from analysis.insight.builder import build_insights
from analysis.mobile_report import (
    FIRST_SCREEN_LINES,
    LINE_BUDGET,
    LINE_WIDTH,
    NOT_ASSESSED_PREFIX,
    render_mobile_report,
)
from contracts.market_data_provider import (
    MarketDataPoint,
    MarketDataSnapshot,
    MarketMetric,
)
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

# A plausible full set of measurements, taken from a real run.
_FULL: dict[str, float] = {
    "pe": 38.2,
    "peg": 2.67,
    "ev_ebitda": 28.9,
    "fcf_yield": 0.022,
    "beta": 1.08,
    "debt_to_equity": 78.4,
    "current_ratio": 1.0,
    "average_volume": 53_800_000.0,
    "float_shares": 14_600_000_000.0,
    "profit_margin": 0.276,
    "return_on_equity": 1.488,
    "free_cash_flow_margin": 0.231,
    "market_direction": 0.149,
    "trend_range_position": 0.717,
    "trend_direction": 0.246,
    "earnings_growth": 0.271,
    "expected_earnings_change": 0.100,
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


def _width(line: str) -> int:
    return sum(2 if unicodedata.east_asian_width(c) in {"W", "F"} else 1 for c in line)


def _asset() -> Asset:
    return Asset(
        ticker="AAPL",
        name="Apple Inc.",
        exchange="NASDAQ",
        currency="USD",
        profile=AssetProfile.MATURE_TECH,
    )


def _snapshot(**values: float) -> MarketDataSnapshot:
    return MarketDataSnapshot(
        symbol="AAPL",
        source="Yahoo Finance",
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
    categories: tuple[Category, ...] = (),
    *,
    market_data: MarketDataSnapshot | None = None,
    events: tuple[CatalystEvent, ...] = (),
    ratings: tuple[CategoryRating, ...] = (),
) -> AnalysisResult:
    """Return a result with its insights and opportunity built, as a run produces."""
    from evaluation.hpo.opportunity_assessor import OpportunityAssessor

    judged = categories or tuple(
        category for category in CATEGORY_ORDER if category is not Category.HPO
    )
    result = AnalysisResult(
        asset=_asset(),
        assessment=OverallAssessment(
            overall_score=12.34,
            confidence=1.0,
            grade="PLACEHOLDER",
            category_scores=tuple(
                CategoryScore(
                    category=category,
                    score=5.0,
                    confidence=1.0,
                    coverage=Coverage(assessed=1, total=1),
                    summary="summary",
                    evidence_references=(f"AAPL.market_data.{category.value}",),
                )
                for category in judged
            ),
        ),
        recommendation=Recommendation(
            decision_state=DecisionState.WATCH,
            confidence=1.0,
            investment_thesis="Placeholder decision.",
            evidence_references=("AAPL.market_data.pe",),
        ),
        market_data=market_data,
        events=events,
        ratings=ratings,
    )
    grades = {
        Category.VALUATION: 5,
        Category.TREND: 4,
        Category.RISK: 3,
        Category.CATALYST: 3,
        Category.POSITIONING: 3,
    }
    result = replace(result, opportunity=OpportunityAssessor().assess(grades))
    return replace(result, insights=build_insights(result))


def _shape_full() -> AnalysisResult:
    return _result(
        market_data=_snapshot(**_FULL), events=(_event(CatalystEventKind.EARNINGS, 43),)
    )


def _shape_busy() -> AnalysisResult:
    """Every block populated: eight categories, a busy calendar, and movement."""
    ratings = tuple(
        CategoryRating(
            category=category,
            grade=4,
            momentum=0.081,
            changed_at=_NOW,
            changed=False,
            previous_grade=None,
            reason="reason",
            since=_NOW - timedelta(days=12),
        )
        for category in (
            Category.VALUATION,
            Category.TREND,
            Category.RISK,
            Category.CATALYST,
            Category.POSITIONING,
        )
    )
    return _result(
        market_data=_snapshot(**_FULL),
        events=(
            _event(CatalystEventKind.EARNINGS, 43),
            _event(CatalystEventKind.PRODUCT_LAUNCH, 12),
            _event(CatalystEventKind.FOMC, 3),
            _event(CatalystEventKind.LAUNCH_WINDOW, 60),
        ),
        ratings=ratings,
    )


def _shape_thin() -> AnalysisResult:
    """An asset almost nothing is known about, with no calendar."""
    return _result(
        (Category.MARKET,),
        market_data=_snapshot(market_direction=0.149),
    )


def _shape_empty() -> AnalysisResult:
    """No market data and no events at all."""
    return _result((Category.MARKET,))


_SHAPES = {
    "full": _shape_full,
    "busy": _shape_busy,
    "thin": _shape_thin,
    "empty": _shape_empty,
}


def _render(shape: str) -> list[str]:
    return render_mobile_report(_SHAPES[shape](), generated_at=_NOW).splitlines()


# --------------------------------------------------------------------------
# The budgets
# --------------------------------------------------------------------------


@pytest.mark.parametrize("shape", sorted(_SHAPES))
def test_no_line_is_wider_than_the_report_width(shape: str) -> None:
    for line in _render(shape):
        assert _width(line) <= LINE_WIDTH, f"{_width(line)} columns: {line}"


@pytest.mark.parametrize("shape", sorted(_SHAPES))
def test_the_report_stays_inside_its_line_budget(shape: str) -> None:
    lines = _render(shape)

    assert len(lines) <= LINE_BUDGET, "\n".join(lines)


@pytest.mark.parametrize("shape", sorted(_SHAPES))
def test_nothing_is_written_past_the_last_section(shape: str) -> None:
    # A trailing blank line is what a budget that counts the wrong thing looks
    # like: the report reads as one line longer than it is.
    report = render_mobile_report(_SHAPES[shape](), generated_at=_NOW)

    assert not report.endswith("\n")
    assert "\n\n" not in report


# --------------------------------------------------------------------------
# The first screen
# --------------------------------------------------------------------------


def _first_screen(shape: str) -> str:
    return "\n".join(_render(shape)[:FIRST_SCREEN_LINES])


@pytest.mark.parametrize("shape", sorted(_SHAPES))
def test_the_first_screen_names_the_stock(shape: str) -> None:
    assert "AAPL" in _first_screen(shape).splitlines()[0]


@pytest.mark.parametrize("shape", sorted(_SHAPES))
def test_the_first_screen_says_whether_this_is_worth_attention(shape: str) -> None:
    assert "HPO" in _first_screen(shape)


@pytest.mark.parametrize("shape", sorted(_SHAPES))
def test_the_first_screen_says_what_to_do(shape: str) -> None:
    assert "结论" in _first_screen(shape)


def test_the_first_screen_says_what_the_most_important_catalyst_is() -> None:
    screen = _first_screen("busy")

    assert "关注" in screen
    assert "产品发布" in screen, "a primary event outranks a nearer secondary one"


def test_the_first_screen_says_what_changed() -> None:
    screen = _first_screen("busy")

    assert "变化" in screen


def test_the_five_things_are_all_on_the_first_screen() -> None:
    # The whole point of the projection: a reader who stops after one screen has
    # been told what they opened the report to find out.
    lines = _render("busy")[:FIRST_SCREEN_LINES]
    screen = "\n".join(lines)

    assert lines[0].startswith("AIS 日报")
    for marker in ("HPO", "结论", "变化", "关注"):
        assert marker in screen, marker


# --------------------------------------------------------------------------
# What the projection leaves out
# --------------------------------------------------------------------------


def test_the_full_calendar_is_not_printed_as_a_list() -> None:
    lines = _render("busy")
    report = "\n".join(lines)

    # Four events are known and two are shown. There is no grouped list under
    # them repeating what the insight already said, and nothing is counted.
    assert "另有" not in report
    assert sum(line.startswith("关注") for line in lines) == 1
    assert "12 天后 产品发布" in report
    assert "10月29日 公布财报" in report
    assert "美联储议息" not in report, "a secondary event gives way to a primary one"


def test_raw_measurements_are_not_printed_once_they_have_been_interpreted() -> None:
    report = "\n".join(_render("full"))

    assert "市盈率" not in report
    assert "PEG" not in report
    assert "贝塔" not in report
    assert "流通股数" not in report


def test_the_model_gap_names_are_not_printed() -> None:
    report = "\n".join(_render("thin"))

    for name in ("业务风险", "证据风险", "长期风险", "DCF 公允价值"):
        assert name not in report, name


def test_only_whole_categories_are_named_as_not_assessed() -> None:
    lines = _render("thin")
    reported = next(line for line in lines if line.startswith(NOT_ASSESSED_PREFIX))

    assert "基本面" in reported
    assert "风险" in reported


def test_the_provenance_line_names_the_source_and_the_state_of_the_data() -> None:
    report = "\n".join(_render("full"))

    assert "Yahoo Finance" in report
    assert "实时" in report
    assert "不构成投资建议" in report


def test_a_run_without_a_source_says_so_without_naming_one() -> None:
    report = "\n".join(_render("empty"))

    assert "Yahoo Finance" not in report
    assert "不构成投资建议" in report


# --------------------------------------------------------------------------
# What the projection keeps
# --------------------------------------------------------------------------


def test_every_assessed_category_is_shown_with_one_sentence() -> None:
    lines = _render("full")
    report = "\n".join(lines)

    for category in (
        "市场环境",
        "基本面",
        "估值",
        "盈利",
        "趋势",
        "风险",
        "催化因素",
        "仓位",
    ):
        assert category in report, category


def test_a_category_is_shown_as_a_heading_and_one_sentence() -> None:
    lines = _render("full")
    start = next(index for index, line in enumerate(lines) if line.startswith("估值"))

    assert lines[start].startswith("估值  ")
    assert "★" in lines[start] or "暂无评级" in lines[start]
    assert lines[start + 1].startswith(" ")


def test_only_the_first_sentence_of_a_category_reaches_the_phone() -> None:
    # The rest are still in the model; the phone gets the headline.
    result = _shape_full()
    report = render_mobile_report(result, generated_at=_NOW)

    for insight in result.insights:
        for line in insight.lines[1:]:
            assert line.text not in report, line.text


def test_a_category_with_nothing_to_say_says_so_rather_than_showing_measurements() -> (
    None
):
    lines = _render("empty")
    report = "\n".join(lines)

    assert "近期暂无明确催化。" in report


def test_the_report_never_shows_a_category_score() -> None:
    report = "\n".join(_render("full"))

    assert "5.0" not in report
    assert "12.34" not in report


def test_a_first_rating_is_not_reported_as_a_change() -> None:
    # Being rated for the first time is the state of the tracker, not a change
    # in the asset, and one line per category for it would fill the report.
    rating = CategoryRating(
        category=Category.TREND,
        grade=4,
        momentum=0.0,
        changed_at=_NOW,
        changed=True,
        previous_grade=None,
        reason="reason",
        since=_NOW,
    )

    report = "\n".join(
        _render_shape(_result(market_data=_snapshot(**_FULL), ratings=(rating,)))
    )

    assert "变化" not in report
    assert "首次评级" not in report


def _render_shape(result: AnalysisResult) -> list[str]:
    """Render one result, for the shapes a fixture cannot express."""
    return render_mobile_report(result, generated_at=_NOW).splitlines()
