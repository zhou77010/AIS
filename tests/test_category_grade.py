"""Tests for the star grade.

The grade is a view of the category's reading and nothing more. These tests
describe that it is drawn from the reading layer rather than from a table of its
own, so that the stars beside a sentence cannot disagree with the sentence.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from analysis.analysis_result import AnalysisResult
from analysis.category_grade import (
    MAX_GRADE,
    MIN_GRADE,
    catalyst_days,
    grade_for_category,
    stars,
)
from contracts.market_data_provider import (
    MarketDataPoint,
    MarketDataSnapshot,
    MarketMetric,
)
from models.asset import Asset
from models.asset_profile import AssetProfile
from models.catalyst_event import CatalystEvent, CatalystEventKind
from models.category import Category
from models.category_score import CategoryScore
from models.coverage import Coverage
from models.decision_state import DecisionState
from models.overall_assessment import OverallAssessment
from models.recommendation import Recommendation

_NOW = datetime(2026, 9, 16, 3, 20, 0, tzinfo=UTC)


def _snapshot(**values: float) -> MarketDataSnapshot:
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


def _result(snapshot: MarketDataSnapshot | None, **events: object) -> AnalysisResult:
    return AnalysisResult(
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
            category_scores=(
                CategoryScore(
                    category=Category.VALUATION,
                    score=1.0,
                    confidence=1.0,
                    coverage=Coverage(assessed=1, total=1),
                    summary="summary",
                    evidence_references=("AAPL.market_data.pe",),
                ),
            ),
        ),
        recommendation=Recommendation(
            decision_state=DecisionState.WATCH,
            confidence=1.0,
            investment_thesis="Placeholder.",
            evidence_references=("AAPL.market_data.pe",),
        ),
        market_data=snapshot,
        events=events.get("events", ()),  # type: ignore[arg-type]
    )


def test_the_grade_is_the_mean_of_the_category_readings() -> None:
    # Prices to earnings of 10 reads five and a margin of 0.30 reads five; the
    # valuation category takes only its own measurements.
    result = _result(_snapshot(pe=10.0, peg=0.8, ev_ebitda=6.0))

    assert grade_for_category(result, Category.VALUATION) == 5


def test_a_cheap_multiple_beside_a_negative_cash_flow_is_not_a_five() -> None:
    # The valuation grade is an average, and the cash reading is part of it. A
    # report that showed five stars here would be contradicting its own sentence
    # about the cash flow.
    result = _result(_snapshot(pe=10.0, peg=0.8, ev_ebitda=6.0, fcf_yield=-0.30))

    assert grade_for_category(result, Category.VALUATION) == 4


def test_a_category_with_nothing_read_shows_no_grade() -> None:
    assert grade_for_category(_result(_snapshot()), Category.VALUATION) is None
    assert grade_for_category(_result(None), Category.VALUATION) is None


@pytest.mark.parametrize(
    ("days", "expected"),
    [(1, 5), (7, 5), (8, 4), (30, 4), (31, 3), (90, 3), (91, 2), (180, 2), (181, 1)],
)
def test_the_catalyst_grade_reads_how_near_the_nearest_event_is(
    days: int, expected: int
) -> None:
    event = CatalystEvent(
        kind=CatalystEventKind.EARNINGS,
        occurs_on=_NOW.date() + timedelta(days=days),
        source="Test source",
        confirmed=True,
        description="季度财报",
    )

    result = _result(_snapshot(), events=(event,))

    assert catalyst_days(result) == days
    assert grade_for_category(result, Category.CATALYST) == expected


def test_an_event_that_moves_no_view_does_not_grade_the_catalyst() -> None:
    event = CatalystEvent(
        kind=CatalystEventKind.EX_DIVIDEND,
        occurs_on=_NOW.date() + timedelta(days=2),
        source="Test source",
        confirmed=True,
        description="除息",
    )

    result = _result(_snapshot(), events=(event,))

    assert catalyst_days(result) is None
    assert grade_for_category(result, Category.CATALYST) is None


def test_how_many_events_there_are_does_not_move_the_grade() -> None:
    one = _result(
        _snapshot(),
        events=(
            CatalystEvent(
                kind=CatalystEventKind.EARNINGS,
                occurs_on=_NOW.date() + timedelta(days=20),
                source="s",
                confirmed=True,
                description="d",
            ),
        ),
    )
    many = _result(
        _snapshot(),
        events=tuple(
            CatalystEvent(
                kind=kind,
                occurs_on=_NOW.date() + timedelta(days=days),
                source="s",
                confirmed=True,
                description="d",
            )
            for kind, days in (
                (CatalystEventKind.EARNINGS, 20),
                (CatalystEventKind.FOMC, 40),
                (CatalystEventKind.PRODUCT_LAUNCH, 60),
            )
        ),
    )

    assert grade_for_category(one, Category.CATALYST) == grade_for_category(
        many, Category.CATALYST
    )


@pytest.mark.parametrize(
    ("grade", "expected"),
    [(5, "★★★★★"), (4, "★★★★☆"), (3, "★★★☆☆"), (1, "★☆☆☆☆")],
)
def test_stars_show_the_grade_out_of_five(grade: int, expected: str) -> None:
    assert stars(grade) == expected


def test_stars_never_leave_the_scale() -> None:
    assert stars(0) == "★☆☆☆☆"
    assert stars(9) == "★★★★★"
    assert MIN_GRADE == 1
    assert MAX_GRADE == 5
