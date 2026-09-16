"""Tests for the rating tracker and the rating model.

A rating says where a category stands and how far it has moved inside that
standing. These tests describe both, and that a grade change starts the
movement again from nothing rather than continuing to accumulate.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.rating_tracker import RatingTracker
from contracts.market_data_provider import MarketMetric
from models.category import Category
from models.category_rating import CategoryRating

_FIRST = datetime(2026, 9, 10, 21, 0, tzinfo=UTC)
_LATER = datetime(2026, 9, 18, 21, 0, tzinfo=UTC)


def _update(
    tracker: RatingTracker,
    grade: int,
    score: float,
    moment: datetime = _FIRST,
    reason: str = "reason",
    measurements: dict[MarketMetric, float] | None = None,
) -> CategoryRating:
    return tracker.update(
        symbol="NVDA",
        category=Category.TREND,
        grade=grade,
        score=score,
        reason=reason,
        measurements=measurements or {},
        moment=moment,
    )


def test_the_first_rating_carries_no_momentum() -> None:
    rating = _update(RatingTracker(), grade=4, score=100.0)

    assert rating.grade == 4
    assert rating.momentum == 0.0
    assert rating.changed is True
    assert rating.previous_grade is None
    assert rating.changed_at == _FIRST
    assert rating.is_accumulating is False


def test_movement_accumulates_while_the_grade_holds() -> None:
    tracker = RatingTracker()
    _update(tracker, grade=4, score=100.0)

    rating = _update(tracker, grade=4, score=105.0, moment=_LATER)

    assert rating.grade == 4
    assert rating.momentum == pytest.approx(0.05)
    assert rating.changed_at == _FIRST
    # No change happened, so nothing may read as one: a grade of four that
    # replaced a grade of four is not a downgrade.
    assert rating.changed is False
    assert rating.previous_grade is None
    assert rating.is_accumulating is True


def test_movement_can_accumulate_in_either_direction() -> None:
    tracker = RatingTracker()
    _update(tracker, grade=4, score=100.0)

    assert _update(tracker, grade=4, score=97.0).momentum == pytest.approx(-0.03)


def test_movement_keeps_accumulating_from_the_score_the_grade_was_set_at() -> None:
    tracker = RatingTracker()
    _update(tracker, grade=4, score=100.0)
    _update(tracker, grade=4, score=103.0)
    _update(tracker, grade=4, score=105.0)

    rating = _update(tracker, grade=4, score=108.0)

    # Measured from the baseline, not from the previous reading.
    assert rating.momentum == pytest.approx(0.08)


def test_a_grade_change_starts_the_movement_again() -> None:
    tracker = RatingTracker()
    _update(tracker, grade=3, score=100.0)
    _update(tracker, grade=3, score=108.0, moment=_LATER)

    rating = _update(tracker, grade=4, score=120.0, moment=_LATER, reason="broke out")

    assert rating.grade == 4
    assert rating.momentum == 0.0
    assert rating.changed is True
    assert rating.previous_grade == 3
    assert rating.changed_at == _LATER
    assert rating.reason == "broke out"


def test_a_downgrade_is_recorded_the_same_way() -> None:
    tracker = RatingTracker()
    _update(tracker, grade=4, score=100.0)

    rating = _update(tracker, grade=2, score=60.0, moment=_LATER)

    assert rating.previous_grade == 4
    assert rating.grade == 2
    assert rating.momentum == 0.0


def test_a_measurement_that_is_not_positive_carries_no_movement() -> None:
    # A category whose measurement is negative is not a quantity a share of it
    # would describe, so no movement is claimed for it.
    tracker = RatingTracker()
    _update(tracker, grade=2, score=-100.0)

    rating = _update(tracker, grade=2, score=-80.0)

    assert rating.momentum == 0.0


def test_each_symbol_keeps_its_own_standing() -> None:
    tracker = RatingTracker()
    tracker.update("NVDA", Category.TREND, 4, 100.0, "a", {}, _FIRST)
    tracker.update("RKLB", Category.TREND, 2, 50.0, "b", {}, _FIRST)

    nvda = tracker.update("NVDA", Category.TREND, 4, 110.0, "a", {}, _LATER)
    rklb = tracker.update("RKLB", Category.TREND, 2, 50.0, "b", {}, _LATER)

    assert nvda.momentum == pytest.approx(0.10)
    assert rklb.momentum == pytest.approx(0.0)


def test_each_category_keeps_its_own_standing() -> None:
    tracker = RatingTracker()
    tracker.update("NVDA", Category.TREND, 4, 100.0, "a", {}, _FIRST)
    tracker.update("NVDA", Category.RISK, 3, 10.0, "b", {}, _FIRST)

    trend = tracker.update("NVDA", Category.TREND, 4, 110.0, "a", {}, _LATER)
    risk = tracker.update("NVDA", Category.RISK, 3, 10.0, "b", {}, _LATER)

    assert trend.momentum == pytest.approx(0.10)
    assert risk.momentum == pytest.approx(0.0)


def test_each_symbol_keeps_its_own_standing_for_every_category() -> None:
    tracker = RatingTracker()
    tracker.update("NVDA", Category.TREND, 4, 100.0, "a", {}, _FIRST)
    tracker.update("RKLB", Category.TREND, 2, 50.0, "b", {}, _FIRST)

    nvda = tracker.update("NVDA", Category.TREND, 4, 110.0, "a", {}, _LATER)
    rklb = tracker.update("RKLB", Category.TREND, 2, 50.0, "b", {}, _LATER)

    assert nvda.momentum == pytest.approx(0.10)
    assert rklb.momentum == pytest.approx(0.0)


# --------------------------------------------------------------------------
# How long a movement has lasted
# --------------------------------------------------------------------------


def test_the_movement_begins_when_the_grade_is_set() -> None:
    rating = _update(RatingTracker(), grade=4, score=100.0)

    assert rating.since == _FIRST


def test_the_movement_keeps_its_start_while_it_continues() -> None:
    tracker = RatingTracker()
    _update(tracker, grade=4, score=100.0)

    rating = _update(tracker, grade=4, score=105.0, moment=_LATER)

    # The length a reader is told is measured from here, not from the last read.
    assert rating.since == _FIRST


def test_the_movement_starts_again_when_it_turns_around() -> None:
    tracker = RatingTracker()
    _update(tracker, grade=4, score=100.0)
    _update(tracker, grade=4, score=103.0)

    rating = _update(tracker, grade=4, score=98.0, moment=_LATER)

    assert rating.since == _LATER


def test_the_movement_starts_again_when_the_grade_changes() -> None:
    tracker = RatingTracker()
    _update(tracker, grade=3, score=100.0)
    _update(tracker, grade=3, score=108.0)

    rating = _update(tracker, grade=4, score=120.0, moment=_LATER)

    assert rating.since == _LATER


# --------------------------------------------------------------------------
# What moved
# --------------------------------------------------------------------------


def test_the_measurement_that_moved_most_is_reported() -> None:
    tracker = RatingTracker()
    _update(
        tracker,
        grade=4,
        score=100.0,
        measurements={
            MarketMetric.TREND_MA20_GAP: 0.010,
            MarketMetric.TREND_RSI: 52.0,
        },
    )

    rating = _update(
        tracker,
        grade=4,
        score=104.0,
        moment=_LATER,
        measurements={
            MarketMetric.TREND_MA20_GAP: 0.020,
            MarketMetric.TREND_RSI: 62.0,
        },
    )

    # The 20 day gap grew by 100%, the index by 19%.
    assert rating.driver is MarketMetric.TREND_MA20_GAP
    assert rating.driver_from == pytest.approx(0.010)
    assert rating.driver_to == pytest.approx(0.020)


def test_no_measurement_is_reported_when_the_grade_has_just_changed() -> None:
    rating = _update(
        RatingTracker(), grade=4, score=100.0, measurements={MarketMetric.PE: 20.0}
    )

    assert rating.driver is None


def test_no_measurement_is_reported_when_nothing_was_measured() -> None:
    tracker = RatingTracker()
    _update(tracker, grade=4, score=100.0)

    rating = _update(tracker, grade=4, score=105.0, moment=_LATER)

    assert rating.driver is None
