"""Tests for the mobile report renderer.

The report is what the user reads on their phone, so these tests describe what
it must say and, just as importantly, what it must never say: model bookkeeping,
raw scores on incomparable scales, or a low grade where nothing was read at all.
"""

from __future__ import annotations

import unicodedata
from datetime import UTC, datetime

from analysis.analysis_result import AnalysisResult
from analysis.labels import METRIC_NAMES, category_label
from analysis.mobile_report import (
    DATA_PREFIX,
    NOT_ASSESSED_PREFIX,
    SECTION_SEPARATOR,
    render_mobile_report,
)
from analysis.report import LIVE_DATA_LABEL
from contracts.market_data_provider import (
    MarketDataPoint,
    MarketDataSnapshot,
    MarketMetric,
)
from models.asset import Asset
from models.asset_profile import AssetProfile
from models.category import CATEGORY_ORDER, Category
from models.category_rating import CategoryRating
from models.category_score import CategoryScore
from models.coverage import Coverage
from models.decision_state import DecisionState
from models.overall_assessment import OverallAssessment
from models.recommendation import Recommendation

_GENERATED_AT = datetime(2026, 9, 16, 3, 20, 0, tzinfo=UTC)
_SOURCE = "Yahoo Finance"
_LINE_WIDTH = 42

_UNITS: dict[Category, int] = {Category.RISK: 8, Category.MARKET: 3, Category.TREND: 3}


def _asset() -> Asset:
    return Asset(
        ticker="NVDA",
        name="NVDA",
        exchange="UNKNOWN",
        currency="USD",
        profile=AssetProfile.UNKNOWN,
    )


def _point(metric: MarketMetric, value: float) -> MarketDataPoint:
    return MarketDataPoint(metric=metric, value=value, reason="test reason")


def _snapshot(**values: float) -> MarketDataSnapshot:
    points = tuple(
        MarketDataPoint(
            metric=metric,
            value=values.get(metric.value),
            reason="test reason",
        )
        for metric in MarketMetric
    )
    return MarketDataSnapshot(
        symbol="NVDA",
        source=_SOURCE,
        retrieved_at=_GENERATED_AT,
        points=points,
    )


def _live(**values: float) -> MarketDataSnapshot:
    """Return a snapshot with a plausible full set of measurements."""
    defaults = {
        "pe": 27.3,
        "peg": 0.46,
        "ev_ebitda": 25.3,
        "fcf_yield": 0.008,
        "beta": 2.22,
        "debt_to_equity": 16.97,
        "current_ratio": 4.59,
        "profit_margin": 0.637,
        "return_on_equity": 1.172,
        "free_cash_flow_margin": 0.138,
        "market_direction": 0.149,
        "trend_range_position": 0.717,
        "trend_direction": 0.246,
        "earnings_growth": 1.259,
        "expected_earnings_change": 0.974,
    }
    defaults.update(values)
    return _snapshot(**defaults)


def _score(category: Category, assessed: int | None = None) -> CategoryScore:
    total = _UNITS.get(category, 5)
    return CategoryScore(
        category=category,
        score=13.10,
        confidence=1.0,
        coverage=Coverage(
            assessed=total if assessed is None else assessed, total=total
        ),
        summary="summary",
        evidence_references=(f"NVDA.market_data.{category.value}",),
    )


def _result(
    categories: tuple[Category, ...] = (Category.VALUATION,),
    market_data: MarketDataSnapshot | None = None,
    assessed: int | None = None,
    ratings: tuple[CategoryRating, ...] = (),
) -> AnalysisResult:
    scores = tuple(
        _score(category, assessed) if assessed is not None else _score(category)
        for category in categories
    )
    return AnalysisResult(
        asset=_asset(),
        assessment=OverallAssessment(
            overall_score=13.10,
            confidence=1.0,
            grade="PLACEHOLDER",
            category_scores=scores,
        ),
        recommendation=Recommendation(
            decision_state=DecisionState.WATCH,
            confidence=1.0,
            investment_thesis="Placeholder decision.",
            evidence_references=("NVDA.market_data.pe",),
        ),
        market_data=_live() if market_data is None else market_data,
        ratings=ratings,
    )


def _rating(
    momentum: float,
    *,
    changed: bool = False,
    previous_grade: int | None = None,
    grade: int = 4,
    changed_at: datetime = _GENERATED_AT,
) -> CategoryRating:
    """Return a rating for the VALUATION category."""
    return CategoryRating(
        category=Category.VALUATION,
        grade=grade,
        momentum=momentum,
        changed_at=changed_at,
        changed=changed,
        previous_grade=previous_grade,
        reason="reason",
    )


def _render(result: AnalysisResult | None = None) -> str:
    return render_mobile_report(result or _result(), generated_at=_GENERATED_AT)


def _width(line: str) -> int:
    return sum(2 if unicodedata.east_asian_width(c) in {"W", "F"} else 1 for c in line)


def _block_for(report: str, category: Category) -> list[str]:
    """Return the lines of one category's block."""
    lines = report.splitlines()
    start = next(
        index
        for index, line in enumerate(lines)
        if line.startswith(category_label(category))
    )
    end = next(
        index
        for index in range(start + 1, len(lines))
        if lines[index] == SECTION_SEPARATOR or not lines[index].startswith(" ")
    )
    return lines[start:end]


# --------------------------------------------------------------------------
# What AIS concluded
# --------------------------------------------------------------------------


def test_report_states_the_decision_in_the_readers_language() -> None:
    report = _render()

    assert "结论  观望" in report
    assert "信心  100%" in report
    assert DecisionState.WATCH.value not in report


