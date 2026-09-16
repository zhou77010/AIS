"""AIS category rating domain model.

A rating says two things about a category that a grade alone cannot: where it
stands, and how far it has moved inside that standing.

The grade is a position. The momentum is the movement inside the position, not a
price return and not a change of grade: it is how far the category's own
measurement has travelled since the grade last changed. A category can improve
for weeks without crossing into the next grade, and the momentum is what shows
it doing so.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from contracts.market_data_provider import MarketMetric
from models.category import Category


@dataclass(frozen=True)
class CategoryRating:
    """Where a category stands, and how it has moved inside that standing.

    Attributes:
        category: Category the rating is about.
        grade: Position from one to five, as the report shows it.
        momentum: How far the category's own measurement has moved since the
            grade last changed, as a share of what it was at that moment. Zero
            means the grade has just changed, and there is nothing accumulated
            inside it yet.
        changed_at: Moment the grade last changed.
        changed: Whether the grade changed on this reading. A rating that is
            merely accumulating inside its grade has not changed.
        previous_grade: The grade this one replaced, or None when the grade did
            not change on this reading, or when there was no grade before it.
        reason: What the category said when the grade last changed.
        since: Moment the current run of movement began. It is a different
            moment from ``changed_at``: a grade can be set weeks before the
            measurement starts moving, and the movement is what a reader is
            being told the length of.
        driver: The measurement that moved most while the movement accumulated,
            or None when there was no movement.
        driver_from: What that measurement read when the movement began.
        driver_to: What it reads now.
    """

    category: Category
    grade: int
    momentum: float
    changed_at: datetime
    changed: bool
    previous_grade: int | None
    reason: str
    since: datetime
    driver: MarketMetric | None = None
    driver_from: float | None = None
    driver_to: float | None = None

    @property
    def is_accumulating(self) -> bool:
        """Return whether movement is building inside the current grade."""
        return self.momentum != 0.0
