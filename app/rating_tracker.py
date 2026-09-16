"""Tracking where each category stood, so its movement can be measured.

A grade says where a category stands today. It cannot say whether it got there
by climbing or by arriving all at once, and it cannot show a category improving
for weeks without yet crossing into the next grade. That needs the previous
reading, which is what this holds.

The tracker is memory only, like the notification change detector. A restart
begins again: the first rating a category is given after a restart carries no
momentum, because there is nothing to have accumulated from, and inventing a
baseline would put a movement in the report that never happened.

Nothing here judges. The grade is decided elsewhere and handed in; the tracker
only remembers it and measures how far the measurement has travelled since.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from models.category import Category
from models.category_rating import CategoryRating


@dataclass
class _Standing:
    """Where a category stood when its grade was last set."""

    grade: int
    score: float
    changed_at: datetime
    reason: str


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
        moment: datetime,
    ) -> CategoryRating:
        """Record where a category stands and return its rating.

        When the grade has changed, the momentum starts again from zero and the
        moment, the previous grade and the reason are all refreshed. When it has
        not, the momentum carries on accumulating from the score the grade was
        set at.

        Args:
            symbol: Symbol the category belongs to.
            category: Category being rated.
            grade: Position the category now stands at, from one to five.
            score: The category's own measurement, which the momentum follows.
            reason: What the category says about itself now.
            moment: Moment the reading was taken.

        Returns:
            The rating for this reading.
        """
        key = (symbol, category)
        previous = self._standings.get(key)

        if previous is None or previous.grade != grade:
            self._standings[key] = _Standing(grade, score, moment, reason)
            return CategoryRating(
                category=category,
                grade=grade,
                momentum=0.0,
                changed_at=moment,
                changed=True,
                previous_grade=None if previous is None else previous.grade,
                reason=reason,
            )

        return CategoryRating(
            category=category,
            grade=grade,
            momentum=_momentum(previous.score, score),
            changed_at=previous.changed_at,
            changed=False,
            previous_grade=None,
            reason=previous.reason,
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