def test_report_carries_the_symbol_and_the_time() -> None:
    report = _render()

    assert report.splitlines()[0] == "AIS 日报 · NVDA"
    assert "2026-09-16 03:20" in report


# --------------------------------------------------------------------------
# What each category says
# --------------------------------------------------------------------------


def test_report_grades_each_assessed_category() -> None:
    report = _render(_result((Category.VALUATION, Category.TREND)))

    assert "估值  " in report
    assert "趋势  " in report
    assert "★" in report


def test_report_explains_each_category_in_the_readers_language() -> None:
    report = _render(_result((Category.VALUATION,)))

    assert "市盈率 27.30" in report
    assert category_label(Category.VALUATION) in report


def test_report_names_measurements_as_an_investor_reads_them() -> None:
    for metric in (MarketMetric.PE, MarketMetric.BETA, MarketMetric.PROFIT_MARGIN):
        assert metric.value not in _render(), metric
        assert METRIC_NAMES[metric]


def test_report_shows_movement_inside_a_grade() -> None:
    report = _render(_result(ratings=(_rating(0.05),)))

    block = _block_for(report, Category.VALUATION)

    assert any("▲5%" in line for line in block)


def test_report_shows_a_falling_movement_too() -> None:
    report = _render(_result(ratings=(_rating(-0.03),)))

    assert "▼3%" in report


def test_report_says_when_a_grade_changed_instead_of_showing_movement() -> None:
    rating = _rating(0.0, changed=True, previous_grade=3, grade=4)

    report = _render(_result(ratings=(rating,)))

    assert "（9月16日 升级）" in report
    assert "▲" not in report


def test_report_calls_a_first_rating_a_first_rating() -> None:
    rating = _rating(0.0, changed=True, previous_grade=None, grade=4)

    report = _render(_result(ratings=(rating,)))

    assert "（9月16日 首次评级）" in report


def test_a_movement_that_rounds_to_nothing_is_not_shown() -> None:
    report = _render(_result(ratings=(_rating(0.0002),)))

    assert "▲0%" not in report
    assert "▼0%" not in report


def test_report_omits_movement_when_no_rating_was_taken() -> None:
    report = _render(_result())

    assert "▲" not in report
    assert "▼" not in report
    assert "首次评级" not in report


def test_report_never_shows_a_raw_category_score() -> None:
    # The scores are means of measurements on different scales. Showing one
    # beside another invites a comparison that cannot be made.
    report = _render()

    assert "13.10" not in report
    assert "13.1" not in report


def test_report_never_shows_how_much_of_a_category_was_assessed() -> None:
    # How much of a category was looked at is bookkeeping about the model. A
    # reader is told what was not examined, by name, further down.
    report = _render(_result((Category.RISK,), assessed=3))

    assert "中已评估" not in report
    assert "已完整评估" not in report


def test_report_translates_trend_into_a_sentence_rather_than_numbers() -> None:
    report = _render(_result((Category.TREND,)))

    block = _block_for(report, Category.TREND)

    assert any("整体趋势" in line or "一年" in line for line in block)
    assert not any("52 周区间位置" in line for line in block)
    assert not any("一年涨跌幅" in line for line in block)


def test_report_shows_no_stars_for_a_category_with_no_graded_measurement() -> None:
    # Only the liquidity measurements, which carry no grade.
    snapshot = _snapshot(average_volume=50_000_000.0, float_shares=2_500_000_000.0)

    report = _render(_result((Category.RISK,), market_data=snapshot))

    assert "暂无评级" in report


# --------------------------------------------------------------------------
# What was not looked at
# --------------------------------------------------------------------------


def test_report_names_the_categories_it_did_not_judge() -> None:
    report = _render(_result((Category.VALUATION,)))

    assert NOT_ASSESSED_PREFIX in report
    for category in CATEGORY_ORDER:
        if category is not Category.VALUATION:
            assert category_label(category) in report


def test_report_names_the_parts_of_a_category_it_could_not_assess() -> None:
    report = _render(_result((Category.RISK,), assessed=3))

    assert "事件风险" in report
    assert "长期风险" in report


def test_report_names_a_measurement_it_could_not_retrieve() -> None:
    report = _render(_result((Category.VALUATION,)))

    assert "DCF 公允价值" in report


def test_report_leaves_hpo_unnamed() -> None:
    # The Constitution does not specify what HPO means, so it cannot be
    # translated without inventing a meaning for it.
    report = _render(_result((Category.VALUATION,)))

    assert "HPO" in report
    assert category_label(Category.HPO) == "HPO"


def test_report_omits_the_not_assessed_block_when_nothing_is_outstanding() -> None:
    # Every category judged, and every measurement retrieved.
    complete = _snapshot(**{metric.value: 1.0 for metric in MarketMetric})

    report = _render(_result(tuple(CATEGORY_ORDER), market_data=complete))

    assert NOT_ASSESSED_PREFIX not in report


# --------------------------------------------------------------------------
# Where the figures came from
# --------------------------------------------------------------------------


def test_report_states_the_data_quality() -> None:
    report = _render()

    assert f"{DATA_PREFIX}  {LIVE_DATA_LABEL}" in report
    assert f"来源  {_SOURCE}" in report


def test_report_says_the_scale_is_not_defined() -> None:
    report = _render()

    assert "综合评分刻度尚未定义，" in report
    assert "不构成投资建议。" in report


# --------------------------------------------------------------------------
# Shape
# --------------------------------------------------------------------------


def test_report_keeps_every_line_within_the_readable_width() -> None:
    for line in _render(_result(tuple(CATEGORY_ORDER))).splitlines():
        assert _width(line) <= _LINE_WIDTH, line


def test_report_is_deterministic() -> None:
    assert _render() == _render()
