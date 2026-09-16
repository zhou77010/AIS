"""Tracking where each category stood, so its movement can be measured.

A grade says where a category stands today. It cannot say whether it got there
by climbing or by arriving all at once, and it cannot show a category improving
for weeks without yet crossing into the next grade. That needs the previous
reading, which is what this holds.

Three things are remembered for each category of each symbol: the score its
grade was set at, the moment the current run of movement began, and what every
measurement read at that moment. The last of those is what lets the report say
*why* a category is moving rather than only that it is.

The tracker is memory only, like the notification change detector. A restart
begins again: the first rating a category is given after a restart carries no
movement, because there is nothing to have accumulated from, and inventing a
baseline would put a movement in the report that never happened.

Nothing here judges. The grade is decided elsewhere and handed in; the tracker
only remembers it and measures how far the measurement has travelled since.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime

from contracts.market_data_provider import MarketMetric
from models.category import Category
from models.category_rating import CategoryRating


@dataclass
class _Standing:
    """Where a category stood when its grade was last set."""

    grade: int
    score: float
    changed_at: datetime
    reason: str
    since: datetime
    direction: int
    measurements: dict[MarketMetric, float] = field(default_factory=dict)


class RatingTracker:
    """Remembers the standing of every category of every symbol it has seen."""

    def __init__(self) -> None:
        """Create a tracker that has seen nothing yet."""
        self._standings: dict[tuple[str, Category], _Standing] = {}

    def update(
        self,
        symbol: str,
        category: Category,
        grade: int,
        score: float,
        reason: str,
        measurements: Mapping[MarketMetric, float],
        moment: datetime,
    ) -> CategoryRating:
        """Record where a category stands and return its rating.

        When the grade has changed, the movement starts again from zero and
        everything is refreshed. When it has not, the movement carries on
        accumulating from the score the grade was set at, and the moment the
        current run began is kept so the report can say how long it has lasted.

        Args:
            symbol: Symbol the category belongs to.
            category: Category being rated.
            grade: Position the category now stands at, from one to five.
            score: The category's own measurement, which the movement follows.
            reason: What the category says about itself now.
            measurements: What the category's measurements read now.
            moment: Moment the reading was taken.

        Returns:
            The rating for this reading.
        """
        key = (symbol, category)
        previous = self._standings.get(key)
        readings = dict(measurements)

        if previous is None or previous.grade != grade:
            self._standings[key] = _Standing(
                grade=grade,
                score=score,
                changed_at=moment,
                reason=reason,
                since=moment,
                direction=0,
                measurements=readings,
            )
            return CategoryRating(
                category=category,
                grade=grade,
                momentum=0.0,
                changed_at=moment,
                changed=True,
                previous_grade=None if previous is None else previous.grade,
                reason=reason,
                since=moment,
            )

        momentum = _momentum(previous.score, score)
        direction = _direction_of(momentum)
        if direction != 0 and previous.direction not in {0, direction}:
            # The measurement turned around, so the run the reader is being told
            # the length of starts here rather than at the grade change. A run
            # that only now starts moving is not a turn: nothing had been moving
            # before it, so the length it has lasted is still the whole standing.
            previous.since = moment
            previous.measurements = readings
        if direction != 0:
            previous.direction = direction

        driver, driver_from, driver_to = _dominant_mover(
            previous.measurements, readings
        )
        return CategoryRating(
            category=category,
            grade=grade,
            momentum=momentum,
            changed_at=previous.changed_at,
            changed=False,
            previous_grade=None,
            reason=previous.reason,
            since=previous.since,
            driver=driver,
            driver_from=driver_from,
            driver_to=driver_to,
        )


def _momentum(baseline: float, score: float) -> float:
    """Return how far a measurement has moved from the score a grade was set at.

    A baseline that is not positive carries no meaningful comparison: the
    measurement is not a quantity that a share of it would describe. That case
    reports no movement rather than a share of a negative number.
    """
    if baseline <= 0:
        return 0.0
    return score / baseline - 1.0


def _direction_of(momentum: float) -> int:
    """Return the way the measurement is going, or zero when it is still."""
    if momentum > 0:
        return 1
    if momentum < 0:
        return -1
    return 0


def _dominant_mover(
    baseline: Mapping[MarketMetric, float],
    current: Mapping[MarketMetric, float],
) -> tuple[MarketMetric | None, float | None, float | None]:
    """Return the measurement that moved most while the movement accumulated.

    Attribution is by size, because how much each measurement contributed to a
    judgement is a method AIS has not defined. The largest movement is the best
    available answer to "what changed", and it is an answer about the evidence
    rather than a summary of the whole category.
    """
    best: tuple[MarketMetric | None, float | None, float | None] = (None, None, None)
    largest = 0.0
    for metric, was in baseline.items():
        now = current.get(metric)
        if now is None or was == 0:
            continue
        change = abs(now / was - 1.0)
        if change > largest:
            largest = change
            best = (metric, was, now)
    return best
