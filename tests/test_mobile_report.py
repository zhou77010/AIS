"""Tests for the mobile report renderer (v1.0).

The renderer is the thing the user reads on their phone, so the tests describe
what the message must say and, just as importantly, what it must never say.

Every block of the report answers one of three questions, and the tests are
grouped the same way:

* what AIS concluded,
* why AIS reached it,
* what we know, and what we do not.
"""

from __future__ import annotations

from datetime import UTC, datetime

from analysis.analysis_result import AnalysisResult
from analysis.mobile_report import (
    NOT_EVALUATED,
    PARTIAL_EVIDENCE_NOTICE,
    SECTION_SEPARATOR,
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
from evaluation.risk.risk_dimensions import RiskDimension
from models.asset import Asset
from models.asset_profile import AssetProfile
from models.category import CATEGORY_ORDER, Category
from models.category_score import CategoryScore
from models.coverage import Coverage
from models.decision_state import DecisionState
from models.overall_assessment import OverallAssessment
from models.recommendation import Recommendation

_GENERATED_AT = datetime(2026, 9, 16, 3, 20, 0, tzinfo=UTC)
_SOURCE = "Yahoo Finance"
_THESIS = "Placeholder decision."


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
    """Return a snapshot with four measurements retrieved and DCF unavailable."""
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


def _category_score(category: Category = Category.VALUATION) -> CategoryScore:
    total = len(RiskDimension) if category is Category.RISK else 5
    return CategoryScore(
        category=category,
        score=13.10,
        confidence=1.0,
        coverage=Coverage(assessed=1, total=total),
        summary="summary",
        evidence_references=(f"NVDA.market_data.{category.value}",),
    )


def _result(
    category_scores: tuple[CategoryScore, ...] | None = None,
    market_data: MarketDataSnapshot | None = _LIVE_SNAPSHOT,
    thesis: str = _THESIS,
) -> AnalysisResult:
    """Return an analysis result for the renderer to work on."""
    scores = (_category_score(),) if category_scores is None else category_scores
    assessment = OverallAssessment(
        overall_score=13.10,
        confidence=1.0,
        grade="PLACEHOLDER",
        category_scores=scores,
    )
    recommendation = Recommendation(
        decision_state=DecisionState.WATCH,
        confidence=1.0,
        investment_thesis=thesis,
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


def _unwrapped(report: str) -> str:
    """Return the report as one line, so a phrase can be checked across a wrap."""
    return " ".join(report.split())


# --------------------------------------------------------------------------
# What AIS concluded
# --------------------------------------------------------------------------


def test_report_states_the_symbol_decision_confidence_and_time() -> None:
    report = _render()

    assert "AIS | NVDA | generated 2026-09-16 03:20" in report
    assert "DECISION    WATCH" in report
    assert "CONFIDENCE  1.00" in report


def test_the_conclusion_comes_before_everything_that_supports_it() -> None:
    report = _render()

    assert report.index("DECISION") < report.index("WHY")
    assert report.index("DECISION") < report.index("CATEGORIES")
    assert report.index("DECISION") < report.index("MISSING")


def test_report_leaves_the_score_unevaluated_when_no_category_was_assessed() -> None:
    report = _render(_result(category_scores=(), market_data=_EMPTY_SNAPSHOT))

    assert f"SCORE       {NOT_EVALUATED}" in report
    assert "0.00" not in report


# --------------------------------------------------------------------------
# Why AIS reached it
# --------------------------------------------------------------------------


def test_report_states_the_thesis_under_why() -> None:
    report = _render()

    assert "WHY\n Placeholder decision." in report


def test_the_evidence_sits_under_the_thesis_it_supports() -> None:
    report = _render()

    why = report.index("WHY")
    thesis = report.index(_THESIS)
    evidence = report.index(" Evidence")

    assert why < thesis < evidence


def test_report_states_when_no_thesis_was_given_rather_than_leaving_it_blank() -> None:
    report = _render(_result(thesis="   "))

    assert "No thesis was given for this recommendation." in _unwrapped(report)


def test_report_shows_at_most_three_evidence_lines() -> None:
    report = _render()

    assert "  Trailing P/E 26.80" in report
    assert "  PEG ratio 0.46" in report
    assert "  EV/EBITDA 25.14" in report
    assert "Free cash flow yield" not in report


def test_report_formats_a_ratio_metric_as_a_percentage() -> None:
    snapshot = _snapshot(
        (
            _point(MarketMetric.FCF_YIELD, 0.0082),
            _point(MarketMetric.PE, 26.80),
        )
    )

    report = _render(_result(market_data=snapshot))

    assert "  Free cash flow yield 0.82%" in report


def test_an_evidence_entry_is_a_list_so_a_reason_can_be_added_later() -> None:
    entry = _evidence_entry(_point(MarketMetric.PE, 26.80))

    assert entry == ["  Trailing P/E 26.80"]


# --------------------------------------------------------------------------
# What we know
# --------------------------------------------------------------------------


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


def test_report_marks_categories_without_an_evaluator() -> None:
    report = _render()

    assert " valuation   13.10  conf 1.00" in report
    for category in Category:
        if category is Category.VALUATION:
            continue
        assert f" {category.value:<11} {NOT_EVALUATED}" in report


def _category_block(report: str) -> list[str]:
    """Return the lines of the category block, without its heading."""
    lines = report.splitlines()
    start = lines.index("CATEGORIES") + 1
    end = next(
        index for index in range(start, len(lines)) if lines[index] == SECTION_SEPARATOR
    )
    return lines[start:end]


def _coverage_line_for(report: str, category: Category) -> str:
    """Return the coverage line reported beneath a category."""
    block = _category_block(report)
    index = next(
        position
        for position, line in enumerate(block)
        if line.strip().startswith(category.value)
    )
    return block[index + 1].strip()


def test_report_states_how_much_of_each_assessed_category_was_checked() -> None:
    report = _render()

    assert _coverage_line_for(report, Category.VALUATION) == "1/5 measurements"


def test_report_names_risk_coverage_in_dimensions_rather_than_measurements() -> None:
    scores = (_category_score(Category.RISK),)

    report = _render(_result(category_scores=scores))

    assert _coverage_line_for(report, Category.RISK) == "1/8 dimensions"


def test_an_unevaluated_category_reports_no_coverage() -> None:
    report = _render()
    block = _category_block(report)

    # One line per category, plus one coverage line for the single category that
    # was assessed. A category that was not evaluated reports no coverage.
    assert len(block) == len(Category) + 1
    assert sum(1 for line in block if "NOT EVALUATED" in line) == len(Category) - 1


def test_report_never_renders_an_absent_category_as_zero() -> None:
    report = _render()

    for line in report.splitlines():
        stripped = line.strip()
        if any(stripped.startswith(category.value) for category in Category):
            assert not stripped.endswith("0.00")


def test_report_states_live_market_data() -> None:
    assert f"{LIVE_DATA_LABEL} - {_SOURCE}" in _render()


# --------------------------------------------------------------------------
# What we do not know
# --------------------------------------------------------------------------


def test_report_names_what_is_missing_in_readable_terms() -> None:
    report = _render()

    assert "MISSING" in report
    assert " 8 of 9 categories not evaluated" in report
    assert "Unavailable: DCF fair value" in report


def test_report_names_every_unavailable_measurement_without_truncating() -> None:
    report = _render(_result(market_data=_EMPTY_SNAPSHOT))

    for metric in MarketMetric:
        assert metric.label in _unwrapped(report)


def test_an_unavailable_measurement_name_is_never_split_across_lines() -> None:
    report = _render(_result(market_data=_EMPTY_SNAPSHOT))

    for metric in MarketMetric:
        assert any(metric.label in line for line in report.splitlines()), metric.label


def test_report_states_the_coverage_of_the_figures_it_shows() -> None:
    report = _render()

    assert " 4 of 5 measurements, 1 of 9 categories" in report


def test_report_says_when_it_rests_on_partial_evidence() -> None:
    assert f" {PARTIAL_EVIDENCE_NOTICE}" in _render()


def test_report_omits_the_partial_evidence_notice_when_coverage_is_complete() -> None:
    scores = tuple(_category_score(category) for category in Category)
    complete = _snapshot(tuple(_point(metric, 1.0) for metric in MarketMetric))

    report = _render(_result(category_scores=scores, market_data=complete))

    assert PARTIAL_EVIDENCE_NOTICE not in report
    assert "MISSING\n none" in report


def test_report_states_no_market_data_when_nothing_was_retrieved() -> None:
    report = _render(_result(category_scores=(), market_data=_EMPTY_SNAPSHOT))

    assert f"{NO_DATA_LABEL} - {_SOURCE}" in report
    assert LIVE_DATA_LABEL not in report


def test_report_states_placeholder_data_when_no_source_was_connected() -> None:
    report = _render(_result(category_scores=(), market_data=None))

    assert PLACEHOLDER_DATA_LABEL in report
    assert "no market data source was connected" in report


def test_report_without_market_data_says_so_in_every_section() -> None:
    report = _render(_result(category_scores=(), market_data=None))

    assert "MISSING\n 9 of 9 categories not evaluated" in report
    assert " Evidence\n  none: no market data source was connected" in report


def test_data_quality_label_classifies_every_case() -> None:
    assert data_quality_label(_result()) == LIVE_DATA_LABEL
    assert data_quality_label(_result(market_data=_EMPTY_SNAPSHOT)) == NO_DATA_LABEL
    assert data_quality_label(_result(market_data=None)) == PLACEHOLDER_DATA_LABEL


# --------------------------------------------------------------------------
# Shape
# --------------------------------------------------------------------------


def test_report_shows_evidence_only_for_categories_it_concluded_from() -> None:
    report = _render(_result(market_data=_EMPTY_SNAPSHOT))

    # Nothing was assessed, so nothing explains the recommendation.
    assert " Evidence\n  none: no measurement could be retrieved" in report


def test_report_draws_evidence_from_every_assessed_category() -> None:
    scores = (_category_score(Category.VALUATION), _category_score(Category.RISK))
    snapshot = _snapshot(
        (
            _point(MarketMetric.PE, 26.80),
            _point(MarketMetric.PEG, 0.46),
            _point(MarketMetric.BETA, 1.24),
        )
    )

    report = _render(_result(category_scores=scores, market_data=snapshot))

    assert "  Trailing P/E 26.80" in report
    assert "  Beta 1.24" in report


def test_report_stays_within_the_mobile_length_budget() -> None:
    assert len(_render().splitlines()) <= 34


def test_report_keeps_every_line_within_the_readable_width() -> None:
    for line in _render().splitlines():
        assert len(line) <= 46, line


def test_report_is_plain_text_with_no_markup() -> None:
    report = _render()

    for markup in ("**", "##", "<", ">", "]"):
        assert markup not in report
