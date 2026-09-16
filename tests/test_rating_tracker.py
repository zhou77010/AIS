"""Tests for the rating tracker and the rating model.

A rating says where a category stands and how far it has moved inside that
standing. These tests describe both, and that a grade change starts the
movement again from nothing rather than continuing to accumulate.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.rating_tracker import RatingTracker
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
) -> CategoryRating:
    return tracker.update(
        symbol="NVDA",
        category=Category.TREND,
        grade=grade,
        score=score,
        reason=reason,
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
    tracker.update("NVDA", Category.TREND, 4, 100.0, "a", _FIRST)
    tracker.update("RKLB", Category.TREND, 2, 50.0, "b", _FIRST)

    nvda = tracker.update("NVDA", Category.TREND, 4, 110.0, "a", _LATER)
    rklb = tracker.update("RKLB", Category.TREND, 2, 50.0, "b", _LATER)

    assert nvda.momentum == pytest.approx(0.10)
    assert rklb.momentum == pytest.approx(0.0)


def test_each_category_keeps_its_own_standing() -> None:
    tracker = RatingTracker()
    tracker.update("NVDA", Category.TREND, 4, 100.0, "a", _FIRST)
    tracker.update("NVDA", Category.RISK, 3, 10.0, "b", _FIRST)

    trend = tracker.update("NVDA", Category.TREND, 4, 110.0, "a", _LATER)
    risk = tracker.update("NVDA", Category.RISK, 3, 10.0, "b", _LATER)

    assert trend.momentum == pytest.approx(0.10)
    assert risk.momentum == pytest.approx(0.0)
