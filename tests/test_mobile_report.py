"""Tests for the mobile report renderer (Runtime Sprint 13A).

The renderer is the thing the user reads on their phone, so the tests describe
what the message must say and, just as importantly, what it must never say.
"""

from __future__ import annotations

from datetime import UTC, datetime

from analysis.analysis_result import AnalysisResult
from analysis.mobile_report import (
    NOT_EVALUATED,
    PARTIAL_EVIDENCE_NOTICE,
    _evidence_entry,
    render_mobile_report,
)
from analysis.report import (
    LIVE_DATA_LABEL,
    NO_DATA_LABEL,
    PLACEHOLDER_DATA_LABEL,
    data_quality_label,
)
from contracts.market_data_provider import (
    MarketDataPoint,
    MarketDataSnapshot,
    MarketMetric,
)
from models.asset import Asset
from models.asset_profile import AssetProfile
from models.category import CATEGORY_ORDER, Category
from models.category_score import CategoryScore
from models.decision_state import DecisionState
from models.overall_assessment import OverallAssessment
from models.recommendation import Recommendation

_GENERATED_AT = datetime(2026, 9, 16, 3, 20, 0, tzinfo=UTC)
_SOURCE = "Yahoo Finance"


def _asset() -> Asset:
    return Asset(
        ticker="NVDA",
        name="NVDA",
        exchange="UNKNOWN",
        currency="USD",
        profile=AssetProfile.UNKNOWN,
    )


def _point(metric: MarketMetric, value: float | None) -> MarketDataPoint:
    reason = "retrieved" if value is not None else "not retrieved"
    return MarketDataPoint(metric=metric, value=value, reason=reason)


def _snapshot(points: tuple[MarketDataPoint, ...]) -> MarketDataSnapshot:
    return MarketDataSnapshot(
        symbol="NVDA",
        source=_SOURCE,
        retrieved_at=_GENERATED_AT,
        points=points,
    )


def _live_snapshot() -> MarketDataSnapshot:
    """Return a snapshot with four metrics retrieved and DCF unavailable."""
    return _snapshot(
        (
            _point(MarketMetric.PE, 26.80),
            _point(MarketMetric.PEG, 0.46),
            _point(MarketMetric.EV_EBITDA, 25.14),
            _point(MarketMetric.FCF_YIELD, 0.0082),
            _point(MarketMetric.DCF, None),
        )
    )


def _empty_snapshot() -> MarketDataSnapshot:
    """Return a snapshot where nothing could be retrieved."""
    return _snapshot(tuple(_point(metric, None) for metric in MarketMetric))


# Module level singletons, so that the helpers below can use them as defaults
# without building a snapshot on every call.
_LIVE_SNAPSHOT = _live_snapshot()
_EMPTY_SNAPSHOT = _empty_snapshot()


def _valuation_score(score: float = 13.10) -> CategoryScore:
    return CategoryScore(
        category=Category.VALUATION,
        score=score,
        confidence=1.0,
        summary="summary",
        evidence_references=("NVDA.market_data.pe",),
    )


def _result(
    category_scores: tuple[CategoryScore, ...] | None = None,
    market_data: MarketDataSnapshot | None = _LIVE_SNAPSHOT,
) -> AnalysisResult:
    """Return an analysis result for the renderer to work on."""
    scores = (_valuation_score(),) if category_scores is None else category_scores
    assessment = OverallAssessment(
        overall_score=13.10,
        confidence=1.0,
        grade="PLACEHOLDER",
        category_scores=scores,
    )
    recommendation = Recommendation(
        decision_state=DecisionState.WATCH,
        confidence=1.0,
        investment_thesis="Placeholder decision.",
        evidence_references=("NVDA.market_data.pe",),
    )
    return AnalysisResult(
        asset=_asset(),
        assessment=assessment,
        recommendation=recommendation,
        market_data=market_data,
    )


def _render(result: AnalysisResult | None = None) -> str:
    return render_mobile_report(result or _result(), generated_at=_GENERATED_AT)


# --------------------------------------------------------------------------
# T2 - required content
# --------------------------------------------------------------------------


def test_report_states_the_symbol_decision_confidence_and_time() -> None:
    report = _render()

    assert "AIS | NVDA" in report
    assert "DECISION    WATCH" in report
    assert "CONFIDENCE  1.00" in report
    assert "Generated 2026-09-16 03:20:00" in report


def test_report_states_the_data_coverage() -> None:
    report = _render()

    assert "COVERAGE    1/9 categories, 4/5 inputs" in report


def test_report_lists_every_category_in_the_canonical_order() -> None:
    report = _render()
    lines = report.splitlines()

    positions = [
        next(
            index
            for index, line in enumerate(lines)
            if line.strip().startswith(category.value)
        )
        for category in CATEGORY_ORDER
    ]

    assert positions == sorted(positions)
    for category in CATEGORY_ORDER:
        assert any(line.strip().startswith(category.value) for line in lines)


def test_canonical_category_order_covers_every_category_exactly_once() -> None:
    assert len(CATEGORY_ORDER) == len(Category)
    assert set(CATEGORY_ORDER) == set(Category)


def test_report_orders_the_sections_as_the_reader_needs_them() -> None:
    report = _render()

    assert report.index("CATEGORIES") < report.index("EVIDENCE")
    assert report.index("EVIDENCE") < report.index("DATA        ")
    assert report.index("DATA        ") < report.index("COVERAGE")
    assert report.index("COVERAGE") < report.index("MISSING")


def test_report_puts_the_decision_before_the_evidence_quality() -> None:
    report = _render()

    assert report.index("DECISION") < report.index("SCORE")
    assert report.index("SCORE") < report.index("CATEGORIES")
    assert report.index("SCORE") < report.index("COVERAGE")


def test_report_marks_categories_without_an_evaluator() -> None:
    report = _render()

    assert " valuation   13.10  conf 1.00" in report
    for category in Category:
        if category is Category.VALUATION:
            continue
        assert f" {category.value:<11} {NOT_EVALUATED}" in report


def test_report_never_renders_an_absent_category_as_zero() -> None:
    report = _render()

    for line in report.splitlines():
        stripped = line.strip()
        if any(stripped.startswith(category.value) for category in Category):
            assert not stripped.endswith("0.00")


def test_report_shows_at_most_three_evidence_lines() -> None:
    report = _render()

    assert "EVIDENCE (max 3)" in report
    assert "Trailing P/E 26.80" in report
    assert "PEG ratio 0.46" in report
    assert "EV/EBITDA 25.14" in report
    assert "Free cash flow yield" not in report


def test_report_formats_a_ratio_metric_as_a_percentage() -> None:
    snapshot = _snapshot(
        (
            _point(MarketMetric.FCF_YIELD, 0.0082),
            _point(MarketMetric.PE, 26.80),
        )
    )

    report = _render(_result(market_data=snapshot))

    assert "Free cash flow yield 0.82%" in report


def test_an_evidence_entry_is_a_list_so_a_reason_can_be_added_later() -> None:
    entry = _evidence_entry(_point(MarketMetric.PE, 26.80))

    assert entry == [" Trailing P/E 26.80"]


def test_report_names_the_missing_categories_and_inputs() -> None:
    report = _render()

    assert "MISSING" in report
    assert "categories: 8 of 9 not evaluated" in report
    assert "inputs: dcf" in report


def test_report_says_when_it_rests_on_partial_evidence() -> None:
    report = _render()

    assert report.splitlines()[-1] == f" {PARTIAL_EVIDENCE_NOTICE}"


def test_report_omits_the_partial_evidence_notice_when_coverage_is_complete() -> None:
    scores = tuple(_valuation_score() for _ in Category)
    complete = _snapshot(tuple(_point(metric, 1.0) for metric in MarketMetric))

    report = _render(_result(category_scores=scores, market_data=complete))

    assert PARTIAL_EVIDENCE_NOTICE not in report
    assert report.splitlines()[-1] == " none"


def test_report_stays_within_the_mobile_length_budget() -> None:
    lines = _render().splitlines()

    assert 20 <= len(lines) <= 30


# --------------------------------------------------------------------------
# T3 - the data quality statement
# --------------------------------------------------------------------------


def test_report_states_live_market_data() -> None:
    assert "DATA        LIVE MARKET DATA (Yahoo Finance)" in _render()


def test_report_states_no_market_data_when_nothing_was_retrieved() -> None:
    report = _render(_result(category_scores=(), market_data=_empty_snapshot()))

    assert f"DATA        {NO_DATA_LABEL} ({_SOURCE})" in report
    assert LIVE_DATA_LABEL not in report


def test_report_states_placeholder_data_when_no_source_was_connected() -> None:
    report = _render(_result(category_scores=(), market_data=None))

    assert f"DATA        {PLACEHOLDER_DATA_LABEL}" in report
    assert "no market data source was connected" in report


def test_data_quality_label_classifies_every_case() -> None:
    assert data_quality_label(_result()) == LIVE_DATA_LABEL
    assert data_quality_label(_result(market_data=_empty_snapshot())) == NO_DATA_LABEL
    assert data_quality_label(_result(market_data=None)) == PLACEHOLDER_DATA_LABEL


# --------------------------------------------------------------------------
# An absent measurement is never rendered as a number
# --------------------------------------------------------------------------


def test_report_leaves_the_score_unevaluated_when_no_category_was_assessed() -> None:
    report = _render(_result(category_scores=(), market_data=_empty_snapshot()))

    assert f"SCORE       {NOT_EVALUATED}" in report
    assert "0.00" not in report


def test_report_without_market_data_says_so_in_every_section() -> None:
    report = _render(_result(category_scores=(), market_data=None))

    assert "MISSING\n categories: 9 of 9 not evaluated" in report
    assert "EVIDENCE (max 3)\n none: no market data source was connected" in report
